-- Iron Court campaign model. Keep localisation calls in the UI draw path;
-- calling them from a turn handler can crash turn 1 even inside pcall.
-- Constants with DB or UI counterparts are checked by the generator and importer.

IC = IC or {}

IC.ORIGINS = {
    {slug = "khorakk",    faction = "cr_chd_house_of_khorakk"},
    {slug = "uzkulak",    faction = "cr_chd_warfleet_of_uzkulak"},
    {slug = "artificers", faction = "cr_chd_snakebeards_artificers"},
    {slug = "fists",      faction = "cr_chd_fists_of_hashut"},
    {slug = "horns",      faction = "cr_chd_horns_of_hashut"},
    {slug = "baal",       faction = "cr_chd_house_of_baal"},
    {slug = "azeros",     faction = "cr_chd_house_of_azeros"},
    {slug = "bzaark",     faction = "cr_chd_house_of_bzaark"},
    {slug = "blackdwarf", faction = "cr_chd_slaves_of_the_black_dwarf"},
    {slug = "kraken",     faction = "cr_chd_black_kraken_armada"},
    {slug = "conclave",   faction = "wh3_dlc23_chd_conclave"},
    {slug = "astragoth",  faction = "wh3_dlc23_chd_astragoth"},
    {slug = "azgorh",     faction = "wh3_dlc23_chd_legion_of_azgorh"},
    {slug = "zhatan",     faction = "wh3_dlc23_chd_zhatan"},
    {slug = "skullstack", faction = "cr_chd_skullstack"},
    {slug = "zharrduk",   faction = "wh3_dlc23_chd_minor_faction"},
    {slug = "zharr"},
    {slug = "plain"},
    {slug = "gorgoth"},
    {slug = "stump"},
    {slug = "zornuzkul"},
    {slug = "gash"},
    {slug = "mines"},
    {slug = "wastes"},
}

IC.PARTIES = {
    "crown", "temple", "forge", "chain", "legion",
    "ledger", "tower", "road", "hearth",
}

IC.CROWN = "crown"

IC.CONTROL = {
    {slug = "grip",      floor = 75},
    {slug = "mastery",   floor = 60},
    {slug = "command",   floor = 40},
    {slug = "contested", floor = 10},
    {slug = "lost",      floor = 0},
}

IC.REBEL_POOL = {
    "wh3_dlc23_chd_chaos_dwarfs_qb1",
    "wh3_dlc23_chd_chaos_dwarfs_qb2",
    "wh3_dlc23_chd_chaos_dwarfs_qb3",
    "wh3_dlc25_chd_chaos_dwarfs_invasion",
}

-- cm:get_faction returns false for missing factions. Prefer a dormant faction;
-- crowning a general over a live faction can crash the campaign.
-- Confederated houses rise under their own banner when possible, never the player's.
function IC.rebel_faction_for(faction_key, slug)
    local own = IC.faction_for_origin(slug)
    if own and own ~= faction_key then
        local ok, f = pcall(function() return cm:get_faction(own) end)
        if ok and f and f ~= false then
            local dead = false
            pcall(function() dead = f:is_dead() end)
            return own, dead
        end
    end
    return IC.rebel_faction(faction_key)
end

function IC.rebel_rename(rebels, name)
    if not rebels or not name or name == "" then return false end
    pcall(function() cm:change_custom_faction_name(rebels, name) end)
    cm:set_saved_value("derpy_ic_risen_" .. rebels, name)
    return true
end

function IC.rebel_rename_all()
    local keys = {}
    for _, rk in ipairs(IC.RACE_ORDER) do
        local R = IC.RACES[rk]
        for i = 1, #R.REBEL_POOL do keys[#keys + 1] = R.REBEL_POOL[i] end
        for i = 1, #R.ORIGINS do
            if R.ORIGINS[i].faction then keys[#keys + 1] = R.ORIGINS[i].faction end
        end
    end
    for i = 1, #keys do
        local name = cm:get_saved_value("derpy_ic_risen_" .. keys[i])
        if name and name ~= "" then
            pcall(function() cm:change_custom_faction_name(keys[i], name) end)
        end
    end
end

-- `exclude` is the seceding court's own faction. A RISING RUNS A COURT TOO - it
-- is a faction of the court's race - so with the pool full its parties secede as well,
-- and the first living key could be itself: war on itself, provinces handed to
-- itself.
-- A FULL POOL WAKES A DEAD HOUSE. Joining a running rising is the last resort:
-- a house faction from IC.ORIGINS that has died or been confederated away is
-- still on the map, the same revival a house rising under its own banner uses,
-- and its name is put back on load by IC.rebel_rename_all. It flies that house's
-- crest (there is no runtime crest setter), so it comes after the pool's own four.
function IC.rebel_faction(exclude)
    local R = IC.R(exclude)
    local fallback = nil
    local function dead_one(key)
        local ok, f = pcall(function() return cm:get_faction(key) end)
        if not ok or not f or f == false then return false end
        if key ~= exclude then fallback = fallback or key end
        local dead = false
        pcall(function() dead = f:is_dead() end)
        return dead
    end
    for i = 1, #R.REBEL_POOL do
        if dead_one(R.REBEL_POOL[i]) then return R.REBEL_POOL[i], true end
    end
    local joined = fallback
    for i = 1, #R.ORIGINS do
        local key = R.ORIGINS[i].faction
        if key and key ~= exclude and dead_one(key) then return key, true end
    end
    return joined, false
end

IC.REBEL_LORD = "wh3_dlc23_chd_overseer"

-- WHAT A RISING'S AI WANTS: aggression. The pool's qb factions keep the passive
-- personality their startpos gave them and sit on what they take. This is the
-- row CA's Will of
-- Hashut crisis forces on its own invading Chaos Dwarfs: the aggressive
-- strategic component and the endgame task generators.
IC.REBEL_PERSONALITY = "wh3_combi_chaos_dwarf_endgame"

IC.REBEL_GENERALS = {
    ["wh3_dlc23_chd_lord_convoy_overseer"] = true,
    ["wh3_dlc23_chd_overseer"] = true,
    ["wh3_dlc23_chd_overseer_hobgoblin_spawned_army"] = true,
    ["wh3_dlc23_chd_sorcerer_prophet_death"] = true,
    ["wh3_dlc23_chd_sorcerer_prophet_fire"] = true,
    ["wh3_dlc23_chd_sorcerer_prophet_hashut"] = true,
    ["wh3_dlc23_chd_sorcerer_prophet_metal"] = true,
}
-- A REBEL ARMY IS A HASHUT ARMY. The keys and their weights are CA's own Will of
-- Hashut crisis (campaign/main_warhammer/crisis/crisis_will_of_hashut.lua,
-- unit_list); that crisis rolls all nineteen from one bag, so an army can come
-- out all hobgoblins. Here each slot is rolled from its ROLE, in the order the
-- draft lists them, so the first N slots are a balanced army for any N, which
-- is what fills out a lord who left with half a stack. The crisis fields only one war
-- machine (the Dreadquake Iron Daemon); the other four are the Tower's own,
-- weighted like it. gen_iron_court --check holds every key to main_units.
IC.REBEL_POOLS = {
    line = {
        {"wh3_dlc23_chd_inf_chaos_dwarf_warriors", 8},
        {"wh3_dlc23_chd_inf_chaos_dwarf_warriors_great_weapons", 6},
        {"wh3_dlc23_chd_inf_infernal_guard", 4},
        {"wh3_dlc23_chd_inf_infernal_guard_great_weapons", 4},
        {"wh3_dlc23_chd_inf_infernal_ironsworn", 3},
    },
    missile = {
        {"wh3_dlc23_chd_inf_chaos_dwarf_blunderbusses", 5},
        {"wh3_dlc23_chd_inf_infernal_guard_fireglaives", 4},
        {"wh3_dlc23_chd_inf_hobgoblin_archers", 6},
    },
    screen = {
        {"wh3_dlc23_chd_inf_hobgoblin_cutthroats", 6},
        {"wh3_dlc23_chd_inf_hobgoblin_sneaky_gits", 6},
    },
    cavalry = {
        {"wh3_dlc23_chd_cav_hobgoblin_wolf_raiders_spears", 5},
        {"wh3_dlc23_chd_cav_hobgoblin_wolf_raiders_bows", 5},
        {"wh3_dlc23_chd_cav_bull_centaurs_axe", 3},
        {"wh3_dlc23_chd_cav_bull_centaurs_dual_axe", 3},
        {"wh3_dlc23_chd_cav_bull_centaurs_greatweapons", 3},
    },
    monster = {
        {"wh3_dlc23_chd_mon_great_taurus", 3},
        {"wh3_dlc23_chd_mon_bale_taurus", 2},
        {"wh3_dlc23_chd_mon_lammasu", 2},
        {"wh3_dlc23_chd_mon_kdaai_fireborn", 3},
        {"wh3_dlc23_chd_mon_kdaai_destroyer", 2},
    },
    war_machine = {
        {"wh3_dlc23_chd_veh_iron_daemon_1dreadquake", 2},
        {"wh3_dlc23_chd_veh_magma_cannon", 2},
        {"wh3_dlc23_chd_veh_deathshrieker_rocket_launcher", 2},
        {"wh3_dlc23_chd_veh_dreadquake_mortar", 2},
        {"wh3_main_chd_art_hobgob_bolt_thrower", 2},
    },
}
-- Nineteen slots: six of line, four missile, three horse, two each of screen,
-- beasts and guns. Interleaved so any prefix of it is a balanced army.
IC.REBEL_DRAFT = {
    "line", "missile", "line", "cavalry", "line", "monster", "missile",
    "war_machine", "line", "screen", "cavalry", "line", "missile", "monster",
    "war_machine", "line", "cavalry", "missile", "screen",
}
-- No more than this many of one unit from the draft.
IC.REBEL_UNIT_CAP = 2

-- CA's `out` is a callable table, not a function. Keep the call isolated from turns.
-- IC.warn is a FAILURE and is always written. IC.say is the routine log, and the
-- detailed_log setting silences it - so a caught error must never go through it.
function IC.warn(text)
    if out then pcall(function() out(tostring(text)) end) end
end

function IC.say(text)
    if IC.TUNE and IC.TUNE.detailed_log == false then return end
    IC.warn(text)
end

IC.BACKGROUNDS = {
    crown  = {"household", "blood", "sworn"},
    temple = {"acolyte", "ashpriest", "taurukh"},
    forge  = {"daemonsmith", "gunnery", "furnace"},
    chain  = {"overseer", "driver", "wrangler"},
    legion = {"immortal", "infernal", "siege"},
    ledger = {"broker", "tribute", "harbour"},
    tower  = {"apprentice", "clerk", "omens"},
    road   = {"caravan", "roadwarden", "pathfinder"},
    hearth = {"ashfarmer", "kiln", "elder"},
}

IC.NOT_DWARF = {
    ["wh3_dlc23_chd_gorduz_backstabber"] = true,
}

IC.LORD_HISTORY = {
    -- `leads` names the lord's faction, not his origin.
    derpy_abnagg     = {origin = "uzkulak",    bg = "harbour",
                        leads = "cr_chd_warfleet_of_uzkulak"},
    derpy_azeros     = {origin = "azeros",     bg = "furnace",
                        leads = "cr_chd_house_of_azeros"},
    derpy_balur      = {origin = "fists",      bg = "infernal",
                        leads = "cr_chd_fists_of_hashut"},
    derpy_black_dwf  = {origin = "blackdwarf", bg = "immortal",
                        leads = "cr_chd_slaves_of_the_black_dwarf"},
    derpy_bzaark     = {origin = "bzaark",     bg = "siege",
                        leads = "cr_chd_house_of_bzaark"},
    derpy_gargath    = {origin = "baal",       bg = "daemonsmith",
                        leads = "cr_chd_house_of_baal"},
    derpy_ghorth     = {origin = "conclave",   bg = "ashpriest",
                        leads = "wh3_dlc23_chd_conclave"},
    derpy_snakebeard = {origin = "artificers", bg = "daemonsmith",
                        leads = "cr_chd_snakebeards_artificers"},
    derpy_tordrek    = {origin = "kraken",     bg = "gunnery",
                        leads = "cr_chd_black_kraken_armada"},
    derpy_urzkhal    = {origin = "khorakk",    bg = "driver",
                        leads = "cr_chd_house_of_khorakk"},
    derpy_vraznak    = {origin = "horns",      bg = "taurukh",
                        leads = "cr_chd_horns_of_hashut"},
    derpy_gordak     = {origin = "uzkulak",    bg = "wrangler"},
    derpy_warrhak    = {origin = "khorakk",    bg = "omens"},
    wh3_dlc23_chd_astragoth = {origin = "astragoth", bg = "ashpriest",
                               leads = "wh3_dlc23_chd_astragoth"},
    wh3_dlc23_chd_drazhoath = {origin = "azgorh",    bg = "daemonsmith",
                               leads = "wh3_dlc23_chd_legion_of_azgorh"},
    wh3_dlc23_chd_zhatan    = {origin = "zhatan",    bg = "immortal",
                               leads = "wh3_dlc23_chd_zhatan"},
    wh3_dlc23_chd_gorduz_backstabber = {origin = "zornuzkul", bg = "wrangler"},
}


-- Always "<Head> of <tail>": a tail-first shape read as a mercenary band
-- ("Ninth Stair Company"). Only Chaos Dwarf factions hold a court, so the words
-- are theirs. A head must not repeat a word of any tail ("Hand of the Branded
-- Hand"), and head + " of " + tail stays within 30 characters.
IC.NAME_HEADS = {
    "Cult", "Covenant", "Conclave", "Sons", "Chosen",
    "Keepers", "Circle", "Kin",
}

IC.NAME_TAILS = {
    crown  = {"the Throne"},
    temple = {"the Burning Bull", "the Black Altar", "Hashut's Breath",
              "the Ashen Word", "the Bull's Horn", "the Brazen Idol"},
    forge  = {"the Hell-Forge", "the Cold Anvil", "the Iron Oath",
              "the Bound Flame", "the Daemon Anvil", "the Ninth Furnace"},
    chain  = {"the Short Chain", "the Iron Collar", "the Deep Pits",
              "the Brand", "the Bound Hundred", "the Lash"},
    legion = {"the Black Standard", "the Second Wall", "the Unbroken Rank",
              "the Iron Muster", "the Fireglaive", "the Bull Banner"},
    ledger = {"the Black Ledger", "the Blood Price", "the Weighed Coin",
              "the Sealed Bond", "the Iron Tally", "the Tithe"},
    tower  = {"the Great Ziggurat", "the Sealed Word", "the Bound Daemon",
              "the Obsidian Eye", "the Stone Tongue", "the Lammasu"},
    road   = {"the Ash Road", "the Salt Track", "the Howling Wastes",
              "the Black Caravan", "the Iron Wheel", "Gash Kadrak"},
    hearth = {"the Old Ash", "the Banked Fire", "the First Hold",
              "Zharr-Naggrund", "Mingol Zharr", "the Home Kilns"},
}

IC.PARTY_TRAITS = {
    {key = "proud", name = "Proud",
     blurb = "No reward ever satisfies them.",
     rule = "-1 a turn",
     n = function() return -1 end},
    {key = "patient", name = "Patient",
     blurb = "They have waited before. They can wait again.",
     rule = "+1 a turn",
     n = function() return 1 end},
    {key = "grasping", name = "Grasping",
     blurb = "They demand land and resent every province denied them.",
     rule = "+1 while they govern a province, -2 when they do not",
     n = function(ctx) return ctx.govs > 0 and 1 or -2 end},
    {key = "zealots", name = "Zealots of Hashut",
     blurb = "They serve strength. A weak Crown earns only contempt.",
     rule = "+1 while the Crown holds half the court, -2 below it",
     n = function(ctx) return ctx.control >= 50 and 1 or -2 end},
    {key = "ambitious", name = "Ambitious",
     blurb = "Every office leaves them wanting another.",
     rule = "0 with no seat, -1 with one, -2 with two or more",
     n = function(ctx) return -math.min(ctx.held, 2) end},
    {key = "dutiful", name = "Dutiful",
     blurb = "They serve where ordered and ask for little.",
     rule = "+2 with no seat, +1 with any",
     n = function(ctx) return ctx.held == 0 and 2 or 1 end},
    {key = "traditionalists", name = "Traditionalists",
     blurb = "Their ancestral office belongs in their own hands.",
     rule = "+1, or -2 while an outsider holds their seat",
     n = function(ctx) return ctx.snubbed and -2 or 1 end},
    {key = "venal", name = "Venal",
     blurb = "Gold is the only argument they respect.",
     rule = "+2 while secured, -1 otherwise",
     n = function(ctx) return ctx.sworn > 0 and 2 or -1 end},
}

IC.LEADER_TRAITS = {
    {key = "thirst", name = "Thirst for Power",
     blurb = "He wants the Tower. He says so openly."},
    {key = "schemer", name = "Schemer",
     blurb = "Every promise hides another bargain."},
    {key = "brute", name = "Brute",
     blurb = "He settles disputes with threats and iron."},
    {key = "steady", name = "Steady",
     blurb = "Threats do not move him. Flattery fares no better."},
    {key = "shrewd", name = "Shrewd",
     blurb = "He spots a profit before anyone else."},
    {key = "faithful", name = "Hashut's Own",
     blurb = "The Father of Darkness set the Crown where it is. That settles it."},
}

IC.LEADER_TRAIT_N = {thirst = -2, schemer = -1, brute = -1,
                     steady = 1, shrewd = 1, faithful = 2}

function IC.trait_rule(trait)
    if not trait then return nil end
    if trait.rule then return trait.rule end
    local n = IC.LEADER_TRAIT_N[trait.key]
    if not n then return nil end
    return string.format("%s%d a turn while he leads them",
                         n > 0 and "+" or "", n)
end

IC.OFFICES = {
    {slug = "priest",    affinity = "temple",    tier = 1},
    {slug = "forge",     affinity = "forge",     tier = 1},

    {slug = "ledger",    affinity = "ledger",    tier = 2},
    {slug = "warden",    affinity = "legion",    tier = 2},
    {slug = "hand",      affinity = "tower",     tier = 2},

    {slug = "chains",    affinity = "chain",     tier = 3},
    {slug = "pits",      affinity = "chain",     tier = 3},
    {slug = "quarry",    affinity = "forge",     tier = 3},
    {slug = "roads",     affinity = "road",      tier = 3},

    {slug = "kilns",     affinity = "hearth",    tier = 4},
    {slug = "fields",    affinity = "hearth",    tier = 4},
    {slug = "scribes",   affinity = "tower",     tier = 4},
    {slug = "muster",    affinity = "legion",    tier = 4},
    {slug = "banners",   affinity = "legion",    tier = 4},
}

IC.CHD_SUBCULTURE = "wh3_dlc23_sc_chd_chaos_dwarfs"
IC.MILITARY_DOCTRINE = "wh3_dlc23_edict_chd_armaments"

IC.TUNE = {
    tier_rank           = {30, 20, 12, 5},


    tier_influence      = {400, 300, 200, 100},
    tier_income         = {20, 15, 10, 5},
    governor_income     = 5,
    -- Set so seats fill: at a lower trickle a turn-32 save had 2 of 14 seats
    -- filled and 12 of 24 men at 0 influence. The bars are the player's only.
    influence_trickle   = 5,
    influence_trickle_general = 0,
    -- TEN, NOT FIVE: every end is a free chance to re-seat, and at five a full
    -- court had three seats to refill every turn.
    term_turns          = 10,
    -- A man whose term ended takes the same seat again only this many turns
    -- later, and without loyalty_appointed.
    renew_wait          = 3,

    battle_influence    = {
        heroic_victory   = 50,
        decisive_victory = 30,
        close_victory    = 16,
        pyrrhic_victory  = 8,
    },
    settlement_influence = 24,  -- for taking a settlement
    rank_influence      = 3,    -- per rank gained

    loyalty_start       = 55,
    loyalty_gain_office = 2,    -- per turn, per office held
    loyalty_military_doctrine = 2,
    loyalty_drift_none  = -1,   -- per turn, holding no office
    loyalty_affinity_snub = -2, -- extra, its own office held by an outsider
    loyalty_battle_won  = 3,
    loyalty_member_died = -8,
    loyalty_appointed   = 8,    -- his party, on taking a seat
    loyalty_snubbed     = -6,   -- the affine party, when an outsider takes it
    loyalty_dismissed   = -12,  -- his party, on being sacked before his term

    favour_gift_cost     = 600,
    favour_gift_loyalty  = 2,
    -- WITHHOLD: a party at or below the line stops
    -- its officers working, every office it holds, for a few turns.
    withhold_line        = 30,
    withhold_motive      = 40,
    withhold_turns       = 3,
    -- SETTLE A FEUD.
    arbit_side_loyalty   = 10,
    arbit_peace_loyalty  = 3,
    -- AI COURTS ACT: this many take a party turn
    -- per round, in rotation; an AI ruler grants a demand below the line.
    ai_party_courts      = 3,
    ai_grant_line        = 50,
    -- NEWS OF AI COURTS kept per human court.
    news_max             = 30,
    -- A GOVERNOR'S RANK: +1 order per this many ranks, +1%
    -- income per that many.
    gov_rank_order_per   = 5,
    gov_rank_income_per  = 2,
    favour_secure_cost   = 2500,
    favour_secure_turns  = 5,

    party_trait_scale   = 1,

    weight_start        = 10,   -- a house entering court
    weight_per_office   = 6,
    -- A GOVERNORSHIP IS WORTH ITS PROVINCE: one weight for every this many
    -- settlement levels held there, rounded up, never less than 1 (a level-1
    -- village counts 1, a level-5 capital 5; IC.gov_weight_of). A Custom slider,
    -- so whole levels, as MCT's sliders step.
    gov_levels_per_weight = 2,
    -- AND IT IS EARNED, NOT HANDED OVER: a new governor starts from nothing and
    -- gains this much a turn up to what his province is worth (IC.grow_governors).
    gov_weight_per_turn = 1,
    ambition_standing_per_weight = 100,
    weight_affinity_mult = 2,   -- appointing the affine house is worth double

    plot_bribe_cost       = 180,
    plot_bribe_loyalty    = 20,   -- and the secession clock stops
    plot_bribe_standing   = 60,   -- the gold lands in HIS pocket too
    plot_discredit_cost   = 140,
    plot_discredit_weight = 8,    -- off the house's weight, not its loyalty
    plot_discredit_standing = 90, -- and off the man's own standing
    plot_rumour_cost      = 80,
    plot_rumour_damage    = 120,  -- off the target man's own standing
    plot_murder_cost      = 250,
    plot_murder_loyalty   = 30,   -- his house knows perfectly well who did it

    plot_chance_bribe     = 65,
    plot_chance_discredit = 60,
    plot_chance_rumour    = 75,
    plot_chance_murder    = 40,
    -- A PARTY MOVE ONLY: a feuding party switches
    -- off an office its enemy holds.
    plot_sabotage_cost    = 200,
    plot_chance_sabotage  = 50,
    sabotage_turns        = 3,
    plot_chance_per_10    = 1,
    plot_chance_min       = 5,
    plot_chance_max       = 95,
    plot_fail_loyalty     = 10,

    plot_provoke_cost     = 120,
    plot_provoke_loyalty  = 25,   -- straight off their loyalty
    plot_chance_provoke   = 80,   -- angering somebody is not difficult
    plot_provoke_clock    = 3,

    plot_purge_cost       = 400,
    plot_purge_witness    = 15,   -- off every surviving house's loyalty
    plot_chance_purge     = 45,   -- and it is very far from certain
    plot_purge_backfire   = 30,

    plot_oath_cost        = 90,
    plot_oath_loyalty     = 4,    -- every turn, for as long as both live
    plot_oath_min_loyalty = 60,   -- "positive loyalty" - above loyalty_start
    plot_chance_oath      = 85,

    plot_embezzle_cost    = 60,
    plot_embezzle_gold    = 2500,
    plot_embezzle_loyalty = 6,    -- off every house but your own
    plot_chance_embezzle  = 70,
    plot_feast_cost       = 100,
    plot_feast_standing   = 140,  -- it pays HIM, which is the point of it
    plot_feast_loyalty    = 3,    -- off every house but your own
    plot_chance_feast     = 90,

    plot_unseat_cost      = 220,
    plot_unseat_loyalty   = 22,   -- ONCE for the move, not once per seat
    plot_chance_unseat    = 50,

    plot_recall_cost      = 160,
    plot_recall_loyalty   = 16,
    plot_chance_recall    = 60,

    plot_patron_cost      = 130,
    plot_patron_standing  = 100,
    plot_patron_loyalty   = 6,
    plot_chance_patron    = 85,

    plot_kinsman_cost     = 200,
    plot_kinsman_weight   = 8,
    plot_kinsman_min_loyalty = 55,
    plot_chance_kinsman   = 60,

    plot_pledge_cost      = 150,
    plot_pledge_loyalty   = 20,
    plot_pledge_weight    = 6,    -- off YOUR house, not theirs
    plot_chance_pledge    = 90,

    plot_audience_cost    = 140,
    plot_audience_loyalty = 5,    -- onto every house but your own
    plot_chance_audience  = 75,

    plot_circuit_cost     = 110,
    plot_circuit_prov     = 8,
    plot_chance_circuit   = 80,

    -- THE CIVIL MISSIONS. NOT MCT settings and not
    -- in IC.TUNE_ORDER. The envoy_* values are ALSO the bundles' effect values:
    -- tools/gen_iron_court.py reads them out of this file.
    mission_turns         = 5,    -- how long an envoy's work lasts
    plot_envoy_cost       = 120,
    plot_chance_envoy     = 80,
    envoy_ctl             = 6,    -- control
    envoy_arm             = 20,   -- % armaments
    envoy_raw             = 20,   -- % raw materials
    envoy_lab             = 15,   -- % fewer labourers lost
    -- THE DWARF ENVOY'S OTHER THREE. Not settings;
    -- gen_iron_court reads them for the bundles' values.
    envoy_oath            = 20,   -- % Oathgold from buildings
    envoy_grow            = 5,    -- growth
    envoy_rec             = 15,   -- % off recruitment cost
    plot_diplomats_cost   = 100,
    plot_chance_diplomats = 75,
    diplomats_bonus       = 4,    -- CA's own -6..+6 scale
    diplomats_rest        = 5,    -- turns before the same faction again


    pressure_below      = IC.CONTROL[#IC.CONTROL - 1].floor,
    pressure_per_point  = 8,    -- chance, in percent, per point below
    pressure_max        = 60,   -- and no higher, ever

    secede_share        = 25,   -- share >= this AND
    secede_loyalty      = 20,   -- loyalty <= this starts the clock
    secede_break        = 0,
    secede_turns        = 5,
    -- THE GRACE PERIOD: for this many turns from the start
    -- of a campaign nobody leaves and the Crown does not split. Not a setting.
    grace_turns         = 10,
    sufferance_share    = 20,   -- the player's own party below this

    -- THE COURT'S SIZE IS THE DIFFICULTY: one fixed number per preset, two
    -- rivals here (Gentle 1, Default 2, Harsh 3, Political Chaos 5). Only Custom
    -- rolls between two.
    rivals_min          = 2,
    rivals_max          = 2,

    prov_loyalty_start  = 60,
    prov_gain_governed  = 3,    -- per turn, a contented party's man governing it
    prov_drift_none     = -1,   -- per turn, nobody governing it at all
    prov_drift_angry    = -4,   -- per turn, its governor's party on the clock
    prov_defect_floor   = 25,
    prov_loyalty_max    = 100,
    rebel_units         = 19,
    rebel_unit_rank     = 3,
    rebel_lord_level    = 5,
    secede_step         = 0.1,
    rebel_lords_per     = 3,
    rebel_lords_max     = 3,
    rebel_heroes_max    = 2,
    rebel_threat        = 30,
    rebel_relation      = -70,
    rebel_relation_step = -6,
    rebel_relation_max  = 30,
    -- EVERY OTHER CHAOS DWARF FACTION sours on rebels too, by at most this many
    -- steps.
    rebel_relation_others_max = 2,
    loyalty_warn        = 35,
    warn_turns          = 3,
    splinter_loyalty    = 25,
    splinter_weight     = 5,

    -- Rumour and discredit at or below this loyalty. Defined here, not in the
    -- parties file, so the settings below can freeze it.
    party_intrigue_line = 55,

    -- GRUDGES, Dwarf courts only. Not on
    -- the MCT page. A grudge is a loyalty line that never fades; a party's
    -- book holds grudge_max. Kinship is every Dwarf party's term.
    grudge_loyalty      = -1,
    grudge_max          = 4,
    kin_loyalty         = 1,
    -- WHAT A BROKEN OATH COSTS ON TOP OF THE INSULT THAT BROKE IT. Nothing,
    -- except under the Dwarfs' Iron Law (DWF.GOVS.chain). Read through IC.tune.
    oath_broken_loyalty = 0,
    -- PAY THE WEREGILD: gold from the treasury,
    -- never a man's influence, and certain. No plot_chance_weregild: it never rolls.
    plot_weregild_cost    = 1000,
    plot_weregild_loyalty = 4,

    -- GOVERNMENTS.
    gov_drift_share     = 30,   -- a rival this big pulls the government its way
    gov_balance_turns   = 2,    -- a court nobody leads drifts to the Conclave this slowly
    gov_pressure_line   = 6,    -- pressure that asks the player to choose
    gov_choice_turns    = 3,    -- an unanswered choice is Accept after this
    gov_accept_gain     = 10,
    gov_accept_loss     = -10,
    gov_hold_cost       = 300,  -- times one more than the holds so far
    gov_hold_loyalty    = -8,
    gov_force_cost      = 400,
    gov_force_loss      = -15,
    gov_force_gain      = 5,
    gov_force_cooldown  = 15,
    governments         = true,
    gov_drift           = true,

    -- DEEDS. Renown a deed gives its party, how fast it
    -- fades, the most one party gains in a turn, and where an absent party is
    -- drawn in. Not on the MCT page; gov_drift_share is the precedent.
    deeds               = true,
    deed_battle         = 3,
    deed_hellforge      = 4,
    deed_rite           = 4,
    deed_temple         = 2,
    deed_slaves         = 3,
    deed_raze           = 3,
    deed_convoy         = 5,
    deed_research       = 2,
    deed_grudge         = 3,    -- a grudge settled (Dwarf courts)
    -- 25% a turn and 6 a turn settle the most deeds at 24-27 renown, near a
    -- party's own weight; 10% and 8 settled at 80-89 and took the Crown's
    -- control with them. The line is below that so an absent party can reach it.
    renown_fade_pct     = 25,
    renown_turn_cap     = 6,
    renown_join_line    = 15,

    -- THE BOOK OF GRUDGES, Dwarf courts only. Not
    -- on the MCT page. A line reached is a line crossed; book_penalty is CA's
    -- -6..+6 dilemma scale, one per band, in order.
    book_bands          = {500, 1000, 2000},
    book_penalty        = {-1, -2, -3},
    book_named          = 1000,  -- a treaty with a faction the Book names this high is a grudge
    book_top            = 3,     -- names on the Court tab

    -- THE LAWS. Constants: only `laws` is a switch, and
    -- only it is in IC.TUNE_ORDER. Multipliers are percent, never floats.
    laws                = true,
    law_propose_cost    = 150,
    law_party_share     = 15,   -- % of the court a party needs to propose
    law_party_rest      = 6,    -- turns between two party proposals
    law_vote_turns      = 2,
    law_loyal_line      = 60,   -- a party with no stance votes with you from here
    law_disloyal_line   = 40,   -- ...and against you below here
    law_push_cost       = {100, 250, 500},   -- reaching each support level
    law_push_mult       = {150, 200, 300},   -- its weight, percent
    law_push_margin     = 10,   -- % of all voting influence that is "close"
    law_win_rate        = 50,   -- % of a man's influence his vote costs
    law_win_ambition    = {cautious = 150, steady = 100, ambitious = 75},
    law_overrule_cost   = 500,
    law_overrule_loyalty = -10,
    law_pass_gain       = 5,
    law_pass_loss       = -5,
    law_fail_loss       = -5,

    -- THE SEVEN SWITCHES (the MCT page's Systems and Debug). All on: a campaign
    -- without MCT plays exactly as it did before they existed.
    parties_act         = true,
    ai_courts           = true,
    secession           = true,
    pressure            = true,
    crown_split         = true,
    detailed_log        = true,
    -- Off, IC.ROUTINE_EVENTS go to the Log tab only.
    all_cards           = true,
    -- DWARF COURTS: off, no Dwarf faction has a
    -- court, and one already running comes off the map at its next turn.
    dwarf_courts        = true,

    -- STARTING MEMBERS. On turn 1 each party of a player's court rolls a
    -- number between these two and is given lords until it has that many men.
    -- 0 and 0 gives nobody. The player's on every difficulty (IC.TUNE_START).
    seed_min            = 3,
    seed_max            = 6,
}

-- SETTINGS. Fifteen numbers and six switches belong to the player, through MCT.
-- Each is read ONCE, frozen into the save as derpy_ic_tuned, and applied over
-- IC.TUNE, so every IC.TUNE.x read in this mod is unchanged and a save plays
-- on the numbers it started with whatever MCT says later.
--
-- REGISTERED THREE TIMES: in IC.TUNE above, in IC.TUNE_ORDER below, and in
-- script/mct/settings/derpy_iron_court.lua. The court harness holds all three
-- against each other, and the packing gate refuses a setting nothing reads.
--
-- A NEW KEY IS APPENDED, NEVER INSERTED. unpack_tune walks this list by
-- position against the saved string, so a key put anywhere but the end moves
-- every value after it onto the wrong setting in every existing save.
IC.TUNE_ORDER = {
    "loyalty_start", "loyalty_drift_none", "secede_loyalty", "secede_share",
    "secede_turns", "pressure_below", "influence_trickle", "settlement_influence",
    "favour_gift_cost", "favour_secure_cost", "party_intrigue_line",
    "rivals_min", "rivals_max", "term_turns",
    "parties_act", "ai_courts", "secession", "pressure", "crown_split",
    "detailed_log", "all_cards",
    "gov_levels_per_weight",
    "governments", "gov_drift", "gov_pressure_line", "gov_hold_cost", "gov_force_cost",
    "deeds",
    "laws",
    "dwarf_courts",
    "seed_min", "seed_max",
}

-- NUMBERS NO DIFFICULTY SETS: read off the page on every difficulty, and named
-- by no IC.PRESETS entry. The MCT page files them under Starting court.
IC.TUNE_START = {seed_min = true, seed_max = true}

-- Today's values, taken off IC.TUNE before anything can change it.
IC.TUNE_DEFAULTS = {}
for _i = 1, #IC.TUNE_ORDER do
    IC.TUNE_DEFAULTS[IC.TUNE_ORDER[_i]] = IC.TUNE[IC.TUNE_ORDER[_i]]
end

-- The difficulty dropdown. Default is IC.TUNE_DEFAULTS and so is not listed,
-- and Custom reads the sliders. A preset names numbers only: the switches are
-- the player's on every difficulty.
IC.PRESET_CUSTOM = "custom"
IC.PRESETS = {
    gentle = {
        loyalty_start = 65, loyalty_drift_none = 0, secede_loyalty = 15,
        secede_share = 30, secede_turns = 7, pressure_below = 5,
        influence_trickle = 7, settlement_influence = 30,
        favour_gift_cost = 400, favour_secure_cost = 1800,
        party_intrigue_line = 45, rivals_min = 1, rivals_max = 1, term_turns = 10,
        gov_levels_per_weight = 2,
        gov_pressure_line = 8, gov_hold_cost = 200, gov_force_cost = 300,
    },
    harsh = {
        loyalty_start = 50, loyalty_drift_none = -2, secede_loyalty = 25,
        secede_share = 20, secede_turns = 4, pressure_below = 15,
        influence_trickle = 4, settlement_influence = 20,
        favour_gift_cost = 800, favour_secure_cost = 3200,
        party_intrigue_line = 60, rivals_min = 3, rivals_max = 3, term_turns = 10,
        gov_levels_per_weight = 2,
        gov_pressure_line = 5, gov_hold_cost = 400, gov_force_cost = 500,
    },
    ruthless = {
        loyalty_start = 45, loyalty_drift_none = -3, secede_loyalty = 30,
        -- THE PRESSURE LINE SITS UNDER A FRESH FULL COURT. Six parties on equal
        -- footing leave the Crown 17 of the court; at 20 it is pressed from
        -- turn 1, before the player has moved.
        secede_share = 15, secede_turns = 3, pressure_below = 15,
        influence_trickle = 3, settlement_influence = 16,
        favour_gift_cost = 1000, favour_secure_cost = 4000,
        -- FIVE RIVALS FILL THE GRID. Only four can rise under a banner of their
        -- own (IC.REBEL_POOL); a fifth wakes a dead house, or joins a rising.
        party_intrigue_line = 65, rivals_min = 5, rivals_max = 5, term_turns = 10,
        gov_levels_per_weight = 2,
        gov_pressure_line = 4, gov_hold_cost = 500, gov_force_cost = 600,
    },
}

-- THE GOVERNMENTS (docs/superpowers/specs/2026-10-02-iron-court-governments-design.md).
-- Lore: no king; the Sorcerer-Prophets sit in council, and the strongest voice
-- is the eldest. Each government bends ONE court rule: `over` names IC.TUNE
-- keys, a number replacing the value and {mul = x} scaling it (a table knob
-- entry by entry), rounded. Read through IC.tune, never IC.TUNE, wherever a key
-- here is read. No Crown and no Hearth government: no lore basis.
IC.GOV_ORDER = {"conclave", "priest", "forge", "legion", "chain", "convoy"}
-- `icon` is a bare name under ui/campaign ui/effect_bundles/: the faction
-- bundle wears it (gen_iron_court reads it from here) and so does the panel.
IC.GOVS = {
    conclave = {icon = "dlc23_region_action_gift_zhar.png",
                parties = {"tower"},
                over = {term_turns = {mul = 0.6}, renew_wait = 1}},
    priest   = {icon = "chd_toz_district_sorcery.png",
                parties = {"temple"},
                over = {rank_influence = 6, battle_influence = {mul = 0.75}}},
    forge    = {icon = "chd_hellforge.png",
                parties = {"forge"},
                over = {governor_income = 8, gov_rank_income_per = 1,
                        influence_trickle = {mul = 0.6}}},
    legion   = {icon = "chd_toz_district_military.png",
                parties = {"legion"},
                over = {battle_influence = {mul = 1.5}, loyalty_battle_won = 5,
                        influence_trickle = 0}},
    chain    = {icon = "chd_labour.png",
                parties = {"chain"},
                over = {plot_murder_cost = {mul = 0.65}, plot_purge_cost = {mul = 0.65},
                        plot_provoke_cost = {mul = 0.65}, plot_fail_loyalty = 20}},
    convoy   = {icon = "dlc23_region_action_sell_labour.png",
                parties = {"road", "ledger"},
                over = {favour_gift_cost = {mul = 0.67}, favour_secure_cost = {mul = 0.67},
                        plot_embezzle_loyalty = 12}},
}

-- WHERE A HOUSE STARTS. A faction not here takes its court's
-- own at its first turn (IC.start_gov). Uzkulak and the Kraken are inference.
IC.START_GOV = {
    wh3_dlc23_chd_astragoth = "priest",
    wh3_dlc23_chd_conclave = "conclave",
    wh3_dlc23_chd_legion_of_azgorh = "legion",
    wh3_dlc23_chd_zhatan = "legion",
    cr_chd_house_of_khorakk = "chain",
    cr_chd_house_of_azeros = "forge",
    cr_chd_house_of_bzaark = "forge",
    cr_chd_snakebeards_artificers = "forge",
    cr_chd_fists_of_hashut = "legion",
    cr_chd_slaves_of_the_black_dwarf = "legion",
    cr_chd_house_of_baal = "priest",
    cr_chd_horns_of_hashut = "priest",
    cr_chd_warfleet_of_uzkulak = "convoy",
    cr_chd_black_kraken_armada = "convoy",
}

function IC.governments_on() return IC.TUNE.governments ~= false end

-- "doctrine", not "gov": derpy_ic_gov_ is the governors' bundles.
function IC.gov_bundle(slug, faction_key) return IC.key("doctrine", slug, faction_key) end

-- THE LAWS. One option per category is in
-- force; the first of each `order` is its start and has no effects. `icon` is
-- a bare name under ui/campaign ui/effect_bundles/: the bundle wears it
-- (gen_iron_court reads it from here) and so does the panel. `pro` and `con`
-- are the parties for and against.
IC.LAW_ORDER = {"labour", "tribute", "worship", "war"}
IC.LAWS = {
    labour = {icon = "chd_labour.png",
              order = {"measure", "lash", "kept", "quota", "ash"},
              opts = {
        measure = {icon = "chd_workload.png"},
        lash    = {icon = "dlc23_region_action_set_example.png", pro = {"chain"}, con = {"hearth"}},
        kept    = {icon = "slaves.png", pro = {"hearth"}, con = {"chain"}},
        quota   = {icon = "wh3_dlc23_edict_chd_higher_quotas.png", pro = {"forge"}, con = {"hearth"}},
        ash     = {icon = "wh3_dlc23_edict_chd_smoke_stacks.png", pro = {"legion"}, con = {"ledger"}},
    }},
    tribute = {icon = "edict_collect_tribute.png",
               order = {"tithe", "roads", "tariff", "mines", "charter"},
               opts = {
        tithe   = {icon = "edict_collect_tribute.png"},
        roads   = {icon = "convoy_icon.png", pro = {"road"}, con = {"crown"}},
        tariff  = {icon = "trade_agreement.png", pro = {"ledger"}, con = {"road"}},
        mines   = {icon = "chd_raw_materials.png", pro = {"forge"}, con = {"road"}},
        charter = {icon = "wh3_dlc23_edict_chd_architects.png", pro = {"road"}, con = {"legion"}},
    }},
    worship = {icon = "chd_conclave_influence.png",
               order = {"rites", "fires", "seats", "lore", "licence"},
               opts = {
        rites   = {icon = "chd_conclave_influence.png"},
        fires   = {icon = "wh3_dlc23_unit_passive_burning_bright.png", pro = {"temple"}, con = {"tower"}},
        seats   = {icon = "chd_toz_tier.png", pro = {"tower"}, con = {"temple"}},
        lore    = {icon = "loremaster.png", pro = {"tower"}, con = {"hearth"}},
        licence = {icon = "hellforged.png", pro = {"forge"}, con = {"temple"}},
    }},
    war = {icon = "edict_levy_conscripts.png",
           order = {"levy", "hellforge", "legions", "grudge", "gunnery"},
           opts = {
        levy      = {icon = "edict_levy_conscripts.png"},
        hellforge = {icon = "chd_armaments.png", pro = {"forge"}, con = {"legion"}},
        legions   = {icon = "chd_toz_district_t3_military.png", pro = {"legion"}, con = {"forge"}},
        grudge    = {icon = "wh3_dlc23_unit_passive_oath_of_contempt.png", pro = {"legion"}, con = {"ledger"}},
        gunnery   = {icon = "artillery.png", pro = {"forge"}, con = {"hearth"}},
    }},
}
IC.LAW_SIDES = {aye = true, nay = true, abstain = true}

function IC.laws_on(faction_key)
    return IC.TUNE.laws ~= false and IC.is_human(faction_key)
end

function IC.law_bundle(category, option, faction_key)
    return IC.key("law", category .. "_" .. option, faction_key)
end

function IC.law_opt(category, option, faction_key)
    local c = IC.R(faction_key).LAWS[category or ""]
    return c and c.opts[option or ""] or nil
end

-- IC.state, not IC.court: asking what is in force must never create a court.
function IC.law_in_force(faction_key, category)
    local R = IC.R(faction_key)
    local court = faction_key and IC.state[faction_key]
    local held = court and court.laws and court.laws[category]
    if IC.law_opt(category, held, faction_key) then return held end
    return R.LAWS[category].order[1]
end

function IC.law_stance(category, option, party, faction_key)
    local o = IC.law_opt(category, option, faction_key)
    for _, p in ipairs(o and o.pro or {}) do if p == party then return "aye" end end
    for _, p in ipairs(o and o.con or {}) do if p == party then return "nay" end end
    return nil
end

-- ONE BUNDLE PER CATEGORY on a player court with laws on, none otherwise. All
-- off first, as the government's bundle does, so a swap never wears two.
function IC.apply_law_bundles(faction_key)
    local R = IC.R(faction_key)
    local on = IC.laws_on(faction_key)
    for _, cat in ipairs(R.LAW_ORDER) do
        for _, opt in ipairs(R.LAWS[cat].order) do
            cm:remove_effect_bundle(IC.law_bundle(cat, opt, faction_key), faction_key)
        end
        if on then
            cm:apply_effect_bundle(IC.law_bundle(cat, IC.law_in_force(faction_key, cat), faction_key),
                                   faction_key, -1)
        end
    end
end

function IC.gov_for_party(slug, faction_key)
    local R = IC.R(faction_key)
    for _, g in ipairs(R.GOV_ORDER) do
        for _, p in ipairs(R.GOVS[g].parties) do
            if p == slug then return g end
        end
    end
    return nil
end

-- IC.state, not IC.court: asking a price must never create a court.
function IC.gov_row(faction_key)
    local R = IC.R(faction_key)
    if not IC.governments_on() then return nil end
    local court = faction_key and IC.state[faction_key]
    return court and R.GOVS[court.gov or ""] or nil
end

-- ONE LAYER OF IC.tune: a number replaces, {mul = x} scales - a table knob
-- entry by entry - rounded.
function IC.tune_layer(base, o)
    if o == nil then return base end
    if type(o) == "number" then return o end
    if type(base) == "table" then
        local out = {}
        for k, v in pairs(base) do out[k] = math.floor(v * o.mul + 0.5) end
        return out
    end
    return math.floor(base * o.mul + 0.5)
end

-- IC.TUNE, THEN THE COURT'S RACE, THEN ITS GOVERNMENT. The race layer is under
-- every government: a Dwarf party's secession counts run half again as long
-- whoever rules.
function IC.tune(faction_key, key)
    local race = faction_key and IC.R(faction_key)
    local base = IC.tune_layer(IC.TUNE[key], race and race.tune and race.tune[key])
    local row = IC.gov_row(faction_key)
    return IC.tune_layer(base, row and row.over[key])
end

-- AN ENGINE CALL THAT ERRORS READS AS SINGLE PLAYER: locking a single-player
-- campaign out of its own settings over a failed call is the worse failure.
function IC.is_mp()
    local ok, v = pcall(function() return cm:is_multiplayer() end)
    return ok and v == true
end

function IC.read_mct_or_defaults()
    local t = {}
    for k, v in pairs(IC.TUNE_DEFAULTS) do t[k] = v end
    -- BEFORE MCT IS EVEN ASKED: two machines holding different settings would
    -- freeze two different courts into two saves at the first tick.
    if IC.is_mp() then return t end
    local ok, mct = pcall(function() return get_mct and get_mct() end)
    if not ok or not mct then return t end
    pcall(function()
        local mod = mct:get_mod_by_key("derpy_iron_court")
        if not mod then return end
        -- TYPE-CHECKED, NOT NIL-CHECKED. MCT hands back whatever the option
        -- holds, and a mis-registered option answers the wrong shape.
        local function read(key)
            local opt = mod:get_option_by_key(key)
            if not opt then return nil end
            local v = opt:get_finalized_setting()
            if type(v) == type(IC.TUNE_DEFAULTS[key]) then return v end
            return nil
        end
        local preset = "default"
        local popt = mod:get_option_by_key("preset")
        local pv = popt and popt:get_finalized_setting()
        if type(pv) == "string" and pv ~= "" then preset = pv end
        -- THE SWITCHES ON EVERY DIFFICULTY, the numbers under Custom only.
        for _, key in ipairs(IC.TUNE_ORDER) do
            local custom_number = type(IC.TUNE_DEFAULTS[key]) == "number"
                and (preset == IC.PRESET_CUSTOM or IC.TUNE_START[key])
            if type(IC.TUNE_DEFAULTS[key]) == "boolean" or custom_number then
                local v = read(key)
                if v ~= nil then t[key] = v end
            end
        end
        for key, v in pairs(IC.PRESETS[preset] or {}) do t[key] = v end
    end)
    -- cm:random_number(max, min) with min above max is no roll at all.
    if t.rivals_min > t.rivals_max then t.rivals_min = t.rivals_max end
    if t.seed_min > t.seed_max then t.seed_min, t.seed_max = t.seed_max, t.seed_min end
    return t
end

function IC.pack_tune(t)
    local parts = {}
    for i = 1, #IC.TUNE_ORDER do
        local key = IC.TUNE_ORDER[i]
        local v = t[key]
        -- A KEY THE TABLE DOES NOT HOLD IS ITS DEFAULT, NEVER 0: for a switch
        -- 0 is OFF, and a table built before the key existed is exactly what an
        -- older save hands this.
        if v == nil then v = IC.TUNE_DEFAULTS[key] end
        if v == true then v = 1 elseif v == false then v = 0 end
        parts[i] = tostring(v)
    end
    return table.concat(parts, "|")
end

function IC.unpack_tune(packed)
    local t, i = {}, 1
    for k, v in pairs(IC.TUNE_DEFAULTS) do t[k] = v end
    -- EVERY FIELD, EMPTY ONES INCLUDED: `[^|]+` steps over an empty field and
    -- slides every later value onto the key before it.
    for chunk in string.gmatch((packed or "") .. "|", "([^|]*)|") do
        local key = IC.TUNE_ORDER[i]
        local n = tonumber(chunk)
        -- AN UNREADABLE FIELD STAYS ON ITS DEFAULT - a switch included, which
        -- must not read as off - and a field past the end is a later build's.
        if key and n ~= nil then
            if type(IC.TUNE_DEFAULTS[key]) == "boolean" then
                t[key] = n ~= 0
            else
                t[key] = n
            end
        end
        i = i + 1
    end
    return t
end

function IC.apply_tune(t)
    for i = 1, #IC.TUNE_ORDER do
        local key = IC.TUNE_ORDER[i]
        if t[key] ~= nil then IC.TUNE[key] = t[key] end
    end
    -- THE ONE COPY TAKEN AT LOAD: the parties file copies this line into the
    -- two intrigue moves, so it is written through to them here.
    for _, move in ipairs(IC.PARTY_MOVES or {}) do
        if move.key == "discredit" or move.key == "rumour" then
            move.line = IC.TUNE.party_intrigue_line
        end
    end
end

-- THE SETTINGS, FROZEN INTO THE SAVE ONCE. First thing at every first tick. A
-- save holding derpy_ic_tuned plays on it; one without (a new campaign, or a
-- save from before this build) reads MCT now and keeps the answer for good -
-- all but IC.LIVE_TUNE, which follows MCT from then on.
-- MCT has already read the player's choices by then, in its own LoadingGame
-- callback (groovy_mct.pack, registry/main.lua, Registry:load).
function IC.freeze_tune()
    local packed = cm:get_saved_value("derpy_ic_tuned")
    local t
    if type(packed) == "string" and packed ~= "" then
        t = IC.unpack_tune(packed)
    else
        t = IC.read_mct_or_defaults()
        cm:set_saved_value("derpy_ic_tuned", IC.pack_tune(t))
    end
    IC.apply_tune(t)
    IC.refresh_live_tune()
    return t
end

-- THE SWITCHES A PLAYER MAY FLIP IN A RUNNING CAMPAIGN.
-- Each one's off path settles what it left running - open business settles,
-- the secession and split countdowns and the pressure mark are cleared - so a
-- flip strands nothing, and one turned back on starts again with its warning.
-- NOT ai_courts: off, it leaves the other courts' office bundles on their men.
-- The difficulty and every number stay frozen. The MCT page names the same
-- ten. Governments off takes the bundle away and drops a waiting choice
-- (IC.settle_switches); drift off only stops the drift; deeds off stops new
-- renown and drawing parties in, and what is held fades on its own. Laws off
-- drops open votes and takes every law bundle off; the laws in force stay in
-- the save.
IC.LIVE_TUNE = {"parties_act", "secession", "pressure", "crown_split",
                "all_cards", "detailed_log", "governments", "gov_drift", "deeds", "laws",
                "dwarf_courts"}

-- READ AT EVERY LOAD AND ON MCT'S Finalize, never in multiplayer, where each
-- machine's MCT is its own. A change goes into the frozen copy too, so the save
-- keeps it if MCT is removed.
function IC.refresh_live_tune()
    if IC.is_mp() then return false end
    local ok, mct = pcall(function() return get_mct and get_mct() end)
    if not ok or not mct then return false end
    local off = {}
    local changed = false
    pcall(function()
        local mod = mct:get_mod_by_key("derpy_iron_court")
        if not mod then return end
        for _, key in ipairs(IC.LIVE_TUNE) do
            local opt = mod:get_option_by_key(key)
            local v = opt and opt:get_finalized_setting()
            if type(v) == "boolean" and v ~= IC.TUNE[key] then
                IC.TUNE[key] = v
                off[key] = not v
                changed = true
            end
        end
    end)
    if not changed then return false end
    cm:set_saved_value("derpy_ic_tuned", IC.pack_tune(IC.TUNE))
    -- A COUNTDOWN SWITCHED OFF ENDS NOW, not at the next turn: the panel reads
    -- every one. With its switch off, each call below only clears.
    -- The courts still on disk are settled by IC.load.
    if off.secession or off.pressure or off.crown_split or off.governments
       or off.gov_drift or off.laws ~= nil then
        for faction_key in pairs(IC.state) do
            IC.settle_switches(faction_key)
            IC.save(faction_key)
        end
    end
    return true
end

-- WHAT A SWITCH THAT IS OFF LEFT RUNNING, cleared. With its switch off each of
-- these only clears, so a court with nothing running is untouched.
function IC.settle_switches(faction_key)
    if not IC.TUNE.secession then IC.tick_secession(faction_key) end
    if not IC.TUNE.pressure then IC.tick_pressure(faction_key) end
    if not IC.TUNE.crown_split then IC.splinter(faction_key) end
    -- DRIFT OFF DROPS THE WAITING CHOICE too: "your government changes only
    -- when you change it", and a waiting choice settles on its own.
    if not IC.governments_on() or IC.TUNE.gov_drift == false then
        IC.court(faction_key).gov_ask = nil
    end
    if not IC.governments_on() then IC.apply_gov_bundle(faction_key) end
    -- LAWS OFF DROPS THE OPEN VOTES; on or off, the bundles follow the switch.
    -- The laws in force stay in the save.
    if IC.TUNE.laws == false then IC.court(faction_key).votes = {} end
    IC.apply_law_bundles(faction_key)
end

IC.AMBITION_ORDER = {"cautious", "steady", "ambitious"}
IC.AMBITION = {
    cautious  = {factor = 75,  roll = 25},
    steady    = {factor = 100, roll = 50},
    ambitious = {factor = 125, roll = 25},
}

function IC.roll_ambition()
    local roll, total = cm:random_number(100, 1), 0
    for i = 1, #IC.AMBITION_ORDER do
        local slug = IC.AMBITION_ORDER[i]
        total = total + IC.AMBITION[slug].roll
        if roll <= total then return slug end
    end
    return IC.AMBITION_ORDER[#IC.AMBITION_ORDER]
end

IC.state = IC.state or {}       -- [faction_key] = court

local function new_court()
    return {
        houses   = {},   -- [slug] = {weight = n, loyalty = n, clock = n}
        offices  = {},   -- [office slug] = character cqi
        terms    = {},   -- [office slug] = turn the term ends
        govs     = {},   -- [province key] = character cqi
        -- [province key] = weight grown under its governor. nil: a governor
        -- from a save before the growth, who counts in full.
        gov_grown = {},
        prov     = {},   -- [province key] = loyalty, 0-100
        standing = {},   -- [character cqi] = influence he holds
        ambition = {},   -- [character cqi] = ambition slug
        last     = {},   -- [office slug] = {cqi, turn his term ended}
        log      = {},
        stalled  = {},   -- [office slug] = {ends, of, by, cause}
        news     = {},   -- {turn, kind, faction, a, b}, newest last
        sent     = {},   -- [faction key] = turn diplomats went
        -- THE GOVERNMENT: gov, gov_toward and gov_ask stay nil
        -- until there is one.
        gov_pressure = 0,
        gov_cool = 0,    -- turn a forced change's cooldown ends
        gov_holds = 0,
        -- DEEDS: [party] = renown, [party] = renown
        -- gained since this court's turn began.
        renown = {},
        renown_got = {},
        confed_turn = 0,  -- the turn this court last took in a confederation
        -- THE LAWS: [category] = option where it is not
        -- the start, and [category] = the open vote. law_rest stays nil until a
        -- party proposes.
        laws = {},
        votes = {},
        -- THE BOOK: [faction key] = bands crossed.
        book = {},
        -- GRUDGES: [party] = {{code, turn}, ...},
        -- oldest first. Kept by party slot: a party that leaves keeps its book.
        grudges = {},
    }
end

-- Bounded, because the whole court is serialised into one saved string. Oldest
-- entries fall off the front.
IC.LOG_MAX = 40

IC.LOG_KINDS = {
    bribe = true, discredit = true, rumour = true, murder = true, fell = true,
    appoint = true, dismiss = true,
    gov_on = true, gov_off = true,
    snub_on = true, snub_off = true,
    warn = true, secede = true, join = true,
    term = true, hire = true,
    gift = true, secure = true,
    plot_failed = true,
    provoke = true, purge = true, oath = true, oath_broken = true,
    embezzle = true, feast = true,
    -- THE GOVERNMENT. "doctrine", not "gov": gov_on and
    -- gov_off above are the governors.
    doctrine = true, doctrine_ask = true, doctrine_hold = true,
    doctrine_force = true, doctrine_lapse = true,
    -- DEEDS: renown a party took, and a party drawn in.
    deed = true, drawn = true,
    -- THE LAWS. key is "category.option".
    law_propose = true, law_pass = true, law_fail = true,
    law_win = true, law_push = true, law_overrule = true,
    unseat = true, recall = true, patron = true, kinsman = true,
    pledge = true, audience = true, circuit = true,
    envoy = true, diplomats = true,
    splinter = true,
    pressed = true, dissolve = true,
    party_warn = true, party_dropped = true, party_unseat = true,
    party_recall = true, feud = true, feud_end = true,
    demand = true, demand_met = true, demand_refused = true, demand_void = true,
    offer = true, offer_taken = true,
    -- Living courts.
    sabotage = true, withhold = true, arbit_side = true, arbit_peace = true,
    -- A death that empties a post, an office back at work.
    died = true, stall_end = true,
    -- GRUDGES: key is the grudge's code; a settled
    -- one's n is 1 for a seat, 0 for the weregild.
    grudge = true, grudge_settled = true, weregild = true,
}

-- WHO A PARTY WAS, for a line of the Record: its rolled name's two numbers, or
-- "c" for a confederate one, and nil for the Crown and anything that is not a
-- seated party. Named at draw time instead, a party that had left would read as
-- its trade's plain name and a later party of the same trade would take over its
-- lines. Numbers, not a name: IC.log runs inside the turn, where a loc call is a
-- turn-1 CTD.
-- A PARTY ALREADY GONE is answered from IC.departed, which IC.remove_house
-- fills: its feud, plot and demand are ended, and its secession written, after.
IC.departed = {}
function IC.who_was(faction_key, slug)
    if not slug or slug == IC.CROWN then return nil end
    local house = IC.court(faction_key).houses[slug]
    if not house then return IC.departed[faction_key .. "|" .. slug] end
    if house.confed then return "c" end
    if house.head and house.tail then return house.head .. "." .. house.tail end
    return nil
end

function IC.log(faction_key, kind, slug, key, n)
    if not IC.LOG_KINDS[kind] then return false end
    local court = IC.court(faction_key)
    court.log = court.log or {}
    court.log[#court.log + 1] = {
        turn = cm:model():turn_number(),
        kind = kind, slug = slug, key = key, n = n,
        sw = IC.who_was(faction_key, slug),
        kw = IC.who_was(faction_key, key),
    }
    while #court.log > IC.LOG_MAX do table.remove(court.log, 1) end
    return true
end

-- GRUDGES INSIDE THE COURT. A wrong the ruler does a party, written where the
-- wrong already takes its one-off loyalty. Contract order; "peace" is a pact
-- with a faction the Book of Grudges names.
IC.GRUDGE_CODES = {"slayer", "castout", "insult", "bar", "recall", "dismiss", "oath", "demand", "peace"}

-- WHAT EACH LINE OF THE BREAKDOWN CALLS IT. Plain English and no loc: the
-- terms are built inside the turn (ICUI.loyalty_tip resolves nothing either).
IC.GRUDGE_WORDS = {
    slayer  = "Driven to the Slayer Oath",
    castout = "Cast Out",
    insult  = "An Insult to the Clan",
    bar     = "Barred from the Hall",
    recall  = "Governors recalled",
    dismiss = "Dismissed before his term",
    oath    = "An oath broken",
    demand  = "A demand refused",
    peace   = "A pact with a named foe",
}

-- IC.state, not IC.court: asking must never create a court.
function IC.grudges(faction_key, slug)
    local court = faction_key and IC.state[faction_key]
    return court and court.grudges and court.grudges[slug or ""] or {}
end

-- A DWARF COURT'S, A RIVAL PARTY'S, A WRONG WE KNOW, AND ROOM IN THE BOOK.
-- A full book takes nothing more; the wrong still costs its one-off loyalty.
function IC.grudge_write(faction_key, slug, code)
    if IC.race_key(faction_key) ~= "dwf" or not IC.GRUDGE_WORDS[code or ""] then return false end
    if not slug or slug == IC.CROWN then return false end
    local court = IC.court(faction_key)
    if not court.houses[slug] then return false end
    court.grudges = court.grudges or {}
    local book = court.grudges[slug] or {}
    if #book >= IC.TUNE.grudge_max then return false end
    book[#book + 1] = {code = code, turn = cm:model():turn_number()}
    court.grudges[slug] = book
    IC.log(faction_key, "grudge", slug, code, 0)
    return true
end

-- THE OLDEST GOES FIRST. `how` is "weregild" or "seat", for the Record.
function IC.grudge_settle(faction_key, slug, how)
    local book = IC.grudges(faction_key, slug)
    if #book == 0 then return nil end
    local g = table.remove(book, 1)
    IC.log(faction_key, "grudge_settled", slug, g.code, how == "seat" and 1 or 0)
    return g
end

-- {index, persistent, where a caller's key goes}. The third field: true, the
-- key is a SENTENCE and is the body (secondary); false, it is a NAME - a seat,
-- a move's result - and is the subtitle (primary). IC.raise_feed.
IC.EVENTS = {
    plot_ok      = {2600, true, false},
    plot_fail    = {2601, true, false},
    office_lost  = {2602, true, false},
    party_joined = {2603, true, true},
    secede_warn  = {2604, true, true},
    -- Combine same-turn slights so the feed does not show one card per office.
    snub         = {2605, false, false},
    secede_done  = {2606, true, true},
    loyalty_warn = {2607, true, true},
    -- Append new events because the generator derives their index from position.
    splinter     = {2608, true, true},
    secede_soon  = {2609, true, true},
    splinter_warn = {2610, true, true},
    dissolved    = {2611, true, true},
    party_plot_warn    = {2612, true, true},
    party_plot_ok      = {2613, true, true},
    party_plot_fail    = {2614, true, true},
    party_plot_dropped = {2615, true, true},
    party_feud         = {2616, true, true},
    party_feud_end     = {2617, true, true},
    party_feud_murder  = {2618, true, true},
    party_demand       = {2619, true, true},
    party_demand_refused = {2620, true, true},
    party_offer        = {2621, true, true},
    term_soon          = {2622, true, false},
    party_sabotage     = {2623, true, true},
    party_withhold     = {2624, true, true},
    realm_secede       = {2625, false, true},
    -- Three events the court would otherwise pass in silence. officer_died and
    -- stall_end name the seat at the call site, as office_lost does.
    officer_died       = {2626, true, false},
    threat_over        = {2627, true, true},
    stall_end          = {2628, true, false},
    -- THE GOVERNMENT: a change, and a court asking for one.
    gov_changed        = {2629, true, true},
    gov_pressure       = {2630, true, true},
    -- DEEDS: the introduction, and a party your deeds
    -- drew in (its body names the deed, per party).
    gov_intro          = {2631, true, true},
    party_drawn        = {2632, true, true},
    -- THE LAWS.
    law_proposed       = {2633, true, true},
    law_passed         = {2634, true, true},
    law_failed         = {2635, true, true},
}

-- RAISED WITH cm:show_message_event_located; the record type must agree with
-- the call (tools/build_director.py measured a mismatch drawing nothing).
IC.LOCATED_EVENTS = {realm_secede = true}

-- ROUTINE NEWS: a card the all_cards setting can silence. Every one of these is
-- written to the court's log where it is raised, so off loses nothing; the
-- warnings, the player's own results, demands and offers are not on it.
IC.ROUTINE_EVENTS = {
    office_lost = true, party_joined = true, snub = true, party_feud = true,
    party_feud_end = true, dissolved = true, party_plot_dropped = true,
    -- The end of a warning, as party_plot_dropped is; both are logged.
    threat_over = true, stall_end = true,
}

-- A DEATH THE COURT ARRANGED already has its card - the plot's result, the
-- feud's murder - so ic_dead reads the mark, clears it, and says nothing more.
-- In memory only: a kill resolves in the session that ordered it.
IC.arranged_deaths = {}

IC.feed_queue = {}
IC.feed_held = false
-- Bound the deferred feed so a stuck hold cannot release hundreds of cards at once.
IC.FEED_QUEUE_MAX = 10

function IC.hold_feed(on)
    -- NOT IN MULTIPLAYER. The panel is open on one machine and not the other,
    -- so a hold would raise the model's event calls at two different times.
    -- The cards show when they are raised, behind the panel or not.
    if IC.is_mp() then return 0 end
    IC.feed_held = on and true or false
    if not IC.feed_held then return IC.flush_feed() end
    return 0
end

-- Clear the queue before raising events so a re-queued event cannot loop forever.
function IC.flush_feed()
    local queued = IC.feed_queue
    IC.feed_queue = {}
    for i = 1, #queued do
        IC.raise_feed(queued[i][1], queued[i][2], queued[i][3])
    end
    return #queued
end

function IC.feed(faction_key, slug, secondary)
    local ev = IC.EVENTS[slug]
    if not ev then return false end
    if not IC.is_human(faction_key) then return false end
    if IC.TUNE.all_cards == false and IC.ROUTINE_EVENTS[slug] then return false end
    -- Hold cards raised behind the open panel until the player can see them.
    if IC.feed_held then
        if #IC.feed_queue < IC.FEED_QUEUE_MAX then
            IC.feed_queue[#IC.feed_queue + 1] = {faction_key, slug, secondary}
        end
        return true
    end
    return IC.raise_feed(faction_key, slug, secondary)
end

-- THE RECORD'S NUMBER FOR A RACE. The picture belongs to the record the number
-- names, so each race has its own run of records, R.EVENT_OFFSET above
-- IC.EVENTS'; a shared run draws a Dwarf court's cards with Chaos Dwarf pictures.
function IC.event_index(slug, faction_key)
    local ev = IC.EVENTS[slug]
    if not ev then return nil end
    return ev[1] + (IC.R(faction_key).EVENT_OFFSET or 0)
end

-- THE CALLER'S KEY TAKES ONE SLOT, the one IC.EVENTS' third field names; the
-- event's own key fills the other. Never "": that draws the slot empty.
function IC.raise_feed(faction_key, slug, line)
    local ev = IC.EVENTS[slug]
    if not ev then return false end
    local stem = "event_feed_strings_text_" .. IC.event_stem(slug, faction_key)
    local primary, secondary = stem .. "_primary", stem .. "_secondary"
    if line and ev[3] then secondary = line elseif line then primary = line end
    pcall(function()
        cm:show_message_event(faction_key, stem .. "_title", primary, secondary,
                              ev[2], IC.event_index(slug, faction_key))
    end)
    return true
end

-- THE RACE'S OWN LINE when a faction is in hand:
-- a Chaos Dwarf key is unchanged, a Dwarf one carries the infix.
function IC.move_result_key(plot_key, ok, faction_key)
    if not plot_key then return nil end
    local stem = IC.key("move", plot_key, faction_key)
    return "event_feed_strings_text_" .. stem .. (ok and "_ok" or "_fail")
end

-- WHICH LOC AN EVENT READS: a race that words an event its own way lists the
-- slug in R.EVENT_LOC, and its keys carry the infix.
function IC.event_stem(slug, faction_key)
    local R = IC.R(faction_key)
    if R.EVENT_LOC and R.EVENT_LOC[slug] then return IC.key("event", slug, faction_key) end
    return "derpy_ic_event_" .. slug
end

function IC.party_drawn_key(faction_key, party)
    return "event_feed_strings_text_" .. IC.key("event_party_drawn", party, faction_key)
end

function IC.office_title_key(office_slug, faction_key)
    return "effect_bundles_localised_title_" .. IC.office_bundle(office_slug, faction_key)
end

function IC.court(faction_key)
    if not faction_key then return nil end
    IC.state[faction_key] = IC.state[faction_key] or new_court()
    return IC.state[faction_key]
end

function IC.ambition_slug(faction_key, cqi)
    if not cqi then return nil end
    local slug = (IC.court(faction_key).ambition or {})[cqi]
    return IC.AMBITION[slug or ""] and slug or nil
end

function IC.ambition_factor(faction_key, cqi)
    local row = IC.AMBITION[IC.ambition_slug(faction_key, cqi) or ""]
    return row and row.factor or 100
end

-- Only office/plot weight is saved; governors and living members add on read.
function IC.house_weight(faction_key, slug)
    local house = IC.court(faction_key).houses[slug or ""]
    if not house then return 0 end
    -- RENOWN IS WEIGHT, kept out of
    -- house.weight because that number is office bookkeeping.
    local renown = (IC.court(faction_key).renown or {})[slug or ""] or 0
    return house.weight + (house.gov_weight or 0)
        + IC.member_weight(faction_key, slug) + renown
end

-- WHAT EACH DEED MOVES. `alt` takes the deed
-- when `party` is not in the court and `alt` is.
IC.DEEDS = {
    battle    = {party = "legion", tune = "deed_battle"},
    hellforge = {party = "forge",  tune = "deed_hellforge"},
    rite      = {party = "temple", tune = "deed_rite"},
    temple    = {party = "temple", tune = "deed_temple"},
    slaves    = {party = "chain",  tune = "deed_slaves"},
    raze      = {party = "chain",  tune = "deed_raze"},
    convoy    = {party = "road",   tune = "deed_convoy", alt = "ledger"},
    research  = {party = "tower",  tune = "deed_research"},
}

function IC.deeds_on(faction_key)
    return IC.TUNE.deeds ~= false and IC.is_human(faction_key)
end

function IC.renown(faction_key, party)
    return (IC.court(faction_key).renown or {})[party or ""] or 0
end

-- ONE ENTRY PER PARTY, DEED AND TURN: a busy turn adds to the last entry rather
-- than burying the Record.
function IC.log_deed(faction_key, party, code, n)
    local log = IC.court(faction_key).log or {}
    local now = cm:model():turn_number()
    -- BACK THROUGH THIS TURN ONLY: another party's deed between two of this
    -- one's still sums them.
    for i = #log, 1, -1 do
        local e = log[i]
        if e.turn ~= now then break end
        if e.kind == "deed" and e.slug == party and e.key == code then
            e.n = (e.n or 0) + n
            return true
        end
    end
    return IC.log(faction_key, "deed", party, code, n)
end

-- AT MOST renown_turn_cap A TURN, and an absent party stops at the join line:
-- there it waits for a lord (IC.deed_join).
function IC.add_renown(faction_key, party, n, code)
    local court = IC.court(faction_key)
    court.renown = court.renown or {}
    court.renown_got = court.renown_got or {}
    local got = court.renown_got[party] or 0
    n = math.min(n or 0, math.max(0, IC.TUNE.renown_turn_cap - got))
    local have = court.renown[party] or 0
    if not court.houses[party] then
        n = math.min(n, math.max(0, IC.TUNE.renown_join_line - have))
    end
    if n <= 0 then return 0 end
    court.renown[party] = have + n
    court.renown_got[party] = got + n
    IC.log_deed(faction_key, party, code, n)
    return n
end

function IC.deed(faction_key, code)
    local R = IC.R(faction_key)
    local d = R.DEEDS[code or ""]
    if not d or not IC.deeds_on(faction_key) then return 0 end
    local court = IC.court(faction_key)
    local party = d.party
    if d.alt and not court.houses[party] and court.houses[d.alt] then party = d.alt end
    local n = IC.add_renown(faction_key, party, IC.TUNE[d.tune], code)
    -- A DEED FOR TWO PARTIES: a grudge settled is the
    -- Clan Warriors' and the Ancestor Priesthood's both.
    if d.also then n = n + IC.add_renown(faction_key, d.also, IC.TUNE[d.tune], code) end
    return n
end

-- AT THIS COURT'S TURN START, every court: renown_fade_pct, at least 1, and
-- the turn's limit begins again.
function IC.fade_renown(faction_key)
    local court = IC.court(faction_key)
    for party, n in pairs(court.renown or {}) do
        local left = n - math.max(1, math.floor(n * IC.TUNE.renown_fade_pct / 100))
        court.renown[party] = left > 0 and left or nil
    end
    court.renown_got = {}
end

function IC.total_weight(faction_key)
    local total = 0
    for slug in pairs(IC.court(faction_key).houses) do
        total = total + IC.house_weight(faction_key, slug)
    end
    return total
end

function IC.share(faction_key, slug)
    local house = IC.court(faction_key).houses[slug or ""]
    if not house then return 0 end
    local total = IC.total_weight(faction_key)
    if total <= 0 then return 0 end
    return (IC.house_weight(faction_key, slug) / total) * 100
end

function IC.house_icon(slug, faction_key)
    local R = IC.R(faction_key)
    if not slug then return nil end
    local sigil = nil
    for i = 1, #R.PARTIES do
        if R.PARTIES[i] == slug then
            sigil = "ui/derpy_ic/party_sigil_" .. slug .. ".png"
        end
    end
    local flag_of = nil
    if slug == IC.CROWN then
        flag_of = faction_key
    elseif faction_key then
        flag_of = IC.party_faction(faction_key, slug)
    end
    if not flag_of then return sigil end
    local f = cm:get_faction(flag_of)
    if not f then return sigil end
    local ok, p = pcall(function() return f:flag_path() end)
    if not ok or type(p) ~= "string" or p == "" then return sigil end
    -- Parentheses discard gsub's second return value.
    return (string.gsub(p, "\\", "/")) .. "/mon_64.png"
end

function IC.faction_for_origin(slug)
    if not slug or slug == "" then return nil end
    for _, rk in ipairs(IC.RACE_ORDER) do
        local list = IC.RACES[rk].ORIGINS
        for i = 1, #list do
            if list[i].slug == slug then return list[i].faction end
        end
    end
    return nil
end

function IC.origin_for_faction(faction_key)
    for _, rk in ipairs(IC.RACE_ORDER) do
        local list = IC.RACES[rk].ORIGINS
        for i = 1, #list do
            if list[i].faction == faction_key then return list[i].slug end
        end
    end
    return nil
end

function IC.party_faction(faction_key, slug)
    if not faction_key or not slug then return nil end
    local house = IC.court(faction_key).houses[slug]
    if not house or not house.confed then return nil end
    return IC.faction_for_origin(slug)
end

function IC.office_by_slug(slug, faction_key)
    local R = IC.R(faction_key)
    for i = 1, #R.OFFICES do
        if R.OFFICES[i].slug == slug then return R.OFFICES[i] end
    end
    return nil
end

local function join(parts, sep) return table.concat(parts, sep) end

function IC.pack(faction_key)
    local court = IC.court(faction_key)
    local houses, offices, govs, terms = {}, {}, {}, {}
    for slug, h in pairs(court.houses) do
        houses[#houses + 1] = string.format(
            "%s,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%s",
            slug, h.weight, h.loyalty, h.clock or 0, h.head or 0, h.tail or 0,
            h.confed and 1 or 0, h.pressed and 1 or 0, h.protected or 0,
            h.t1 or 0, h.t2 or 0,
            h.oath_mine or 0, h.oath_theirs or 0,
            h.snubbed and 1 or 0,
            h.split or 0,
            h.stored and 1 or 0,
            h.fielded or 0,
            h.gifted or 0,
            h.provoked and 1 or 0,
            h.snub_key or "-")
    end
    for slug, cqi in pairs(court.offices) do
        offices[#offices + 1] = slug .. "," .. tostring(cqi)
    end
    for province, cqi in pairs(court.govs) do
        local grown = court.gov_grown and court.gov_grown[province]
        govs[#govs + 1] = province .. "," .. tostring(cqi)
                          .. (grown and ("," .. tostring(grown)) or "")
    end
    for slug, turn in pairs(court.terms) do
        terms[#terms + 1] = slug .. "," .. tostring(turn)
    end
    local standing = {}
    for cqi, n in pairs(court.standing) do
        standing[#standing + 1] = tostring(cqi) .. "," .. tostring(n)
    end
    -- Use "-" for absent fields because split() drops empty comma-separated values.
    local logged = {}
    for i = 1, #(court.log or {}) do
        local e = court.log[i]
        logged[#logged + 1] = string.format("%d,%s,%s,%s,%s,%s,%s",
            e.turn or 0, e.kind or "-", e.slug or "-", e.key or "-",
            tostring(e.n or 0), e.sw or "-", e.kw or "-")
    end
    local prov, ambition, last = {}, {}, {}
    for office_slug, e in pairs(court.last or {}) do
        last[#last + 1] = string.format("%s,%d,%d", office_slug, e.cqi, e.turn)
    end
    for province, n in pairs(court.prov or {}) do
        prov[#prov + 1] = province .. "," .. tostring(n)
    end
    for cqi, slug in pairs(court.ambition or {}) do
        if IC.AMBITION[slug or ""] then
            ambition[#ambition + 1] = tostring(cqi) .. "," .. slug
        end
    end
    local stalled = {}
    for office_slug, s in pairs(court.stalled or {}) do
        stalled[#stalled + 1] = string.format("%s,%d,%s,%s,%s", office_slug,
            s.ends, s.of, s.by or "-", s.cause or "-")
    end
    table.sort(stalled)
    -- NEWS TEXT IS A PARTY'S NAME OR A KEY; the separators are taken out so a
    -- name can never split a field.
    local function clean(text)
        return (string.gsub(tostring(text or "-"), "[|;,]", " "))
    end
    local news = {}
    for i = 1, #(court.news or {}) do
        local n = court.news[i]
        news[#news + 1] = string.format("%d,%s,%s,%s,%s", n.turn or 0,
            clean(n.kind), clean(n.faction), clean(n.a), clean(n.b))
    end
    -- WHERE DIPLOMATS WENT: only the rests still
    -- running, so the field never outgrows diplomats_rest turns of sending.
    local sent = {}
    local now = cm:model():turn_number()
    for key, t in pairs(court.sent or {}) do
        if t + IC.TUNE.diplomats_rest > now then
            sent[#sent + 1] = key .. "," .. tostring(t)
        end
    end
    table.sort(sent)
    -- THE GOVERNMENT: "-" for nothing, as above.
    local ask = court.gov_ask
    local gov = string.format("%s,%d,%s,%d,%d,%s,%d,%s", court.gov or "-",
        court.gov_pressure or 0, court.gov_toward or "-", court.gov_cool or 0,
        court.gov_holds or 0, ask and ask.gov or "-", ask and ask.ends or 0,
        ask and ask.party or "-")
    -- DEEDS: field 15 is "party,renown,got" per party,
    -- field 16 is "intro,confed_turn".
    local renown = {}
    for party, n in pairs(court.renown or {}) do
        renown[#renown + 1] = string.format("%s,%d,%d", party, n,
                                            (court.renown_got or {})[party] or 0)
    end
    table.sort(renown)
    local deeds = string.format("%d,%d", court.gov_intro and 1 or 0, court.confed_turn or 0)
    -- THE LAWS: field 17 is "category,option" per law
    -- away from its start, and "rest,turn"; field 18 is the open votes, as
    -- "category,option,proposer,ends,stance,won,push" with won as cqi:side and
    -- push as party:level, "/" between pairs and "-" for none, then answered as
    -- 1 or 0.
    local laws = {}
    for cat, opt in pairs(court.laws or {}) do laws[#laws + 1] = cat .. "," .. opt end
    table.sort(laws)
    if (court.law_rest or 0) > 0 then laws[#laws + 1] = "rest," .. tostring(court.law_rest) end
    local votes = {}
    for cat, v in pairs(court.votes or {}) do
        local won, push = {}, {}
        for cqi, side in pairs(v.won or {}) do won[#won + 1] = tostring(cqi) .. ":" .. side end
        for party, level in pairs(v.push or {}) do push[#push + 1] = party .. ":" .. tostring(level) end
        table.sort(won)
        table.sort(push)
        votes[#votes + 1] = string.format("%s,%s,%s,%d,%s,%s,%s,%d", cat, v.option,
            v.proposer or IC.CROWN, v.ends or 0, v.stance or "abstain",
            #won > 0 and table.concat(won, "/") or "-",
            #push > 0 and table.concat(push, "/") or "-", v.answered and 1 or 0)
    end
    table.sort(votes)
    -- GRUDGES: field 19 is "slug:code.turn;code.turn"
    -- per party, "/" between parties, oldest first. Empty on every Chaos Dwarf court.
    local grudges = {}
    for slug, book in pairs(court.grudges or {}) do
        local g = {}
        for i = 1, #book do g[i] = book[i].code .. "." .. tostring(book[i].turn) end
        if #g > 0 then grudges[#grudges + 1] = slug .. ":" .. table.concat(g, ";") end
    end
    table.sort(grudges)
    -- THE BOOK: field 20 is "faction:bands" per named
    -- faction, "/" between them.
    local book = {}
    for key, n in pairs(court.book or {}) do book[#book + 1] = key .. ":" .. tostring(n) end
    table.sort(book)
    return join({join(houses, ";"), join(offices, ";"), join(govs, ";"),
                 join(terms, ";"), join(standing, ";"),
                 join(logged, ";"), join(prov, ";"), join(ambition, ";"),
                 court.rolled and "1" or "", join(last, ";"),
                 join(stalled, ";"), join(news, ";"), join(sent, ";"), gov, join(renown, ";"), deeds, join(laws, ";"), join(votes, ";"), join(grudges, "/"), join(book, "/")}, "|")
end

local function split(text, sep)
    local out = {}
    if not text or text == "" then return out end
    for piece in string.gmatch(text, "([^" .. sep .. "]+)") do
        out[#out + 1] = piece
    end
    return out
end

function IC.unpack(faction_key, packed)
    local R = IC.R(faction_key)
    local court = new_court()
    local fields = {}
    for field in string.gmatch(packed .. "|", "([^|]*)|") do
        fields[#fields + 1] = field
    end
    for _, entry in ipairs(split(fields[1] or "", ";")) do
        local bits = split(entry, ",")
        if #bits >= 3 then
            court.houses[bits[1]] = {
                weight  = tonumber(bits[2]) or 0,
                loyalty = tonumber(bits[3]) or IC.TUNE.loyalty_start,
                clock   = tonumber(bits[4]) or 0,
                split   = tonumber(bits[15]) or 0,
                -- Zero means "not named yet"; Lua arrays have no valid index zero.
                head    = tonumber(bits[5]),
                tail    = tonumber(bits[6]),
                confed  = (tonumber(bits[7]) == 1) or nil,
                -- Older seven-field saves have no pressure flag.
                pressed = (tonumber(bits[8]) == 1) or nil,
                protected = tonumber(bits[9]),
                oath_mine   = (tonumber(bits[12]) or 0) > 0
                              and tonumber(bits[12]) or nil,
                oath_theirs = (tonumber(bits[13]) or 0) > 0
                              and tonumber(bits[13]) or nil,
                t1 = tonumber(bits[10]),
                t2 = tonumber(bits[11]),
                snubbed = (tonumber(bits[14]) == 1),
                -- Older fifteen-field saves have made no lord in store.
                stored = (tonumber(bits[16]) == 1) or nil,
                -- The turn a leader was put in the field; older saves put none.
                fielded = (tonumber(bits[17]) or 0) > 0 and tonumber(bits[17]) or nil,
                -- The turn of the last gift; older saves have sent none.
                gifted = (tonumber(bits[18]) or 0) > 0 and tonumber(bits[18]) or nil,
                -- A count Provoke set; older saves have none.
                provoked = (tonumber(bits[19]) == 1) or nil,
                -- The insulting seat; older saves name none until the next drift.
                snub_key = bits[20] ~= "-" and bits[20] or nil,
            }
            if court.houses[bits[1]].protected == 0 then
                court.houses[bits[1]].protected = nil
            end
            if court.houses[bits[1]].t1 == 0 then
                court.houses[bits[1]].t1 = nil
            end
            if court.houses[bits[1]].t2 == 0 then
                court.houses[bits[1]].t2 = nil
            end
            if court.houses[bits[1]].head == 0 then
                court.houses[bits[1]].head = nil
            end
            if court.houses[bits[1]].tail == 0 then
                court.houses[bits[1]].tail = nil
            end
        end
    end
    for _, entry in ipairs(split(fields[2] or "", ";")) do
        local bits = split(entry, ",")
        if #bits >= 2 then court.offices[bits[1]] = tonumber(bits[2]) end
    end
    for _, entry in ipairs(split(fields[3] or "", ";")) do
        local bits = split(entry, ",")
        if #bits >= 2 then
            court.govs[bits[1]] = tonumber(bits[2])
            court.gov_grown[bits[1]] = tonumber(bits[3])
        end
    end
    for _, entry in ipairs(split(fields[4] or "", ";")) do
        local bits = split(entry, ",")
        if #bits >= 2 then court.terms[bits[1]] = tonumber(bits[2]) end
    end
    for _, entry in ipairs(split(fields[5] or "", ";")) do
        local bits = split(entry, ",")
        local cqi, n = tonumber(bits[1]), tonumber(bits[2])
        if cqi and n then court.standing[cqi] = n end
    end
    -- Field 6 is optional so saves from before the event log still load.
    for _, entry in ipairs(split(fields[6] or "", ";")) do
        local bits = split(entry, ",")
        if #bits >= 5 and IC.LOG_KINDS[bits[2]] then
            court.log[#court.log + 1] = {
                turn = tonumber(bits[1]) or 0,
                kind = bits[2],
                slug = bits[3] ~= "-" and bits[3] or nil,
                key  = bits[4] ~= "-" and bits[4] or nil,
                n    = tonumber(bits[5]) or 0,
                -- Older five-field saves kept no names.
                sw   = bits[6] ~= "-" and bits[6] or nil,
                kw   = bits[7] ~= "-" and bits[7] or nil,
            }
        end
    end
    for _, entry in ipairs(split(fields[7] or "", ";")) do
        local bits = split(entry, ",")
        local n = tonumber(bits[2])
        if bits[1] and n then court.prov[bits[1]] = n end
    end
    for _, entry in ipairs(split(fields[8] or "", ";")) do
        local bits = split(entry, ",")
        local cqi, slug = tonumber(bits[1]), bits[2]
        if cqi and IC.AMBITION[slug or ""] then court.ambition[cqi] = slug end
    end
    -- Field 9 is optional: a save from before it is marked by court_rolled.
    court.rolled = (fields[9] == "1") or nil
    -- Field 10 is optional too: a save from before it has no seat to wait for.
    for _, entry in ipairs(split(fields[10] or "", ";")) do
        local bits = split(entry, ",")
        local cqi, ended = tonumber(bits[2]), tonumber(bits[3])
        if bits[1] and cqi and ended then
            court.last[bits[1]] = {cqi = cqi, turn = ended}
        end
    end
    -- Fields 11 and 12 are optional: a save from before them has no stalled
    -- office and no news.
    for _, entry in ipairs(split(fields[11] or "", ";")) do
        local b = split(entry, ",")
        if #b >= 5 then
            court.stalled[b[1]] = {ends = tonumber(b[2]) or 0, of = b[3],
                                   by = b[4] ~= "-" and b[4] or nil,
                                   cause = b[5] ~= "-" and b[5] or nil}
        end
    end
    for _, entry in ipairs(split(fields[12] or "", ";")) do
        local b = split(entry, ",")
        if #b >= 5 then
            court.news[#court.news + 1] = {turn = tonumber(b[1]) or 0,
                kind = b[2], faction = b[3], a = b[4], b = b[5]}
        end
    end
    -- Field 13 is optional: a save from before the missions rests nobody.
    for _, entry in ipairs(split(fields[13] or "", ";")) do
        local b = split(entry, ",")
        local t = tonumber(b[2])
        if b[1] and t then court.sent[b[1]] = t end
    end
    -- Field 14 is optional: a save from before governments has none, and the
    -- court takes its start at its next turn.
    local g = split(fields[14] or "", ",")
    court.gov = R.GOVS[g[1] or ""] and g[1] or nil
    court.gov_pressure = tonumber(g[2]) or 0
    court.gov_toward = R.GOVS[g[3] or ""] and g[3] or nil
    court.gov_cool = tonumber(g[4]) or 0
    court.gov_holds = tonumber(g[5]) or 0
    if R.GOVS[g[6] or ""] then
        court.gov_ask = {gov = g[6], ends = tonumber(g[7]) or 0,
                         party = (g[8] and g[8] ~= "-") and g[8] or nil}
    end
    -- Fields 15 and 16 are optional: a save from before deeds has no renown,
    -- has not shown the introduction, and took no confederation.
    for _, entry in ipairs(split(fields[15] or "", ";")) do
        local b = split(entry, ",")
        local n = tonumber(b[2])
        if b[1] and n and n > 0 then
            court.renown[b[1]] = n
            local got = tonumber(b[3]) or 0
            if got > 0 then court.renown_got[b[1]] = got end
        end
    end
    local d = split(fields[16] or "", ",")
    court.gov_intro = (tonumber(d[1]) == 1) or nil
    court.confed_turn = tonumber(d[2]) or 0
    -- Fields 17 and 18 are optional: a save from before laws holds the start
    -- options and no votes. A law this build no longer has is dropped.
    for _, entry in ipairs(split(fields[17] or "", ";")) do
        local b = split(entry, ",")
        if b[1] == "rest" then
            court.law_rest = tonumber(b[2])
        elseif IC.law_opt(b[1], b[2], faction_key) and b[2] ~= R.LAWS[b[1]].order[1] then
            court.laws[b[1]] = b[2]
        end
    end
    for _, entry in ipairs(split(fields[18] or "", ";")) do
        local b = split(entry, ",")
        if #b >= 7 and IC.law_opt(b[1], b[2], faction_key) then
            local v = {option = b[2], proposer = b[3], ends = tonumber(b[4]) or 0,
                       stance = IC.LAW_SIDES[b[5]] and b[5] or "abstain", won = {}, push = {},
                       answered = (b[8] == "1") or nil}
            if b[6] ~= "-" then
                for _, pair in ipairs(split(b[6], "/")) do
                    local p = split(pair, ":")
                    local cqi = tonumber(p[1])
                    if cqi and (p[2] == "aye" or p[2] == "nay") then v.won[cqi] = p[2] end
                end
            end
            if b[7] ~= "-" then
                for _, pair in ipairs(split(b[7], "/")) do
                    local p = split(pair, ":")
                    local level = tonumber(p[2])
                    if p[1] and level and level >= 1 and level <= #IC.TUNE.law_push_cost then
                        v.push[p[1]] = level
                    end
                end
            end
            court.votes[b[1]] = v
        end
    end
    -- Field 19 is optional: a save from before grudges has none. A wrong this
    -- build does not know is dropped.
    for _, entry in ipairs(split(fields[19] or "", "/")) do
        local slug, list = string.match(entry, "^([%w_]+):(.+)$")
        if slug then
            local book = {}
            for _, g in ipairs(split(list, ";")) do
                local code, t = string.match(g, "^([%w_]+)%.(%d+)$")
                if code and IC.GRUDGE_WORDS[code] then
                    book[#book + 1] = {code = code, turn = tonumber(t)}
                end
            end
            if #book > 0 then court.grudges[slug] = book end
        end
    end
    -- Field 20 is optional: a save from before the Book has crossed no band. A
    -- count past the last band is the last band.
    for _, pair in ipairs(split(fields[20] or "", "/")) do
        local b = split(pair, ":")
        local n = tonumber(b[2])
        if b[1] and n and n >= 1 then
            court.book[b[1]] = math.min(n, #IC.TUNE.book_bands)
        end
    end
    IC.state[faction_key] = court
    return court
end

function IC.save(faction_key)
    cm:set_saved_value("derpy_ic_" .. faction_key, IC.pack(faction_key))
end

function IC.load(faction_key)
    local packed = cm:get_saved_value("derpy_ic_" .. faction_key)
    if packed and packed ~= "" then
        IC.unpack(faction_key, packed)
        -- NOT SAVED, SO REBUILT: IC.turn loads before its
        -- drift, and the drift read shares with no governors in them.
        pcall(IC.refresh_gov_weight, faction_key)
        -- AND A SWITCH TURNED OFF WHILE IT WAS ON DISK: at a load the switches
        -- are read before any court is.
        IC.settle_switches(faction_key)
    end
    return IC.court(faction_key)
end

-- A COURT READ FROM THE SAVE IF IT IS NOT IN MEMORY YET. After a load an AI court
-- is read on its own turn; an event that reaches it earlier in the round would
-- build an empty court and save it over the real one. Every
-- listener that can touch another faction's court calls this first.
function IC.loaded(faction_key)
    if faction_key and not IC.state[faction_key] then IC.load(faction_key) end
end

local function real_faction(faction_key)
    local faction = cm:get_faction(faction_key)
    if not faction then return nil end
    if faction:is_null_interface() then return nil end
    return faction
end

-- THE VOTERS: every living man of the court with influence
-- and a party, richest first.
function IC.law_voters(faction_key)
    local out = {}
    local faction = real_faction(faction_key)
    local ok, list = pcall(function() return faction:character_list() end)
    if not ok or not list then return out end
    for i = 0, list:num_items() - 1 do
        pcall(function()
            local man = list:item_at(i)
            if man and not man:is_null_interface() and man:is_alive() then
                local cqi = man:command_queue_index()
                local n = IC.standing(faction_key, cqi)
                local party = IC.house_of_character(man, faction_key)
                if n > 0 and party then out[#out + 1] = {cqi = cqi, party = party, n = n} end
            end
        end)
    end
    table.sort(out, function(a, b)
        if a.n ~= b.n then return a.n > b.n end
        return a.cqi < b.cqi
    end)
    return out
end

-- HIS PARTY'S LINE: the side its men vote, or nil, and why.
function IC.law_line(faction_key, vote, category, party)
    if party == IC.CROWN then
        if vote.stance == "abstain" then return nil, "crown" end
        return vote.stance, "crown"
    end
    local s = IC.law_stance(category, vote.option, party, faction_key)
    if s then return s, s == "aye" and "for" or "against" end
    if vote.stance == "abstain" then return nil, "no_stance" end
    local house = IC.court(faction_key).houses[party]
    local loyalty = house and house.loyalty or IC.TUNE.loyalty_start
    if loyalty >= IC.TUNE.law_loyal_line then return vote.stance, "loyal" end
    if loyalty < IC.TUNE.law_disloyal_line then
        return vote.stance == "aye" and "nay" or "aye", "disloyal"
    end
    return nil, "torn"
end

function IC.law_mult(level)
    if not level or level <= 0 then return 100 end
    return IC.TUNE.law_push_mult[level] or 100
end

-- THE TALLY. A man won votes his won side at his
-- own influence; a man voting his party's line is multiplied by its level.
function IC.law_tally(faction_key, category, vote)
    vote = vote or (IC.court(faction_key).votes or {})[category]
    local t = {aye = 0, nay = 0, abstain = 0, men = {}}
    if not vote then return t end
    local lines = {}
    for _, m in ipairs(IC.law_voters(faction_key)) do
        if not lines[m.party] then
            lines[m.party] = {IC.law_line(faction_key, vote, category, m.party)}
        end
        local side, why = lines[m.party][1], lines[m.party][2]
        local w = m.n
        local won = vote.won and vote.won[m.cqi]
        if won then
            side, why = won, "won"
        elseif side then
            w = math.floor(m.n * IC.law_mult((vote.push or {})[m.party]) / 100)
        end
        t.men[#t.men + 1] = {cqi = m.cqi, party = m.party, n = m.n, side = side, why = why, w = w}
        if side then t[side] = t[side] + w else t.abstain = t.abstain + m.n end
    end
    return t
end

function IC.law_passes(t) return t.aye > t.nay end

-- WHAT THE COURT WOULD SAY TODAY: the Crown for it, nobody
-- won, nobody pushing.
function IC.law_project(faction_key, category, option)
    return IC.law_tally(faction_key, category,
                        {option = option, stance = "aye", won = {}, push = {}})
end

function IC.law_vote_of(faction_key, category)
    if not IC.laws_on(faction_key) then return nil end
    return (IC.court(faction_key).votes or {})[category]
end

local function law_key(category, vote) return category .. "." .. vote.option end

-- A MAN'S PRICE, or nil and why he cannot be won.
function IC.law_win_price(faction_key, category, cqi)
    local vote = IC.law_vote_of(faction_key, category)
    if not vote then return nil, "law_none" end
    if vote.stance == "abstain" then return nil, "law_abstain" end
    local man = nil
    for _, m in ipairs(IC.law_tally(faction_key, category, vote).men) do
        if m.cqi == cqi then man = m end
    end
    if not man then return nil, "law_no_man" end
    if man.party == IC.CROWN then return nil, "law_crown_man" end
    if vote.won[cqi] then return nil, "law_won" end
    if man.side == vote.stance then return nil, "law_with_you" end
    local amb = IC.TUNE.law_win_ambition[IC.ambition_slug(faction_key, cqi) or "steady"] or 100
    local price = math.floor(man.n * IC.TUNE.law_win_rate * amb / 10000)
    local s = IC.law_stance(category, vote.option, man.party, faction_key)
    if s and s ~= vote.stance then price = price * 2 end
    return math.max(1, price)
end

function IC.law_win(faction_key, category, cqi)
    local price, why = IC.law_win_price(faction_key, category, cqi)
    if not price then return false, why end
    local ok, short = IC.spend_crown(faction_key, price)
    if not ok then return false, "law_purse", short end
    local vote = IC.law_vote_of(faction_key, category)
    vote.won[cqi] = vote.stance
    local party = nil
    for _, m in ipairs(IC.law_tally(faction_key, category, vote).men) do
        if m.cqi == cqi then party = m.party end
    end
    IC.log(faction_key, "law_win", party, law_key(category, vote), price)
    IC.save(faction_key)
    return true
end

function IC.law_push_price(vote, party, level)
    local cost = IC.TUNE.law_push_cost
    local had = (vote.push or {})[party]
    return cost[level] - (had and cost[had] or 0)
end

function IC.law_can_push(faction_key, category, level)
    local vote = IC.law_vote_of(faction_key, category)
    if not vote then return false, "law_none" end
    if not IC.TUNE.law_push_cost[level or 0] then return false, "no such level" end
    if vote.stance == "abstain" then return false, "law_abstain" end
    if level <= (vote.push[IC.CROWN] or 0) then return false, "law_pushed" end
    local price = IC.law_push_price(vote, IC.CROWN, level)
    local total = IC.crown_purse(faction_key)
    if total < price then return false, "law_purse", price - total end
    return true
end

function IC.law_push(faction_key, category, level)
    local ok, why, n = IC.law_can_push(faction_key, category, level)
    if not ok then return false, why, n end
    local vote = IC.law_vote_of(faction_key, category)
    local price = IC.law_push_price(vote, IC.CROWN, level)
    IC.spend_crown(faction_key, price)
    vote.push[IC.CROWN] = level
    IC.log(faction_key, "law_push", IC.CROWN, law_key(category, vote), level)
    IC.save(faction_key)
    return true
end

function IC.law_set_stance(faction_key, category, stance)
    local vote = IC.law_vote_of(faction_key, category)
    if not vote then return false, "law_none" end
    if not IC.LAW_SIDES[stance or ""] then return false, "no such stance" end
    vote.stance = stance
    vote.answered = true
    IC.save(faction_key)
    return true
end

-- THE END OF A VOTE, by tally or by overrule.
function IC.law_settle(faction_key, category, passed)
    local R = IC.R(faction_key)
    local court = IC.court(faction_key)
    local vote = court.votes[category]
    if not vote then return nil end
    court.votes[category] = nil
    local key = law_key(category, vote)
    if passed then
        if vote.option == R.LAWS[category].order[1] then
            court.laws[category] = nil
        else
            court.laws[category] = vote.option
        end
        -- THE LAW'S OWN LISTS, not pairs(court.houses): the order is the data's.
        local o = IC.law_opt(category, vote.option, faction_key) or {}
        for _, slug in ipairs(o.pro or {}) do
            if court.houses[slug] then IC.move_loyalty(faction_key, slug, IC.TUNE.law_pass_gain) end
        end
        for _, slug in ipairs(o.con or {}) do
            if court.houses[slug] then IC.move_loyalty(faction_key, slug, IC.TUNE.law_pass_loss) end
        end
        IC.apply_law_bundles(faction_key)
        IC.log(faction_key, "law_pass", vote.proposer, key, 0)
        IC.feed(faction_key, "law_passed")
    else
        if vote.proposer ~= IC.CROWN then
            IC.move_loyalty(faction_key, vote.proposer, IC.TUNE.law_fail_loss)
        end
        IC.log(faction_key, "law_fail", vote.proposer, key, 0)
        IC.feed(faction_key, "law_failed")
    end
    return passed
end

function IC.law_overrule(faction_key, category, pass)
    local vote = IC.law_vote_of(faction_key, category)
    if not vote then return false, "law_none" end
    local ok, short = IC.spend_crown(faction_key, IC.TUNE.law_overrule_cost)
    if not ok then return false, "law_purse", short end
    local losing = pass and "nay" or "aye"
    local court = IC.court(faction_key)
    local slugs = {}
    for slug in pairs(court.houses) do slugs[#slugs + 1] = slug end
    table.sort(slugs)
    for _, slug in ipairs(slugs) do
        if slug ~= IC.CROWN and IC.law_line(faction_key, vote, category, slug) == losing then
            IC.move_loyalty(faction_key, slug, IC.TUNE.law_overrule_loyalty)
        end
    end
    IC.log(faction_key, "law_overrule", IC.CROWN, law_key(category, vote), pass and 1 or 0)
    IC.law_settle(faction_key, category, pass)
    IC.save(faction_key)
    return true
end

function IC.law_can_propose(faction_key, category, option)
    if not IC.laws_on(faction_key) then return false, "laws_off" end
    if not IC.law_opt(category, option, faction_key) then return false, "no such law" end
    if (IC.court(faction_key).votes or {})[category] then return false, "law_open" end
    if IC.law_in_force(faction_key, category) == option then return false, "law_same" end
    local total = IC.crown_purse(faction_key)
    if total < IC.TUNE.law_propose_cost then
        return false, "law_purse", IC.TUNE.law_propose_cost - total
    end
    return true
end

function IC.law_open(faction_key, category, option, proposer, stance)
    IC.court(faction_key).votes[category] = {option = option, proposer = proposer,
        ends = cm:model():turn_number() + IC.TUNE.law_vote_turns,
        stance = stance, won = {}, push = {}}
    IC.log(faction_key, "law_propose", proposer, category .. "." .. option, 0)
    IC.feed(faction_key, "law_proposed")
end

function IC.law_propose(faction_key, category, option)
    local ok, why, n = IC.law_can_propose(faction_key, category, option)
    if not ok then return false, why, n end
    IC.spend_crown(faction_key, IC.TUNE.law_propose_cost)
    IC.law_open(faction_key, category, option, IC.CROWN, "aye")
    IC.save(faction_key)
    return true
end

-- WHAT A PARTY WOULD PUT TO THE COURT, picked with
-- cm:random_number so every machine picks the same.
function IC.law_party_pick(faction_key, slug)
    local R = IC.R(faction_key)
    if not IC.laws_on(faction_key) then return nil end
    local court = IC.court(faction_key)
    local now = cm:model():turn_number()
    if now - (court.law_rest or 0) < IC.TUNE.law_party_rest then return nil end
    if IC.share(faction_key, slug) < IC.TUNE.law_party_share then return nil end
    local list = {}
    for _, cat in ipairs(R.LAW_ORDER) do
        if not court.votes[cat] then
            for _, opt in ipairs(R.LAWS[cat].order) do
                if opt ~= IC.law_in_force(faction_key, cat)
                   and IC.law_stance(cat, opt, slug, faction_key) == "aye" then
                    list[#list + 1] = {category = cat, option = opt}
                end
            end
        end
    end
    if #list == 0 then return nil end
    return list[cm:random_number(#list, 1)]
end

-- THE PARTIES WITH A STAKE PUSH: one step each, in slug
-- order, when their side is losing or within the margin and they can pay.
function IC.law_party_push(faction_key, category)
    local court = IC.court(faction_key)
    local vote = court.votes[category]
    if not vote then return 0 end
    local slugs = {}
    for slug in pairs(court.houses) do
        if slug ~= IC.CROWN and IC.law_stance(category, vote.option, slug, faction_key) then
            slugs[#slugs + 1] = slug
        end
    end
    table.sort(slugs)
    local steps = 0
    for _, slug in ipairs(slugs) do
        local side = IC.law_stance(category, vote.option, slug, faction_key)
        local other = side == "aye" and "nay" or "aye"
        local level = (vote.push[slug] or 0) + 1
        if IC.TUNE.law_push_cost[level] then
            local t = IC.law_tally(faction_key, category, vote)
            -- OF THE VOTES CAST: abstainers are not "close".
            local margin = math.floor((t.aye + t.nay) * IC.TUNE.law_push_margin / 100)
            local price = IC.law_push_price(vote, slug, level)
            if t[side] - t[other] <= margin and IC.spend_party(faction_key, slug, price) then
                vote.push[slug] = level
                IC.log(faction_key, "law_push", slug, category .. "." .. vote.option, level)
                steps = steps + 1
            end
        end
    end
    return steps
end

-- ONCE A TURN, player courts: votes at their end resolve,
-- the rest are pushed, and the bundles are worn.
function IC.law_turn(faction_key)
    local R = IC.R(faction_key)
    if not IC.laws_on(faction_key) then return nil end
    local court = IC.court(faction_key)
    local now = cm:model():turn_number()
    for _, cat in ipairs(R.LAW_ORDER) do
        local vote = court.votes[cat]
        if vote and now >= vote.ends then
            IC.law_settle(faction_key, cat, IC.law_passes(IC.law_tally(faction_key, cat, vote)))
        elseif vote then
            IC.law_party_push(faction_key, cat)
        end
    end
    IC.apply_law_bundles(faction_key)
end

function IC.member_weight(faction_key, slug)
    if not faction_key or not slug then return 0 end
    local ok_faction, faction = pcall(real_faction, faction_key)
    if not ok_faction or not faction then return 0 end
    local ok_list, list = pcall(function() return faction:character_list() end)
    if not ok_list or not list then return 0 end
    local ok_count, count = pcall(function() return list:num_items() end)
    if not ok_count or not count then return 0 end
    local total = 0
    for i = 0, count - 1 do
        local ok_weight, weight = pcall(function()
            local man = list:item_at(i)
            if not man or man:is_null_interface() or not man:is_alive()
                    or IC.house_of_character(man, faction_key) ~= slug then
                return 0
            end
            local cqi = man:command_queue_index()
            return IC.standing(faction_key, cqi)
                * IC.ambition_factor(faction_key, cqi) / 100
                / IC.TUNE.ambition_standing_per_weight
        end)
        if ok_weight then total = total + weight end
    end
    return total
end

function IC.is_chd(faction)
    local r = IC.race_of(faction)
    return r ~= nil and r.key == "chd"
end

-- A FACTION WHOSE RACE HOLDS A COURT THIS CAMPAIGN RUNS. With the ai_courts
-- setting off, a player's only: an AI court is never rolled, ticked or fed.
function IC.runs_court(faction)
    if not IC.has_court(faction) then return false end
    if IC.TUNE.ai_courts then return true end
    return IC.is_human(faction:name())
end

function IC.present_houses(faction_key)
    local R = IC.R(faction_key)
    local court = IC.court(faction_key)
    local out = {}
    for i = 1, #R.PARTIES do
        if court.houses[R.PARTIES[i]] then out[#out + 1] = R.PARTIES[i] end
    end
    for i = 1, #R.ORIGINS do
        local slug = R.ORIGINS[i].slug
        if R.ORIGINS[i].faction and court.houses[slug]
           and court.houses[slug].confed then
            out[#out + 1] = slug
        end
    end
    return out
end

function IC.is_party(slug, faction_key)
    local R = IC.R(faction_key)
    for i = 1, #R.PARTIES do
        if R.PARTIES[i] == slug then return true end
    end
    return false
end

-- ONCE ROLLED, ALWAYS ROLLED. A court whose last rival is purged or secedes
-- rules alone; without the marker it looks unrolled and the next turn rolls a
-- whole new court. A save from before the marker is
-- marked the first time it is seen with a rival, which is before it can lose
-- its last one.
function IC.court_rolled(faction_key)
    local court = IC.court(faction_key)
    if court.rolled then return true end
    local n = 0
    for slug in pairs(court.houses) do
        if IC.is_party(slug, faction_key) then n = n + 1 end
    end
    if n > 1 then court.rolled = true end
    return n > 1
end

function IC.add_house(faction_key, slug, confed, loyalty)
    local court = IC.court(faction_key)
    if court.houses[slug] then return false end
    court.houses[slug] = {
        weight  = IC.TUNE.weight_start,
        loyalty = math.max(0, math.min(100,
                                       loyalty or IC.TUNE.loyalty_start)),
        clock   = 0,
        confed  = confed or nil,
    }
    IC.save(faction_key)
    return true
end

function IC.remove_house(faction_key, slug)
    local court = IC.court(faction_key)
    if not court.houses[slug] then return false end
    -- ITS RENOWN GOES WITH IT: kept, a purged or seceded party would stand at
    -- the join line and the next lord would bring it straight back.
    if court.renown then court.renown[slug] = nil end
    -- ASKED BEFORE THE DELETE. house_of_cqi answers the Crown for a man whose
    -- party is gone, so asked after it no post would match and a leaver would
    -- keep his seat and his province as a Crown man.
    local seats, provinces = {}, {}
    for office_slug, cqi in pairs(court.offices) do
        if IC.house_of_cqi(faction_key, cqi) == slug then
            seats[#seats + 1] = office_slug
        end
    end
    for province, cqi in pairs(court.govs) do
        if IC.house_of_cqi(faction_key, cqi) == slug then
            provinces[#provinces + 1] = province
        end
    end
    IC.departed[faction_key .. "|" .. slug] = IC.who_was(faction_key, slug)
    court.houses[slug] = nil
    for i = 1, #seats do
        -- AND HIS TITLE, as dismiss takes it: otherwise a stayer keeps the
        -- office trait of a seat he no longer holds.
        local man = IC.character_by_cqi(faction_key, court.offices[seats[i]])
        if man then
            cm:force_remove_trait(cm:char_lookup_str(man), IC.office_trait(seats[i], faction_key))
        end
        court.offices[seats[i]] = nil
        court.terms[seats[i]] = nil
    end
    for i = 1, #provinces do court.govs[provinces[i]] = nil end
    if IC.drop_party_business then IC.drop_party_business(faction_key, slug) end
    -- AND THE BONUSES FOLLOW NOW, not at whatever redraws them next.
    if #seats > 0 then IC.apply_office_bundles(faction_key) end
    if #provinces > 0 then IC.apply_governor_bundles(faction_key) end
    IC.save(faction_key)
    return true
end

function IC.origin_of_character(character)
    if not character or character:is_null_interface() then return nil end
    for _, k in ipairs(IC.RACE_ORDER) do
        local R = IC.RACES[k]
        for i = 1, #R.ORIGINS do
            local slug = R.ORIGINS[i].slug
            if character:has_trait(IC.rkey("house", slug, R)) then return slug, R end
        end
    end
    return nil
end

function IC.bg_of_character(character)
    if not character or character:is_null_interface() then return nil end
    for _, k in ipairs(IC.RACE_ORDER) do
        local R = IC.RACES[k]
        for i = 1, #R.PARTIES do
            local list = R.BACKGROUNDS[R.PARTIES[i]]
            for j = 1, #list do
                if character:has_trait(IC.rkey("bg", list[j], R)) then return list[j], R end
            end
        end
    end
    return nil
end

-- THE MAN ON THE THRONE IS THE CROWN, whatever trade he was dealt: a generic or
-- another mod's lord made faction leader is no legend, and his background put
-- him in a rival party while a lesser man spoke for his own house.
function IC.is_ruler(character, faction_key)
    if not faction_key or not character or character:is_null_interface() then return false end
    local cqi = IC.faction_leader_cqi(faction_key)
    return cqi ~= nil and character:command_queue_index() == cqi
end

function IC.house_of_character(character, faction_key)
    if IC.is_legend(character) or IC.is_ruler(character, faction_key) then return IC.CROWN end
    local origin = IC.origin_of_character(character)
    if origin and faction_key then
        local came_from = IC.faction_for_origin(origin)
        if came_from and came_from ~= faction_key
           and IC.court(faction_key).houses[origin] then
            return origin
        end
    end
    local bg, R = IC.bg_of_character(character)
    if not bg then return nil end
    local party = R.PARTY_OF_BG[bg]
    if not party then return nil end
    if not faction_key then return party end
    if IC.court(faction_key).houses[party] then return party end
    return IC.CROWN
end

IC.KINDS = {"general", "lord", "retainer", "hero"}

function IC.kind_of_character(character)
    if not character or character:is_null_interface() then return nil end
    local ok, general = pcall(function()
        return character:character_type("general")
    end)
    if not ok then return nil end
    local held, force = pcall(function()
        return character:has_military_force()
    end)
    if general then
        if not held then return "lord" end
        return force and "general" or "lord"
    end
    if not held then return "hero" end
    return force and "retainer" or "hero"
end

function IC.character_by_cqi(faction_key, cqi)
    local faction = real_faction(faction_key)
    if not faction then return nil end
    local list = faction:character_list()
    for i = 0, list:num_items() - 1 do
        local character = list:item_at(i)
        if character:command_queue_index() == cqi then return character end
    end
    return nil
end

function IC.house_of_cqi(faction_key, cqi)
    return IC.house_of_character(IC.character_by_cqi(faction_key, cqi),
                                 faction_key)
end

-- THE DEAL. A man goes to the seated party with the FEWEST members, ties
-- rolled. One independent roll per man would let a Conclave start roll the
-- Chain for all six men who are not lords.
--
-- ONE TALLY PER PASS: counted once off the traits, then kept by hand as men
-- are dealt, so a pass never waits on has_trait to answer a trait it has only
-- just added. Filled on first use, so a turn with nobody new counts nothing.
function IC.fill_tally(tally, faction_key)
    local R = IC.R(faction_key)
    if tally.count then return tally end
    tally.count, tally.led = {}, {}
    local seated = IC.present_houses(faction_key)
    for i = 1, #seated do
        local slug = seated[i]
        if R.BACKGROUNDS[slug] then
            tally.count[slug] = 0
            tally.led[slug] = IC.party_leader(faction_key, slug) ~= nil
        end
    end
    local faction = real_faction(faction_key)
    if not faction then return tally end
    local list = faction:character_list()
    for i = 0, list:num_items() - 1 do
        local slug = IC.house_of_character(list:item_at(i), faction_key)
        if slug and tally.count[slug] then tally.count[slug] = tally.count[slug] + 1 end
    end
    return tally
end

-- The party in `pool` with the fewest members, ties rolled.
function IC.fewest(pool, tally)
    local least, best = nil, {}
    for i = 1, #pool do
        local n = tally.count[pool[i]] or 0
        if not least or n < least then
            least, best = n, {pool[i]}
        elseif n == least then
            best[#best + 1] = pool[i]
        end
    end
    if #best == 0 then return nil end
    return best[cm:random_number(#best, 1)]
end

function IC.roll_background(faction_key, tally)
    local R = IC.R(faction_key)
    tally = IC.fill_tally(tally or {}, faction_key)
    local seated = IC.present_houses(faction_key)
    local pool = {}
    for i = 1, #seated do
        if R.BACKGROUNDS[seated[i]] then pool[#pool + 1] = seated[i] end
    end
    if #pool == 0 then pool = {IC.CROWN} end
    local list = R.BACKGROUNDS[IC.fewest(pool, tally)]
    if not list or #list == 0 then return nil end
    return list[cm:random_number(#list, 1)]
end

function IC.fixed_history(character)
    if not character or character:is_null_interface() then return nil end
    local ok, key = pcall(function() return character:character_subtype_key() end)
    if not ok or not key then return nil end
    return IC.LORD_HISTORY[key]
end

function IC.origin_for(character, faction_key)
    local fixed = IC.fixed_history(character)
    if fixed and fixed.origin then return fixed.origin end
    return IC.roll_origin(faction_key)
end

function IC.background_for(character, faction_key, tally)
    local R = IC.R(faction_key)
    local fixed = IC.fixed_history(character)
    if fixed and fixed.bg then return fixed.bg end
    -- Already stamped: stamp_bg would refuse anyway, and the tally below walks
    -- the whole court.
    if IC.bg_of_character(character) then return nil end
    tally = IC.fill_tally(tally or {}, faction_key)
    local bg = IC.leaderless_bg(character, faction_key, tally)
               or IC.roll_background(faction_key, tally)
    local party = bg and R.PARTY_OF_BG[bg]
    if party and tally.count[party] then
        tally.count[party] = tally.count[party] + 1
        if IC.can_lead(character) then tally.led[party] = true end
    end
    return bg
end

-- ROOM FOR ONE MORE: fewer rival parties than rivals_max.
function IC.deed_room(faction_key)
    local R = IC.R(faction_key)
    local court, rivals = IC.court(faction_key), 0
    for i = 1, #R.PARTIES do
        local p = R.PARTIES[i]
        if p ~= IC.CROWN and court.houses[p] then rivals = rivals + 1 end
    end
    return rivals < IC.TUNE.rivals_max
end

-- THE ABSENT PARTY AT THE JOIN LINE with the most renown; IC.PARTIES order
-- breaks a tie.
function IC.deed_waiting(faction_key)
    local R = IC.R(faction_key)
    if not IC.deeds_on(faction_key) or not IC.deed_room(faction_key) then return nil end
    local court = IC.court(faction_key)
    local best, most = nil, 0
    for i = 1, #R.PARTIES do
        local p = R.PARTIES[i]
        local n = IC.renown(faction_key, p)
        if p ~= IC.CROWN and not court.houses[p] and R.BACKGROUNDS[p]
           and n >= IC.TUNE.renown_join_line and n > most then
            best, most = p, n
        end
    end
    return best
end

-- A NEW LORD WHO CAN SPEAK FOR A PARTY, with no history of his own, joins the
-- waiting party; it enters in the same call, so it never stands empty.
function IC.deed_join(character, faction_key)
    local R = IC.R(faction_key)
    if not IC.can_lead(character) or IC.fixed_history(character) then return nil end
    if IC.bg_of_character(character) then return nil end
    local party = IC.deed_waiting(faction_key)
    if not party or not IC.add_house(faction_key, party) then return nil end
    IC.name_party(faction_key, party)
    IC.roll_party_traits(faction_key, party)
    IC.log(faction_key, "drawn", party, nil, IC.renown(faction_key, party))
    IC.feed(faction_key, "party_drawn", IC.party_drawn_key(faction_key, party))
    IC.save(faction_key)
    local list = R.BACKGROUNDS[party]
    return list[cm:random_number(#list, 1)]
end

-- WHO CAN SPEAK FOR A PARTY: a lord, or a garrison commander (IC.party_colonel)
-- - never a legend, who is the Crown's whatever his trade, and never a greenskin.
function IC.can_lead(character)
    if not (IC.is_lordly(character) or IC.is_colonel(character)) then return false end
    if IC.is_legend(character) then return false end
    local key
    pcall(function() key = character:character_subtype_key() end)
    return not (key and IC.NOT_DWARF[key])
end

-- A PARTY ALWAYS HAS A LEADER. A man who could speak for a house goes to one
-- that has nobody to speak for it before anywhere else; a dealt-evenly
-- background leaves most rivals leaderless at campaign start. A garrison
-- commander too, dealt after the lords (stamp_court).
function IC.leaderless_bg(character, faction_key, tally)
    local R = IC.R(faction_key)
    if not faction_key or not IC.can_lead(character) then return nil end
    tally = IC.fill_tally(tally or {}, faction_key)
    local pool = {}
    local seated = IC.present_houses(faction_key)
    for i = 1, #seated do
        local slug = seated[i]
        if slug ~= IC.CROWN and R.BACKGROUNDS[slug] and not tally.led[slug] then
            pool[#pool + 1] = slug
        end
    end
    if #pool == 0 then return nil end
    local list = R.BACKGROUNDS[IC.fewest(pool, tally)]
    return list[cm:random_number(#list, 1)]
end

-- The generic Chaos Dwarf lords a party may be given, of any lord type.
-- IC.REBEL_GENERALS minus its convoy and hobgoblin-army variants.
IC.STORE_LORDS = {
    "wh3_dlc23_chd_overseer",
    "wh3_dlc23_chd_sorcerer_prophet_death",
    "wh3_dlc23_chd_sorcerer_prophet_fire",
    "wh3_dlc23_chd_sorcerer_prophet_hashut",
    "wh3_dlc23_chd_sorcerer_prophet_metal",
}

-- THE RACE'S OWN WHERE IT HAS ONE. The Chaos Dwarf
-- constants stay where they are and answer for a race that names none; IC.R
-- answers the Chaos Dwarfs for a caller with no faction in hand.
function IC.store_lords(faction_key)
    return IC.R(faction_key).STORE_LORDS or IC.STORE_LORDS
end

-- WHAT A STARTING LORD COSTS: the normal recruit price, once. The engine hires
-- a lord already in character_list for nothing and hides the cost on his card, so IC.raise_hired charges this at his hire and
-- ICUI.price_pool_cards writes it on the card. agent_subtypes.cost, every lord
-- IC.STORE_LORDS and DWF.STORE_LORDS can make; gen_iron_court's
-- check_seed_price holds it to CA's DB, since no script call reads a price.
IC.SEED_PRICE = {
    ["wh3_dlc23_chd_overseer"] = 1500,
    ["wh3_dlc23_chd_sorcerer_prophet_death"] = 1500,
    ["wh3_dlc23_chd_sorcerer_prophet_fire"] = 1500,
    ["wh3_dlc23_chd_sorcerer_prophet_hashut"] = 1500,
    ["wh3_dlc23_chd_sorcerer_prophet_metal"] = 1500,
    ["wh_main_dwf_lord"] = 900,
    ["wh_dlc06_dwf_runelord"] = 850,
}

function IC.seed_price(faction_key, cqi)
    local man = IC.character_by_cqi(faction_key, cqi)
    return man and IC.SEED_PRICE[man:character_subtype_key()] or nil
end

function IC.rebel_lord(faction_key)
    return IC.R(faction_key).REBEL_LORD or IC.REBEL_LORD
end

function IC.rebel_personality(faction_key)
    return IC.R(faction_key).REBEL_PERSONALITY or IC.REBEL_PERSONALITY
end

function IC.doctrine_name(faction_key)
    return IC.R(faction_key).MILITARY_DOCTRINE_NAME or "Military Doctrine"
end

-- The Crown lord a leaderless party may take: a lord of any type who holds no
-- office or province, is not the faction leader, not a legend (always the
-- Crown's whatever his trade) and has no fixed history (correct_history would
-- put him back). A lord before a garrison commander (the last resort),
-- then lowest standing first - the Crown keeps its best men.
function IC.idle_crown_lord(faction_key, taken)
    local court = IC.court(faction_key)
    local faction = real_faction(faction_key)
    if not faction then return nil end
    local busy = {}
    for _office, cqi in pairs(court.offices) do busy[cqi] = true end
    for _province, cqi in pairs(court.govs) do busy[cqi] = true end
    local ruler = IC.faction_leader_cqi(faction_key)
    local best, best_standing, best_tier
    local list = faction:character_list()
    for i = 0, list:num_items() - 1 do
        local man = list:item_at(i)
        local kind = man and not man:is_null_interface() and IC.kind_of_character(man)
        local tier = (kind == "general" or kind == "lord") and 1
                     or (kind and IC.is_colonel(man) and 2) or nil
        if tier and not IC.is_legend(man) and not IC.fixed_history(man) then
            local cqi = man:command_queue_index()
            local key
            pcall(function() key = man:character_subtype_key() end)
            local standing = IC.standing(faction_key, cqi)
            if not busy[cqi] and not taken[cqi] and cqi ~= ruler
                    and not (key and IC.NOT_DWARF[key])
                    and IC.house_of_character(man, faction_key) == IC.CROWN
                    and (not best or tier < best_tier
                         or (tier == best_tier and standing < best_standing)) then
                best, best_standing, best_tier = man, standing, tier
            end
        end
    end
    return best
end

-- A PARTY ALWAYS HAS A LEADER. First an idle Crown lord moves over (the repair
-- on load), which is what makes an existing save's leaderless parties led at
-- once. Where there is none, a player's party gets a lord put in the field
-- (IC.field_leader), once per party; after that, and for the AI always, a lord
-- is made in the recruitment pool already carrying the party's background, and
-- leads it once recruited.
-- EXCEPT ON TURN 1, when the lord only goes in the recruit pool: the court is
-- founded on the first tick, before the turn's own men arrive, and a party not
-- yet dealt one would get a lord alone on the map, paying upkeep. On turn 1 the
-- pool lord IS the party's one gift, so no army follows him while he waits;
-- hired, he still gets his recruit rank (IC.raise_hired).
-- A freshly pooled lord is not in character_list, so `stored` is what stops one
-- being made every turn; it clears as soon as the party has a leader.
-- ponytail: one stored lord per party at a time; one left unrecruited when the
-- party finds a leader elsewhere stays in the pool.
function IC.ensure_leaders(faction_key)
    -- NOT WHILE THE COURT IS BEING SEEDED (IC.seed_members): a pass mid-seeding
    -- can move a starting lord to another party while he is wounded, and his
    -- return to the pool is lost. The seeding leads every party itself.
    if IC._seeding[faction_key] then return 0 end
    local R = IC.R(faction_key)
    local court = IC.court(faction_key)
    local now = cm:model():turn_number()
    local made = 0
    -- Men already moved this pass, in case the engine answers has_trait late.
    local taken = {}
    for slug, house in pairs(court.houses) do
        if slug ~= IC.CROWN and R.BACKGROUNDS[slug] then
            local led = IC.party_leader(faction_key, slug)
            local man = not led and IC.idle_crown_lord(faction_key, taken)
            if led then
                house.stored = nil
            elseif man then
                local list = R.BACKGROUNDS[slug]
                local lookup = cm:char_lookup_str(man)
                local old = IC.bg_of_character(man)
                if old then cm:force_remove_trait(lookup, IC.bg_trait(old)) end
                cm:force_add_trait(lookup, IC.bg_trait(list[cm:random_number(#list, 1)]), false)
                taken[man:command_queue_index()] = true
                house.stored = nil
                IC.say("IRON COURT: " .. slug .. " in " .. faction_key .. " had no leader - "
                       .. "cqi " .. man:command_queue_index() .. " moved over from the Crown")
            elseif house.fielded == now then
                -- HIS ARMY IS ON ITS WAY: the spawn lands after this frame.
            elseif not house.fielded and IC.is_human(faction_key) and now > 1
                    and IC.field_leader(faction_key, slug) then
                house.fielded = now
                made = made + 1
            elseif not house.stored and not IC.seeding(faction_key) then
                local lords = IC.store_lords(faction_key)
                local subtype = lords[cm:random_number(#lords, 1)]
                local list = R.BACKGROUNDS[slug]
                local bg = list[cm:random_number(#list, 1)]
                local ok, err = pcall(function()
                    local details = cm:spawn_character_to_pool(faction_key, "", "", "",
                        "", 30, true, "general", subtype, false, "")
                    cm:force_add_trait_to_character_details(details, IC.bg_trait(bg))
                end)
                -- Marked even on a failure: a call that fails once fails every
                -- turn, and one log line per party is enough to see it.
                house.stored = true
                if now <= 1 and IC.is_human(faction_key) then house.fielded = now end
                if ok then made = made + 1 end
                -- A LORD THAT COULD NOT BE MADE is a failure; one waiting is not.
                local log = ok and IC.say or IC.warn
                log("IRON COURT: " .. tostring(slug) .. " in " .. faction_key
                       .. " has no leader - " .. (ok and ("a " .. subtype
                       .. " waits in the lord pool") or ("no lord made: " .. tostring(err))))
            end
        end
    end
    IC.save(faction_key)
    return made
end

-- STARTING MEMBERS, player courts only, both races. A Karaz-a-Karak start has
-- three men, so dealing evenly would give each party one. On turn 1 each party of
-- a player's court rolls a number between IC.TUNE.seed_min and seed_max and is
-- given lords until it has that many men; a party with nobody to speak for it
-- gets one even when it already has enough.
--
-- THE POOL ROUTE, measured live: a lord made on the map, wounded and
-- returned to the pool stays in character_list with his traits - a member, and
-- one who leads - and has no army to pay for. A lord made straight into the pool
-- is in no list until hired, and a hero cannot wait in the pool at
-- all: the Recruit Hero panel lists types, not men. The wound gives him a NEW
-- cqi (2695 came back as 2696), so he is found again by his background.
-- Hiring him fires CharacterRecruited, and IC.raise_hired gives him a fresh
-- recruit's rank where he is hired, once (IC.seeded_lords).
--
-- One lord at a time, so two never want the same spawn tile, with the event
-- feed shut from the first spawn until after the last return. Marked done only
-- at the end; a reload in the middle counts again and makes only what is still
-- missing.
--
-- QUIET BY EVENT AS WELL AS BY CATEGORY, AND AGAIN BEFORE EVERY LORD. Shutting
-- IC.QUIET_FEED once still leaves a Wounded! entry per lord on a Karaz-a-Karak
-- start: the switch is one flag per category, and the seeding runs through the
-- turn-1 start and CA's intro. character_wounded is in
-- wh_event_subcategory_character_deaths and the two trait events in
-- wh_event_subcategory_character_traits (event_feed_events).
IC.SEED_DONE = "derpy_ic_seeded_"
IC.SEED_LORDS = "derpy_ic_seedlords_"
IC.SEED_RETRIES = 6
IC.SEED_QUIET_EVENTS = {"character_wounded", "character_trait_gained", "character_trait_lost"}
IC._seeding = {}
IC._seed_wait = {}
-- The background the next lord born in that faction is made for (ic_born).
IC._seed_bg = {}

function IC.seed_quiet(off)
    for i = 1, #IC.QUIET_FEED do
        cm:disable_event_feed_events(off, IC.QUIET_FEED[i], "", "")
    end
    for i = 1, #IC.SEED_QUIET_EVENTS do
        cm:disable_event_feed_events(off, "", "", IC.SEED_QUIET_EVENTS[i])
    end
end

function IC.seeding(faction_key)
    if (IC.TUNE.seed_max or 0) <= 0 or not IC.is_human(faction_key) then return false end
    if cm:model():turn_number() > 1 then return false end
    return not cm:get_saved_value(IC.SEED_DONE .. faction_key)
end

-- One entry per lord to make, the party's slug, Crown included.
function IC.seed_plan(faction_key)
    local R = IC.R(faction_key)
    local lo, hi = IC.TUNE.seed_min, IC.TUNE.seed_max
    if lo > hi then lo, hi = hi, lo end
    local plan = {}
    local seated = IC.present_houses(faction_key)
    for i = 1, #seated do
        local slug = seated[i]
        if R.BACKGROUNDS[slug] then
            local _lords, members = IC.party_lords(faction_key, slug)
            local want = lo + cm:random_number(hi - lo + 1, 1) - 1 - (members or 0)
            if want < 1 and slug ~= IC.CROWN and not IC.party_leader(faction_key, slug) then
                want = 1
            end
            for _ = 1, want do plan[#plan + 1] = slug end
        end
    end
    return plan
end

function IC.seeded_lords(faction_key)
    local out = {}
    local s = cm:get_saved_value(IC.SEED_LORDS .. faction_key)
    if type(s) == "string" then
        for n in string.gmatch(s, "%d+") do out[tonumber(n)] = true end
    end
    return out
end

function IC.save_seeded_lords(faction_key, set)
    local list = {}
    for cqi in pairs(set) do list[#list + 1] = cqi end
    table.sort(list)
    cm:set_saved_value(IC.SEED_LORDS .. faction_key, table.concat(list, ";"))
end

function IC.seed_members(faction_key)
    if IC._seeding[faction_key] or not IC.seeding(faction_key) then return 0 end
    local plan = IC.seed_plan(faction_key)
    if #plan == 0 then
        cm:set_saved_value(IC.SEED_DONE .. faction_key, true)
        return 0
    end
    IC._seeding[faction_key] = true
    IC.seed_step(faction_key, plan, 1, 0)
    return #plan
end

function IC.seed_finish(faction_key, made, wanted)
    IC._seeding[faction_key] = nil
    IC._seed_wait[faction_key] = nil
    IC._seed_bg[faction_key] = nil
    cm:set_saved_value(IC.SEED_DONE .. faction_key, true)
    -- AFTER the last return's own messages arrive.
    cm:callback(function() IC.seed_quiet(false) end, 2)
    local log = made == wanted and IC.say or IC.warn
    log("IRON COURT: " .. made .. " of " .. wanted .. " starting lords sent to the pool for "
        .. faction_key)
end

function IC.seed_step(faction_key, plan, i, made)
    if i > #plan then return IC.seed_finish(faction_key, made, #plan) end
    IC.seed_quiet(true)
    local slug = plan[i]
    local R = IC.R(faction_key)
    local region = IC.hire_region(real_faction(faction_key))
    local x, y = -1, -1
    if region then
        x, y = cm:find_valid_spawn_location_for_character_from_settlement(
            faction_key, region:name(), false, true, 5)
    end
    if not x or x < 0 then
        IC.warn("IRON COURT: no spawn point for a starting lord of " .. slug)
        return IC.seed_finish(faction_key, made, #plan)
    end
    local lords = IC.store_lords(faction_key)
    local subtype = lords[cm:random_number(#lords, 1)]
    local list = R.BACKGROUNDS[slug]
    local bg = list[cm:random_number(#list, 1)]
    local token = {}
    IC._seed_wait[faction_key] = token
    IC._seed_bg[faction_key] = bg
    local ok, err = pcall(function()
        cm:create_force_with_general(faction_key, "", region:name(), x, y, "general",
            subtype, "", "", "", "", false, function(cqi)
                if IC._seed_wait[faction_key] ~= token then return end
                IC._seed_wait[faction_key] = nil
                IC.seed_land(faction_key, plan, i, made, cqi, bg)
            end)
    end)
    if not ok then
        IC._seed_wait[faction_key] = nil
        IC._seed_bg[faction_key] = nil
        IC.warn("IRON COURT: starting lord for " .. slug .. ": " .. tostring(err))
        return IC.seed_finish(faction_key, made, #plan)
    end
    -- A SPAWN THAT NEVER LANDS must not leave the feed shut for good.
    cm:callback(function()
        if IC._seed_wait[faction_key] ~= token then return end
        IC._seed_wait[faction_key] = nil
        IC._seed_bg[faction_key] = nil
        IC.warn("IRON COURT: a starting lord for " .. slug .. " never arrived")
        IC.seed_step(faction_key, plan, i + 1, made)
    end, 5)
end

function IC.seed_land(faction_key, plan, i, made, cqi, bg)
    local wounded, why = pcall(function()
        local man = IC.character_by_cqi(faction_key, cqi)
        if not man then error("no lord at cqi " .. tostring(cqi)) end
        local lookup = cm:char_lookup_str(man)
        local old = IC.bg_of_character(man)
        if old ~= bg then
            if old then cm:force_remove_trait(lookup, IC.bg_trait(old)) end
            cm:force_add_trait(lookup, IC.bg_trait(bg), false)
        end
        cm:wound_character(lookup, 1)
    end)
    if not wounded then IC.warn("IRON COURT: starting lord " .. tostring(cqi) .. ": " .. tostring(why)) end
    local tries = 0
    local function back()
        local cqi_back, hurt = nil, false
        if wounded then cqi_back, hurt = IC.seed_wounded(faction_key, cqi, bg) end
        if cqi_back then
            if hurt then cm:stop_character_convalescing(cqi_back) end
            local set = IC.seeded_lords(faction_key)
            set[cqi_back] = true
            IC.save_seeded_lords(faction_key, set)
            return IC.seed_step(faction_key, plan, i + 1, made + 1)
        end
        tries = tries + 1
        if wounded and tries < IC.SEED_RETRIES then return cm:callback(back, 0.5) end
        IC.warn("IRON COURT: starting lord " .. tostring(cqi) .. " was not found in the pool")
        IC.seed_step(faction_key, plan, i + 1, made)
    end
    cm:callback(back, 0.5)
end

-- THE WOUNDED MAN OF THIS BACKGROUND MADE AFTER `after`: the lord just wounded,
-- under the cqi the wound gave him.
function IC.seed_wounded(faction_key, after, bg)
    local faction = real_faction(faction_key)
    if not faction then return nil end
    local list = faction:character_list()
    -- NOT is_wounded: on the first live start the first lord of a party came
    -- back from the wound with his army gone and is_wounded false, so he was
    -- never found and never recorded. An armyless lord newer than the one made
    -- is him; he is only sent home if he is convalescing.
    local best, hurt = nil, false
    for i = 0, list:num_items() - 1 do
        local man = list:item_at(i)
        if man and not man:is_null_interface() and not man:has_military_force() then
            local cqi = man:command_queue_index()
            if cqi > after and IC.bg_of_character(man) == bg and (not best or cqi > best) then
                best, hurt = cqi, man:is_wounded()
            end
        end
    end
    return best, hurt
end

-- A LEADER PUT IN THE FIELD. A lord alone at the capital, in his party's trade
-- and at the rank a lord hired there would have, with the character, agent and
-- trait messages held back, the way CA puts down a Mortarch. A pool lord is
-- invisible until hired, so the party would read as leaderless on its card.
--
-- True when the army was asked for. It lands after this frame, when the
-- wrapper's ScriptedForceCreated hands back his cqi - AFTER his own
-- CharacterCreated, whose ic_born deals him a background of its own, which is
-- why the callback puts the party's back rather than trusting the deal.
IC.QUIET_FEED = {"wh_event_category_character", "wh_event_category_agent",
                 "wh_event_category_traits_ancillaries"}

function IC.field_leader(faction_key, slug)
    local R = IC.R(faction_key)
    local region = IC.hire_region(real_faction(faction_key))
    if not region then return false end
    local region_key = region:name()
    local x, y = cm:find_valid_spawn_location_for_character_from_settlement(
        faction_key, region_key, false, true, 5)
    if not x or x < 0 then return false end
    local lords = IC.store_lords(faction_key)
    local subtype = lords[cm:random_number(#lords, 1)]
    local list = R.BACKGROUNDS[slug]
    local bg = list[cm:random_number(#list, 1)]
    local okr, rank = pcall(IC.recruit_rank, faction_key, region_key)
    if not okr then
        IC.warn("IRON COURT: no recruit rank read for " .. faction_key .. ": " .. tostring(rank))
        rank = 0
    end
    for i = 1, #IC.QUIET_FEED do
        cm:disable_event_feed_events(true, IC.QUIET_FEED[i], "", "")
    end
    local ok, err = pcall(function()
        cm:create_force_with_general(faction_key, "", region_key, x, y, "general",
            subtype, "", "", "", "", false, function(cqi)
                local done, why = pcall(function()
                    local man = IC.character_by_cqi(faction_key, cqi)
                    if not man then return end
                    local lookup = cm:char_lookup_str(man)
                    local old = IC.bg_of_character(man)
                    if old ~= bg then
                        if old then cm:force_remove_trait(lookup, IC.bg_trait(old)) end
                        cm:force_add_trait(lookup, IC.bg_trait(bg), false)
                    end
                    -- BY, NOT TO: CA's wrapper calls level_up_agent_rank.
                    if rank > 0 then cm:add_agent_experience(lookup, rank, true) end
                    IC.say("IRON COURT: " .. slug .. " in " .. faction_key .. " had no leader - a "
                           .. subtype .. " takes the field at " .. region_key
                           .. ", " .. rank .. " ranks up")
                end)
                if not done then IC.warn("IRON COURT: leader for " .. slug .. ": " .. tostring(why)) end
            end)
    end)
    -- AFTER THIS FRAME, which is when the spawn's own messages arrive.
    cm:callback(function()
        for i = 1, #IC.QUIET_FEED do
            cm:disable_event_feed_events(false, IC.QUIET_FEED[i], "", "")
        end
    end, 1)
    if not ok then
        IC.warn("IRON COURT: no leader put in the field for " .. slug .. ": " .. tostring(err))
    end
    return ok
end

-- A LORD HIRED FOR A PARTY THAT WAITED ON ONE still gets recruit-rank effects
-- such as rank +3. The engine gives recruit rank to a
-- lord it recruits and not to one the script makes; one the script put in the
-- pool and the player hired has not been measured, so he is raised to AT LEAST
-- the rank a lord hired where he stands would have. At least: a man the engine
-- raised itself is left as he is. A lord only, and only for a party with a lord
-- in store - every other hire is the engine's alone.
function IC.raise_hired(faction_key, character)
    local kind = IC.kind_of_character(character)
    if kind ~= "general" and kind ~= "lord" then return end
    local slug = IC.house_of_character(character, faction_key)
    local house = slug and IC.court(faction_key).houses[slug]
    -- OR ONE OF THE STARTING LORDS (IC.seed_members), raised once: he is
    -- struck off the list at his hire, whatever rank he came in at.
    local seeded = IC.seeded_lords(faction_key)
    local cqi = character:command_queue_index()
    local was = seeded[cqi]
    if was then
        seeded[cqi] = nil
        IC.save_seeded_lords(faction_key, seeded)
        -- THE PRICE HIS CARD SHOWED, once: the engine charged nothing.
        local price = IC.SEED_PRICE[character:character_subtype_key()]
        if price then cm:treasury_mod(faction_key, -price) end
    end
    if not (house and (house.stored or was)) then return end
    local region_key
    pcall(function()
        if character:has_region() then region_key = character:region():name() end
    end)
    if not region_key then
        local home = IC.hire_region(real_faction(faction_key))
        region_key = home and home:name()
    end
    if not region_key then return end
    local want = 1 + IC.recruit_rank(faction_key, region_key)
    local have = character:rank()
    -- BY, NOT TO: CA's wrapper calls level_up_agent_rank.
    if have < want then
        cm:add_agent_experience(cm:char_lookup_str(character), want - have, true)
        IC.say("IRON COURT: " .. slug .. "'s lord in " .. faction_key .. " hired at rank "
               .. have .. " - raised to " .. want .. ", a recruit's at " .. region_key)
    end
end

-- LORD RECRUIT RANK, which the engine gives a lord hired from the pool and not
-- one made by script: measured, rank 1 under a +10 bundle. The sum of
-- IC.RECRUIT_RANK at `region_key`. A "province" source counts only where he is
-- raised; a building counts once for every one standing, the way separate
-- buildings' effects add up; a bundle counts on the faction or on any region.
function IC.recruit_rank(faction_key, region_key)
    local faction = real_faction(faction_key)
    if not faction then return 0 end
    local by = {}
    for i = 1, #IC.RECRUIT_RANK do
        local kind, key, n, reach = unpack(IC.RECRUIT_RANK[i])
        by[kind] = by[kind] or {}
        by[kind][key] = by[kind][key] or {faction = 0, province = 0}
        by[kind][key][reach] = by[kind][key][reach] + n
    end
    local total = 0
    for key, row in pairs(by.technology or {}) do
        if faction:has_technology(key) then total = total + row.faction + row.province end
    end
    for key, row in pairs(by.bundle or {}) do
        if faction:has_effect_bundle(key) then total = total + row.faction + row.province end
    end
    local men = faction:character_list()
    for i = 0, men:num_items() - 1 do
        local man = men:item_at(i)
        for key, row in pairs(by.skill or {}) do
            if man:has_skill(key) then total = total + row.faction + row.province end
        end
    end
    local regions = faction:region_list()
    local here
    for i = 0, regions:num_items() - 1 do
        if regions:item_at(i):name() == region_key then
            here = regions:item_at(i):province_name()
        end
    end
    for i = 0, regions:num_items() - 1 do
        local region = regions:item_at(i)
        local local_ok = here ~= nil and region:province_name() == here
        local function count(row)
            total = total + row.faction + (local_ok and row.province or 0)
        end
        for key, row in pairs(by.bundle or {}) do
            if region:has_effect_bundle(key) then count(row) end
        end
        local slots = region:slot_list()
        for j = 0, slots:num_items() - 1 do
            local slot = slots:item_at(j)
            if slot:has_building() then
                local row = (by.building or {})[slot:building():name()]
                if row then count(row) end
            end
        end
    end
    return total
end

-- EVERY SOURCE IN CA'S DB, as {kind, key, ranks, reach}. Written and held
-- against db.pack by gen_iron_court.check_recruit_rank - never edit by hand.
IC.RECRUIT_RANK = {
    {"building", "wh2_dlc09_tmb_estate_1", 1, "faction"},
    {"building", "wh2_dlc11_foreign_infamy_1", 1, "faction"},
    {"building", "wh2_dlc11_vampirecoast_port_3", 1, "faction"},
    {"building", "wh2_main_def_coldones_2", 1, "faction"},
    {"building", "wh2_main_hef_dragons_1", 1, "faction"},
    {"building", "wh2_main_hef_dragons_2", 2, "faction"},
    {"building", "wh2_main_skv_temple_1", 1, "faction"},
    {"building", "wh2_main_special_altar_of_ultimate_darkness", 1, "faction"},
    {"building", "wh2_main_special_altar_of_ultimate_darkness_vmp", 1, "faction"},
    {"building", "wh2_main_special_altdorf_imperial_palace", 2, "faction"},
    {"building", "wh2_main_special_castle_drachenfels_2", 2, "faction"},
    {"building", "wh2_main_special_castle_drachenfels_nag_2", 2, "faction"},
    {"building", "wh2_main_special_chamber_of_visions", 1, "faction"},
    {"building", "wh2_main_special_clar_karond_lairs_other", 2, "faction"},
    {"building", "wh2_main_special_dorks_rock", 2, "faction"},
    {"building", "wh2_main_special_everqueen_court", 1, "faction"},
    {"building", "wh2_main_special_everqueen_court_def", 1, "faction"},
    {"building", "wh2_main_special_everqueen_court_hef", 1, "faction"},
    {"building", "wh2_main_special_hexoatl_stellar_pyramids", 2, "faction"},
    {"building", "wh2_main_special_hexoatl_stellar_pyramids_other", 1, "faction"},
    {"building", "wh2_main_special_mousillon_merovech", 1, "faction"},
    {"building", "wh2_main_special_naggarond_witch_king_def", 2, "faction"},
    {"building", "wh2_main_special_naggarond_witch_king_hef", 2, "faction"},
    {"building", "wh2_main_special_phoenix_king_court", 2, "faction"},
    {"building", "wh2_main_special_pyramid_of_nagash_other", 3, "faction"},
    {"building", "wh2_main_special_pyramid_of_nagash_vmp", 3, "faction"},
    {"building", "wh2_main_special_shrine_of_asuryan_1_other", 1, "faction"},
    {"building", "wh2_main_special_skavenblight_council13", 2, "faction"},
    {"building", "wh2_main_special_skeggi_hall", 2, "faction"},
    {"building", "wh3_dlc20_woc_dark_fortress_knights_3", 1, "province"},
    {"building", "wh3_dlc23_chd_resource_gold_1", 1, "faction"},
    {"building", "wh3_dlc23_chd_resource_gold_2", 1, "faction"},
    {"building", "wh3_dlc23_chd_resource_gold_3", 2, "faction"},
    {"building", "wh3_dlc23_chd_tower_living_quaters_1", 1, "province"},
    {"building", "wh3_dlc23_chd_tower_living_quaters_2", 2, "province"},
    {"building", "wh3_dlc23_chd_tower_living_quaters_3", 2, "province"},
    {"building", "wh3_dlc23_chd_tower_living_quaters_4", 2, "faction"},
    {"building", "wh3_dlc24_special_celestial_palace_other", 2, "faction"},
    {"building", "wh3_dlc24_special_the_palace_of_scrolls", 2, "faction"},
    {"building", "wh3_dlc25_special_ancestors_hall_1", 1, "faction"},
    {"building", "wh3_dlc26_special_bone_nose_idols_1", 3, "faction"},
    {"building", "wh3_dlc27_hef_special_chamber_of_the_phoenix_crown", 5, "faction"},
    {"building", "wh3_dlc27_sla_dec_palace_characters_1", 5, "province"},
    {"building", "wh3_dlc27_sla_dec_palace_characters_2", 7, "province"},
    {"building", "wh3_dlc27_sla_dec_palace_characters_3", 10, "province"},
    {"building", "wh3_dlc27_special_skeggi_hall_0", 1, "faction"},
    {"building", "wh3_dlc29_special_altar_of_ultimate_darkness_nag", 1, "faction"},
    {"building", "wh3_dlc29_special_hexoatl_stellar_pyramids_skv", 1, "faction"},
    {"building", "wh3_dlc29_special_pyramid_of_nagash_nag_2", 1, "faction"},
    {"building", "wh3_dlc29_special_pyramid_of_nagash_nag_3", 2, "faction"},
    {"building", "wh3_main_kho_infra_champion_1", 1, "province"},
    {"building", "wh3_main_kho_infra_champion_2", 2, "province"},
    {"building", "wh3_main_minor_cult_myrmidia_1", 3, "faction"},
    {"building", "wh3_main_ogr_camp_monster_1", 1, "faction"},
    {"building", "wh3_main_ogr_camp_monster_2", 2, "faction"},
    {"building", "wh3_main_ogr_camp_monster_3", 3, "faction"},
    {"building", "wh3_main_special_celestial_palace", 2, "faction"},
    {"building", "wh3_main_special_ksl_erengrad_2_1", 2, "province"},
    {"building", "wh3_main_special_ksl_erengrad_2_2", 3, "province"},
    {"building", "wh3_main_special_ksl_erengrad_2_3", 4, "province"},
    {"building", "wh3_main_special_ksl_praag_3_1", 2, "province"},
    {"building", "wh3_main_special_ksl_praag_3_2", 3, "province"},
    {"building", "wh3_main_special_ksl_praag_3_3", 4, "province"},
    {"building", "wh_dlc06_grn_boss_3_skarsnik", 2, "faction"},
    {"building", "wh_dlc06_grn_eight_peaks_1", 1, "faction"},
    {"building", "wh_dlc06_grn_eight_peaks_2", 2, "faction"},
    {"building", "wh_dlc06_grn_eight_peaks_3", 4, "faction"},
    {"building", "wh_main_brt_worship_3", 1, "faction"},
    {"building", "wh_main_dwf_resource_gold_4", 1, "faction"},
    {"building", "wh_main_dwf_workshop_3", 1, "faction"},
    {"building", "wh_main_grn_boss_3", 2, "faction"},
    {"building", "wh_main_horde_chaos_weapons_1", 2, "province"},
    {"building", "wh_main_horde_chaos_weapons_2", 4, "province"},
    {"building", "wh_main_nor_worship_2", 1, "province"},
    {"building", "wh_main_nor_worship_3", 1, "faction"},
    {"building", "wh_main_special_bokha_palace", 2, "faction"},
    {"building", "wh_main_special_high_king_throne_hall", 2, "faction"},
    {"bundle", "wh2_dlc09_payload_dilemma_scaly_sacrifice_second", 5, "faction"},
    {"bundle", "wh2_dlc09_ritual_tmb_tahoth", 3, "faction"},
    {"bundle", "wh2_dlc11_minister_cst_first_mate", 3, "faction"},
    {"bundle", "wh2_dlc13_victory_wulfhart", 5, "faction"},
    {"bundle", "wh2_main_faction_boost_reward_level1_lizardmen", 2, "faction"},
    {"bundle", "wh2_main_faction_boost_reward_level2_lizardmen", 4, "faction"},
    {"bundle", "wh2_main_faction_boost_reward_level3_lizardmen", 6, "faction"},
    {"bundle", "wh2_main_queek_karak_owned_true", 2, "faction"},
    {"bundle", "wh3_dlc20_payload_eye_of_the_gods_character_recruit", 10, "faction"},
    {"bundle", "wh3_dlc23_chd_ancestor_relic_of_grimnir_reward_a", 5, "faction"},
    {"bundle", "wh3_dlc24_ritual_cth_mos_balance_faction_gain_doctrine_war", 10, "faction"},
    {"bundle", "wh3_dlc25_dwf_ritual_lord_hero_recruit_rank", 5, "faction"},
    {"bundle", "wh3_dlc26_golgfag_contracts_reward_12", 3, "faction"},
    {"bundle", "wh3_dlc26_payload_skarr_bloodwrath_2", 3, "faction"},
    {"bundle", "wh3_dlc27_dechala_ritual_palace_4", 5, "faction"},
    {"bundle", "wh3_dlc29_ie_victory_conditions_characters_recruit_rank_bundle", 10, "faction"},
    {"bundle", "wh3_dlc29_ie_victory_conditions_lord_recruit_rank_bundle", 10, "faction"},
    {"bundle", "wh3_dlc29_payload_great_mausoleum_discovered", 3, "faction"},
    {"bundle", "wh3_main_bundle_belakor_banished", 14, "faction"},
    {"bundle", "wh3_main_bundle_dae_undivided_02", 3, "faction"},
    {"bundle", "wh3_main_ie_victory_objective_chaos_long", 10, "faction"},
    {"bundle", "wh3_main_minor_cult_myrmidia", 3, "faction"},
    {"bundle", "wh3_main_time_of_legends_capital_buffs", 4, "faction"},
    {"bundle", "wh3_main_time_of_legends_kislev_buffs", 2, "faction"},
    {"bundle", "wh3_main_tzeentch_realm_dilemma_reward_5", 9, "faction"},
    {"bundle", "wh_dlc05_UI_bundle_oak_of_ages_mp_2", 2, "faction"},
    {"bundle", "wh_dlc05_UI_bundle_oak_of_ages_mp_3", 3, "faction"},
    {"bundle", "wh_dlc05_UI_bundle_oak_of_ages_mp_4", 4, "faction"},
    {"bundle", "wh_dlc05_UI_bundle_oak_of_ages_mp_5", 5, "faction"},
    {"bundle", "wh_dlc06_bundle_eight_peaks_recapture", 5, "faction"},
    {"bundle", "wh_dlc07_bretonnia_chivalry_bar_401_600", 1, "faction"},
    {"bundle", "wh_dlc07_bretonnia_chivalry_bar_601_800", 3, "faction"},
    {"bundle", "wh_dlc07_bretonnia_chivalry_bar_801_1000", 5, "faction"},
    {"skill", "wh2_dlc09_skill_tmb_liche_priest_incantation_of_preservation", 1, "faction"},
    {"skill", "wh2_dlc11_skill_cst_lokhir_unique_5", 3, "faction"},
    {"skill", "wh2_dlc11_skill_cst_noctilus_unique_0", 2, "faction"},
    {"skill", "wh2_dlc14_skill_skv_snikch_contract_loopholes", 3, "faction"},
    {"skill", "wh2_dlc16_wef_ariel_campaign_2", 3, "faction"},
    {"skill", "wh2_main_skill_def_malekith_warleader_3", 2, "faction"},
    {"skill", "wh2_main_skill_innate_hef_noble_campaign_7_conscientious", 2, "faction"},
    {"skill", "wh3_dlc23_skill_chd_astragoth_infernal_lord", 3, "faction"},
    {"skill", "wh3_dlc27_skill_innate_hef_noble_campaign_7_conscientious_affinity", 2, "faction"},
    {"skill", "wh3_main_skill_ogr_greasus_unique_overtyrant", 3, "faction"},
    {"skill", "wh_dlc08_skill_chs_lord_unique_archaon_0", 3, "faction"},
    {"skill", "wh_dlc08_skill_emp_lord_unique_karl_0", 3, "faction"},
    {"technology", "tech_dlc14_brt_heroic_duties", 5, "faction"},
    {"technology", "tech_grn_end_5_2", 5, "faction"},
    {"technology", "wh2_dlc11_tech_cst_command_03", 5, "faction"},
    {"technology", "wh2_dlc13_tech_emp_economy_3_a", 3, "faction"},
    {"technology", "wh2_main_tech_def_3_3_1", 2, "faction"},
    {"technology", "wh2_main_tech_hef_2_03", 2, "faction"},
    {"technology", "wh2_main_tech_hef_5_03", 2, "faction"},
    {"technology", "wh2_main_tech_lzd_1_1", 4, "faction"},
    {"technology", "wh2_main_tech_lzd_1_7", 2, "faction"},
    {"technology", "wh2_main_tech_skv_7_1", 2, "faction"},
    {"technology", "wh3_cp1_tech_cth_33_bhashiva", 3, "faction"},
    {"technology", "wh3_dlc20_chs_und_shared_corruption", 3, "faction"},
    {"technology", "wh3_dlc23_tech_chd_sorcery_5", 2, "faction"},
    {"technology", "wh3_dlc27_tech_hef_aislinn_5_03", 2, "faction"},
    {"technology", "wh3_dlc27_tech_nor_cam_leaders", 3, "faction"},
    {"technology", "wh3_dlc27_tech_nor_cul_slaanesh", 5, "faction"},
    {"technology", "wh3_dlc29_chs_nur_glottkin_character_rank", 3, "faction"},
    {"technology", "wh3_main_tech_cth_33", 3, "faction"},
    {"technology", "wh3_main_tech_kho_2_3", 2, "faction"},
    {"technology", "wh3_main_tech_ksl_2_07", 2, "faction"},
    {"technology", "wh3_main_tech_ksl_3_10_prologue", 1, "faction"},
    {"technology", "wh3_main_tech_nur_growth_28", 3, "faction"},
    {"technology", "wh3_main_tech_ogr_0_3_0", 2, "faction"},
    {"technology", "wh3_main_tech_sla_5_1", 3, "faction"},
    {"technology", "wh3_main_tech_tze_1_2", 3, "faction"},
    {"technology", "wh3_main_tech_tze_4_5", 3, "faction"},
    {"technology", "wh_dlc05_tech_1_hoeth", 2, "faction"},
    {"technology", "wh_dlc08_tech_nor_nw_07", 5, "faction"},
    {"technology", "wh_main_tech_dwf_civ_1_3", 3, "faction"},
}

function IC.correct_history(character)
    local want = IC.fixed_history(character)
    if not want then return false end
    if not character or character:is_null_interface() then return false end
    local lookup = cm:char_lookup_str(character)
    local moved = false

    local has = IC.origin_of_character(character)
    if want.origin and has ~= want.origin then
        if has then
            cm:force_remove_trait(lookup, IC.origin_trait(has))
        end
        cm:force_add_trait(lookup, IC.origin_trait(want.origin), false)
        moved = true
    end

    local trade = IC.bg_of_character(character)
    if want.bg and trade ~= want.bg then
        if trade then
            cm:force_remove_trait(lookup, IC.bg_trait(trade))
        end
        cm:force_add_trait(lookup, IC.bg_trait(want.bg), false)
        moved = true
    end
    return moved
end

function IC.roll_origin(faction_key)
    local R = IC.R(faction_key)
    local places = {}
    for i = 1, #R.ORIGINS do
        if not R.ORIGINS[i].faction then
            places[#places + 1] = R.ORIGINS[i].slug
        end
    end
    if #places == 0 then return nil end
    return places[cm:random_number(#places, 1)]
end

function IC.stamp_court(faction_key, attempts)
    local faction = real_faction(faction_key)
    if not faction then return 0 end
    local list = faction:character_list()
    if list:num_items() == 0 then
        attempts = attempts or 0
        if attempts < 6 then
            cm:callback(function() IC.stamp_court(faction_key, attempts + 1) end, 2)
        end
        return 0
    end
    local stamped = 0
    local men = {}
    for i = 0, list:num_items() - 1 do
        local character = list:item_at(i)
        if character and not character:is_null_interface() then
            if IC.correct_history(character) then
                stamped = stamped + 1
            end
            -- Use the fixed-history readers so legendary lords are never rerolled.
            if IC.stamp_origin(character, IC.origin_for(character, faction_key), true) then
                stamped = stamped + 1
            end
            if IC.stamp_ambition(faction_key, character) then
                stamped = stamped + 1
            end
            men[#men + 1] = {man = character, at = i,
                             first = IC.is_lordly(character) and 1
                                     or (IC.is_colonel(character) and 2 or 3)}
        end
    end
    -- LORDS, THEN GARRISON COMMANDERS, THEN EVERYONE ELSE: an empty lead goes to
    -- the best man for it, whatever order character_list hands them over in.
    table.sort(men, function(a, b)
        if a.first ~= b.first then return a.first < b.first end
        return a.at < b.at
    end)
    local tally = {}
    for i = 1, #men do
        local character = men[i].man
        if IC.stamp_bg(character,
                       IC.background_for(character, faction_key, tally), true) then
            stamped = stamped + 1
        end
    end
    return stamped
end

-- QUIET when a whole court is stamped at once (the roll at the start of a
-- campaign, a confederation's men arriving); otherwise a new campaign opens on a
-- Trait Gained card per trait per man. One new recruit still gets his two cards.
function IC.stamp_origin(character, slug, quiet)
    if not slug then return false end
    if not character or character:is_null_interface() then return false end
    if IC.origin_of_character(character) then return false end
    cm:force_add_trait(cm:char_lookup_str(character),
                       IC.origin_trait(slug), not quiet)
    return true
end

function IC.stamp_bg(character, slug, quiet)
    if not slug then return false end
    if not character or character:is_null_interface() then return false end
    if IC.bg_of_character(character) then return false end
    cm:force_add_trait(cm:char_lookup_str(character),
                       IC.bg_trait(slug), not quiet)
    return true
end

function IC.stamp_ambition(faction_key, character)
    if not character or character:is_null_interface() then return false end
    local cqi = character:command_queue_index()
    local court = IC.court(faction_key)
    local slug = IC.ambition_slug(faction_key, cqi)
    local moved = false
    if not slug then
        slug = IC.roll_ambition()
        court.ambition[cqi] = slug
        moved = true
    end
    local want = IC.ambition_trait(slug, faction_key)
    local lookup = cm:char_lookup_str(character)
    for i = 1, #IC.AMBITION_ORDER do
        local key = IC.ambition_trait(IC.AMBITION_ORDER[i], faction_key)
        if key ~= want and character:has_trait(key) then
            cm:force_remove_trait(lookup, key)
            moved = true
        end
    end
    if not character:has_trait(want) then
        cm:force_add_trait(lookup, want, false)
        moved = true
    end
    return moved
end

function IC.office_bundle(slug, faction_key)  return IC.key("office", slug, faction_key) end
function IC.vacancy_bundle(slug, faction_key) return IC.key("vacant", slug, faction_key) end
function IC.office_trait(slug, faction_key)   return IC.key("title", slug, faction_key) end

function IC.standing(faction_key, cqi)
    if not cqi then return 0 end
    return IC.court(faction_key).standing[cqi] or 0
end

local function add_standing_raw(faction_key, cqi, amount)
    if not cqi or not amount or amount == 0 then return nil end
    local court = IC.court(faction_key)
    court.standing[cqi] = math.max(0, (court.standing[cqi] or 0) + amount)
    return court.standing[cqi]
end

function IC.add_standing(faction_key, cqi, amount)
    local now = add_standing_raw(faction_key, cqi, amount)
    if not now then return 0 end
    -- Save here because battles, captures, and rank gains occur between turn starts.
    IC.save(faction_key)
    return now
end

function IC.standing_tier(faction_key, cqi)
    local R = IC.R(faction_key)
    local has = IC.standing(faction_key, cqi)
    for i = 1, #R.TIERS do
        if has >= IC.tier_influence(R.TIERS[i]) then return R.TIERS[i] end
    end
    return 0
end

function IC.standing_trait(tier, faction_key) return IC.key("standing", tier, faction_key) end
function IC.ambition_trait(slug, faction_key) return IC.key("ambition", slug, faction_key) end

function IC.stamp_standing(faction_key, character)
    local R = IC.R(faction_key)
    if not character or character:is_null_interface() then return false end
    local want = IC.standing_trait(
        IC.standing_tier(faction_key, character:command_queue_index()), faction_key)
    if character:has_trait(want) then return false end
    local lookup = cm:char_lookup_str(character)
    for i = 0, #R.TIERS do
        local key = IC.standing_trait(i, faction_key)
        if key ~= want and character:has_trait(key) then
            cm:force_remove_trait(lookup, key)
        end
    end
    cm:force_add_trait(lookup, want, false)
    return true
end

-- WHICH PARTY HE SITS WITH, as a trait on the man: nothing else on the
-- character shows his party. A rolled party's name lives in the save and a
-- trait's in the DB, so there is one trait per tail the roll can land on (the
-- part of "Covenant of the Cold Anvil" that tells two parties apart).
-- tools/gen_iron_court.py reads IC.NAME_TAILS for them.
function IC.member_trait(faction_key, slug)
    if not slug then return nil end
    if slug == IC.CROWN then return IC.key("member", IC.CROWN, faction_key) end
    local house = IC.court(faction_key).houses[slug]
    if not house then return nil end
    -- A CONFEDERATE PARTY keeps its faction's name, as ICUI.house_name draws it.
    if house.confed then return IC.key("member", slug, faction_key) end
    local tails = IC.R(faction_key).NAME_TAILS[slug]
    if not house.tail or not tails or #tails == 0 then return nil end
    -- Wrapped as IC.party_name wraps it, so the trait and the panel agree.
    return IC.key("member", slug .. "_" .. ((house.tail - 1) % #tails + 1), faction_key)
end

-- Every key member_trait can answer for this court's race: every row the DB must carry.
function IC.member_trait_keys(faction_key)
    local R = IC.R(faction_key)
    local keys = {IC.rkey("member", IC.CROWN, R)}
    for i = 1, #R.ORIGINS do
        keys[#keys + 1] = IC.rkey("member", R.ORIGINS[i].slug, R)
    end
    for i = 1, #R.PARTIES do
        local slug = R.PARTIES[i]
        local tails = R.NAME_TAILS[slug]
        if slug ~= IC.CROWN and tails then
            for j = 1, #tails do
                keys[#keys + 1] = IC.rkey("member", slug .. "_" .. j, R)
            end
        end
    end
    return keys
end

-- ONE QUESTION A TURN for a man whose party has not moved; only a man missing
-- the trait he should wear is searched for the one he should not.
function IC.stamp_member(faction_key, character, keys)
    if not character or character:is_null_interface() then return false end
    local want = IC.member_trait(faction_key,
                                 IC.house_of_character(character, faction_key))
    if want and character:has_trait(want) then return false end
    local lookup = cm:char_lookup_str(character)
    local moved = false
    for i = 1, #keys do
        if keys[i] ~= want and character:has_trait(keys[i]) then
            cm:force_remove_trait(lookup, keys[i])
            moved = true
        end
    end
    if want then
        cm:force_add_trait(lookup, want, false)
        moved = true
    end
    return moved
end

function IC.stamp_members(faction_key)
    local faction = real_faction(faction_key)
    if not faction then return 0 end
    local keys = IC.member_trait_keys(faction_key)
    local list = faction:character_list()
    local moved = 0
    for i = 0, list:num_items() - 1 do
        local man = list:item_at(i)
        if man and not man:is_null_interface()
                and IC.stamp_member(faction_key, man, keys) then
            moved = moved + 1
        end
    end
    return moved
end

-- Every courtier, once a turn.
function IC.stamp_standings(faction_key)
    local faction = real_faction(faction_key)
    if not faction then return 0 end
    local list = faction:character_list()
    local moved = 0
    for i = 0, list:num_items() - 1 do
        local one_of = list:item_at(i)
        if one_of and not one_of:is_null_interface() then
            if IC.stamp_standing(faction_key, one_of) then moved = moved + 1 end
        end
    end
    return moved
end

function IC.tier_influence(tier)
    return IC.TUNE.tier_influence[tier] or 0
end

function IC.tier_income(tier)
    return IC.TUNE.tier_income[tier] or 0
end

function IC.tier_rank(tier)
    return IC.TUNE.tier_rank[tier] or 0
end

function IC.office_influence(office_slug, faction_key)
    local office = IC.office_by_slug(office_slug, faction_key)
    if not office then return 0 end
    return IC.tier_influence(office.tier)
end

function IC.office_rank(office_slug, faction_key)
    local office = IC.office_by_slug(office_slug, faction_key)
    if not office then return 0 end
    return IC.tier_rank(office.tier)
end

function IC.candidates(faction_key)
    local faction = real_faction(faction_key)
    local out = {}
    if not faction then return out end
    local court = IC.court(faction_key)
    local busy = {}
    for office_slug, cqi in pairs(court.offices) do
        busy[cqi] = {kind = "office", key = office_slug}
    end
    for province_key, cqi in pairs(court.govs) do
        busy[cqi] = {kind = "gov", key = province_key}
    end
    local list = faction:character_list()
    for i = 0, list:num_items() - 1 do
        local character = list:item_at(i)
        if character and not character:is_null_interface() then
            local cqi = character:command_queue_index()
            local rank = 0
            local ok, r = pcall(function() return character:rank() end)
            if ok and r then rank = r end
            out[#out + 1] = {
                cqi     = cqi,
                rank    = rank,
                kind    = IC.kind_of_character(character),
                slug    = IC.house_of_character(character, faction_key),
                busy    = busy[cqi],
                character = character,
            }
        end
    end
    return out
end

-- The capital, else the first region with a settlement: where a hired officer
-- or a party leader put in the field turns up.
function IC.hire_region(faction)
    if not faction or faction:is_null_interface() then return nil end
    local home = faction:home_region()
    if home and not home:is_null_interface() then
        local at = home:settlement()
        if at and not at:is_null_interface() then return home end
    end
    local regions = faction:region_list()
    for i = 0, regions:num_items() - 1 do
        local region = regions:item_at(i)
        if region and not region:is_null_interface() then
            local at = region:settlement()
            if at and not at:is_null_interface() then return region end
        end
    end
    return nil
end

function IC.hire_settlement(faction)
    local region = IC.hire_region(faction)
    return region and region:settlement() or nil
end

-- A NEW MAN'S INFLUENCE, off the SEAT LADDER. Each tier's level buys that
-- tier's bar, evenly in between; below the lowest level the lowest bar, above
-- the highest the highest. Read off IC.TUNE, so a retuned ladder moves it too.
function IC.recruit_influence(rank, faction_key)
    local ladder = {}
    for _, t in ipairs(IC.R(faction_key).TIERS) do
        ladder[#ladder + 1] = {IC.tier_rank(t), IC.tier_influence(t)}
    end
    table.sort(ladder, function(x, y) return x[1] < y[1] end)
    if #ladder == 0 then return 0 end
    rank = rank or 1
    if rank <= ladder[1][1] then return ladder[1][2] end
    for i = 2, #ladder do
        local a, b = ladder[i - 1], ladder[i]
        if rank <= b[1] then
            return a[2] + math.floor((b[2] - a[2]) * (rank - a[1]) / (b[1] - a[1]))
        end
    end
    return ladder[#ladder][2]
end

-- ONCE, AS HE ARRIVES, and only into a court that has its parties: a man with
-- influence already on the books has earned it, and the start's own cast is
-- dealt by the roll, not priced here.
function IC.price_recruit(faction_key, character)
    if not character or character:is_null_interface() then return end
    local faction = character:faction()
    if not faction or faction:is_null_interface() or not IC.runs_court(faction) then
        return
    end
    if not IC.court_rolled(faction_key) then return end
    local cqi = character:command_queue_index()
    local court = IC.court(faction_key)
    if court.standing[cqi] ~= nil then return end
    court.standing[cqi] = IC.recruit_influence(character:rank(), faction_key)
    IC.save(faction_key)
end

function IC.can_appoint(faction_key, office_slug, cqi)
    local court = IC.court(faction_key)
    local office = IC.office_by_slug(office_slug, faction_key)
    if not office then return false, "no such office" end
    local character = IC.character_by_cqi(faction_key, cqi)
    if not character then return false, "no such character" end
    -- Return the rank shortfall so the panel can explain the refusal.
    local rank_bar = IC.office_rank(office_slug, faction_key)
    if character:rank() < rank_bar then
        return false, "rank", rank_bar - character:rank()
    end
    -- THE BAR IS THE PLAYER'S CLIMB, and only the player can climb it. An AI
    -- lord in the field earns influence_trickle_general, which is 0, so his
    -- only income is battles - and the lowest of the four seats asks 100. A
    -- measured AI court stayed completely empty until turn 20 to 29 while every
    -- party drifted at the no-seat rate from turn 1, and four of eight were
    -- gone before the first seat was ever filled. Raising the trickle does not
    -- reach it either: swept to 8 a turn, the first seat only moves to turn 13
    -- and the same parties still leave.
    --
    -- The rank bar, the term, one-post-per-man and the affinity preference all
    -- still bind the AI. This is the one rule it cannot play around.
    if IC.is_human(faction_key) then
        local need = IC.tier_influence(office.tier)
        local has = IC.standing(faction_key, cqi)
        if has < need then return false, "standing", need - has end
    end
    local wait = IC.renew_wait(faction_key, office_slug, cqi)
    if wait > 0 then return false, "renew", wait end
    return true
end

-- What a seat weighs for the party that holds it. Taking the seat adds this and
-- every way of losing it takes the same back: it once added the claimed
-- party's double and took back the single, and each term leaked the difference.
function IC.office_weight(office_slug, slug, faction_key)
    local office = IC.office_by_slug(office_slug, faction_key)
    local gain = IC.TUNE.weight_per_office
    if office and slug == office.affinity then
        gain = gain * IC.TUNE.weight_affinity_mult
    end
    return gain
end

-- The man whose term in this seat ended last, until someone else takes it.
function IC.is_renewal(faction_key, office_slug, cqi)
    local last = IC.court(faction_key).last[office_slug]
    return last ~= nil and last.cqi == cqi
end

-- Turns before he may take the seat back; 0 when he may, or is not its last man.
function IC.renew_wait(faction_key, office_slug, cqi)
    if not IC.is_renewal(faction_key, office_slug, cqi) then return 0 end
    local last = IC.court(faction_key).last[office_slug]
    return math.max(0, last.turn + IC.tune(faction_key, "renew_wait") - cm:model():turn_number())
end

function IC.appoint(faction_key, office_slug, cqi)
    local ok, why, spare = IC.can_appoint(faction_key, office_slug, cqi)
    if not ok then return false, why, spare end

    local court = IC.court(faction_key)
    local office = IC.office_by_slug(office_slug, faction_key)
    local character = IC.character_by_cqi(faction_key, cqi)
    local renewal = IC.is_renewal(faction_key, office_slug, cqi)

    IC.dismiss(faction_key, office_slug, true)

    court.last[office_slug] = nil
    court.offices[office_slug] = cqi
    court.terms[office_slug] = cm:model():turn_number() + IC.tune(faction_key, "term_turns")
    cm:force_add_trait(cm:char_lookup_str(character), IC.office_trait(office_slug, faction_key), true)

    local slug = IC.house_of_character(character, faction_key)
    if slug and court.houses[slug] then
        court.houses[slug].weight = court.houses[slug].weight
            + IC.office_weight(office_slug, slug, faction_key)
    end
    if not renewal then
        IC.move_loyalty(faction_key, slug, IC.TUNE.loyalty_appointed)
        -- A SEAT THEIR PARTY CLAIMS settles one grudge; a renewal pays no
        -- loyalty and settles nothing.
        if slug == office.affinity then IC.grudge_settle(faction_key, slug, "seat") end
    end
    if slug ~= office.affinity then
        IC.move_loyalty(faction_key, office.affinity, IC.TUNE.loyalty_snubbed)
    end

    IC.log(faction_key, "appoint", slug, office_slug, 0)
    IC.apply_office_bundles(faction_key)
    IC.save(faction_key)
    return true
end

function IC.dismiss(faction_key, office_slug, quiet)
    local court = IC.court(faction_key)
    local cqi = court.offices[office_slug]
    if not cqi then return false end
    local character = IC.character_by_cqi(faction_key, cqi)
    if character then
        cm:force_remove_trait(cm:char_lookup_str(character), IC.office_trait(office_slug, faction_key))
    end
    local slug = IC.house_of_cqi(faction_key, cqi)
    -- A TERM ON ITS LAST TURN IS NOT CUT SHORT: the
    -- card reads "Term ends this turn", and a grudge never fades.
    local ending = IC.term_left(faction_key, office_slug) == 0
    court.offices[office_slug] = nil
    if slug and court.houses[slug] then
        court.houses[slug].weight = math.max(1,
            court.houses[slug].weight - IC.office_weight(office_slug, slug, faction_key))
    end
    if not quiet then
        IC.move_loyalty(faction_key, slug, IC.TUNE.loyalty_dismissed)
        if not ending then IC.grudge_write(faction_key, slug, "dismiss") end
        -- AND HE WAITS FOR IT as a man whose term ended does: otherwise,
        -- dismissed and re-seated, he gets a fresh full term with the seat
        -- never empty.
        court.last[office_slug] = {cqi = cqi, turn = cm:model():turn_number()}
    end
    if not quiet then
        IC.log(faction_key, "dismiss", slug, office_slug, 0)
        IC.apply_office_bundles(faction_key)
        IC.save(faction_key)
    end
    return true
end

function IC.apply_office_bundles(faction_key)
    local R = IC.R(faction_key)
    local court = IC.court(faction_key)
    -- A STALL ENDS HERE TOO, so every call that seats or unseats a man - they
    -- all end in this function - ends a stall aimed at the man who left.
    IC.end_stalls(faction_key)
    for i = 1, #R.OFFICES do
        local slug = R.OFFICES[i].slug
        cm:remove_effect_bundle(IC.office_bundle(slug, faction_key), faction_key)
        cm:remove_effect_bundle(IC.vacancy_bundle(slug, faction_key), faction_key)
        if court.offices[slug] and not court.stalled[slug] then
            cm:apply_effect_bundle(IC.office_bundle(slug, faction_key), faction_key, -1)
        end
    end
end

function IC.filled_offices(faction_key)
    local court, n = IC.court(faction_key), 0
    for _ in pairs(court.offices) do n = n + 1 end
    return n
end

function IC.gov_bundle_base(faction_key) return IC.key("gov", "base", faction_key) end
function IC.gov_bundle_house(slug, faction_key) return IC.key("gov_house", slug, faction_key) end

-- THE GOVERNOR'S BASE BUNDLE, BUILT AT RUNTIME so it grows with his rank. The
-- two effect keys are the ones tools/gen_iron_court.py
-- ships as E_ORDER and E_GDP_PROVINCE, and GOV_BASE_ORDER is GOVERNOR_BASE's
-- order value; gen_iron_court --check holds all four to the generator. The income
-- is PROVINCE-scoped: every vanilla payload put on one province (the Eshin
-- steal-money action, the Glottkin marks) scopes this effect province_to_*, and
-- faction_to_region_own is what the realm-wide bundles use.
IC.GOV_BASE_ORDER = 2
IC.GOV_ORDER_EFFECT = "wh_main_effect_public_order_faction"
IC.GOV_INCOME_EFFECT = "wh_main_effect_economy_gdp_mod_all"
IC.GOV_INCOME_SCOPE = "province_to_region_own"

function IC.gov_rank_bonus(rank, faction_key)
    rank = math.max(0, tonumber(rank) or 0)
    return math.floor(rank / IC.TUNE.gov_rank_order_per),
           math.floor(rank / IC.tune(faction_key, "gov_rank_income_per"))
end

function IC.apply_gov_base(character, region)
    local rank = 0
    local fk = nil
    pcall(function() rank = character:rank() end)
    pcall(function() fk = character:faction():name() end)
    local order, income = IC.gov_rank_bonus(rank, fk)
    local ok = pcall(function()
        local b = cm:create_new_custom_effect_bundle(IC.gov_bundle_base(fk))
        -- NOT is_null_interface: CA's own corruption_swing.lua says that call
        -- is broken on a custom bundle, and a pcall that always fails would
        -- ship the plain bundle forever without a word.
        if not b then error("no custom bundle") end
        b:set_duration(0)
        b:set_effect_value_by_key(IC.GOV_ORDER_EFFECT, IC.GOV_BASE_ORDER + order)
        if income > 0 then
            b:add_effect(IC.GOV_INCOME_EFFECT, IC.GOV_INCOME_SCOPE, income)
        end
        cm:apply_custom_effect_bundle_to_faction_province(b, region)
    end)
    -- THE PLAIN BUNDLE IF THE RUNTIME ONE FAILED: a governor still governs.
    if not ok then
        cm:apply_effect_bundle_to_faction_province(IC.gov_bundle_base(fk), region, -1)
    end
end

local function province_of_character(character)
    if not character or character:is_null_interface() then return nil end
    if not character:has_region() then return nil end
    local region = character:region()
    if not region or region:is_null_interface() then return nil end
    local province = region:province()
    if not province or province:is_null_interface() then return nil end
    return province, region
end


function IC.assign_governor(faction_key, province_key, cqi)
    local court = IC.court(faction_key)
    local character = IC.character_by_cqi(faction_key, cqi)
    if not character then return false, "no such character" end
    -- NO STANDING BAR. A province is not a seat: there are as many of them as
    -- the player has conquered and they do nothing for the house that holds
    -- one but pay its man a wage, so charging the office's currency for one
    -- only keeps the early court's provinces empty. The offices still compete
    -- for the best men; a governorship is what the rest of them do.
    -- THE MAN HE REPLACES LEAVES ON THE RECORD. The Governors tab never appoints
    -- over a sitting governor; the party map's picker does.
    local was = court.govs[province_key]
    if was and was ~= cqi then
        IC.log(faction_key, "gov_off", IC.house_of_cqi(faction_key, was), province_key, 0)
    end
    court.govs[province_key] = cqi
    court.gov_grown = court.gov_grown or {}
    if was ~= cqi then court.gov_grown[province_key] = 0 end
    IC.log(faction_key, "gov_on", IC.house_of_character(character, faction_key),
           province_key, 0)
    IC.save(faction_key)
    IC.apply_governor_bundles(faction_key)
    return true
end

function IC.release_governor(faction_key, province_key)
    local court = IC.court(faction_key)
    if not court.govs[province_key] then return false end
    IC.log(faction_key, "gov_off",
           IC.house_of_cqi(faction_key, court.govs[province_key]),
           province_key, 0)
    court.govs[province_key] = nil
    if court.gov_grown then court.gov_grown[province_key] = nil end
    IC.save(faction_key)
    IC.apply_governor_bundles(faction_key)
    return true
end

function IC.seats_named(faction_key)
    local faction = real_faction(faction_key)
    local out = {}
    if not faction then return out end
    local ok, regions = pcall(function() return faction:region_list() end)
    if not ok or not regions then return out end
    local seen = {}
    local count = 0
    local ok_n, n = pcall(function() return regions:num_items() end)
    if ok_n and n then count = n end
    for i = 0, count - 1 do
        local got, region = pcall(function() return regions:item_at(i) end)
        if got and region and not region:is_null_interface() then
            local okp, province = pcall(function() return region:province() end)
            if okp and province and not province:is_null_interface() then
                local key = province:key()
                if key and not seen[key] then
                    seen[key] = true
                    local name = key
                    local okn, pn = pcall(function() return region:province_name() end)
                    if okn and pn and pn ~= "" then name = pn end
                    out[#out + 1] = {key = key, name = name}
                end
            end
        end
    end
    return out
end

-- A REGION OF `province_key` THE FACTION HOLDS, or nil.
function IC.held_region(faction_key, province_key)
    local faction = real_faction(faction_key)
    if not faction or not province_key then return nil end
    local found = nil
    pcall(function()
        local list = faction:region_list()
        for i = 0, list:num_items() - 1 do
            local region = list:item_at(i)
            if region and not region:is_null_interface()
                    and region:province():key() == province_key then
                found = region
                return
            end
        end
    end)
    return found
end

function IC.seats(faction_key)
    local out = {}
    for _, seat in ipairs(IC.seats_named(faction_key)) do
        out[#out + 1] = seat.key
    end
    return out
end

function IC.province_loyalty(faction_key, province_key)
    local court = IC.court(faction_key)
    local n = court.prov and court.prov[province_key]
    if n == nil then return IC.TUNE.prov_loyalty_start end
    return n
end

function IC.province_party(faction_key, province_key)
    local cqi = IC.court(faction_key).govs[province_key]
    if not cqi then return nil end
    return IC.house_of_cqi(faction_key, cqi)
end

function IC.tick_provinces(faction_key)
    local court = IC.court(faction_key)
    court.prov = court.prov or {}
    local held = {}
    for _, key in ipairs(IC.seats(faction_key)) do held[key] = true end
    for key in pairs(court.prov) do
        if not held[key] then court.prov[key] = nil end
    end
    for key in pairs(held) do
        local was = IC.province_loyalty(faction_key, key)
        local slug = IC.province_party(faction_key, key)
        local house = slug and court.houses[slug] or nil
        local delta
        if not house then
            delta = IC.TUNE.prov_drift_none
        elseif (house.clock or 0) > 0 then
            delta = IC.TUNE.prov_drift_angry
        else
            delta = IC.TUNE.prov_gain_governed
        end
        court.prov[key] = math.max(0,
            math.min(IC.TUNE.prov_loyalty_max, was + delta))
    end
end

function IC.reconcile_governors(faction_key)
    local court = IC.court(faction_key)
    local held = {}
    for _, key in ipairs(IC.seats(faction_key)) do held[key] = true end

    for province_key, cqi in pairs(court.govs) do
        local drop = false
        if not held[province_key] then
            drop = true                       -- province lost, razed or never held
        else
            local character = IC.character_by_cqi(faction_key, cqi)
            if not character then
                drop = true                   -- dead, or gone with a seceded house
            else
            end
        end
        if drop then court.govs[province_key] = nil end
    end
    IC.save(faction_key)
end

function IC.governor_active(faction_key, province_key)
    local court = IC.court(faction_key)
    local cqi = court.govs[province_key]
    if not cqi then return false end
    local character = IC.character_by_cqi(faction_key, cqi)
    if not character then return false end
    -- ONLY A LORD IN THE FIELD CAN BE AWAY. A garrison
    -- commander never leaves his settlement, a lord back in the pool has no
    -- place on the map at all, and a hero governs from wherever he is. Seen
    -- live: six of seven governors "away", all colonels or pool lords.
    if IC.kind_of_character(character) ~= "general" then return true end
    local province = province_of_character(character)
    return province ~= nil and province:key() == province_key
end

-- The commandment on a province, from any region of it the faction holds:
-- every region of a province reports the same edict (measured live).
function IC.province_edict(faction_key, province_key)
    local faction = real_faction(faction_key)
    if not faction then return nil end
    local regions = faction:region_list()
    for i = 0, regions:num_items() - 1 do
        local region = regions:item_at(i)
        if region:province():key() == province_key then
            return region:get_active_edict_key()
        end
    end
    return nil
end

function IC.governor_edict(faction_key, province_key)
    if not IC.governor_active(faction_key, province_key) then return nil end
    local cqi = IC.court(faction_key).govs[province_key]
    local character = IC.character_by_cqi(faction_key, cqi)
    if not character then return nil end
    local ok, key = pcall(function()
        -- A lord in the field stands in the province, so his own region
        -- answers. A colonel, a pool lord or a hero may be anywhere or nowhere.
        if IC.kind_of_character(character) ~= "general" then
            return IC.province_edict(faction_key, province_key)
        end
        local region = character:region()
        if not region or region:is_null_interface() then return nil end
        return region:get_active_edict_key()
    end)
    if not ok or not key or key == "" then return nil end
    return key
end

-- THE SETTLEMENT LEVELS A FACTION HOLDS IN EACH PROVINCE, in one walk of its
-- regions. A settlement's level is its primary building's building_level() + 1:
-- the value counts from 0. A ruin - a null building - counts 0. One pcall per
-- region, so a region that fails to answer costs its own levels and nothing else.
function IC.province_levels(faction_key)
    local out = {}
    local ok_f, faction = pcall(real_faction, faction_key)
    if not ok_f or not faction then return out end
    local ok_l, list = pcall(function() return faction:region_list() end)
    if not ok_l or not list then return out end
    local ok_n, n = pcall(function() return list:num_items() end)
    for i = 0, (ok_n and n or 0) - 1 do
        pcall(function()
            local region = list:item_at(i)
            if not region or region:is_null_interface() then return end
            local key = region:province():key()
            local level = 0
            local b = region:settlement():primary_slot():building()
            if b and not b:is_null_interface() then level = b:building_level() + 1 end
            out[key] = (out[key] or 0) + level
        end)
    end
    return out
end

-- WHAT A GOVERNORSHIP OVER `levels` SETTLEMENT LEVELS ADDS TO ITS PARTY.
function IC.gov_weight_of(levels)
    return math.max(1, math.ceil((levels or 0) / IC.TUNE.gov_levels_per_weight))
end

-- WHAT EACH GOVERNOR HAS GROWN SO FAR, capped at his province's worth. A
-- province that loses levels loses the weight at once; one that gains them is
-- climbed a step a turn, like any new governorship.
function IC.gov_grown_weight(court, province_key, levels)
    local worth = IC.gov_weight_of(levels[province_key])
    local grown = court.gov_grown and court.gov_grown[province_key]
    if grown == nil then return worth end
    return math.min(worth, grown)
end

-- ONCE A TURN (IC.turn): every governor a step nearer his province's worth.
function IC.grow_governors(faction_key)
    local court = IC.court(faction_key)
    court.gov_grown = court.gov_grown or {}
    local levels = IC.province_levels(faction_key)
    for province_key in pairs(court.govs) do
        local grown = court.gov_grown[province_key]
        if grown ~= nil then
            court.gov_grown[province_key] = math.min(IC.gov_weight_of(levels[province_key]),
                grown + IC.TUNE.gov_weight_per_turn)
        end
    end
end

function IC.refresh_gov_weight(faction_key)
    local court = IC.court(faction_key)
    for _, house in pairs(court.houses) do house.gov_weight = 0 end
    local levels = IC.province_levels(faction_key)
    for province_key, cqi in pairs(court.govs) do
        local slug = IC.house_of_cqi(faction_key, cqi)
        local house = slug and court.houses[slug]
        if house then
            house.gov_weight = house.gov_weight + IC.gov_grown_weight(court, province_key, levels)
        end
    end
end

-- OFF EVERY PROVINCE. The bundles go on per province, so they come off
-- per province: a faction-wide removal never touches them, and a province
-- would keep its last governor's bonus for ever.
-- One region per province is enough: CA removes from "the portion of the
-- province owned by the owner of the specified region".
function IC.clear_gov_bundles(faction_key)
    local R = IC.R(faction_key)
    pcall(function()
        local faction = real_faction(faction_key)
        if not faction then return end
        local list = faction:region_list()
        local seen = {}
        for i = 0, list:num_items() - 1 do
            local region = list:item_at(i)
            local province = region and not region:is_null_interface()
                             and region:province_name()
            if province and not seen[province] then
                seen[province] = true
                cm:remove_effect_bundle_from_faction_province(IC.gov_bundle_base(faction_key), region)
                for j = 1, #R.PARTIES do
                    cm:remove_effect_bundle_from_faction_province(
                        IC.gov_bundle_house(R.PARTIES[j], faction_key), region)
                end
            end
        end
    end)
end

-- A COURT SWITCHED OFF comes off the map whole: otherwise a save loaded with AI
-- courts off stops running them and leaves every office, control and governor
-- bonus and every office title on for good. Party and
-- trade traits are who a man is and stay.
function IC.dismantle(faction_key)
    local R = IC.R(faction_key)
    IC.loaded(faction_key)
    local court = IC.court(faction_key)
    for i = 1, #R.OFFICES do
        local slug = R.OFFICES[i].slug
        cm:remove_effect_bundle(IC.office_bundle(slug, faction_key), faction_key)
        cm:remove_effect_bundle(IC.vacancy_bundle(slug, faction_key), faction_key)
        local man = court.offices[slug] and IC.character_by_cqi(faction_key, court.offices[slug])
        if man then
            pcall(function()
                cm:force_remove_trait(cm:char_lookup_str(man), IC.office_trait(slug, faction_key))
            end)
        end
    end
    for i = 1, #IC.CONTROL do
        cm:remove_effect_bundle(IC.control_bundle(IC.CONTROL[i].slug, faction_key), faction_key)
    end
    -- THE GOVERNMENT AND THE LAWS TOO: a player's court switched off would keep
    -- both, and nothing else takes them off.
    local race = IC.R(faction_key)
    for _, g in ipairs(race.GOV_ORDER) do
        cm:remove_effect_bundle(IC.key("doctrine", g, faction_key), faction_key)
    end
    for _, cat in ipairs(race.LAW_ORDER) do
        for _, opt in ipairs(race.LAWS[cat].order) do
            cm:remove_effect_bundle(IC.key("law", cat .. "_" .. opt, faction_key), faction_key)
        end
    end
    IC.clear_gov_bundles(faction_key)
    IC.forget_court(faction_key)
    IC.say("IRON COURT: AI courts are off - " .. tostring(faction_key)
           .. "'s court taken off the map")
end

function IC.apply_governor_bundles(faction_key)
    local R = IC.R(faction_key)
    local court = IC.court(faction_key)
    IC.refresh_gov_weight(faction_key)

    IC.clear_gov_bundles(faction_key)

    for province_key, cqi in pairs(court.govs) do
        local character = IC.character_by_cqi(faction_key, cqi)
        -- THE PANEL'S OWN TEST. A hero, a garrison commander or a lord in the
        -- pool governs from wherever he is, so a bonus on the region the man
        -- stands in would leave most governors giving nothing.
        -- Any region of the province will do: CA applies to "the portion of the
        -- province owned by the owner of the specified region".
        local region = character and IC.governor_active(faction_key, province_key)
                       and IC.held_region(faction_key, province_key)
        if region then
            IC.apply_gov_base(character, region)
            local slug = IC.house_of_character(character, faction_key)
            if slug and R.BACKGROUNDS[slug] then
                cm:apply_effect_bundle_to_faction_province(
                    IC.gov_bundle_house(slug, faction_key), region, -1)
            end
        end
    end
end

function IC.trickle_for(character, faction_key)
    if not character or character:is_null_interface() then
        return IC.TUNE.influence_trickle_general
    end
    -- A garrison commander's garrison is a force, but he never leaves home.
    if IC.is_colonel(character) then return IC.tune(faction_key, "influence_trickle") end
    local ok, has = pcall(function() return character:has_military_force() end)
    if not ok or has then return IC.TUNE.influence_trickle_general end
    return IC.tune(faction_key, "influence_trickle")
end

function IC.income(faction_key)
    local faction = real_faction(faction_key)
    if not faction then return 0 end
    local court = IC.court(faction_key)

    -- Keep the character here because influence income depends on army status.
    local alive = {}
    local list = faction:character_list()
    for i = 0, list:num_items() - 1 do
        local one_of = list:item_at(i)
        if one_of and not one_of:is_null_interface() then
            alive[one_of:command_queue_index()] = one_of
        end
    end
    for cqi in pairs(court.standing) do
        if not alive[cqi] then court.standing[cqi] = nil end
    end
    for cqi in pairs(court.ambition or {}) do
        if not alive[cqi] then court.ambition[cqi] = nil end
    end

    local paid = 0
    for cqi, man in pairs(alive) do
        local trickle = IC.trickle_for(man, faction_key)
        add_standing_raw(faction_key, cqi, trickle)
        paid = paid + trickle
    end
    for office_slug, cqi in pairs(court.offices) do
        local office = IC.office_by_slug(office_slug, faction_key)
        if office and alive[cqi] then
            local wage = IC.tier_income(office.tier)
            add_standing_raw(faction_key, cqi, wage)
            paid = paid + wage
        end
    end
    for _province, cqi in pairs(court.govs) do
        if alive[cqi] then
            add_standing_raw(faction_key, cqi, IC.tune(faction_key, "governor_income"))
            paid = paid + IC.tune(faction_key, "governor_income")
        end
    end
    return paid
end

function IC.expire_terms(faction_key)
    local court = IC.court(faction_key)
    local turn = cm:model():turn_number()
    local done = {}
    for office_slug, cqi in pairs(court.offices) do
        local ends = court.terms[office_slug]
        if ends and turn >= ends then
            done[#done + 1] = {slug = office_slug, cqi = cqi}
        end
    end
    for i = 1, #done do
        local slug = IC.house_of_cqi(faction_key, done[i].cqi)
        -- An expired term is not a dismissal and does not anger the holder's party.
        IC.dismiss(faction_key, done[i].slug, true)
        court.terms[done[i].slug] = nil
        court.last[done[i].slug] = {cqi = done[i].cqi, turn = turn}
        IC.log(faction_key, "term", slug, done[i].slug, 0)
    end
    if #done > 0 then
        IC.feed(faction_key, "office_lost",
                #done == 1 and IC.office_title_key(done[1].slug, faction_key) or nil)
    end
    return #done
end

-- The seats whose terms end at the next turn start, in IC.OFFICES' order.
function IC.terms_ending(faction_key)
    local R = IC.R(faction_key)
    local court = IC.court(faction_key)
    local turn = cm:model():turn_number()
    local out = {}
    for i = 1, #R.OFFICES do
        local slug = R.OFFICES[i].slug
        local ends = court.offices[slug] and court.terms[slug]
        if ends and ends - turn == 1 then out[#out + 1] = slug end
    end
    return out
end

-- A TERM THAT ENDS NEXT TURN, said this turn: the seat
-- empties at the next turn start whatever the player does, and its man cannot
-- take it straight back. One card for all of them; it names the seat when there
-- is only one.
function IC.warn_terms(faction_key)
    if not IC.is_human(faction_key) then return 0 end
    local ending = IC.terms_ending(faction_key)
    if #ending == 0 then return 0 end
    IC.feed(faction_key, "term_soon",
            #ending == 1 and IC.office_title_key(ending[1], faction_key) or nil)
    return #ending
end

function IC.term_left(faction_key, office_slug)
    local court = IC.court(faction_key)
    if not court.offices[office_slug] then return nil end
    local ends = court.terms[office_slug]
    if not ends then return nil end
    return math.max(0, ends - cm:model():turn_number())
end

function IC.move_loyalty(faction_key, slug, delta)
    if not slug or not delta or delta == 0 then return false end
    local house = IC.court(faction_key).houses[slug]
    if not house then return false end
    local was = house.loyalty or IC.TUNE.loyalty_start
    house.loyalty = math.max(0, math.min(100, was + delta))
    if slug ~= IC.CROWN
       and was > IC.TUNE.loyalty_warn
       and house.loyalty <= IC.TUNE.loyalty_warn then
        IC.feed(faction_key, "loyalty_warn")
    end
    return house.loyalty ~= was
end

function IC.loyalty_terms(faction_key, slug)
    local R = IC.R(faction_key)
    local court = IC.court(faction_key)
    local terms, snub_key = {}, nil
    local house = court.houses[slug or ""]
    if not house then return terms, nil end

    local held = 0
    for _office_slug, cqi in pairs(court.offices) do
        if IC.house_of_cqi(faction_key, cqi) == slug then held = held + 1 end
    end
    if held > 0 then
        terms[#terms + 1] = {
            label = held == 1 and "A seat at court"
                    or string.format("%d seats at court", held),
            n = held * IC.TUNE.loyalty_gain_office}
    else
        terms[#terms + 1] = {label = "No seat at court",
                             n = IC.TUNE.loyalty_drift_none}
    end

    local govs, doctrine = 0, 0
    for province_key, cqi in pairs(court.govs) do
        if IC.house_of_cqi(faction_key, cqi) == slug then
            govs = govs + 1
            if IC.governor_edict(faction_key, province_key)
                    == R.MILITARY_DOCTRINE then
                doctrine = doctrine + 1
            end
        end
    end
    if govs > 0 then
        terms[#terms + 1] = {
            label = govs == 1 and "A province governed"
                    or string.format("%d provinces governed", govs),
            n = govs * IC.TUNE.loyalty_gain_office}
    end
    if doctrine > 0 then
        terms[#terms + 1] = {
            label = doctrine == 1 and IC.doctrine_name(faction_key)
                    or string.format("%s in %d provinces", IC.doctrine_name(faction_key), doctrine),
            n = doctrine * IC.TUNE.loyalty_military_doctrine,
        }
    end

    for i = 1, #R.OFFICES do
        local office = R.OFFICES[i]
        if office.affinity == slug then
            local holder = court.offices[office.slug]
            if holder and IC.house_of_cqi(faction_key, holder) ~= slug then
                terms[#terms + 1] = {label = "Claimed office held by a rival",
                                     n = IC.TUNE.loyalty_affinity_snub,
                                     key = office.slug}
                snub_key = office.slug
            end
        end
    end

    local ctx = {held = held, govs = govs, snubbed = (snub_key ~= nil),
                 control = IC.control(faction_key),
                 sworn = IC.protected_for(faction_key, slug)}
    for _, which in ipairs({house.t1, house.t2}) do
        local trait = R.PARTY_TRAITS[which or 0]
        if trait then
            -- Isolate trait callbacks so one bad rule cannot abort the faction turn.
            local ok, value = pcall(trait.n, ctx)
            if ok and type(value) == "number" then
                terms[#terms + 1] = {
                    label = trait.name, note = trait.blurb, trait = trait.key,
                    n = value * IC.TUNE.party_trait_scale}
            end
        end
    end
    if house.oath_mine and house.oath_theirs then
        terms[#terms + 1] = {
            label = "Blood-Oath",
            note = "The oath holds while both men live.",
            n = IC.TUNE.plot_oath_loyalty}
    end

    -- GRUDGES AND KINSHIP: a line per
    -- grudge in the party's book, and the kinship every party of a Dwarf
    -- court shares. The first grudge carries the way out as its note.
    local dwarf = IC.race_key(faction_key) == "dwf"
    if dwarf then
        for i, g in ipairs(IC.grudges(faction_key, slug)) do
            terms[#terms + 1] = {
                label = string.format("Grudge: %s, turn %d",
                                      IC.GRUDGE_WORDS[g.code] or g.code, g.turn),
                note = i == 1 and "A grudge never fades. Pay the Weregild, or seat "
                    .. "their man in an office they claim." or nil,
                n = IC.TUNE.grudge_loyalty}
        end
        terms[#terms + 1] = {label = "Kin of the Karak", n = IC.TUNE.kin_loyalty}
    end

    local lead = IC.leader_trait(faction_key, slug)
    if lead then
        terms[#terms + 1] = {
            label = lead.name, note = lead.blurb, trait = lead.key,
            leader = true,
            n = (IC.LEADER_TRAIT_N[lead.key] or 0) * IC.TUNE.party_trait_scale}
    end
    return terms, snub_key
end

function IC.loyalty_net(terms)
    local net = 0
    for i = 1, #(terms or {}) do net = net + (terms[i].n or 0) end
    return net
end

function IC.drift_loyalty(faction_key)
    local court = IC.court(faction_key)
    for slug, house in pairs(court.houses) do
        local terms, snub_key = IC.loyalty_terms(faction_key, slug)
        IC.move_loyalty(faction_key, slug, IC.loyalty_net(terms))
        local snubbed = (snub_key ~= nil)
        if snubbed ~= (house.snubbed == true) then
            IC.log(faction_key, snubbed and "snub_on" or "snub_off",
                   slug, snub_key or house.snub_key, 0)
            if snubbed then
                IC.feed(faction_key, "snub",
                        snub_key and IC.office_by_slug(snub_key, faction_key)
                        and IC.office_title_key(snub_key, faction_key) or nil)
            end
            house.snubbed = snubbed
        end
        house.snub_key = snub_key
    end
end

function IC.control(faction_key)
    local court = IC.court(faction_key)
    if not court.houses[IC.CROWN] then return 0 end
    return math.floor(IC.share(faction_key, IC.CROWN) + 0.5)
end

function IC.control_band(faction_key)
    local n = IC.control(faction_key)
    for i = 1, #IC.CONTROL do
        if n >= IC.CONTROL[i].floor then return IC.CONTROL[i].slug end
    end
    return IC.CONTROL[#IC.CONTROL].slug
end

function IC.control_bundle(slug, faction_key) return IC.key("control", slug, faction_key) end

function IC.apply_control_bundle(faction_key)
    local want = IC.control_band(faction_key)
    for i = 1, #IC.CONTROL do
        cm:remove_effect_bundle(IC.control_bundle(IC.CONTROL[i].slug, faction_key),
                                faction_key)
    end
    cm:apply_effect_bundle(IC.control_bundle(want, faction_key), faction_key, -1)
    return want
end

function IC.strongest_rival(faction_key)
    local court = IC.court(faction_key)
    local seated = IC.present_houses(faction_key)
    local best, best_weight = nil, nil
    for i = 1, #seated do
        local slug = seated[i]
        if slug ~= IC.CROWN then
            local w = IC.house_weight(faction_key, slug)
            if best_weight == nil or w > best_weight then
                best, best_weight = slug, w
            end
        end
    end
    return best
end

function IC.control_pressure(faction_key)
    local n = IC.control(faction_key)
    if n >= IC.TUNE.pressure_below then return 0 end
    local chance = (IC.TUNE.pressure_below - n) * IC.TUNE.pressure_per_point
    if chance > IC.TUNE.pressure_max then chance = IC.TUNE.pressure_max end
    return chance
end

-- cm:random_number takes maximum first and is multiplayer-safe.
function IC.tick_pressure(faction_key)
    local court = IC.court(faction_key)
    -- NOT THE AI'S PROBLEM, because pressure is a threat with an answer and the
    -- AI holds none of the answers: a player losing control takes seats for the
    -- Crown, sacks a rival or discredits him, and all three are panel moves.
    -- The Crown claims NO office of the fourteen, so a court that fills up
    -- hands weight to rivals and to nobody else - which means the better the AI
    -- ran its court, the faster its strongest party was pressed. Measured: with
    -- the seats filling from turn 1, forge left on turn 11 and legion on turn
    -- 17, both at 100 loyalty, because a pressed house secedes whatever it
    -- thinks of you.
    -- AND NOBODY'S AT ALL with the pressure setting off, or in the grace period.
    if not IC.TUNE.pressure or IC.grace_left() > 0 or not IC.is_human(faction_key) then
        for _slug, house in pairs(court.houses) do house.pressed = nil end
        return 0
    end
    local chance = IC.control_pressure(faction_key)
    if chance <= 0 then
        -- Clear pressure when control recovers so the secession clock stops.
        for _slug, house in pairs(court.houses) do house.pressed = nil end
        return 0
    end
    if cm:random_number(100, 1) > chance then return 0 end
    local slug = IC.strongest_rival(faction_key)
    if not slug then return 0 end
    local house = court.houses[slug]
    if house.pressed then return 0 end
    house.pressed = true
    IC.log(faction_key, "pressed", slug, nil, chance)
    return chance
end

function IC.sufferance(faction_key)
    local own = IC.CROWN
    if not own then return nil end
    local court = IC.court(faction_key)
    if not court.houses[own] then return nil end
    local share = IC.share(faction_key, own)
    if share >= IC.TUNE.sufferance_share then return nil end
    return share
end

function IC.capital_province(faction_key)
    local faction = real_faction(faction_key)
    if not faction then return nil end
    local ok, key = pcall(function()
        local region = faction:home_region()
        if not region or region:is_null_interface() then return nil end
        return region:province_name()
    end)
    if not ok then return nil end
    return key
end

function IC.defecting_provinces(faction_key, slug)
    local capital = IC.capital_province(faction_key)
    local out = {}
    local pool = {}
    local must = 0
    for _, key in ipairs(IC.seats(faction_key)) do
        if key ~= capital then
            local theirs = (IC.province_party(faction_key, key) == slug)
            local n = IC.province_loyalty(faction_key, key)
            local sour = n <= IC.TUNE.prov_defect_floor
            if theirs or sour then must = must + 1 end
            pool[#pool + 1] = {key = key, theirs = theirs, loyalty = n,
                               claimed = (theirs or sour)}
        end
    end
    if #pool == 0 then return out end

    local share = IC.share(faction_key, slug) or 0
    local want = math.ceil(#pool * share / 100)
    if want < must then want = must end
    if want < 1 then want = 1 end
    if want > #pool then want = #pool end

    table.sort(pool, function(a, b)
        if a.theirs ~= b.theirs then return a.theirs end
        if a.claimed ~= b.claimed then return a.claimed end
        if a.loyalty ~= b.loyalty then return a.loyalty < b.loyalty end
        return a.key < b.key
    end)
    for i = 1, want do out[i] = pool[i].key end
    return out
end

function IC.defect_province(faction_key, province_key, rebels)
    local faction = real_faction(faction_key)
    if not faction then return 0 end
    local moved = 0
    local keys = {}
    local ok, regions = pcall(function() return faction:region_list() end)
    if not ok or not regions then return 0 end
    for i = 0, regions:num_items() - 1 do
        local region = regions:item_at(i)
        if region and not region:is_null_interface() then
            local okp, province = pcall(function() return region:province() end)
            if okp and province and not province:is_null_interface()
               and province:key() == province_key then
                keys[#keys + 1] = region:name()
            end
        end
    end
    for i = 1, #keys do
        local okt = pcall(function()
            cm:transfer_region_to_faction(keys[i], rebels)
        end)
        if okt then moved = moved + 1 end
    end
    return moved
end

function IC.rebel_general(faction_key, cqi)
    local R = IC.R(faction_key)
    local out = {subtype = IC.rebel_lord(faction_key), forename = "", surname = ""}
    if not cqi then return out end
    local man = IC.character_by_cqi(faction_key, cqi)
    if not man then return out end
    pcall(function()
        local key = man:character_subtype_key()
        if key and key ~= "" and R.REBEL_GENERALS[key] then
            out.subtype = key
        end
    end)
    pcall(function() out.forename = man:get_forename() or "" end)
    pcall(function() out.surname = man:get_surname() or "" end)
    return out
end

function IC.rebel_kit(faction_key, cqi)
    local kit = {}
    local want = IC.TUNE.rebel_units
    local function take(force)
        if #kit >= want then return end
        if not force or force:is_null_interface() then return end
        local citizenry = false
        pcall(function() citizenry = force:is_armed_citizenry() end)
        if citizenry then return end
        local list = nil
        pcall(function() list = force:unit_list() end)
        if not list then return end
        for i = 0, list:num_items() - 1 do
            if #kit >= want then break end
            local unit = list:item_at(i)
            if unit and not unit:is_null_interface() then
                local led = false
                pcall(function() led = unit:has_unit_commander() end)
                local key = nil
                pcall(function() key = unit:unit_key() end)
                if not led and key and key ~= "" then
                    kit[#kit + 1] = key
                end
            end
        end
    end
    -- HIS OWN ARMY FIRST, modded units and all: that is how a unit mod reaches
    -- the rebels. NOT the faction's other armies: with nobody leaving, the
    -- first of those is the ruler's own stack, which would be copied.
    local man = nil
    if cqi then man = IC.character_by_cqi(faction_key, cqi) end
    if man then
        local force = nil
        pcall(function() force = man:military_force() end)
        take(force)
    end
    -- THE REST IS THE HASHUT DRAFT, not his stack again in order.
    local extra = IC.rebel_draw(want - #kit, faction_key)
    for i = 1, #extra do kit[#kit + 1] = extra[i] end
    return kit
end

-- COUNT UNITS OFF THE DRAFT: slot i is rolled from IC.REBEL_DRAFT[i]'s pool by
-- its weight, skipping a unit already drawn IC.REBEL_UNIT_CAP times. The dice are
-- cm:random_number, so both machines of a multiplayer game roll the same army.
function IC.rebel_draw(count, faction_key)
    local R = IC.R(faction_key)
    local out, used = {}, {}
    for i = 1, math.max(0, count or 0) do
        local role = R.REBEL_DRAFT[(i - 1) % #R.REBEL_DRAFT + 1]
        local pool = R.REBEL_POOLS[role] or {}
        local open, total = {}, 0
        for _, u in ipairs(pool) do
            if (used[u[1]] or 0) < IC.REBEL_UNIT_CAP then
                open[#open + 1] = u
                total = total + u[2]
            end
        end
        if #open == 0 then
            open = pool
            for _, u in ipairs(pool) do total = total + u[2] end
        end
        if total > 0 then
            local roll = cm:random_number(total)
            for _, u in ipairs(open) do
                roll = roll - u[2]
                if roll <= 0 then
                    out[#out + 1] = u[1]
                    used[u[1]] = (used[u[1]] or 0) + 1
                    break
                end
            end
        end
    end
    return out
end

function IC.rebel_rank(faction_key, cqi)
    if not cqi then return IC.TUNE.rebel_lord_level end
    local man = IC.character_by_cqi(faction_key, cqi)
    if not man then return IC.TUNE.rebel_lord_level end
    local rank = nil
    pcall(function() rank = man:rank() end)
    if type(rank) ~= "number" or rank < 1 then
        return IC.TUNE.rebel_lord_level
    end
    return rank
end

function IC.rebel_roll(rebels)
    local seen = {}
    if not rebels then return seen end
    local ok, faction = pcall(function() return cm:get_faction(rebels) end)
    if not ok or not faction or faction == false then return seen end
    local list = nil
    pcall(function() list = faction:character_list() end)
    if not list then return seen end
    for i = 0, list:num_items() - 1 do
        local man = list:item_at(i)
        if man and not man:is_null_interface() then
            seen[man:command_queue_index()] = true
        end
    end
    return seen
end

function IC.rebel_muster(rebels, before, level)
    if not rebels then return 0 end
    local ok, faction = pcall(function() return cm:get_faction(rebels) end)
    if not ok or not faction or faction == false then return 0 end
    local done = 0
    local list = nil
    pcall(function() list = faction:character_list() end)
    if not list then return 0 end
    for i = 0, list:num_items() - 1 do
        local man = list:item_at(i)
        if man and not man:is_null_interface()
                and not before[man:command_queue_index()] then
            local force = nil
            pcall(function() force = man:military_force() end)
            if force and not force:is_null_interface() then
                local look = cm:char_lookup_str(man)
                pcall(function() cm:heal_military_force(force) end)
                pcall(function()
                    cm:add_experience_to_units_commanded_by_character(
                        look, IC.TUNE.rebel_unit_rank)
                end)
                pcall(function()
                    cm:add_agent_experience(
                        look, level or IC.TUNE.rebel_lord_level, true)
                end)
                pcall(function() cm:replenish_action_points(look) end)
                done = done + 1
            end
        end
    end
    return done
end

function IC.rebel_sour(rebels, other, max_steps)
    if not rebels or not other or rebels == other then return 0 end
    local a, b
    pcall(function() a = cm:get_faction(rebels) end)
    pcall(function() b = cm:get_faction(other) end)
    if not a or a == false or not b or b == false then return 0 end
    local n = 0
    while n < (max_steps or IC.TUNE.rebel_relation_max) do
        local now
        -- A KEY, as CA's caravan script passes it: handed the
        -- interface, the pcall ate the refusal and every souring ran all steps.
        pcall(function() now = a:diplomatic_standing_with(other) end)
        if now and now <= IC.TUNE.rebel_relation then break end
        -- BOTH WAYS. CA's five calls put the faction whose regard
        -- moves SECOND, so (rebels, other) alone moved other's regard and left
        -- the one read above - the rebels' own, the number on the player's
        -- diplomacy screen - where it was, and every souring ran all its steps.
        -- The spec also wants the others to dislike the rebels, so each step
        -- moves both; the read then moves whichever way the order really runs.
        pcall(function()
            cm:apply_dilemma_diplomatic_bonus(other, rebels,
                                              IC.TUNE.rebel_relation_step)
        end)
        pcall(function()
            cm:apply_dilemma_diplomatic_bonus(rebels, other,
                                              IC.TUNE.rebel_relation_step)
        end)
        n = n + 1
    end
    return n
end

-- EVERY LIVING FACTION OF THE COURT'S OWN RACE, in key order, off that race's
-- ORIGINS - the court's own list of its houses. The name says Chaos Dwarf from
-- before the court served more than one race.
function IC.chd_factions(faction_key)
    local R = IC.R(faction_key)
    local out = {}
    for i = 1, #R.ORIGINS do
        local key = R.ORIGINS[i].faction
        -- ONE BAD INTERFACE MUST NOT STOP THE SECESSION this runs inside.
        local ok, live = pcall(function()
            local f = key and real_faction(key)
            return f and IC.race_of(f) == R and not f:is_dead()
        end)
        if ok and live then out[#out + 1] = key end
    end
    table.sort(out)
    return out
end

function IC.rebel_sour_all(rebels, faction_key)
    local seen, total = {}, 0
    local targets = {faction_key}
    local ok, human = pcall(function() return cm:get_human_factions() end)
    if ok and human then
        for i = 1, #human do targets[#targets + 1] = human[i] end
    end
    for i = 1, #targets do
        local key = targets[i]
        if key and not seen[key] then
            seen[key] = true
            total = total + IC.rebel_sour(rebels, key)
        end
    end
    -- AND EVERY OTHER CHAOS DWARF FACTION, by less.
    for _, key in ipairs(IC.chd_factions(faction_key)) do
        if not seen[key] and key ~= rebels then
            seen[key] = true
            total = total + IC.rebel_sour(rebels, key, IC.TUNE.rebel_relation_others_max)
        end
    end
    return total
end

function IC.rebel_garrisons(rebels)
    if not rebels then return 0 end
    local ok, faction = pcall(function() return cm:get_faction(rebels) end)
    if not ok or not faction or faction == false then return 0 end
    local healed = 0
    local list = nil
    pcall(function() list = faction:region_list() end)
    if not list then return 0 end
    for i = 0, list:num_items() - 1 do
        local region = list:item_at(i)
        if region and not region:is_null_interface() then
            if pcall(function() cm:heal_garrison(region:cqi()) end) then
                healed = healed + 1
            end
        end
    end
    return healed
end

function IC.rebel_force(rebels, region_key, x, y, general, crown, kit, court_key)
    if not rebels or not region_key then return false end
    -- THE COURT IT LEFT DECIDES THE RACE; a dormant
    -- faction's own interface is not asked.
    general = general or {subtype = IC.rebel_lord(court_key or rebels), forename = "", surname = ""}
    local units = {}
    if kit and #kit > 0 then
        for i = 1, math.min(IC.TUNE.rebel_units, #kit) do
            units[i] = kit[i]
        end
    else
        units = IC.rebel_draw(IC.TUNE.rebel_units, court_key or rebels)
    end
    IC.rebel_serial = (IC.rebel_serial or 0) + 1
    local ok, err = pcall(function()
        cm.game_interface:create_force_with_general(
            rebels, table.concat(units, ","), region_key, x, y,
            "general", general.subtype, general.forename, "",
            general.surname, "",
            "derpy_ic_secession_" .. IC.rebel_serial,
            crown == true, true, false)
    end)
    if not ok then
        IC.warn("IRON COURT: the rebel army did not spawn - " .. tostring(err))
    end
    return ok
end

function IC.rebel_site(faction_key, province_key)
    local faction = real_faction(faction_key)
    if not faction then return nil end
    local ok, regions = pcall(function() return faction:region_list() end)
    if not ok or not regions then return nil end
    for i = 0, regions:num_items() - 1 do
        local region = regions:item_at(i)
        if region and not region:is_null_interface() then
            local okp, province = pcall(function() return region:province() end)
            if okp and province and not province:is_null_interface()
               and (province_key == nil or province:key() == province_key) then
                local okx, x, y = pcall(function()
                    local s = region:settlement()
                    return s:logical_position_x(), s:logical_position_y()
                end)
                if okx and x and y then return region:name(), x, y end
            end
        end
    end
    return nil
end

function IC.secede_step(steps, i)
    i = i or 1
    if i > #steps then return end
    pcall(steps[i])
    cm:callback(function() IC.secede_step(steps, i + 1) end,
                IC.TUNE.secede_step)
end

function IC.secede(faction_key, slug)
    local doomed = IC.defecting_provinces(faction_key, slug)
    local rebels, waking = IC.rebel_faction_for(faction_key, slug)
    -- A DEAD FACTION'S COURT IS NOT THIS RISING'S: woken, it would run the
    -- last rising's parties, counts and quarrels.
    if rebels and waking then IC.forget_court(rebels) end
    local flying = IC.party_name(faction_key, slug)
    local lords, members, defectors, leavers = IC.party_lords(faction_key, slug)
    local want_lords = math.ceil(members / IC.TUNE.rebel_lords_per)
    local leaving = math.min(#defectors, want_lords, IC.TUNE.rebel_lords_max)
    local taking = math.min(#leavers, IC.TUNE.rebel_heroes_max)

    IC.say("IRON COURT: secession of " .. tostring(slug) .. " from "
           .. tostring(faction_key) .. " begins - rebels " .. tostring(rebels)
           .. ", " .. #doomed .. " province(s), " .. #defectors .. " of "
           .. #lords .. " lord(s) able to leave, " .. leaving .. " leaving, "
           .. taking .. " of " .. #leavers .. " hero(s) going too")
    local risings = {}
    for i = 1, math.max(leaving, 1) do
        local where = doomed[math.min(i, #doomed)]
        local name, x, y = IC.rebel_site(faction_key, where)
        if name then
            risings[#risings + 1] = {
                cqi = defectors[i],
                general = IC.rebel_general(faction_key, defectors[i]),
                kit = IC.rebel_kit(faction_key, defectors[i]),
                rank = IC.rebel_rank(faction_key, defectors[i]),
                region = name, x = x, y = y}
        end
    end

    -- NEWS FOR EVERYONE WHO HAS MET THEM, and a card that shows where.
    if not IC.is_human(faction_key) and IC.news(faction_key, "secede", slug) > 0 then
        local okh, human = pcall(function() return cm:get_human_factions() end)
        for i = 1, (okh and human) and #human or 0 do
            if IC.hears(human[i], faction_key) and risings[1] then
                IC.raise_feed_located(human[i], "realm_secede",
                                      risings[1].x, risings[1].y, faction_key)
            end
        end
    end

    local steps = {}
    local lost = 0
    local site = risings[1] and risings[1].region



    if rebels then
        for i = 1, #risings do
            local rise = risings[i]
            local crown = waking and i == 1
            steps[#steps + 1] = function()
                IC.say("IRON COURT: rising " .. i .. " of " .. #risings .. " at "
                       .. tostring(rise.region) .. " under "
                       .. tostring(rise.general.subtype) .. " (cqi "
                       .. tostring(rise.cqi) .. ", level "
                       .. tostring(rise.rank) .. ", " .. #rise.kit
                       .. " unit(s))")
                rise.before = IC.rebel_roll(rebels)
                IC.rebel_force(rebels, rise.region, rise.x, rise.y,
                               rise.general, crown, rise.kit, faction_key)
                IC.say("IRON COURT: rising " .. i .. " spawned"
                       .. (crown and " and took the throne" or ""))
            end
            steps[#steps + 1] = function()
                local n = IC.rebel_muster(rebels, rise.before or {}, rise.rank)
                IC.say("IRON COURT: rising " .. i .. " mustered - " .. n
                       .. " army(s) healed, units to rank "
                       .. IC.TUNE.rebel_unit_rank .. ", lord to level "
                       .. tostring(rise.rank))
            end
            if rise.cqi then
                steps[#steps + 1] = function()
                    -- LEFT, NOT DEAD: ic_dead charges nobody for him, or the
                    -- Crown would pay for every man who walked out.
                    IC.arranged_deaths[rise.cqi] = "left"
                    pcall(function() cm:kill_character(rise.cqi, false) end)
                    IC.say("IRON COURT: cqi " .. tostring(rise.cqi)
                           .. " taken off the board, his army left standing")
                end
            end
        end
    end

    -- JOINING A RISING ALREADY RUNNING KEEPS ITS NAME. With the pool full a
    -- fifth party joins one of the four, and renaming it after the newcomer
    -- took the name the first party rose under off the map and out of the save.
    -- A woken faction, or one that never rose under a party, takes the name.
    local risen = rebels and cm:get_saved_value("derpy_ic_risen_" .. rebels)
    if rebels and flying and (waking or not risen or risen == "") then
        steps[#steps + 1] = function()
            IC.rebel_rename(rebels, flying)
            IC.say("IRON COURT: " .. tostring(rebels) .. " now flies as "
                   .. tostring(flying))
        end
    end

    for i = 1, taking do
        local man = leavers[i]
        local rise = risings[((i - 1) % math.max(#risings, 1)) + 1]
        if rebels and rise then
            steps[#steps + 1] = function()
                IC.say("IRON COURT: hero " .. i .. " of " .. taking
                       .. " changing sides at " .. tostring(rise.region)
                       .. " as " .. tostring(man.agent) .. "/"
                       .. tostring(man.subtype))
                pcall(function()
                    local f = cm:get_faction(rebels)
                    if f and f ~= false then
                        cm:spawn_agent_at_position(f, rise.x, rise.y,
                                                   man.agent, man.subtype)
                    end
                end)
            end
            steps[#steps + 1] = function()
                IC.arranged_deaths[man.cqi] = "left"
                pcall(function() cm:kill_character(man.cqi, false) end)
                IC.say("IRON COURT: hero cqi " .. tostring(man.cqi)
                       .. " taken off the board")
            end
        end
    end

    for i = 1, #doomed do
        steps[#steps + 1] = function()
            IC.say("IRON COURT: handing over " .. tostring(doomed[i])
                   .. " (" .. i .. " of " .. #doomed .. ")")
            if rebels
                    and IC.defect_province(faction_key, doomed[i], rebels) > 0
            then
                lost = lost + 1
            end
        end
    end

    if rebels then
        steps[#steps + 1] = function()
            local n = IC.rebel_garrisons(rebels)
            IC.say("IRON COURT: " .. n .. " garrison(s) brought to strength")
        end
    end

    steps[#steps + 1] = function()
        if rebels then
            IC.say("IRON COURT: declaring war on " .. tostring(rebels))
            pcall(function()
                cm:force_declare_war(rebels, faction_key, false, false)
            end)
            IC.say("IRON COURT: war declared")
            pcall(function()
                cm:force_change_cai_faction_personality(rebels, IC.rebel_personality(faction_key))
            end)
            pcall(function()
                local f = cm:get_faction(rebels)
                if f and f ~= false then
                    cm:set_base_strategic_threat_score(f, IC.TUNE.rebel_threat)
                end
            end)
            local soured = IC.rebel_sour_all(rebels, faction_key)
            IC.say("IRON COURT: " .. soured
                   .. " diplomatic penalty(s) applied to " .. tostring(rebels))
        end
        IC.say("IRON COURT: " .. tostring(slug) .. " secedes from "
               .. tostring(faction_key) .. " as " .. tostring(rebels) .. " - "
               .. #doomed .. " province(s) taken, " .. lost
               .. " transferred, " .. #risings .. " army(s) of "
               .. #defectors .. " of " .. #lords
               .. " lord(s) able to leave, " .. taking .. " hero(s) with them"
               .. ", in a party of " .. members
               .. ", first at " .. tostring(site)
               .. " under "
               .. tostring(risings[1] and risings[1].general.subtype)
               .. " (was cqi " .. tostring(risings[1] and risings[1].cqi) .. ")")
        -- THE GROUND HAS MOVED, so the governors are read again now: the turn
        -- reconciled them before the clocks ticked, and a Crown man governing
        -- a province the rebels just took stayed on the list for a turn.
        IC.reconcile_governors(faction_key)
        IC.apply_governor_bundles(faction_key)
        IC.log(faction_key, "secede", slug, nil, lost)
        IC.feed(faction_key, "secede_done")
        IC.save(faction_key)
    end

    IC.remove_house(faction_key, slug)
    IC.save(faction_key)
    IC.secede_step(steps)
    return lost
end

function IC.splinter(faction_key)
    local R = IC.R(faction_key)
    local court = IC.court(faction_key)
    local crown = court.houses[IC.CROWN]
    -- THE crown_split SETTING OFF: the Crown never splits, and gives no notice.
    -- A count already running stops, or the card reads SPLITS for good. The
    -- same in the grace period.
    if not IC.TUNE.crown_split or IC.grace_left() > 0 then
        if crown then crown.split = 0 end
        return nil
    end
    if not crown then return nil end
    local backed = {}
    local faction = real_faction(faction_key)
    if faction then
        local list = faction:character_list()
        for i = 0, list:num_items() - 1 do
            local man = list:item_at(i)
            if man and not man:is_null_interface() and not IC.is_legend(man)
                    and not IC.is_ruler(man, faction_key) then
                local bg = IC.bg_of_character(man)
                local party = bg and R.PARTY_OF_BG[bg]
                if party then backed[party] = true end
            end
        end
    end
    local pool = {}
    for i = 1, #R.PARTIES do
        local slug = R.PARTIES[i]
        if slug ~= IC.CROWN and not court.houses[slug] and backed[slug] then
            pool[#pool + 1] = slug
        end
    end
    local can = (crown.loyalty or IC.TUNE.loyalty_start)
                    <= IC.TUNE.splinter_loyalty
                and (crown.weight or 0) > IC.TUNE.splinter_weight
                and #pool > 0
    if not can then
        if (crown.split or 0) > 0 then
            crown.split = 0
            -- THE SAME CARD as a party standing down: splinter_warn was left
            -- hanging over a split that was never going to happen.
            IC.log(faction_key, "snub_off", IC.CROWN, nil, 0)
            IC.feed(faction_key, "threat_over")
            IC.save(faction_key)
        end
        return nil
    end
    if (crown.split or 0) <= 0 then
        crown.split = IC.TUNE.warn_turns
        IC.feed(faction_key, "splinter_warn")
        IC.save(faction_key)
        return nil
    end
    crown.split = crown.split - 1
    if crown.split > 0 then
        IC.save(faction_key)
        return nil
    end
    local slug = pool[cm:random_number(#pool, 1)]
    local keep = crown.loyalty or IC.TUNE.loyalty_start
    if not IC.add_house(faction_key, slug, nil, keep) then return nil end
    IC.name_party(faction_key, slug)
    IC.roll_party_traits(faction_key, slug)
    local house = court.houses[slug]
    house.weight = IC.TUNE.splinter_weight
    crown.weight = math.max(1, (crown.weight or 0) - IC.TUNE.splinter_weight)
    -- AND THE SEATS ITS MEN HOLD. appoint credited the Crown, and dismiss
    -- debits the party a man answers to now: without this the Crown keeps the
    -- weight for good and the new party loses it twice.
    for office_slug, cqi in pairs(court.offices) do
        if IC.house_of_cqi(faction_key, cqi) == slug then
            crown.weight = math.max(1, crown.weight - IC.office_weight(office_slug, IC.CROWN, faction_key))
            house.weight = house.weight + IC.office_weight(office_slug, slug, faction_key)
        end
    end
    IC.move_loyalty(faction_key, IC.CROWN, IC.TUNE.loyalty_start - keep)
    IC.log(faction_key, "splinter", slug, nil, house.weight)
    IC.news(faction_key, "splinter", slug)
    IC.feed(faction_key, "splinter")
    IC.save(faction_key)
    return slug
end

-- TURNS OF GRACE LEFT, counting this one: 10 on turn 1, 1 on turn 10, 0 after.
function IC.grace_left()
    return math.max(0, IC.TUNE.grace_turns + 1 - cm:model():turn_number())
end

-- WHETHER ANYBODY MAY BREAK WITH YOU THIS TURN: the setting, and the grace period.
function IC.secession_on()
    return IC.TUNE.secession ~= false and IC.grace_left() == 0
end

function IC.at_breaking_point(faction_key, slug)
    if not IC.secession_on() or not slug or slug == IC.CROWN then return false end
    local house = IC.court(faction_key).houses[slug]
    if not house then return false end
    return (house.loyalty or IC.TUNE.loyalty_start) <= IC.TUNE.secede_break
end

function IC.tick_secession(faction_key)
    local court = IC.court(faction_key)
    -- THE secession SETTING OFF, OR THE GRACE PERIOD: no countdown runs, so
    -- nothing is warned and nobody leaves. A clock already running is stopped.
    if not IC.secession_on() then
        for _slug, house in pairs(court.houses) do house.clock = 0 end
        return {}
    end
    local own = IC.CROWN
    local warned = {}
    -- Collect first because mutating a table during pairs() traversal is undefined.
    local seceding = {}
    for slug, house in pairs(court.houses) do
        local angry = false
        local breaking = false
        -- AN INSULT LASTS AS LONG AS ITS COUNT. Whatever zeroed the clock - a
        -- bribe, Secure Loyalty, the setting - ended it.
        if (house.clock or 0) <= 0 then house.provoked = nil end
        if slug ~= own then
            local share = IC.share(faction_key, slug)
            angry = share >= IC.TUNE.secede_share
                and house.loyalty <= IC.TUNE.secede_loyalty
            -- A PROVOKED PARTY KEEPS COUNTING however content it is: that is
            -- the move, so the next tick must not call it off.
            if house.pressed or house.provoked then angry = true end
            if IC.protected_for(faction_key, slug) > 0 then angry = false end
            breaking = IC.at_breaking_point(faction_key, slug)
        end
        if breaking then
            seceding[#seceding + 1] = slug
            house.clock = 0
        elseif angry then
            if (house.clock or 0) <= 0 then
                house.clock = IC.tune(faction_key, "secede_turns")
                IC.log(faction_key, "warn", slug, nil, house.clock)
                IC.feed(faction_key, "secede_warn")
            else
                house.clock = house.clock - 1
                if house.clock <= 0 then
                    seceding[#seceding + 1] = slug
                -- ONE TURN AFTER THE START CARD when the count is too short to
                -- reach warn_turns once started: Ruthless counts from 3.
                elseif house.clock == math.min(IC.TUNE.warn_turns,
                                               IC.tune(faction_key, "secede_turns") - 1) then
                    IC.feed(faction_key, "secede_soon")
                end
            end
            warned[#warned + 1] = {slug = slug, turns = house.clock}
        else
            if (house.clock or 0) > 0 then
                IC.log(faction_key, "snub_off", slug, nil, 0)
                -- AND SAID. The count had a card when it started and one when it
                -- ran out, and none when it stopped.
                IC.feed(faction_key, "threat_over")
            end
            house.clock = 0
        end
    end
    for i = 1, #seceding do
        if IC.nothing_to_take(faction_key, seceding[i]) then
            IC.dissolve(faction_key, seceding[i])
        else
            IC.secede(faction_key, seceding[i])
        end
    end
    return warned
end

-- NOBODY IN IT AND NO PROVINCE TO TAKE: it dissolves instead, with a card.
-- Seceding, it would found a rebel faction with 0 provinces and 0 armies whose
-- only act is to rename another rising's faction (when the pool is full) and
-- start a war between the two.
function IC.nothing_to_take(faction_key, slug)
    local _, members = IC.party_lords(faction_key, slug)
    if (members or 0) > 0 then return false end
    return #(IC.defecting_provinces(faction_key, slug) or {}) == 0
end

function IC.dissolve(faction_key, slug)
    IC.news(faction_key, "dissolve", slug)
    IC.log(faction_key, "dissolve", slug, nil, 0)
    IC.remove_house(faction_key, slug)
    IC.feed(faction_key, "dissolved")
    IC.say("IRON COURT: " .. tostring(slug) .. " in " .. faction_key
           .. " dissolves - nobody in it and no province to take")
end

function IC.is_human(faction_key)
    local ok, human = pcall(function() return cm:get_human_factions() end)
    if not ok or not human then return false end
    for i = 1, #human do
        if human[i] == faction_key then return true end
    end
    return false
end

-- WHO WOULD TAKE EACH EMPTY SEAT, seating nobody: the AI's turn and the
-- player's Fill button both read it, so a player's fill
-- never snubs a party the AI's would not. Best man first, highest seat first.
-- Planning without appointing picks the same men appointing as it went did:
-- nothing IC.can_appoint asks depends on another appointment, and `used` is
-- one post per man.
function IC.fill_plan(faction_key)
    local R = IC.R(faction_key)
    local court = IC.court(faction_key)
    local pool = {}
    for _, cand in ipairs(IC.candidates(faction_key)) do
        if not cand.busy then pool[#pool + 1] = cand end
    end
    table.sort(pool, function(a, b)
        local sa = IC.standing(faction_key, a.cqi)
        local sb = IC.standing(faction_key, b.cqi)
        if sa ~= sb then return sa > sb end
        return a.cqi < b.cqi
    end)
    local used, plan = {}, {}
    for i = 1, #R.OFFICES do
        local office = R.OFFICES[i]
        if not court.offices[office.slug] then
            -- THE CLAIMED PARTY, and nobody else while it sits in this court.
            -- An outsider in a claimed seat costs that party loyalty_snubbed at
            -- once and loyalty_affinity_snub every turn after, and the AI has no
            -- move that can ever pay either back. The outsider is nearly always
            -- a Crown man already at or near 100, so the seat buys nothing. In
            -- live saves every AI party still falling was one whose claimed seat
            -- had gone to an outsider. A seat claimed by a party that is not in
            -- this court goes to anybody.
            local passes = court.houses[office.affinity] and 1 or 2
            for pass = 1, passes do
                local done = false
                for j = 1, #pool do
                    local cqi = pool[j].cqi
                    local affine = pool[j].slug == office.affinity
                    if not used[cqi] and ((pass == 1) == affine)
                            and IC.can_appoint(faction_key, office.slug, cqi) then
                        used[cqi] = true
                        plan[#plan + 1] = {slug = office.slug, cqi = cqi}
                        done = true
                        break
                    end
                end
                if done then break end
            end
        end
    end
    return plan
end

-- The plan, seated. Returns how many.
function IC.fill_offices(faction_key)
    local plan, seated = IC.fill_plan(faction_key), 0
    for i = 1, #plan do
        if IC.appoint(faction_key, plan[i].slug, plan[i].cqi) then
            seated = seated + 1
        end
    end
    return seated
end

function IC.ai_fill_offices(faction_key)
    if IC.is_human(faction_key) then return 0 end
    return IC.fill_offices(faction_key)
end

-- The other half of the AI's court. Offices need standing an AI lord in the
-- field never earns, so for the first thirty turns ai_fill_offices has nobody
-- it can seat and every party is drifting at the no-seat rate. A province asks
-- nothing, pays the same loyalty as a seat, and settles the grasping trait,
-- which is otherwise a flat penalty on an AI for the whole campaign.
function IC.ai_fill_governors(faction_key)
    if IC.is_human(faction_key) then return 0 end
    local court = IC.court(faction_key)
    local pool = {}
    for _, cand in ipairs(IC.candidates(faction_key)) do
        if not cand.busy then pool[#pool + 1] = cand end
    end
    -- HOW MANY POSTS HIS PARTY ALREADY HOLDS, lowest first. Handing every
    -- province to the same party leaves the rest drifting, which is the thing
    -- this is here to stop.
    local holds = {}
    for _office_slug, cqi in pairs(court.offices) do
        local slug = IC.house_of_cqi(faction_key, cqi)
        if slug then holds[slug] = (holds[slug] or 0) + 1 end
    end
    for _province_key, cqi in pairs(court.govs) do
        local slug = IC.house_of_cqi(faction_key, cqi)
        if slug then holds[slug] = (holds[slug] or 0) + 1 end
    end
    local used, seated = {}, 0
    for _, province_key in ipairs(IC.seats(faction_key)) do
        if not court.govs[province_key] then
            -- PICKED FRESH FOR EACH PROVINCE, not off one sort done up front:
            -- handing out the first province changes who is neediest for the
            -- second, and a list sorted once gives two provinces to the same
            -- party whenever it happens to field two idle men.
            local best, fewest
            for j = 1, #pool do
                local cand = pool[j]
                local n = cand.slug and (holds[cand.slug] or 0) or 0
                if not used[cand.cqi]
                        and (not best or n < fewest
                             or (n == fewest and cand.cqi < best.cqi)) then
                    best, fewest = cand, n
                end
            end
            if best and IC.assign_governor(faction_key, province_key, best.cqi) then
                used[best.cqi] = true
                seated = seated + 1
                if best.slug then
                    holds[best.slug] = (holds[best.slug] or 0) + 1
                end
            end
        end
    end
    return seated
end


IC.PLOT_CATS = {
    {key = "man",    name = "Against a Man"},
    {key = "house",  name = "Against a Party"},
    {key = "bond",   name = "Bonds"},
    {key = "errand", name = "Errands"},
    {key = "mission", name = "Missions"},
}

-- WHETHER A RACE'S COURT HAS A MOVE: no `race` is every race's; a race's
-- PLOT_KEYS list, where one is set, names its moves (contract).
function IC.plot_for_race(plot, race_key)
    if plot.race and plot.race ~= race_key then return false end
    local r = IC.RACES[race_key or ""]
    if not (r and r.PLOT_KEYS) then return true end
    for _, key in ipairs(r.PLOT_KEYS) do
        if key == plot.key then return true end
    end
    return false
end

-- A CATEGORY'S MOVES FOR ONE RACE; the Chaos Dwarf grid when none is named,
-- which is the grid the panel lays out at load.
function IC.plots_in(cat, race_key)
    local out = {}
    for i = 1, #IC.PLOTS do
        local p = IC.PLOTS[i]
        if p.cat == cat and IC.plot_for_race(p, race_key or "chd") then out[#out + 1] = p end
    end
    return out
end

IC.PLOTS = {
    {key = "bribe", name = "Bribe",
     icon = "ui/campaign ui/skills/character_oathgold.png",
     cat = "man",
     cost = "plot_bribe_cost",
     effect = string.format(
         "+%d influence for him. +%d party loyalty. Stops their secession countdown.",
         IC.TUNE.plot_bribe_standing,
         IC.TUNE.plot_bribe_loyalty),
     blurb = "Gold and Labourers buy favour."},
    {key = "discredit", name = "Discredit",
     icon = "ui/campaign ui/skills/campaign_chaos_corruption.png",
     cat = "man",
     cost = "plot_discredit_cost",
     effect = string.format(
         "-%d influence for him. -%d influence from his party.",
         IC.TUNE.plot_discredit_standing,
         IC.TUNE.plot_discredit_weight),
     blurb = "His ore comes up short."},
    {key = "rumour", name = "Spread Rumours",
     icon = "ui/campaign ui/skills/wh3_main_lord_passive_whispers_in_the_darkness.png",
     cat = "man",
     cost = "plot_rumour_cost",
     effect = string.format(
         "-%d influence for him. His party is unaffected.",
         IC.TUNE.plot_rumour_damage),
     blurb = "Paid tongues ruin one name."},
    {key = "murder", name = "A Forge Accident",
     icon = "ui/campaign ui/skills/wh3_dlc23_character_ability_reforge.png",
     cat = "man",
     cost = "plot_murder_cost",
     -- BOTH TERMS: ic_dead charges loyalty_member_died on top.
     effect = string.format(
         "He dies. -%d loyalty from his party.",
         IC.TUNE.plot_murder_loyalty - IC.TUNE.loyalty_member_died),
     blurb = "His party will know who arranged it."},
    -- Rome II-style actions against an entire party.
    -- PROVOKE AND PURGE ARE cat "party", which IC.PLOT_CATS does not list, so
    -- the Intrigue grid never draws them. They are the court tab's action bar:
    -- the player picks the party on its card and the move is aimed at the man
    -- who speaks for it.
    {key = "provoke", name = "Provoke",
     icon = "ui/campaign ui/skills/wh3_dlc23_character_ability_malign_authority.png",
     cat = "party",
     cost = "plot_provoke_cost",
     effect = string.format(
         "-%d loyalty. Sets their secession countdown to %d turns.",
         IC.TUNE.plot_provoke_loyalty,
         IC.TUNE.plot_provoke_clock),
     -- WITH SECESSION SWITCHED OFF no count starts (IC.plot), so none is
     -- promised.
     effect_no_secession = string.format(
         "-%d loyalty. With secession switched off, no countdown starts.",
         IC.TUNE.plot_provoke_loyalty),
     blurb = "An insult they cannot ignore."},
    {key = "purge", name = "Purge the House",
     icon = "ui/campaign ui/skills/wh3_dlc23_character_abilities_skjalandirs_fall.png",
     cat = "party",
     cost = "plot_purge_cost",
     effect = string.format(
         "Removes the party. -%d loyalty to all others. Failure: another -%d to the target.",
         IC.TUNE.plot_purge_witness,
         IC.TUNE.plot_purge_backfire),
     blurb = "The court watches."},
    {key = "unseat", name = "Strike Their Seats",
     icon = "ui/campaign ui/skills/wh2_dlc11_forgery.png",
     cat = "house",
     cost = "plot_unseat_cost",
     effect = string.format(
         "Empties every office they hold. -%d loyalty.",
         IC.TUNE.plot_unseat_loyalty),
     blurb = "They keep only their name."},
    {key = "recall", name = "Recall Governors",
     icon = "ui/campaign ui/skills/wh3_dlc24_hero_passive_assume_command.png",
     cat = "house",
     cost = "plot_recall_cost",
     effect = string.format(
         "Recalls every governor from their party. -%d loyalty.",
         IC.TUNE.plot_recall_loyalty),
     blurb = "The Tower takes back its provinces."},
    -- PAY THE WEREGILD: Dwarf courts only, GOLD from the treasury, and SURE: a
    -- blood-price is paid, not tried. In the party column, not Bonds.
    {key = "weregild", name = "Pay the Weregild", race = "dwf", gold = true, sure = true,
     icon = "ui/campaign ui/skills/wh_dlc06_character_abilities_oath_stone.png",
     cat = "house",
     cost = "plot_weregild_cost",
     effect = string.format(
         "Settles their oldest grudge. +%d loyalty. Paid from the treasury.",
         IC.TUNE.plot_weregild_loyalty),
     blurb = "Gold for the wrong, weighed out."},
    {key = "oath", name = "Blood-Oath",
     icon = "ui/campaign ui/skills/wh3_dlc23_character_abilities_by_our_blood.png",
     cat = "bond",
     cost = "plot_oath_cost",
     effect = string.format(
         "+%d loyalty each turn while both men live. Requires %d loyalty.",
         IC.TUNE.plot_oath_loyalty,
         IC.TUNE.plot_oath_min_loyalty),
     blurb = "Two names in hot iron."},
    {key = "patron", name = "Stand His Patron",
     icon = "ui/campaign ui/skills/character_diplomacy.png",
     cat = "bond",
     cost = "plot_patron_cost",
     effect = string.format(
         "+%d influence for him. +%d loyalty for his party.",
         IC.TUNE.plot_patron_standing,
         IC.TUNE.plot_patron_loyalty),
     blurb = "He will remember."},
    {key = "kinsman", name = "Name Him Kinsman",
     icon = "ui/campaign ui/ancillaries/wh3_dlc23_anc_banner_chd_standard_of_zharr.png",
     cat = "bond",
     cost = "plot_kinsman_cost",
     effect = string.format(
         "Moves up to %d influence to the Crown. Requires %d loyalty.",
         IC.TUNE.plot_kinsman_weight,
         IC.TUNE.plot_kinsman_min_loyalty),
     blurb = "His party loses influence."},
    {key = "pledge", name = "Pledge of the Forge",
     icon = "ui/campaign ui/skills/mount_anvil_of_doom.png",
     cat = "bond",
     cost = "plot_pledge_cost",
     effect = string.format(
         "+%d loyalty. Stops their secession countdown. Costs the Crown %d influence.",
         IC.TUNE.plot_pledge_loyalty,
         IC.TUNE.plot_pledge_weight),
     blurb = "Forge-sworn."},
    {key = "embezzle", name = "Embezzle", aimed = false,
     icon = "ui/campaign ui/ancillaries/wh_main_anc_human_spy.png",
     cat = "errand",
     cost = "plot_embezzle_cost",
     effect = string.format(
         "+%d gold. -%d loyalty across the whole court.",
         IC.TUNE.plot_embezzle_gold,
         IC.TUNE.plot_embezzle_loyalty),
     blurb = "The books will betray the theft."},
    {key = "feast", name = "A Feast of Ash", aimed = false,
     icon = "ui/campaign ui/skills/wh3_main_unit_passive_gorefeast.png",
     cat = "errand",
     cost = "plot_feast_cost",
     effect = string.format(
         "+%d influence to the man you send. -%d loyalty across "
         .. "the court.",
         IC.TUNE.plot_feast_standing,
         IC.TUNE.plot_feast_loyalty),
     blurb = "The court learns his name."},
    {key = "audience", name = "Hold the Ash Court", aimed = false,
     icon = "ui/campaign ui/skills/campaign_public_order.png",
     cat = "errand",
     cost = "plot_audience_cost",
     effect = string.format(
         "+%d loyalty to every party in the court.",
         IC.TUNE.plot_audience_loyalty),
     blurb = "A day of smoke and grievances."},
    {key = "circuit", name = "Ride the Circuit", aimed = false,
     icon = "ui/campaign ui/ancillaries/wh3_dlc23_anc_follower_convoy_enforcer.png",
     cat = "errand",
     cost = "plot_circuit_cost",
     effect = string.format(
         "+%d control in every province you hold.",
         IC.TUNE.plot_circuit_prov),
     blurb = "A ledger and an armed escort."},
    -- THE CIVIL MISSIONS: aimed at a PLACE, not a man.
    -- `target` says which kind; IC.may_target reads it, and the panel opens the
    -- matching picker. The four envoy tasks are IC.ENVOY_TASKS.
    {key = "envoy", name = "Send an Envoy", aimed = false, target = "province",
     icon = "ui/campaign ui/ancillaries/wh3_dlc23_anc_follower_veteran_overseer.png",
     cat = "mission",
     cost = "plot_envoy_cost",
     effect = string.format(
         "One of your provinces, for %d turns: control, armaments, raw materials "
         .. "or labour.", IC.TUNE.mission_turns),
     blurb = "He sees it done."},
    {key = "diplomats", name = "Send Diplomats", aimed = false, target = "faction",
     icon = "ui/campaign ui/ancillaries/wh3_main_anc_cathay_diplomat.png",
     cat = "mission",
     cost = "plot_diplomats_cost",
     effect = string.format(
         "Improves relations with a faction you have met. Each faction once per %d turns.",
         IC.TUNE.diplomats_rest),
     blurb = "Gifts and a long table."},
}

function IC.plot_is_aimed(plot_key)
    local plot = IC.plot_by_key(plot_key)
    if not plot then return false end
    return plot.aimed ~= false
end

function IC.is_civil_mission(plot_key)
    return not IC.plot_is_aimed(plot_key)
end

IC.FAVOURS = {
    {key = "gift", name = "Send a Gift",
     cost = "favour_gift_cost",
     blurb = "Labourers, ore and strong drink buy patience."},
    {key = "secure", name = "Secure Loyalty",
     cost = "favour_secure_cost",
     blurb = "Hostages and oaths delay rebellion. They will not stop it at zero loyalty."},
}

function IC.favour_by_key(key)
    for i = 1, #IC.FAVOURS do
        if IC.FAVOURS[i].key == key then return IC.FAVOURS[i] end
    end
    return nil
end

-- A MOVE'S AND A FAVOUR'S WORDS FOR THIS COURT: the
-- race's own where it has them, IC.PLOTS / IC.FAVOURS otherwise. The panel
-- draws these; the numbers stay IC.PLOTS'.
function IC.plot_text(plot_key, faction_key)
    local plot = IC.plot_by_key(plot_key)
    if not plot then return nil end
    local R = IC.R(faction_key)
    local t = (R.PLOT_TEXT or {})[plot_key] or {}
    return t.name or plot.name, t.blurb or plot.blurb, t.effect or plot.effect,
           t.effect_no_secession or plot.effect_no_secession, t.icon or plot.icon
end

function IC.favour_text(key, faction_key)
    local favour = IC.favour_by_key(key)
    if not favour then return nil end
    local R = IC.R(faction_key)
    local t = (R.FAVOUR_TEXT or {})[key] or {}
    return t.name or favour.name, t.blurb or favour.blurb
end

function IC.favour_cost(key, faction_key)
    local favour = IC.favour_by_key(key)
    if not favour then return 0 end
    return IC.tune(faction_key, favour.cost) or 0
end

-- Guard the treasury read so an engine error cannot leave the button inert.
function IC.treasury(faction_key)
    local faction = real_faction(faction_key)
    if not faction then return 0 end
    local ok, gold = pcall(function() return faction:treasury() end)
    if not ok or type(gold) ~= "number" then return 0 end
    return gold
end

function IC.protected_for(faction_key, slug)
    local house = IC.court(faction_key).houses[slug or ""]
    if not house or not house.protected then return 0 end
    return math.max(0, house.protected - cm:model():turn_number())
end

-- Returns ok, why, shortfall. The refusal codes are strings the panel turns
-- into sentences; a code it does not know still says something.
function IC.can_favour(faction_key, key, slug)
    local favour = IC.favour_by_key(key)
    if not favour then return false, "no such favour" end
    local court = IC.court(faction_key)
    local house = court.houses[slug or ""]
    if not house then return false, "no such house" end
    if slug == IC.CROWN then return false, "your own house" end
    local cost = IC.favour_cost(key, faction_key)
    local gold = IC.treasury(faction_key)
    if gold < cost then return false, "gold", cost - gold end
    if key == "gift" and (house.loyalty or 0) >= 100 then
        return false, "content"
    end
    -- ONE GIFT PER PARTY PER TURN. Otherwise a full
    -- treasury buys a party from its start to 100 in one sitting.
    if key == "gift" and house.gifted == cm:model():turn_number() then
        return false, "given"
    end
    if key == "secure" then
        local left = IC.protected_for(faction_key, slug)
        if left > 0 then return false, "sworn", left end
        if IC.at_breaking_point(faction_key, slug) then
            return false, "breaking"
        end
    end
    return true
end

function IC.favour(faction_key, key, slug)
    local ok, why, short = IC.can_favour(faction_key, key, slug)
    if not ok then return false, why, short end
    local court = IC.court(faction_key)
    local house = court.houses[slug]
    local cost = IC.favour_cost(key, faction_key)
    cm:treasury_mod(faction_key, -cost)

    -- WHAT IT GAVE, in the slot a refusal's shortfall uses: loyalty stops at
    -- 100, so at 99 a gift gives one point, and the answer says so.
    local gained = nil
    if key == "gift" then
        local was = house.loyalty or IC.TUNE.loyalty_start
        IC.move_loyalty(faction_key, slug, IC.TUNE.favour_gift_loyalty)
        gained = (house.loyalty or was) - was
        house.gifted = cm:model():turn_number()
    elseif key == "secure" then
        house.protected = cm:model():turn_number() + IC.TUNE.favour_secure_turns
        house.clock = 0
        house.pressed = nil
        -- AND THEIR OFFICERS GO BACK TO WORK.
        for office_slug, s in pairs(court.stalled or {}) do
            if s.by == slug and s.cause == "withhold" then
                court.stalled[office_slug] = nil
            end
        end
        IC.apply_office_bundles(faction_key)
    end

    IC.log(faction_key, key, slug, nil, cost)
    IC.save(faction_key)
    return true, nil, gained
end

function IC.plot_by_key(key)
    for i = 1, #IC.PLOTS do
        if IC.PLOTS[i].key == key then return IC.PLOTS[i] end
    end
    return nil
end

-- THE ENVOY'S FOUR TASKS, in display order. The
-- bundle's VALUE is IC.TUNE[knob]: tools/gen_iron_court.py reads both out of
-- this file, so the text and the effect are one number. `icon` is the bundle's,
-- under ui/campaign ui/effect_bundles/.
IC.ENVOY_TASKS = {
    {code = "ctl", name = "Control", knob = "envoy_ctl", fmt = "+%d control",
     bundle = "derpy_ic_envoy_ctl", icon = "wh3_dlc23_edict_chd_smoke_stacks.png"},
    {code = "arm", name = "Armaments", knob = "envoy_arm", fmt = "+%d%% armaments",
     bundle = "derpy_ic_envoy_arm", icon = "wh3_dlc23_edict_chd_higher_quotas.png"},
    {code = "raw", name = "Raw Materials", knob = "envoy_raw", fmt = "+%d%% Raw Materials",
     bundle = "derpy_ic_envoy_raw", icon = "chd_toz_district_industry.png"},
    {code = "lab", name = "Labour", knob = "envoy_lab", fmt = "-%d%% Labourers lost",
     bundle = "derpy_ic_envoy_lab", icon = "public_order_jubilant.png"},
}

-- THE COURT'S OWN FOUR. No faction gives the Chaos Dwarf list, which every
-- race-blind caller expects.
function IC.envoy_tasks(faction_key)
    local R = IC.R(faction_key)
    return R.ENVOY_TASKS or IC.ENVOY_TASKS
end

function IC.envoy_task(code, faction_key)
    local tasks = IC.envoy_tasks(faction_key)
    for i = 1, #tasks do
        if tasks[i].code == code then return tasks[i] end
    end
    return nil
end

function IC.envoy_effect(task)
    return string.format(task.fmt, IC.TUNE[task.knob])
end

-- "province:code" -> the province key and the task; either is nil when the
-- target is malformed. Province keys never hold a ":".
function IC.envoy_split(target, faction_key)
    local province, code = string.match(tostring(target or ""), "^(.+):(%a+)$")
    return province, IC.envoy_task(code, faction_key)
end

-- THE TURNS LEFT on a bundle already on the faction province, or nil.
function IC.envoy_running(faction_key, province_key, bundle)
    local region = IC.held_region(faction_key, province_key)
    if not region then return nil end
    local left = nil
    pcall(function()
        if not region:faction_province_has_effect_bundle(bundle) then return end
        left = 0
        local list = region:faction_province_effect_bundles()
        for i = 0, list:num_items() - 1 do
            local b = list:item_at(i)
            if b:key() == bundle then left = b:duration() end
        end
    end)
    return left
end

function IC.may_send_envoy(faction_key, target)
    local province, task = IC.envoy_split(target, faction_key)
    if not province then return false, "no such task" end
    local held = false
    for _, p in ipairs(IC.seats(faction_key)) do
        if p == province then held = true end
    end
    if not held then return false, "lost" end
    if not task then return false, "no such task" end
    local left = IC.envoy_running(faction_key, province, task.bundle)
    if left then return false, "running", left end
    return true
end

-- ANY FACTION YOU HAVE MET that is alive, not a rebel, not a player and not
-- resting from the last send.
function IC.may_send_diplomats(faction_key, target)
    if not target or target == faction_key then return false, "lost" end
    local them = cm:get_faction(target)
    if not them or them:is_null_interface() or them:is_dead() then
        return false, "lost"
    end
    local met = false
    pcall(function()
        local list = cm:get_faction(faction_key):factions_met()
        for i = 0, list:num_items() - 1 do
            if list:item_at(i):name() == target then met = true break end
        end
    end)
    if not met then return false, "unmet" end
    if them:is_rebel() then return false, "rebel" end
    if them:is_human() then return false, "player" end
    local sent = IC.court(faction_key).sent[target]
    if sent then
        local left = sent + IC.TUNE.diplomats_rest - cm:model():turn_number()
        if left > 0 then return false, "resting", left end
    end
    return true
end

function IC.plot_cost(key, faction_key)
    local plot = IC.plot_by_key(key)
    -- A PARTY-ONLY MOVE has no IC.PLOTS row; its price is on the tune.
    if not plot then return IC.tune(faction_key, "plot_" .. tostring(key) .. "_cost") or 0 end
    return IC.tune(faction_key, plot.cost) or 0
end

IC.LEGEND_SUBTYPES = {
    ["wh3_dlc23_chd_astragoth"] = true,
    ["wh3_dlc23_chd_drazhoath"] = true,
    ["wh3_dlc23_chd_gorduz_backstabber"] = true,
    ["wh3_dlc23_chd_zhatan"] = true,
    ["derpy_abnagg"] = true,
    ["derpy_azeros"] = true,
    ["derpy_balur"] = true,
    ["derpy_black_dwf"] = true,
    ["derpy_bzaark"] = true,
    ["derpy_gargath"] = true,
    ["derpy_ghorth"] = true,
    ["derpy_gordak"] = true,
    ["derpy_snakebeard"] = true,
    ["derpy_tordrek"] = true,
    ["derpy_urzkhal"] = true,
    ["derpy_vraznak"] = true,
    ["derpy_vraznak3"] = true,
    ["derpy_warrhak"] = true,
}

-- A SUBTYPE KEY NAMES ONE RACE'S CHARACTER, so a lookup by it asks every race.
local function in_any_race(field, key)
    if key == nil then return nil end
    for _, rk in ipairs(IC.RACE_ORDER) do
        local v = IC.RACES[rk][field][key]
        if v ~= nil then return v end
    end
    return nil
end

function IC.is_legend(character)
    if not character or character:is_null_interface() then return false end
    if IC.is_unique(character) then return true end
    local key = nil
    pcall(function() key = character:character_subtype_key() end)
    return in_any_race("LEGEND_SUBTYPES", key) == true
end

-- is_unique() belongs to character details, not the character interface.
function IC.is_unique(character)
    if not character or character:is_null_interface() then return false end
    local details = character:character_details()
    if not details or details:is_null_interface() then return false end
    return details:is_unique() == true
end

function IC.may_target(faction_key, plot_key, cqi)
    local plot = IC.plot_by_key(plot_key)
    if not plot then return false, "no such plot" end
    -- ANOTHER RACE'S MOVE does not exist here, whoever sends it.
    if not IC.plot_for_race(plot, IC.race_key(faction_key)) then
        return false, "no such plot"
    end
    -- A CIVIL MISSION'S TARGET IS A PLACE: the third argument
    -- is a "province:code" or a faction key, not a cqi, and a refusal that waits
    -- on turns returns them third.
    if plot.target == "province" then return IC.may_send_envoy(faction_key, cqi) end
    if plot.target == "faction" then return IC.may_send_diplomats(faction_key, cqi) end
    if not IC.plot_is_aimed(plot_key) then return true end
    -- NOTHING TO START IN THE GRACE PERIOD: Provoke is a countdown, and none
    -- may run yet. With secession switched off it stays a plain loyalty cost.
    if plot_key == "provoke" and IC.TUNE.secession ~= false
            and IC.grace_left() > 0 then
        return false, "grace"
    end
    local victim = IC.character_by_cqi(faction_key, tonumber(cqi))
    if not victim then return false, "no such target" end
    if plot_key == "murder" and IC.is_legend(victim) then
        return false, "unique"
    end
    if IC.house_of_character(victim, faction_key) == IC.CROWN then
        return false, "own party"
    end
    if plot_key == "weregild" then
        local slug = IC.house_of_character(victim, faction_key)
        if #IC.grudges(faction_key, slug) == 0 then return false, "no grudge" end
    end
    if plot_key == "purge" then
        local slug = IC.house_of_character(victim, faction_key)
        if not slug or not IC.court(faction_key).houses[slug] then
            return false, "no house"
        end
    end
    if plot_key == "unseat" then
        local slug = IC.house_of_character(victim, faction_key)
        if #IC.offices_of_house(faction_key, slug) == 0 then
            return false, "no seats"
        end
    end
    if plot_key == "recall" then
        local slug = IC.house_of_character(victim, faction_key)
        if #IC.provinces_of_house(faction_key, slug) == 0 then
            return false, "no provinces"
        end
    end
    if plot_key == "kinsman" then
        local slug = IC.house_of_character(victim, faction_key)
        local house = slug and IC.court(faction_key).houses[slug]
        if not house then return false, "no house" end
        if (house.loyalty or IC.TUNE.loyalty_start)
                < IC.TUNE.plot_kinsman_min_loyalty then
            return false, "kin cold"
        end
        if (house.weight or 0) <= IC.TUNE.plot_kinsman_weight then
            return false, "spent"
        end
    end
    if plot_key == "pledge" then
        local crown = IC.court(faction_key).houses[IC.CROWN]
        if not crown or (crown.weight or 0)
                <= IC.TUNE.plot_pledge_weight then
            return false, "crown spent"
        end
    end
    if plot_key == "oath" then
        local slug = IC.house_of_character(victim, faction_key)
        local house = slug and IC.court(faction_key).houses[slug]
        if not house then return false, "no house" end
        if (house.loyalty or IC.TUNE.loyalty_start)
                < IC.TUNE.plot_oath_min_loyalty then
            return false, "cold"
        end
        if house.oath_mine then return false, "oathed" end
    end
    return true
end

function IC.may_plot_as(faction_key, actor_cqi)
    if not IC.is_human(faction_key) then return true end
    return IC.house_of_cqi(faction_key, actor_cqi) == IC.CROWN
end

function IC.can_plot(faction_key, plot_key, actor_cqi, target)
    local ok, why, short = IC.may_target(faction_key, plot_key, target)
    if not ok then return false, why, short end
    local actor = IC.character_by_cqi(faction_key, actor_cqi)
    if not actor then return false, "no such character" end
    if not IC.may_plot_as(faction_key, actor_cqi) then
        return false, "not yours"
    end
    if IC.is_civil_mission(plot_key) and actor:has_military_force() then
        return false, "commands"
    end
    if not IC.plot_is_aimed(plot_key) then
        local cost0 = IC.plot_cost(plot_key, faction_key)
        local has0 = IC.standing(faction_key, actor_cqi)
        if has0 < cost0 then return false, "standing", cost0 - has0 end
        return true
    end
    local victim = IC.character_by_cqi(faction_key, tonumber(target))
    if victim:command_queue_index() == actor_cqi then return false, "himself" end
    local mine = IC.house_of_character(actor, faction_key)
    if mine and IC.house_of_character(victim, faction_key) == mine then
        return false, "his own house"
    end

    local cost = IC.plot_cost(plot_key, faction_key)
    -- A GOLD MOVE is the treasury's to pay, not his.
    if IC.plot_by_key(plot_key).gold then
        local gold = IC.treasury(faction_key)
        if gold < cost then return false, "gold", cost - gold end
        return true
    end
    local has = IC.standing(faction_key, actor_cqi)
    if has < cost then return false, "standing", cost - has end
    return true
end

function IC.mood_of_the_court(faction_key, delta)
    local moved = 0
    for slug, _house in pairs(IC.court(faction_key).houses) do
        if slug ~= IC.CROWN then
            IC.move_loyalty(faction_key, slug, delta)
            moved = moved + 1
        end
    end
    return moved
end

function IC.house_of_victim(faction_key, cqi)
    local slug = IC.house_of_cqi(faction_key, cqi)
    if not slug then return nil end
    return IC.court(faction_key).houses[slug]
end

function IC.offices_of_house(faction_key, slug)
    local out = {}
    if not slug then return out end
    for office_slug, cqi in pairs(IC.court(faction_key).offices) do
        if IC.house_of_cqi(faction_key, cqi) == slug then
            out[#out + 1] = office_slug
        end
    end
    return out
end

function IC.provinces_of_house(faction_key, slug)
    local out = {}
    if not slug then return out end
    for province_key, cqi in pairs(IC.court(faction_key).govs) do
        if IC.house_of_cqi(faction_key, cqi) == slug then
            out[#out + 1] = province_key
        end
    end
    return out
end

function IC.plot_chance(faction_key, plot_key, actor_cqi, target)
    if not IC.can_plot(faction_key, plot_key, actor_cqi, target) then
        return nil
    end
    -- A SURE MOVE never rolls (the weregild).
    if IC.plot_by_key(plot_key).sure then return nil end
    local base = IC.TUNE["plot_chance_" .. tostring(plot_key)]
    if not base then return nil end
    local edge = 0
    if IC.plot_is_aimed(plot_key) then
        local mine = IC.standing(faction_key, actor_cqi) or 0
        local theirs = IC.standing(faction_key, tonumber(target)) or 0
        edge = math.floor((mine - theirs) / 10) * IC.TUNE.plot_chance_per_10
    end
    local chance = base + edge
    if chance < IC.TUNE.plot_chance_min then chance = IC.TUNE.plot_chance_min end
    if chance > IC.TUNE.plot_chance_max then chance = IC.TUNE.plot_chance_max end
    return chance
end

function IC.plot(faction_key, plot_key, actor_cqi, target)
    local ok, why, short = IC.can_plot(faction_key, plot_key, actor_cqi, target)
    if not ok then return false, why, short end
    local court = IC.court(faction_key)
    local plot = IC.plot_by_key(plot_key)
    local cost = IC.plot_cost(plot_key, faction_key)
    local slug = IC.house_of_cqi(faction_key, actor_cqi)
    local cqi = tonumber(target)
    local against = IC.house_of_cqi(faction_key, cqi)

    -- THE ODDS BEFORE THE PRICE: plot_chance asks can_plot, which refuses a man
    -- who can no longer afford the move, and a nil chance never rolls - so read
    -- after paying, a man holding under twice the price could not fail.
    local chance = IC.plot_chance(faction_key, plot_key, actor_cqi, target)
    if plot.gold then
        cm:treasury_mod(faction_key, -cost)
    else
        IC.add_standing(faction_key, actor_cqi, -cost)
    end

    if chance and cm:random_number(100, 1) > chance then
        if against then
            IC.move_loyalty(faction_key, against, -IC.tune(faction_key, "plot_fail_loyalty"))
            if plot_key == "purge" then
                IC.move_loyalty(faction_key, against,
                                -IC.TUNE.plot_purge_backfire)
            end
        end
        -- AN ERRAND HAS NO TARGET, so its line names the errand, not "moves
        -- against A party".
        -- A MISSION'S LINE carries where it went; an errand's
        -- its own key, an aimed move's the party it was aimed at.
        IC.log(faction_key, "plot_failed", slug,
               IC.plot_is_aimed(plot_key) and against
               or (plot.target and (plot_key .. ":" .. tostring(target)))
               or plot_key, cost)
        IC.feed(faction_key, "plot_fail",
                IC.move_result_key(plot_key, false, faction_key))
        IC.enforce_bars(faction_key)
        IC.apply_office_bundles(faction_key)
        IC.save(faction_key)
        -- A failed attempt still happened, so close the picker and report it.
        return true, "failed"
    end

    if plot_key == "bribe" then
        IC.add_standing(faction_key, cqi, IC.TUNE.plot_bribe_standing)
        IC.move_loyalty(faction_key, against, IC.TUNE.plot_bribe_loyalty)
        local house = IC.house_of_victim(faction_key, cqi)
        -- THE COUNT, NOT THE INSULT: the outsider still sits in their seat, and
        -- clearing the snub would announce it all over again.
        if house then house.clock = 0 end
    elseif plot_key == "discredit" then
        IC.add_standing(faction_key, cqi, -IC.TUNE.plot_discredit_standing)
        local house = IC.house_of_victim(faction_key, cqi)
        if house then
            house.weight = math.max(1, (house.weight or 0)
                                    - IC.TUNE.plot_discredit_weight)
        end
    elseif plot_key == "rumour" then
        IC.add_standing(faction_key, cqi, -IC.TUNE.plot_rumour_damage)
    elseif plot_key == "provoke" then
        -- Provoke sets the clock as well as reducing loyalty.
        IC.move_loyalty(faction_key, against, -IC.TUNE.plot_provoke_loyalty)
        IC.grudge_write(faction_key, against, "insult")
        local house = IC.house_of_victim(faction_key, cqi)
        if house then
            local now = house.clock or 0
            -- NO COUNTDOWN WITH SECESSION SWITCHED OFF: the insult still costs
            -- them loyalty, but nothing may start a clock the switch stops.
            -- THE RACE'S COUNT: a Dwarf party
            -- insulted counts half again as long.
            local count = IC.tune(faction_key, "plot_provoke_clock")
            if IC.TUNE.secession ~= false
               and (now <= 0 or now > count) then
                house.clock = count
                house.provoked = true
                if house.clock <= IC.TUNE.warn_turns
                   and (now <= 0 or now > IC.TUNE.warn_turns) then
                    IC.feed(faction_key, "secede_soon")
                end
            end
            if house.oath_mine then
                house.oath_mine, house.oath_theirs = nil, nil
                IC.log(faction_key, "oath_broken", against or "", "provoked", 0)
                -- A SECOND WRONG, and under the Iron Law a dearer one.
                IC.grudge_write(faction_key, against, "oath")
                IC.move_loyalty(faction_key, against, IC.tune(faction_key, "oath_broken_loyalty"))
            end
        end
    elseif plot_key == "purge" then
        -- BEFORE THE PARTY GOES: its book outlives it.
        IC.grudge_write(faction_key, against, "castout")
        IC.remove_house(faction_key, against)
        for slug2, _house2 in pairs(IC.court(faction_key).houses) do
            if slug2 ~= IC.CROWN then
                IC.move_loyalty(faction_key, slug2,
                                -IC.TUNE.plot_purge_witness)
            end
        end
    elseif plot_key == "oath" then
        local house = IC.house_of_victim(faction_key, cqi)
        if house then
            house.oath_mine = actor_cqi
            house.oath_theirs = cqi
        end
    elseif plot_key == "embezzle" then
        cm:treasury_mod(faction_key, IC.TUNE.plot_embezzle_gold)
        IC.mood_of_the_court(faction_key, -IC.tune(faction_key, "plot_embezzle_loyalty"))
    elseif plot_key == "feast" then
        IC.add_standing(faction_key, actor_cqi, IC.TUNE.plot_feast_standing)
        IC.mood_of_the_court(faction_key, -IC.TUNE.plot_feast_loyalty)
    elseif plot_key == "unseat" then
        for _, office_slug in ipairs(IC.offices_of_house(faction_key, against)) do
            IC.dismiss(faction_key, office_slug, true)
        end
        IC.move_loyalty(faction_key, against, -IC.TUNE.plot_unseat_loyalty)
        IC.grudge_write(faction_key, against, "bar")
    elseif plot_key == "recall" then
        for _, province_key in ipairs(IC.provinces_of_house(faction_key,
                                                            against)) do
            IC.release_governor(faction_key, province_key)
        end
        IC.move_loyalty(faction_key, against, -IC.TUNE.plot_recall_loyalty)
        IC.grudge_write(faction_key, against, "recall")
    elseif plot_key == "patron" then
        IC.add_standing(faction_key, cqi, IC.TUNE.plot_patron_standing)
        IC.move_loyalty(faction_key, against, IC.TUNE.plot_patron_loyalty)
    elseif plot_key == "kinsman" then
        local house = IC.house_of_victim(faction_key, cqi)
        local crown = IC.court(faction_key).houses[IC.CROWN]
        if house and crown then
            local moved = math.min(IC.TUNE.plot_kinsman_weight,
                                   math.max(0, (house.weight or 0) - 1))
            house.weight = (house.weight or 0) - moved
            crown.weight = (crown.weight or 0) + moved
        end
    elseif plot_key == "pledge" then
        IC.move_loyalty(faction_key, against, IC.TUNE.plot_pledge_loyalty)
        local house = IC.house_of_victim(faction_key, cqi)
        if house then house.clock = 0 end
        local crown = IC.court(faction_key).houses[IC.CROWN]
        if crown then
            crown.weight = math.max(1, (crown.weight or 0)
                                    - IC.TUNE.plot_pledge_weight)
        end
    elseif plot_key == "audience" then
        IC.mood_of_the_court(faction_key, IC.TUNE.plot_audience_loyalty)
    elseif plot_key == "circuit" then
        local court = IC.court(faction_key)
        court.prov = court.prov or {}
        for _, province_key in ipairs(IC.seats(faction_key)) do
            court.prov[province_key] = math.min(IC.TUNE.prov_loyalty_max,
                IC.province_loyalty(faction_key, province_key)
                + IC.TUNE.plot_circuit_prov)
        end
    elseif plot_key == "envoy" then
        local province, task = IC.envoy_split(target, faction_key)
        cm:apply_effect_bundle_to_faction_province(task.bundle,
            IC.held_region(faction_key, province), IC.TUNE.mission_turns)
    elseif plot_key == "diplomats" then
        -- (PLAYER, TARGET): CA's order, the one who acts first and the faction
        -- whose regard moves second (Neferata's theft is (neferata, victim, -3)).
        -- The rest is set on SUCCESS only - a failed send bought nothing, and
        -- resting too would charge twice.
        cm:apply_dilemma_diplomatic_bonus(faction_key, target, IC.TUNE.diplomats_bonus)
        court.sent[target] = cm:model():turn_number()
    elseif plot_key == "weregild" then
        IC.grudge_settle(faction_key, against, "weregild")
        IC.move_loyalty(faction_key, against, IC.TUNE.plot_weregild_loyalty)
    elseif plot_key == "murder" then
        local victim = IC.character_by_cqi(faction_key, cqi)
        IC.move_loyalty(faction_key, against, -IC.TUNE.plot_murder_loyalty)
        IC.grudge_write(faction_key, against, "slayer")
        IC.arranged_deaths[victim:command_queue_index()] = true
        cm:kill_character(cm:char_lookup_str(victim), false)
    end

    -- A MISSION'S TARGET IS ITS PLACE, which is what its Record line names.
    -- A GOLD MOVE IS THE TREASURY'S, so the Record
    -- names the throne as the payer, not the man sent.
    IC.log(faction_key, plot_key, plot.gold and IC.CROWN or slug,
           plot.target and target or against, cost)
    IC.feed(faction_key, "plot_ok", IC.move_result_key(plot_key, true, faction_key))
    IC.enforce_bars(faction_key)
    IC.apply_office_bundles(faction_key)
    IC.save(faction_key)
    return true, "landed"
end

-- THE SEAT A MOVE CAN COST THE MAN WHO MAKES IT: paying
-- can leave him under his seat's bar, and IC.plot unseats him the moment it is
-- paid. The price alone, since a move may fail and pay him nothing back.
function IC.plot_costs_seat(faction_key, plot_key, actor_cqi)
    local plot = IC.plot_by_key(plot_key)
    if plot and plot.gold then return nil end
    local after = IC.standing(faction_key, actor_cqi) - IC.plot_cost(plot_key, faction_key)
    for office_slug, cqi in pairs(IC.court(faction_key).offices) do
        local office = IC.office_by_slug(office_slug, faction_key)
        if cqi == actor_cqi and office and after < IC.tier_influence(office.tier) then
            return office_slug
        end
    end
    return nil
end

function IC.enforce_bars(faction_key)
    -- The other half of the exemption in IC.can_appoint: seating an AI officer
    -- under the bar and then unseating him on the next turn start would be
    -- worse than never seating him, because a dismissal is a loyalty event.
    if not IC.is_human(faction_key) then return end
    local court = IC.court(faction_key)
    local fallen = {}
    for office_slug, cqi in pairs(court.offices) do
        local office = IC.office_by_slug(office_slug, faction_key)
        if office and IC.standing(faction_key, cqi)
                < IC.tier_influence(office.tier) then
            fallen[#fallen + 1] = {slug = office_slug, cqi = cqi}
        end
    end
    for i = 1, #fallen do
        local slug = IC.house_of_cqi(faction_key, fallen[i].cqi)
        IC.dismiss(faction_key, fallen[i].slug, true)
        court.terms[fallen[i].slug] = nil
        IC.log(faction_key, "fell", slug, fallen[i].slug, 0)
    end
end

-- THE PARTY THAT LEADS THE COURT, Crown included, and its share. Ties go to
-- the first in IC.present_houses' order, the same on every machine.
function IC.gov_top(faction_key)
    local top, best = nil, -1
    for _, slug in ipairs(IC.present_houses(faction_key)) do
        local s = IC.share(faction_key, slug)
        if s > best then top, best = slug, s end
    end
    return top, math.max(best, 0)
end

-- WHERE A COURT STARTS: its house's own, else its strongest rival's, else the
-- Conclave - lore's own picture of Chaos Dwarf rule with nobody leading.
function IC.start_gov(faction_key)
    local R = IC.R(faction_key)
    if R.START_GOV[faction_key] then return R.START_GOV[faction_key] end
    local best, best_share = nil, -1
    for _, slug in ipairs(IC.present_houses(faction_key)) do
        if slug ~= IC.CROWN then
            local s = IC.share(faction_key, slug)
            if s > best_share then best, best_share = slug, s end
        end
    end
    return (best and IC.gov_for_party(best, faction_key)) or "conclave"
end

function IC.apply_gov_bundle(faction_key)
    local R = IC.R(faction_key)
    local want = IC.governments_on() and IC.court(faction_key).gov or nil
    for _, g in ipairs(R.GOV_ORDER) do
        cm:remove_effect_bundle(IC.gov_bundle(g, faction_key), faction_key)
    end
    if want then cm:apply_effect_bundle(IC.gov_bundle(want, faction_key), faction_key, -1) end
    return want
end

-- ONCE A TURN, every court: the start, or (player courts) the drift. A court
-- that only now takes its government - a new campaign, a save from before
-- governments - builds no pressure the same turn.
function IC.gov_step(faction_key)
    if not IC.governments_on() then return IC.apply_gov_bundle(faction_key) end
    local court = IC.court(faction_key)
    if not court.gov then
        court.gov = IC.start_gov(faction_key)
    elseif IC.gov_turn then
        IC.gov_turn(faction_key)
    end
    -- ONCE PER PLAYER COURT, a court that already had a government included.
    if not court.gov_intro and IC.is_human(faction_key) then
        court.gov_intro = true
        IC.feed(faction_key, "gov_intro")
    end
    return IC.apply_gov_bundle(faction_key)
end

-- WHAT THE COURT IS PULLING TOWARD NOW, ignoring the clock: the leading
-- rival's government at gov_drift_share, the Conclave when no rival is that
-- big, nothing when the leader has no government (the Crown, the Hearth) at
-- any share. `step` is this turn's pressure: the Conclave's pull comes every
-- gov_balance_turns.
function IC.gov_pull(faction_key)
    local top, share = IC.gov_top(faction_key)
    if not top or not IC.gov_for_party(top, faction_key) then return nil, top, 0 end
    if share >= IC.TUNE.gov_drift_share then
        return IC.gov_for_party(top, faction_key), top, 1
    end
    local now = cm:model():turn_number()
    return "conclave", nil, (now % IC.TUNE.gov_balance_turns == 0) and 1 or 0
end

function IC.gov_drift_on(faction_key)
    return IC.governments_on() and IC.TUNE.gov_drift ~= false
        and IC.is_human(faction_key) and IC.grace_left() == 0
end

-- THE DRIFT. Player courts only; frozen in the grace period,
-- a cooldown, or while a choice waits.
function IC.gov_turn(faction_key)
    local court = IC.court(faction_key)
    if IC.gov_expire then IC.gov_expire(faction_key) end
    local now = cm:model():turn_number()
    if not IC.gov_drift_on(faction_key) or now < (court.gov_cool or 0)
       or court.gov_ask then
        return false
    end
    local want, top, step = IC.gov_pull(faction_key)
    if not want then return false end
    -- THE GOVERNMENT'S OWN PARTY LEADING is a different leader: the count
    -- toward anything else starts again.
    if want == court.gov then
        court.gov_toward, court.gov_pressure = nil, 0
        return false
    end
    if court.gov_toward ~= want then court.gov_toward, court.gov_pressure = want, 0 end
    court.gov_pressure = (court.gov_pressure or 0) + step
    if court.gov_pressure >= IC.TUNE.gov_pressure_line then
        court.gov_ask = {gov = want, ends = now + IC.TUNE.gov_choice_turns, party = top}
        IC.log(faction_key, "doctrine_ask", top, want, court.gov_pressure)
        IC.feed(faction_key, "gov_pressure")
    end
    return true
end

-- WHAT A PARTY'S MEN CAN SPARE: each man's influence above his own seat's bar,
-- richest first, so paying never unseats anybody.
function IC.party_purse(faction_key, slug)
    local court, men, total, bar = IC.court(faction_key), {}, 0, {}
    for office_slug, cqi in pairs(court.offices) do
        local office = IC.office_by_slug(office_slug, faction_key)
        if office then bar[cqi] = math.max(bar[cqi] or 0, IC.tier_influence(office.tier)) end
    end
    local faction = real_faction(faction_key)
    local ok, list = pcall(function() return faction:character_list() end)
    if not ok or not list then return 0, men end
    for i = 0, list:num_items() - 1 do
        pcall(function()
            local man = list:item_at(i)
            if man and not man:is_null_interface() and man:is_alive()
               and IC.house_of_character(man, faction_key) == slug then
                local cqi = man:command_queue_index()
                local spare = IC.standing(faction_key, cqi) - (bar[cqi] or 0)
                if spare > 0 then
                    men[#men + 1] = {cqi = cqi, spare = spare}
                    total = total + spare
                end
            end
        end)
    end
    table.sort(men, function(a, b)
        if a.spare ~= b.spare then return a.spare > b.spare end
        return a.cqi < b.cqi
    end)
    return total, men
end

function IC.spend_party(faction_key, slug, cost)
    local total, men = IC.party_purse(faction_key, slug)
    if total < cost then return false, cost - total end
    local left, court = cost, IC.court(faction_key)
    for _, m in ipairs(men) do
        if left <= 0 then break end
        local take = math.min(m.spare, left)
        court.standing[m.cqi] = IC.standing(faction_key, m.cqi) - take
        left = left - take
    end
    return true
end

function IC.crown_purse(faction_key) return IC.party_purse(faction_key, IC.CROWN) end
function IC.spend_crown(faction_key, cost) return IC.spend_party(faction_key, IC.CROWN, cost) end

-- ONE CHANGE, for Accept and for a forced doctrine alike.
function IC.gov_change(faction_key, to, gain, loss, kind)
    local R = IC.R(faction_key)
    local court = IC.court(faction_key)
    local from = court.gov
    for _, p in ipairs(from and R.GOVS[from] and R.GOVS[from].parties or {}) do
        IC.move_loyalty(faction_key, p, loss)
    end
    for _, p in ipairs(R.GOVS[to].parties) do IC.move_loyalty(faction_key, p, gain) end
    court.gov, court.gov_pressure, court.gov_toward, court.gov_ask = to, 0, nil, nil
    IC.apply_gov_bundle(faction_key)
    IC.log(faction_key, kind or "doctrine", nil, to, 0)
    IC.feed(faction_key, "gov_changed")
end

-- THE WAITING CHOICE, if the court still pulls toward it. A party that asked
-- can leave in the same turn (a secession, a purge) after the lapse test ran,
-- and paying for or taking a choice nobody backs is the fault this closes.
function IC.gov_ask_live(faction_key)
    local court = IC.court(faction_key)
    local ask = court.gov_ask
    if not ask then return nil end
    if IC.gov_pull(faction_key) ~= ask.gov then
        court.gov_ask = nil
        IC.log(faction_key, "doctrine_lapse", ask.party, ask.gov, 0)
        return nil
    end
    return ask
end

function IC.gov_accept(faction_key)
    local ask = IC.gov_ask_live(faction_key)
    if not ask then return false, "no choice" end
    IC.gov_change(faction_key, ask.gov, IC.TUNE.gov_accept_gain, IC.TUNE.gov_accept_loss, "doctrine")
    IC.save(faction_key)
    return true
end

function IC.gov_hold_price(faction_key)
    return IC.TUNE.gov_hold_cost * (1 + (IC.court(faction_key).gov_holds or 0))
end

function IC.gov_hold(faction_key)
    local court = IC.court(faction_key)
    local ask = IC.gov_ask_live(faction_key)
    if not ask then return false, "no choice" end
    local price = IC.gov_hold_price(faction_key)
    local ok, short = IC.spend_crown(faction_key, price)
    if not ok then return false, "gov_purse", short end
    court.gov_holds = (court.gov_holds or 0) + 1
    court.gov_pressure = math.floor(IC.TUNE.gov_pressure_line / 2)
    court.gov_ask = nil
    if ask.party then IC.move_loyalty(faction_key, ask.party, IC.TUNE.gov_hold_loyalty) end
    IC.log(faction_key, "doctrine_hold", ask.party, ask.gov, price)
    IC.save(faction_key)
    return true
end

-- THE CHOICE'S END, inside the court's turn so every machine settles it the
-- same: a choice the court no longer pulls toward lapses, an unanswered one
-- at its end is Accept. No test of ask.party: either party of a two-party
-- government backs it, and the pull already answers that.
function IC.gov_expire(faction_key)
    local court = IC.court(faction_key)
    local ask = court.gov_ask
    if not ask then return nil end
    local want = IC.gov_pull(faction_key)
    if ask.gov == court.gov or want ~= ask.gov then
        court.gov_ask = nil
        IC.log(faction_key, "doctrine_lapse", ask.party, ask.gov, 0)
        return "lapsed"
    end
    if cm:model():turn_number() >= ask.ends then
        IC.gov_accept(faction_key)
        return "accepted"
    end
    return nil
end

-- FORCING A DOCTRINE: from the Court tab, any time, paid
-- from the Crown's spare influence. A government whose party sits in no court
-- can be forced; it pleases nobody.
function IC.can_force_gov(faction_key, to)
    local R = IC.R(faction_key)
    if not IC.governments_on() then return false, "gov_off" end
    if not R.GOVS[to or ""] then return false, "no such government" end
    local court = IC.court(faction_key)
    if to == court.gov then return false, "gov_same" end
    local now = cm:model():turn_number()
    if now < (court.gov_cool or 0) then return false, "gov_cool", court.gov_cool - now end
    local total = IC.crown_purse(faction_key)
    if total < IC.TUNE.gov_force_cost then
        return false, "gov_purse", IC.TUNE.gov_force_cost - total
    end
    return true
end

function IC.gov_force(faction_key, to)
    local ok, why, n = IC.can_force_gov(faction_key, to)
    if not ok then return false, why, n end
    IC.spend_crown(faction_key, IC.TUNE.gov_force_cost)
    IC.gov_change(faction_key, to, IC.TUNE.gov_force_gain, IC.TUNE.gov_force_loss, "doctrine_force")
    IC.court(faction_key).gov_cool = cm:model():turn_number() + IC.TUNE.gov_force_cooldown
    IC.save(faction_key)
    return true
end

-- THE BOOK OF GRUDGES, Dwarf courts only. CA keeps
-- grudge points ON the offender's armies and settlements, in two pooled
-- resources (wh3_campaign_grudges.lua:129-131), not per Dwarf faction - so a
-- faction's weight is one number for every Dwarf court.
IC.BOOK_ARMY = "wh3_dlc25_dwf_grudge_points_enemy_armies"
IC.BOOK_SETTLEMENT = "wh3_dlc25_dwf_grudge_points_enemy_settlements"
IC.GRUDGE_POINTS = "wh3_dlc25_dwf_grudge_points"

-- ONE POOL, as CA reads it (remove_grudge_points_for_faction): 0 when the
-- entity has none, since resource() is "Null if not present".
local function book_pool(entity, key)
    local r = entity:pooled_resource_manager():resource(key)
    if r:is_null_interface() then return 0 end
    return r:value()
end

-- ARMIES, NOT GARRISONS (CA never writes points on armed citizenry), then
-- settlements.
local function book_sum(other)
    local total = 0
    local forces = other:military_force_list(true)
    for i = 0, forces:num_items() - 1 do
        total = total + book_pool(forces:item_at(i), IC.BOOK_ARMY)
    end
    local regions = other:region_list()
    for i = 0, regions:num_items() - 1 do
        total = total + book_pool(regions:item_at(i), IC.BOOK_SETTLEMENT)
    end
    return total
end

-- {turn = n, w = {[faction key] = weight}}: unsaved, and FILLED ON THE TURN PATH
-- ONLY (IC.book_list with fill, from IC.book_tick). The panel reads it and never
-- fills it, so what a machine holds never depends on its player opening the
-- court. ponytail: a faction is weighed at the first Dwarf court's turn start of
-- the round; points it gains later in the round count next turn.
IC._book = nil

-- faction_key is the court asking; the number does not depend on it (above).
function IC.book_weight(faction_key, other_key)
    local c = IC._book
    if c and c.turn == cm:model():turn_number() and c.w[other_key] then
        return c.w[other_key]
    end
    local other = real_faction(other_key)
    if not other then return 0 end
    local ok, w = pcall(book_sum, other)
    if not ok then
        IC.warn("IRON COURT: the Book failed to weigh " .. tostring(other_key) .. ": " .. tostring(w))
        return 0
    end
    return w
end

-- ONE MET FACTION: nil to skip it (null, dead, or a Dwarf - CA writes no points
-- on one), else its key and weight.
local function book_weigh(other, now, fill)
    if other:is_null_interface() or other:is_dead()
            or other:subculture() == IC.RACES.dwf.subculture then
        return nil
    end
    local key = other:name()
    local c = IC._book
    local w = c and c.turn == now and c.w[key]
    if not w then
        w = book_sum(other)
        if fill then c.w[key] = w end
    end
    return key, w
end

-- EVERY FACTION THIS COURT HAS MET that carries points, heaviest first, ties by
-- key so every machine sorts alike. `fill` = the turn path; the panel omits it.
function IC.book_list(faction_key, fill)
    local out = {}
    local own = real_faction(faction_key)
    if not own or IC.race_key(faction_key) ~= "dwf" then return out end
    local now = cm:model():turn_number()
    if fill and not (IC._book and IC._book.turn == now) then
        IC._book = {turn = now, w = {}}
    end
    local met = own:factions_met()
    for i = 0, met:num_items() - 1 do
        local ok, key, w = pcall(book_weigh, met:item_at(i), now, fill)
        if not ok then
            IC.warn("IRON COURT: the Book failed to weigh a faction met by "
                    .. faction_key .. ": " .. tostring(key))
        elseif key and w > 0 then
            out[#out + 1] = {key = key, weight = w}
        end
    end
    table.sort(out, function(a, b)
        if a.weight ~= b.weight then return a.weight > b.weight end
        return a.key < b.key
    end)
    return out
end

function IC.book_names(faction_key, n)
    local all, out = IC.book_list(faction_key), {}
    for i = 1, math.min(n or IC.TUNE.book_top, #all) do out[i] = all[i] end
    return out
end

-- THE BANDS: reaching book_bands[i] applies book_penalty[i]
-- ONCE, in order, never reversed. court.book[other] is how many are crossed,
-- saved in field 20, so a load never fires one again. (own, them): CA's five
-- calls put the actor first and the faction whose regard moves second, so it
-- is the named faction's regard for the court that falls.
function IC.book_tick(faction_key)
    local court = IC.court(faction_key)
    local bands, penalty = IC.TUNE.book_bands, IC.TUNE.book_penalty
    local fired = 0
    for _, e in ipairs(IC.book_list(faction_key, true)) do
        local had = court.book[e.key] or 0
        local n = had
        while n < #bands and e.weight >= bands[n + 1] do n = n + 1 end
        for i = had + 1, n do
            cm:apply_dilemma_diplomatic_bonus(faction_key, e.key, penalty[i])
            fired = fired + 1
        end
        if n > had then court.book[e.key] = n end
    end
    return fired
end

-- A TREATY WITH A FACTION THE BOOK NAMES wrongs these two.
IC.BOOK_WRONGED = {"legion", "temple"}

-- NAMED = THE SAVED BANDS reach book_named, not the live weight: CA's own
-- listener on the same event wipes an ally's points (wh3_campaign_grudges.lua,
-- remove_grudge_points_when_form_alliance_with_dwarfs), and which runs first is
-- not ours to know. IC.state, not IC.court: asking must never create a court.
function IC.in_book(faction_key, other_key)
    local n = ((IC.state[faction_key] or {}).book or {})[other_key] or 0
    return n > 0 and IC.TUNE.book_bands[n] >= IC.TUNE.book_named
end

-- A "peace" grudge in each wronged party's book, at most one each a turn: a
-- deal that is peace and trade at once is one wrong, however many events.
function IC.book_peace(faction_key, other_key)
    if IC.race_key(faction_key) ~= "dwf" then return false end
    IC.loaded(faction_key)
    if not IC.in_book(faction_key, other_key) then return false end
    local now = cm:model():turn_number()
    local wrote = false
    for _, slug in ipairs(IC.BOOK_WRONGED) do
        local again = false
        for _, g in ipairs(IC.grudges(faction_key, slug)) do
            if g.code == "peace" and g.turn == now then again = true end
        end
        if not again then
            IC.grudge_write(faction_key, slug, "peace")
            wrote = true
        end
    end
    return wrote
end

function IC.turn(faction_key)
    IC.load(faction_key)
    -- BEFORE ANYTHING THIS TURN MOVES LOYALTY. See IC.party_placate.
    if IC.party_placate then IC.party_placate(faction_key) end
    -- Roll the court before backgrounds, as IC.seed does, or an AI faction's
    -- first turn deals every starting man to the Crown and every rival party
    -- is born empty. Only the player's court went through IC.seed.
    IC.roll_court(faction_key)
    IC.stamp_court(faction_key)
    IC.reconcile_houses(faction_key)
    -- BEFORE ANYTHING READS A SHARE THIS TURN.
    IC.fade_renown(faction_key)
    IC.ensure_leaders(faction_key)
    IC.reconcile_governors(faction_key)
    IC.tick_provinces(faction_key)
    IC.grow_governors(faction_key)
    IC.income(faction_key)
    IC.expire_terms(faction_key)
    IC.warn_terms(faction_key)
    IC.enforce_bars(faction_key)
    IC.ai_fill_offices(faction_key)
    IC.ai_fill_governors(faction_key)
    -- Reconcile standing traits after this turn's income.
    IC.stamp_standings(faction_key)
    IC.drift_loyalty(faction_key)
    IC.apply_office_bundles(faction_key)
    IC.apply_governor_bundles(faction_key)
    -- Apply pressure after loyalty drift and before advancing secession clocks.
    IC.apply_control_bundle(faction_key)
    -- BEFORE THE GOVERNMENT.
    IC.law_turn(faction_key)
    IC.gov_step(faction_key)
    IC.tick_pressure(faction_key)
    if not IC.feed_held then IC.flush_feed() end
    if IC.party_turn then
        -- CAUGHT AND SAID. Uncaught, one error in the parties' turn skips the
        -- secession clocks, the Crown's split and the save below for the whole
        -- court. The harness fails on any such line.
        local ok, err = pcall(IC.party_turn, faction_key)
        if not ok then
            IC.warn("IRON COURT: the parties' turn failed in " .. faction_key
                   .. ": " .. tostring(err))
        end
    end
    local warned = IC.tick_secession(faction_key)
    IC.splinter(faction_key)
    -- LAST: a secession or a split above is what moves a man between parties.
    IC.stamp_members(faction_key)
    -- AND THE BAND AGAIN, after everything above that moves weight: otherwise
    -- a split across a floor wears the old band all turn.
    IC.apply_control_bundle(faction_key)
    -- THE BOOK, caught and said like the parties'
    -- turn: a Book that fails must not cost the court its save.
    local ok_book, err_book = pcall(IC.book_tick, faction_key)
    if not ok_book then
        IC.warn("IRON COURT: the Book failed in " .. faction_key .. ": " .. tostring(err_book))
    end
    IC.save(faction_key)
    return warned
end

function IC.ensure_own_house(faction_key)
    local court = IC.court(faction_key)
    if court.houses[IC.CROWN] then return false end
    IC.add_house(faction_key, IC.CROWN)
    IC.save(faction_key)
    return true
end

function IC.roll_court(faction_key)
    local R = IC.R(faction_key)
    if IC.court_rolled(faction_key) then return false end
    IC.add_house(faction_key, IC.CROWN)
    local pool = {}
    for i = 1, #R.PARTIES do
        if R.PARTIES[i] ~= IC.CROWN then pool[#pool + 1] = R.PARTIES[i] end
    end
    local want = cm:random_number(IC.TUNE.rivals_max, IC.TUNE.rivals_min)
    for _ = 1, want do
        if #pool == 0 then break end
        local pick = cm:random_number(#pool, 1)
        local slug = table.remove(pool, pick)
        IC.add_house(faction_key, slug)
        IC.name_party(faction_key, slug)
        IC.roll_party_traits(faction_key, slug)
    end
    IC.court(faction_key).rolled = true
    IC.save(faction_key)
    return true
end

function IC.name_party(faction_key, slug)
    local R = IC.R(faction_key)
    local court = IC.court(faction_key)
    local house = court.houses[slug]
    if not house then return false end
    local tails = R.NAME_TAILS[slug]
    if not tails or #tails == 0 then return false end
    house.head = cm:random_number(#R.NAME_HEADS, 1)
    house.tail = cm:random_number(#tails, 1)
    return true
end

function IC.roll_party_traits(faction_key, slug)
    local R = IC.R(faction_key)
    local house = IC.court(faction_key).houses[slug]
    if not house then return false end
    local n = #R.PARTY_TRAITS
    if n < 2 then return false end
    house.t1 = cm:random_number(n, 1)
    local second = cm:random_number(n - 1, 1)
    if second >= house.t1 then second = second + 1 end
    house.t2 = second
    return true
end

function IC.party_leader(faction_key, slug)
    local court = IC.court(faction_key)
    local faction = real_faction(faction_key)
    if not faction or not slug then return nil end
    if slug == IC.CROWN then
        local seated = IC.faction_leader_cqi(faction_key)
        if seated and IC.house_of_cqi(faction_key, seated) == IC.CROWN then
            return seated
        end
    end
    local lords = IC.party_lords(faction_key, slug)
    for i = 1, #lords do
        if IC.may_speak(faction_key, lords[i]) then return lords[i] end
    end
    return IC.party_colonel(faction_key, slug)
end

-- A garrison commander, by type: "retainer" (a non-general with a force) would
-- also take a hero stub with an army.
function IC.is_colonel(character)
    local ok, yes = pcall(function() return character:character_type("colonel") end)
    return ok and yes == true
end

-- THE LAST RESORT, a garrison commander: a court whose
-- lords are all legends or all busy still gives every party a face. He is not
-- in party_lords, so he never leads a rising. Highest standing first.
function IC.party_colonel(faction_key, slug)
    local faction = real_faction(faction_key)
    if not faction or not slug then return nil end
    local best, best_standing
    local list = faction:character_list()
    for i = 0, list:num_items() - 1 do
        local man = list:item_at(i)
        if man and not man:is_null_interface()
                and IC.is_colonel(man)
                and IC.house_of_character(man, faction_key) == slug then
            local cqi = man:command_queue_index()
            local standing = IC.standing(faction_key, cqi)
            if IC.may_speak(faction_key, cqi)
                    and (not best or standing > best_standing) then
                best, best_standing = cqi, standing
            end
        end
    end
    return best
end

function IC.may_speak(faction_key, cqi)
    if not cqi then return false end
    local man = IC.character_by_cqi(faction_key, cqi)
    if not man then return false end
    local key
    pcall(function() key = man:character_subtype_key() end)
    if not key or key == "" then return true end
    return not IC.NOT_DWARF[key]
end

function IC.party_lords(faction_key, slug)
    local R = IC.R(faction_key)
    local out = {}
    local heroes = {}
    local members = 0
    local court = IC.court(faction_key)
    local faction = real_faction(faction_key)
    if not court or not faction or not slug then return out, 0, {}, {} end
    local list = faction:character_list()
    for i = 0, list:num_items() - 1 do
        local man = list:item_at(i)
        if man and not man:is_null_interface()
                and IC.house_of_character(man, faction_key) == slug then
            members = members + 1
            if IC.can_defect_hero(man) then
                local key = nil
                pcall(function() key = man:character_subtype_key() end)
                heroes[#heroes + 1] = {cqi = man:command_queue_index(),
                                       subtype = key,
                                       agent = R.REBEL_HEROES[key]}
            end
            if IC.is_lordly(man) then
                local cqi = man:command_queue_index()
                local row = {cqi = cqi, standing = court.standing[cqi] or 0,
                             defects = IC.can_defect(man)}
                out[#out + 1] = row
            end
        end
    end
    table.sort(out, function(a, b)
        if a.standing ~= b.standing then return a.standing > b.standing end
        return a.cqi < b.cqi
    end)
    local cqis = {}
    local able = {}
    for i = 1, #out do
        cqis[i] = out[i].cqi
        if out[i].defects then able[#able + 1] = out[i].cqi end
    end
    return cqis, members, able, heroes
end

IC.REBEL_HEROES = {
    ["wh3_dlc23_chd_bull_centaur_taurruk"] = "champion",
    ["wh3_dlc23_chd_infernal_castellan"] = "engineer",
    ["wh3_dlc23_chd_daemonsmith_sorcerer_death"] = "wizard",
    ["wh3_dlc23_chd_daemonsmith_sorcerer_fire"] = "wizard",
    ["wh3_dlc23_chd_daemonsmith_sorcerer_hashut"] = "wizard",
    ["wh3_dlc23_chd_daemonsmith_sorcerer_metal"] = "wizard",
}

function IC.can_defect_hero(character)
    if not character or character:is_null_interface() then return false end
    if IC.is_lordly(character) then return false end
    if IC.is_legend(character) then return false end
    local key = nil
    pcall(function() key = character:character_subtype_key() end)
    return in_any_race("REBEL_HEROES", key) ~= nil
end

function IC.can_defect(character)
    if not IC.is_lordly(character) then return false end
    if IC.is_legend(character) then return false end
    local key = nil
    pcall(function() key = character:character_subtype_key() end)
    return in_any_race("REBEL_GENERALS", key) == true
end

function IC.is_lordly(character)
    local kind = IC.kind_of_character(character)
    return kind == "general" or kind == "lord"
end

function IC.party_traits(faction_key, slug)
    local R = IC.R(faction_key)
    local out = {}
    local house = IC.court(faction_key).houses[slug or ""]
    if not house then return out end
    for _, which in ipairs({house.t1 or 0, house.t2 or 0}) do
        local trait = R.PARTY_TRAITS[which]
        if trait then out[#out + 1] = trait end
    end
    return out
end

function IC.faction_leader_cqi(faction_key)
    local faction = real_faction(faction_key)
    if not faction then return nil end
    local ok, leader = pcall(function() return faction:faction_leader() end)
    if not ok or not leader or leader:is_null_interface() then return nil end
    local cqi = nil
    pcall(function() cqi = leader:command_queue_index() end)
    return cqi
end

-- Derive the leader trait from CQI so a successor brings a different trait.
function IC.leader_trait(faction_key, slug)
    local R = IC.R(faction_key)
    local cqi = IC.party_leader(faction_key, slug)
    if not cqi then return nil end
    return R.LEADER_TRAITS[(cqi % #R.LEADER_TRAITS) + 1]
end

-- AN OFFICE WHOSE BONUS IS SWITCHED OFF until a turn. `of` is the party whose
-- man holds it, `by` the party that did it. It ends at its turn or the moment the seat stops being `of`'s, whichever is first.
function IC.stall_office(faction_key, office_slug, turns, by, cause)
    local court = IC.court(faction_key)
    local cqi = court.offices[office_slug or ""]
    if not cqi then return false end
    local of = IC.house_of_cqi(faction_key, cqi)
    if not of then return false end
    court.stalled[office_slug] = {ends = cm:model():turn_number() + turns,
                                  of = of, by = by, cause = cause}
    IC.apply_office_bundles(faction_key)
    IC.save(faction_key)
    return true
end

function IC.stalled_for(faction_key, office_slug)
    local s = IC.court(faction_key).stalled[office_slug or ""]
    if not s then return 0 end
    return math.max(0, s.ends - cm:model():turn_number())
end

function IC.end_stalls(faction_key)
    local court = IC.court(faction_key)
    court.stalled = court.stalled or {}
    local now = cm:model():turn_number()
    local gone, back = {}, {}
    for office_slug, s in pairs(court.stalled) do
        local cqi = court.offices[office_slug]
        local same = cqi and IC.house_of_cqi(faction_key, cqi) == s.of
        if now >= s.ends or not same then
            gone[#gone + 1] = office_slug
            -- BACK AT WORK only when it ran its turns with its man still in it;
            -- a stall that ended because he left has nothing coming back.
            if same then back[#back + 1] = {slug = office_slug, of = s.of} end
        end
    end
    for i = 1, #gone do court.stalled[gone[i]] = nil end
    for i = 1, #back do
        IC.log(faction_key, "stall_end", back[i].of, back[i].slug, 0)
    end
    if #back > 0 then
        IC.feed(faction_key, "stall_end",
                #back == 1 and IC.office_title_key(back[1].slug, faction_key) or nil)
    end
    return #gone
end

-- HAS THIS FACTION MET THAT ONE. faction:factions_met() is CA's own list.
function IC.has_met(a_key, b_key)
    local faction = real_faction(a_key)
    if not faction then return false end
    local met = false
    pcall(function()
        local list = faction:factions_met()
        for i = 0, list:num_items() - 1 do
            if list:item_at(i):name() == b_key then met = true; return end
        end
    end)
    return met
end

-- NEWS OF AN AI COURT, for every human who has met it. A PARTY'S NAME, NOT A
-- LOC CALL: the name is the rolled string, read now because a seceded party's is gone afterwards; the faction stays a
-- key and the panel names it at draw time.
-- A HUMAN WHO HEARS A COURT'S NEWS: one who has met it and runs a court of his
-- own. An Empire player has no panel and no Record tab to read it in.
function IC.hears(human_key, source_key)
    if not IC.has_met(human_key, source_key) then return false end
    local ok, runs = pcall(function()
        local f = cm:get_faction(human_key)
        return f and not f:is_null_interface() and IC.runs_court(f)
    end)
    return ok and runs == true
end

function IC.news(source_key, kind, a, b)
    if not source_key or IC.is_human(source_key) then return 0 end
    local ok, human = pcall(function() return cm:get_human_factions() end)
    if not ok or not human then return 0 end
    local a_name = a and (IC.party_name(source_key, a) or a) or "-"
    local b_name = b and (IC.party_name(source_key, b) or b) or "-"
    local told = 0
    for i = 1, #human do
        if IC.hears(human[i], source_key) then
            local court = IC.court(human[i])
            court.news = court.news or {}
            court.news[#court.news + 1] = {turn = cm:model():turn_number(),
                kind = kind, faction = source_key, a = a_name, b = b_name}
            while #court.news > IC.TUNE.news_max do table.remove(court.news, 1) end
            IC.save(human[i])
            told = told + 1
        end
    end
    return told
end

-- `about` is the court the news is about, whose race words it; the card goes
-- to faction_key.
function IC.raise_feed_located(faction_key, slug, x, y, about)
    local ev = IC.EVENTS[slug]
    if not ev or not x or not y then return false end
    local key = IC.event_stem(slug, about or faction_key)
    pcall(function()
        cm:show_message_event_located(faction_key,
            "event_feed_strings_text_" .. key .. "_title",
            "event_feed_strings_text_" .. key .. "_primary",
            "event_feed_strings_text_" .. key .. "_secondary",
            x, y, ev[2], IC.event_index(slug, about or faction_key))
    end)
    return true
end

-- WHAT A CONFEDERATED COURT BRINGS: its parties'
-- loyalty, weighted by their weight and held to 25..75; nil when it had no
-- court.
function IC.inherited_loyalty(host_key, joined_key)
    if not IC.state[joined_key] then IC.load(joined_key) end
    local total, sum = 0, 0
    for _, h in pairs(IC.court(joined_key).houses) do
        local w = math.max(0, h.weight or 0)
        total = total + w
        sum = sum + w * (h.loyalty or IC.TUNE.loyalty_start)
    end
    if total <= 0 then return nil end
    return math.max(25, math.min(75, math.floor(sum / total + 0.5)))
end

-- AND THEN IT IS GONE: its countdowns, feuds, plot and demand go with it.
function IC.forget_court(faction_key)
    IC.state[faction_key] = nil
    if IC.agenda_state then IC.agenda_state[faction_key] = nil end
    cm:set_saved_value("derpy_ic_" .. faction_key, "")
    cm:set_saved_value("derpy_ic_agenda_" .. faction_key, "")
end

function IC.party_name(faction_key, slug)
    local house = IC.court(faction_key).houses[slug]
    return house and IC.rolled_name(slug, house.head, house.tail, faction_key)
end

function IC.rolled_name(slug, head, tail, faction_key)
    if not head or not tail then return nil end
    local R = IC.R(faction_key)
    local tails = R.NAME_TAILS[slug]
    if not tails or #tails == 0 then return nil end
    -- Wrapped, not indexed: a save rolled against the older, longer head list
    -- still names every party.
    return R.NAME_HEADS[(head - 1) % #R.NAME_HEADS + 1] .. " of "
           .. tails[(tail - 1) % #tails + 1]
end

function IC.reconcile_houses(faction_key)
    local court = IC.court(faction_key)
    local dead = {}
    for slug, house in pairs(court.houses) do
        if not IC.is_party(slug, faction_key) and not house.confed then
            dead[#dead + 1] = slug
        end
    end
    local changed = false
    for i = 1, #dead do
        IC.remove_house(faction_key, dead[i])
        changed = true
    end
    if IC.roll_court(faction_key) then changed = true end
    for slug, house in pairs(court.houses) do
        if slug ~= IC.CROWN and not house.head then
            if IC.name_party(faction_key, slug) then changed = true end
        end
        if not house.t1 then
            if IC.roll_party_traits(faction_key, slug) then changed = true end
        end
    end
    if IC.prune_confed(faction_key) > 0 then changed = true end
    if changed then IC.save(faction_key) end
    return changed
end

function IC.prune_confed(faction_key)
    local court = IC.court(faction_key)
    local orphans = {}
    local any = false
    for slug, house in pairs(court.houses) do
        if house.confed then orphans[slug] = true; any = true end
    end
    if not any then return 0 end
    local faction = real_faction(faction_key)
    if not faction then return 0 end
    local list = faction:character_list()
    if list:num_items() == 0 then return 0 end
    for i = 0, list:num_items() - 1 do
        local origin = IC.origin_of_character(list:item_at(i))
        if origin then orphans[origin] = nil end
    end
    local gone = 0
    for slug in pairs(orphans) do
        IC.log(faction_key, "dissolve", slug, nil, 0)
        IC.remove_house(faction_key, slug)
        gone = gone + 1
    end
    return gone
end

function IC.seed(faction_key)
    local faction = real_faction(faction_key)
    if not faction then return end
    -- Roll the court before backgrounds, or every lord defaults to the Crown.
    IC.roll_court(faction_key)
    IC.stamp_court(faction_key)
    IC.apply_office_bundles(faction_key)
    IC.save(faction_key)
end

function IC.stamp_incoming(faction_key, slug, attempts, before, loyalty)
    attempts = attempts or 0
    local faction = real_faction(faction_key)
    if not faction then return end
    local list = faction:character_list()
    before = before or {}
    local stamped = 0
    local tally = {}
    for i = 0, list:num_items() - 1 do
        local man = list:item_at(i)
        if man and not man:is_null_interface()
           and not before[man:command_queue_index()] then
        local fixed = IC.fixed_history(man)
        local want = fixed and fixed.origin or slug
        -- AN AI COURT HAS STAMPED ITS MEN ALREADY: a rolled birthplace gives
        -- way to the hall they arrive from, or stamp_origin refuses every one
        -- and the house never joins.
        local had = IC.origin_of_character(man)
        if had and had ~= want and not (fixed and fixed.origin) then
            cm:force_remove_trait(cm:char_lookup_str(man), IC.origin_trait(had))
        end
        if IC.stamp_origin(man, want, true) or had == want then
            stamped = stamped + 1
        end
        IC.stamp_bg(man, IC.background_for(man, faction_key, tally), true)
        end
    end
    if stamped > 0 and IC.add_house(faction_key, slug, true, loyalty) then
        IC.log(faction_key, "join", slug, nil, stamped)
        IC.feed(faction_key, "party_joined")
        IC.save(faction_key)
    end
    if stamped == 0 and attempts < 6 then
        cm:callback(function()
            IC.stamp_incoming(faction_key, slug, attempts + 1, before, loyalty)
        end, 3)
    end
end

-- MULTIPLAYER. A change to the campaign made on one machine and not the others
-- is a desync, so nothing the panel does changes the model straight off a click.
-- It goes through IC.mp_send, which in multiplayer broadcasts with
-- CampaignUI.TriggerCampaignScriptEvent. CA delivers the UITrigger to every
-- machine in one order, and IC.mp_receive runs the same op on all of them. The
-- Great Guilds' transport, copied so this mod depends on no other.
--
-- SINGLE PLAYER RUNS THE SAME OPS, called at once instead of broadcast, so every
-- op is exercised by ordinary play and only the round trip is not.
--
-- NO OP RELOADS THE COURT. The first tick loads every human court on every
-- machine, and IC.load replaces the court from the save, which would drop
-- anything this turn has not saved yet.
--
-- NOT YET TRIED IN A TWO-PLAYER CAMPAIGN.
IC.MP_TAG = "ic1"
-- The only committed ceiling on a trigger string: MCT's MultiplayerCommunicator.
IC.MP_MAX = 100
IC.MP_OPS = {}

-- CQI -> HUMAN FACTION. Only a human can send one of these.
function IC.faction_by_cqi(cqi)
    if not cqi then return nil end
    local found = nil
    pcall(function()
        local humans = cm:get_human_factions()
        for i = 1, #humans do
            local f = cm:get_faction(humans[i])
            if f and not f:is_null_interface() and f:command_queue_index() == cqi then
                found = humans[i]
                return
            end
        end
    end)
    return found
end

-- True when the op ran (single player) or went out (multiplayer); false when
-- it was refused, so the panel knows whether an answer is coming.
function IC.mp_send(faction_key, op, arg)
    if not faction_key or not IC.MP_OPS[op] then
        IC.warn("IRON COURT: action " .. tostring(op) .. " for "
                .. tostring(faction_key) .. " not sent")
        return false
    end
    arg = tostring(arg or "")
    if not IC.is_mp() then
        IC.MP_OPS[op](faction_key, arg)
        return true
    end
    local id = IC.MP_TAG .. "|" .. op .. "|" .. arg
    -- REFUSE, NEVER FALL BACK. Applied here instead, the change would reach this
    -- machine only - the fault this section exists to prevent.
    if #id > IC.MP_MAX then
        IC.warn("IRON COURT: " .. op .. " is " .. #id .. " characters, over "
                .. IC.MP_MAX .. " - not sent")
        return false
    end
    local cqi = nil
    pcall(function()
        local f = cm:get_faction(faction_key)
        if f and not f:is_null_interface() then cqi = f:command_queue_index() end
    end)
    if not cqi then
        IC.warn("IRON COURT: no command queue index for " .. tostring(faction_key)
                .. " - " .. op .. " not sent")
        return false
    end
    local ok, err = pcall(function() CampaignUI.TriggerCampaignScriptEvent(cqi, id) end)
    if not ok then IC.warn("IRON COURT: " .. op .. " not sent: " .. tostring(err)) end
    return ok
end

-- THE RECEIVING END. Returns the faction it acted for, and nil for anything not
-- ours: every other mod's UITrigger comes through the same event, silently.
function IC.mp_receive(id, cqi)
    if type(id) ~= "string" then return nil end
    local op, arg = string.match(id, "^" .. IC.MP_TAG .. "|([^|]*)|(.*)$")
    if not op then return nil end
    local fn = IC.MP_OPS[op]
    if not fn then
        IC.warn("IRON COURT: unknown action " .. op .. " received")
        return nil
    end
    local faction_key = IC.faction_by_cqi(cqi)
    if not faction_key then
        IC.warn("IRON COURT: " .. op .. " from unknown faction cqi " .. tostring(cqi))
        return nil
    end
    fn(faction_key, arg)
    return faction_key
end

-- The argument's `|`-separated fields, an empty one kept as "".
local function fields(arg)
    local out = {}
    for piece in string.gmatch((arg or "") .. "|", "([^|]*)|") do out[#out + 1] = piece end
    return out
end

-- AND THE ANSWER, to whoever asked. The panel sets IC.after_op; the model never
-- names the panel. Returns what the model said.
local function answer(faction_key, op, arg, done, why, spare)
    -- THE BAND THE MOVE REACHED, worn now: the panel names the live band, so
    -- the bundle cannot wait for the next turn start.
    if done then IC.apply_control_bundle(faction_key) end
    if IC.after_op then IC.after_op(faction_key, op, arg, done, why, spare) end
    return done, why, spare
end

-- A number crosses the wire as its decimal string and comes back through
-- tonumber. A plot's target stays the string the panel passes, and an empty
-- one is nil, as the panel passes it when a plot has no target.
IC.MP_OPS.appoint = function(fk, arg)          -- office|cqi
    local f = fields(arg)
    return answer(fk, "appoint", arg, IC.appoint(fk, f[1], tonumber(f[2])))
end
IC.MP_OPS.dismiss = function(fk, arg)          -- office
    return answer(fk, "dismiss", arg, IC.dismiss(fk, fields(arg)[1]))
end
IC.MP_OPS.gov = function(fk, arg)              -- province|cqi
    local f = fields(arg)
    return answer(fk, "gov", arg, IC.assign_governor(fk, f[1], tonumber(f[2])))
end
IC.MP_OPS.ungov = function(fk, arg)            -- province
    return answer(fk, "ungov", arg, IC.release_governor(fk, fields(arg)[1]))
end
IC.MP_OPS.plot = function(fk, arg)             -- plot|actor cqi|target
    local f = fields(arg)
    local target = f[3]
    if target == "" then target = nil end
    return answer(fk, "plot", arg, IC.plot(fk, f[1], tonumber(f[2]), target))
end
IC.MP_OPS.favour = function(fk, arg)           -- favour|party
    local f = fields(arg)
    return answer(fk, "favour", arg, IC.favour(fk, f[1], f[2]))
end
IC.MP_OPS.grant = function(fk, arg)
    return answer(fk, "grant", arg, IC.grant_demand(fk))
end
IC.MP_OPS.refuse = function(fk, arg)
    return answer(fk, "refuse", arg, IC.refuse_demand(fk))
end
IC.MP_OPS.accept = function(fk, arg)           -- party
    return answer(fk, "accept", arg, IC.accept_offer(fk, fields(arg)[1]))
end
IC.MP_OPS.decline = function(fk, arg)          -- party
    return answer(fk, "decline", arg, IC.decline_offer(fk, fields(arg)[1]))
end
IC.MP_OPS.arbit = function(fk, arg)            -- party|back, or party|peace
    local f = fields(arg)
    return answer(fk, "arbit", arg, IC.arbitrate(fk, f[1], f[2]))
end
IC.MP_OPS.fill = function(fk, arg)             -- nothing: the plan is re-read here
    local n = IC.fill_offices(fk)
    return answer(fk, "fill", arg, n > 0, n > 0 and nil or "no fill", n)
end
IC.MP_OPS.gov_accept = function(fk, arg)       -- nothing
    return answer(fk, "gov_accept", arg, IC.gov_accept(fk))
end
IC.MP_OPS.gov_hold = function(fk, arg)         -- nothing
    return answer(fk, "gov_hold", arg, IC.gov_hold(fk))
end
IC.MP_OPS.doctrine = function(fk, arg)         -- government slug
    return answer(fk, "doctrine", arg, IC.gov_force(fk, fields(arg)[1]))
end

-- THE LAWS. Every one is re-checked by the
-- model function it calls.
IC.MP_OPS.law_propose = function(fk, arg)      -- category|option
    local f = fields(arg)
    return answer(fk, "law_propose", arg, IC.law_propose(fk, f[1], f[2]))
end
IC.MP_OPS.law_stance = function(fk, arg)       -- category|aye|nay|abstain
    local f = fields(arg)
    return answer(fk, "law_stance", arg, IC.law_set_stance(fk, f[1], f[2]))
end
IC.MP_OPS.law_win = function(fk, arg)          -- category|cqi
    local f = fields(arg)
    return answer(fk, "law_win", arg, IC.law_win(fk, f[1], tonumber(f[2])))
end
IC.MP_OPS.law_push = function(fk, arg)         -- category|level
    local f = fields(arg)
    return answer(fk, "law_push", arg, IC.law_push(fk, f[1], tonumber(f[2])))
end
IC.MP_OPS.law_overrule = function(fk, arg)     -- category|1 pass, category|0 fail
    local f = fields(arg)
    return answer(fk, "law_overrule", arg, IC.law_overrule(fk, f[1], f[2] == "1"))
end

-- THE DEEDS' DISCRIMINATORS. Keys read out of CA's db: the guardhouse chain is
-- military and is not a temple, and recruiting captives (enslave_replenishment_only) is not taking slaves.
IC.TEMPLE_BUILDINGS = {
    wh3_dlc23_chd_tower_temple_of_hashut_1 = true,
    wh3_dlc23_special_great_temple_of_hashut_chd = true,
}
IC.ENSLAVE_RECORD = "wh3_dlc23_captive_option_enslave_chaos_dwarfs"
IC.ENSLAVE_OUTCOME = "enslave_slaves_only"

function IC.deed_of_ritual(category)
    category = tostring(category or "")
    -- NO PLAIN FLAG: in this game it corrupts the string library process-wide.
    if string.find(category, "HELLFORGE_CAPS") then return "hellforge" end
    if string.sub(category, 1, 10) == "DISTRICTS_" or category == "TOZ_TIER_4" then
        return "rite"
    end
    return nil
end

-- ONCE PER BATTLE: CharacterCompletedBattle fires for every character in it.
-- Keyed on the two commanders; a battle the interface cannot name scores.
IC.battles_seen, IC.battles_turn = {}, nil
function IC.battle_once(faction_key, battle)
    local now = cm:model():turn_number()
    if IC.battles_turn ~= now then IC.battles_seen, IC.battles_turn = {}, now end
    local a, d
    pcall(function()
        if battle:has_attacker() then a = battle:attacker():command_queue_index() end
        if battle:has_defender() then d = battle:defender():command_queue_index() end
    end)
    if not a and not d then return true end
    local key = faction_key .. ":" .. tostring(a) .. ":" .. tostring(d)
    if IC.battles_seen[key] then return false end
    IC.battles_seen[key] = true
    return true
end

function IC.register()
    -- THE MULTIPLAYER TRANSPORT'S RECEIVING END - see IC.mp_send. Registered and
    -- silent in single player, where nothing is ever broadcast.
    core:add_listener("ic_mp", "UITrigger", true, function(context)
        local ok, err = pcall(function()
            IC.mp_receive(context:trigger(), context:faction_cqi())
        end)
        if not ok then IC.warn("IRON COURT: UITrigger failed: " .. tostring(err)) end
    end, true)

    -- THE PLAYER PRESSED Finalize IN MCT: the live switches follow it now.
    core:add_listener("ic_live_tune", "MctFinalized", true, function()
        local ok, err = pcall(IC.refresh_live_tune)
        if not ok then IC.warn("IRON COURT: live settings failed: " .. tostring(err)) end
    end, true)

    core:add_listener("ic_turn", "FactionTurnStart", true, function(context)
        local faction = context:faction()
        if not IC.runs_court(faction) then
            -- A COURT OF A RACE THE SETTINGS SWITCHED OFF, still in the save.
            if IC.race_of(faction) then
                local packed = cm:get_saved_value("derpy_ic_" .. faction:name())
                if packed and packed ~= "" then IC.dismantle(faction:name()) end
            end
            return
        end
        IC.turn(faction:name())
    end, true)
    -- PEACE, TRADE OR AN ALLIANCE WITH A FACTION THE BOOK NAMES, from either
    -- side of the table.
    core:add_listener("ic_book_peace", "PositiveDiplomaticEvent", true, function(context)
        local ok, err = pcall(function()
            if not (context:is_peace_treaty() or context:is_trade_agreement()
                    or context:is_alliance() or context:is_military_alliance()
                    or context:is_defensive_alliance()) then
                return
            end
            local a, b = context:proposer(), context:recipient()
            for _, pair in ipairs({{a, b}, {b, a}}) do
                local own, them = pair[1], pair[2]
                if IC.runs_court(own) and IC.book_peace(own:name(), them:name()) then
                    IC.save(own:name())
                end
            end
        end)
        if not ok then IC.warn("IRON COURT: the Book failed on a treaty: " .. tostring(err)) end
    end, true)

    core:add_listener("ic_confed", "FactionJoinsConfederation", true, function(context)
        local host = context:confederation()
        local joined = context:faction()
        if not IC.runs_court(host) then return end
        -- CA RE-PERFORMS THE JOINER'S TOWER SEATS THIS TURN: no deed for them.
        IC.loaded(host:name())
        IC.court(host:name()).confed_turn = cm:model():turn_number()
        local slug = IC.origin_for_faction(joined:name())
        if not slug then return end
        local host_key = host:name()
        IC.loaded(host_key)
        local before = {}
        local own = host:character_list()
        for i = 0, own:num_items() - 1 do
            local man = own:item_at(i)
            if man and not man:is_null_interface() then
                before[man:command_queue_index()] = true
            end
        end
        -- READ BEFORE IT IS FORGOTTEN.
        local loyalty = IC.inherited_loyalty(host_key, joined:name())
        IC.forget_court(joined:name())
        IC.stamp_incoming(host_key, slug, 0, before, loyalty)
    end, true)


    core:add_listener("ic_born", "CharacterCreated", true, function(context)
        local character = context:character()
        if not character or character:is_null_interface() then return end
        local faction = character:faction()
        if not faction or faction:is_null_interface() then return end
        local faction_key = faction:name()
        if IC.runs_court(faction) then IC.loaded(faction_key) end
        IC.price_recruit(faction_key, character)
        if IC.has_court(faction) and IC.court_rolled(faction_key) then
            -- A STARTING LORD (IC.seed_step) is born to the party he was made
            -- for, quietly: dealt elsewhere and swapped, he would show a Trait
            -- Gained and a Trait Removed card each.
            local seeded = IC._seed_bg[faction_key]
            if seeded then
                IC._seed_bg[faction_key] = nil
                IC.stamp_origin(character, IC.origin_for(character, faction_key), true)
                IC.stamp_bg(character, seeded, true)
                return
            end
            -- A GARRISON CAPTAIN joins quietly: one is made at every capture,
            -- and each would show two Trait Gained entries.
            local quiet = IC.is_colonel(character)
            IC.stamp_origin(character, IC.origin_for(character, faction_key), quiet)
            IC.stamp_bg(character, IC.deed_join(character, faction_key)
                                   or IC.background_for(character, faction_key), quiet)
        end
    end, true)

    -- A MOMENT AFTER THE HIRE, so a rank the engine gives on recruitment is
    -- already on him and is not given twice.
    core:add_listener("ic_hired", "CharacterRecruited", true, function(context)
        local character = context:character()
        if not character or character:is_null_interface() then return end
        local faction = character:faction()
        if not faction or faction:is_null_interface() or not IC.runs_court(faction) then return end
        local faction_key, cqi = faction:name(), character:command_queue_index()
        IC.loaded(faction_key)
        cm:callback(function()
            local man = IC.character_by_cqi(faction_key, cqi)
            if man then IC.raise_hired(faction_key, man) end
        end, 0.5)
    end, true)

    core:add_listener("ic_battle", "CharacterCompletedBattle", true, function(context)
        local character = context:character()
        if not character or character:is_null_interface() then return end
        if not character:won_battle() then return end
        local faction = character:faction()
        if not faction or faction:is_null_interface() then return end
        if not IC.runs_court(faction) then return end
        local battle = context:pending_battle()
        if not battle or battle:is_null_interface() then return end
        local faction_key = faction:name()
        IC.loaded(faction_key)
        local worth = IC.tune(faction_key, "battle_influence")
        local result = battle:attacker_battle_result()
        if not worth[result] then
            result = battle:defender_battle_result()
        end
        local gain = worth[result]
        if not gain then return end
        IC.move_loyalty(faction_key,
                        IC.house_of_character(character, faction_key),
                        IC.tune(faction_key, "loyalty_battle_won"))
        IC.add_standing(faction_key, character:command_queue_index(), gain)
        if IC.battle_once(faction_key, battle) and IC.deed(faction_key, "battle") > 0 then
            IC.save(faction_key)
        end
    end, true)

    -- THE DEEDS. Each reads its faction and its deed,
    -- or nothing; a failure is said and drops nothing else.
    local function on_deed(name, event, read)
        core:add_listener(name, event, true, function(context)
            local ok, err = pcall(function()
                local faction, code = read(context)
                if not faction or faction:is_null_interface() or not code then return end
                if not IC.runs_court(faction) then return end
                local faction_key = faction:name()
                IC.loaded(faction_key)
                if IC.deed(faction_key, code) > 0 then IC.save(faction_key) end
            end)
            if not ok then IC.warn("IRON COURT: " .. name .. " failed: " .. tostring(err)) end
        end, true)
    end
    on_deed("ic_deed_ritual", "RitualCompletedEvent", function(context)
        local faction = context:performing_faction()
        if not IC.runs_court(faction) then return nil end
        IC.loaded(faction:name())
        local code = IC.deed_of_ritual(context:ritual():ritual_category())
        if code == "rite" and IC.court(faction:name()).confed_turn
                == cm:model():turn_number() then
            return nil
        end
        return faction, code
    end)
    on_deed("ic_deed_building", "BuildingCompleted", function(context)
        local building = context:building()
        local faction = building:faction()
        local fk = faction and not faction:is_null_interface() and faction:name() or nil
        return faction, IC.R(fk).TEMPLE_BUILDINGS[building:name()] and "temple" or nil
    end)
    on_deed("ic_deed_captives", "CharacterPostBattleCaptureOption", function(context)
        local yes = context:get_outcome_key() == IC.ENSLAVE_OUTCOME
                    or context:get_record_key() == IC.ENSLAVE_RECORD
        return context:character():faction(), yes and "slaves" or nil
    end)
    on_deed("ic_deed_raze", "CharacterRazedSettlement", function(context)
        return context:character():faction(), "raze"
    end)
    -- NOT ScriptEventCaravanCompleted too: CA re-raises this same context.
    on_deed("ic_deed_convoy", "CaravanCompleted", function(context)
        return context:faction(), "convoy"
    end)
    on_deed("ic_deed_research", "ResearchCompleted", function(context)
        return context:faction(), "research"
    end)
    -- A GRUDGE SETTLED: CA pays the faction's own
    -- grudge points when one is (wh3_campaign_grudges.lua grudges_pr_key). A
    -- rise only: a ritual spends them, and that is no deed. The key first,
    -- because this event fires for every pooled resource on the map. A Chaos
    -- Dwarf court has no grudge deed, so IC.deed answers 0 for one.
    on_deed("ic_deed_grudge", "PooledResourceChanged", function(context)
        if context:resource():key() ~= IC.GRUDGE_POINTS or context:amount() <= 0 then
            return nil
        end
        return context:faction(), "grudge"
    end)

    core:add_listener("ic_took", "GarrisonOccupiedEvent", true, function(context)
        local character = context:character()
        if not character or character:is_null_interface() then return end
        local faction = character:faction()
        if not faction or faction:is_null_interface() then return end
        if not IC.runs_court(faction) then return end
        IC.loaded(faction:name())
        IC.add_standing(faction:name(), character:command_queue_index(),
                        IC.TUNE.settlement_influence)
    end, true)

    core:add_listener("ic_rank", "CharacterRankUp", true, function(context)
        local character = context:character()
        if not character or character:is_null_interface() then return end
        local faction = character:faction()
        if not faction or faction:is_null_interface() then return end
        if not IC.runs_court(faction) then return end
        local gained = context:ranks_gained() or 1
        IC.loaded(faction:name())
        IC.add_standing(faction:name(), character:command_queue_index(),
                        gained * IC.tune(faction:name(), "rank_influence"))
    end, true)

    core:add_listener("ic_dead", "CharacterConvalescedOrKilled", true, function(context)
        local character = context:character()
        if not character or character:is_null_interface() then return end
        if character:is_alive() ~= false then return end
        local faction = character:faction()
        if not IC.runs_court(faction) then return end
        local faction_key = faction:name()
        IC.loaded(faction_key)
        local cqi = character:command_queue_index()
        local court = IC.court(faction_key)
        local arranged = IC.arranged_deaths[cqi]
        IC.arranged_deaths[cqi] = nil
        local seats, provinces = {}, {}
        for office_slug, holder in pairs(court.offices) do
            if holder == cqi then
                local slug = IC.house_of_character(character, faction_key)
                seats[#seats + 1] = office_slug
                court.offices[office_slug] = nil
                -- AND ITS TERM: expire_terms walks held offices only, so a
                -- dead man's term was never cleared out of the save.
                court.terms[office_slug] = nil
                if slug and court.houses[slug] then
                    court.houses[slug].weight = math.max(1,
                        court.houses[slug].weight
                        - IC.office_weight(office_slug, slug, faction_key))
                end
            end
        end
        for province_key, holder in pairs(court.govs) do
            if holder == cqi then
                provinces[#provinces + 1] = province_key
                court.govs[province_key] = nil
            end
        end
        -- A DEATH IN BATTLE OR OF OLD AGE empties his posts, and is said: one
        -- card, and a line in the record per post.
        if not arranged and (#seats > 0 or #provinces > 0) then
            local slug = IC.house_of_character(character, faction_key)
            for i = 1, #seats do IC.log(faction_key, "died", slug, seats[i], 0) end
            for i = 1, #provinces do
                IC.log(faction_key, "died", slug, provinces[i], 1)
            end
            IC.feed(faction_key, "officer_died",
                    #seats == 1 and IC.office_title_key(seats[1], faction_key) or nil)
        end
        -- A MAN WHO LEFT is nobody's loss: his party is gone, and asked now
        -- house_of_character would answer the Crown.
        if arranged ~= "left" then
            IC.move_loyalty(faction_key,
                            IC.house_of_character(character, faction_key),
                            IC.TUNE.loyalty_member_died)
        end
        for slug2, house2 in pairs(court.houses) do
            if house2.oath_mine == cqi or house2.oath_theirs == cqi then
                house2.oath_mine, house2.oath_theirs = nil, nil
                IC.log(faction_key, "oath_broken", slug2, "died", 0)
            end
        end
        IC.apply_office_bundles(faction_key)
        -- AND HIS PROVINCES' BONUS AND WEIGHT, now and not at the turn start.
        if #provinces > 0 then IC.apply_governor_bundles(faction_key) end
        IC.save(faction_key)
    end, true)
end

-- THE RACES. A court reads its tables off its faction's race,
-- R = IC.R(faction_key), never off IC.X. The Chaos Dwarf race IS the IC.X
-- tables above (the same tables, not copies), so every scraper and harness
-- reference to them still holds. The race is never saved: it is the faction's
-- subculture.
--
-- WHAT A PARTY OFFERS THE CROWN (the offers are in the parties file). Defined
-- here, not there: the Chaos Dwarf race registers below, before that file loads,
-- and registration refuses a race missing a field.
IC.PARTY_TROOPS = {
    temple = "wh3_dlc23_chd_inf_infernal_guard_fireglaives",
    forge  = "wh3_dlc23_chd_inf_chaos_dwarf_blunderbusses",
    chain  = "wh3_dlc23_chd_inf_hobgoblin_cutthroats",
    legion = "wh3_dlc23_chd_inf_infernal_guard",
    ledger = "wh3_dlc23_chd_inf_chaos_dwarf_warriors",
    tower  = "wh3_dlc23_chd_inf_chaos_dwarf_warriors_great_weapons",
    road   = "wh3_dlc23_chd_cav_hobgoblin_wolf_raiders_bows",
    hearth = "wh3_dlc23_chd_inf_chaos_dwarf_warriors",
}
-- A confederated house's slug is not one of the eight.
IC.TROOPS_DEFAULT = "wh3_dlc23_chd_inf_chaos_dwarf_warriors"

IC.RACE_FIELDS = {
    "ORIGINS", "PARTIES", "OFFICES", "GOVS", "GOV_ORDER", "START_GOV", "LAWS",
    "LAW_ORDER", "DEEDS", "REBEL_POOL", "REBEL_POOLS", "REBEL_GENERALS",
    "REBEL_HEROES", "REBEL_DRAFT", "BACKGROUNDS", "NAME_HEADS", "NAME_TAILS",
    "PARTY_TRAITS", "LEADER_TRAITS", "LEGEND_SUBTYPES", "TEMPLE_BUILDINGS",
    "MILITARY_DOCTRINE", "PARTY_TROOPS", "TROOPS_DEFAULT",
}
IC.RACES = {}
IC.RACE_ORDER = {}
IC._race_cache = {}

-- TIERS, TIER_SEATS, PARTY_OF_BG and MAX_SEATS, off the race's own offices,
-- parties, backgrounds and origins.
function IC.build_race(r)
    r.TIERS, r.TIER_SEATS = {}, {}
    for i = 1, #r.OFFICES do
        local t = r.OFFICES[i].tier
        if not r.TIER_SEATS[t] then r.TIERS[#r.TIERS + 1] = t end
        r.TIER_SEATS[t] = (r.TIER_SEATS[t] or 0) + 1
    end
    r.PARTY_OF_BG = {}
    for i = 1, #r.PARTIES do
        local list = r.BACKGROUNDS[r.PARTIES[i]]
        for j = 1, #list do r.PARTY_OF_BG[list[j]] = r.PARTIES[i] end
    end
    r.MAX_SEATS = #r.PARTIES
    for i = 1, #r.ORIGINS do
        if r.ORIGINS[i].faction then r.MAX_SEATS = r.MAX_SEATS + 1 end
    end
    return r
end

function IC.register_race(r)
    -- A RACE MISSING A FIELD is refused here, loudly: left in, the first court of
    -- it to read the field would fail silently, mid-campaign. switch, layout, grid
    -- and art are optional.
    for _, f in ipairs({"key", "subculture", "infix", "tune"}) do
        if r[f] == nil then error("IC.register_race: race is missing field " .. f, 2) end
    end
    for _, f in ipairs(IC.RACE_FIELDS) do
        if r[f] == nil then
            error("IC.register_race: race " .. tostring(r.key) .. " is missing field " .. f, 2)
        end
    end
    IC.build_race(r)
    if not IC.RACES[r.key] then IC.RACE_ORDER[#IC.RACE_ORDER + 1] = r.key end
    IC.RACES[r.key] = r
    -- SIZED FOR THE LARGEST RACE: the panel makes its dial's seats once, at load,
    -- so every race registers before the panel file loads.
    IC.MAX_SEATS = math.max(IC.MAX_SEATS or 0, r.MAX_SEATS)
    return r
end

function IC.race_of(faction)
    if not faction or faction:is_null_interface() then return nil end
    local sc = faction:subculture()
    for _, k in ipairs(IC.RACE_ORDER) do
        if IC.RACES[k].subculture == sc then return IC.RACES[k] end
    end
    return nil
end

function IC.race_key(faction_key)
    if not faction_key then return nil end
    local ok, r = pcall(function() return IC.race_of(real_faction(faction_key)) end)
    return ok and r and r.key or nil
end

-- KEYS: "derpy_ic_" .. kind .. "_" .. the race's infix .. slug. The Chaos
-- Dwarfs' infix is "", so every key they had is the key they have.
function IC.rkey(kind, slug, R)
    return "derpy_ic_" .. kind .. "_" .. (R or IC.RACES.chd).infix .. slug
end

function IC.key(kind, slug, faction_key)
    return IC.rkey(kind, slug, IC.R(faction_key))
end

-- A TRAIT FROM A SLUG ALONE, for the stampers that hold no faction. Origin and
-- background slugs are unique across races, so the slug names its race.
function IC.origin_trait(slug)
    for _, k in ipairs(IC.RACE_ORDER) do
        local R = IC.RACES[k]
        for i = 1, #R.ORIGINS do
            if R.ORIGINS[i].slug == slug then return IC.rkey("house", slug, R) end
        end
    end
    return IC.rkey("house", slug, IC.RACES.chd)
end

function IC.bg_trait(slug)
    for _, k in ipairs(IC.RACE_ORDER) do
        if IC.RACES[k].PARTY_OF_BG[slug] then return IC.rkey("bg", slug, IC.RACES[k]) end
    end
    return IC.rkey("bg", slug, IC.RACES.chd)
end

function IC.R(faction_key)
    if not faction_key then return IC.RACES.chd end
    local k = IC._race_cache[faction_key] or IC.race_key(faction_key)
    -- ONLY A FOUND RACE IS KEPT: before the world exists cm:get_faction fails,
    -- and a court that cached the fallback then would run on it all session.
    if k then IC._race_cache[faction_key] = k end
    return IC.RACES[k or "chd"]
end

-- A FACTION WHOSE RACE HOLDS A COURT, with that race switched on. `switch`
-- names an IC.TUNE switch; the Chaos Dwarfs have none and always hold one.
function IC.race_on(r)
    return r.switch == nil or IC.TUNE[r.switch] ~= false
end

function IC.has_court(faction)
    local r = IC.race_of(faction)
    return r ~= nil and IC.race_on(r)
end

do
    local chd = {key = "chd", subculture = IC.CHD_SUBCULTURE, infix = "",
                 tune = {}, layout = "ziggurat", art = {}}
    for _, k in ipairs(IC.RACE_FIELDS) do chd[k] = IC[k] end
    IC.register_race(chd)
    -- THE OLD NAMES, still the Chaos Dwarf race's own: the harness and the
    -- importer's Lua stubs read them, and the ziggurat grid is theirs alone.
    for _, k in ipairs({"TIERS", "TIER_SEATS", "PARTY_OF_BG"}) do IC[k] = chd[k] end
end

-- THE MODEL'S FIRST TICK, named so the harness can drive it: the harness's cm
-- keeps only the last first-tick callback added, which is the panel's.
function IC.first_tick()
    -- FIRST: a new campaign rolls the player's court below, on these numbers.
    IC.freeze_tune()
    IC.register()
    IC.rebel_rename_all()
    local human = cm:get_human_factions()
    for i = 1, #human do
        local faction = real_faction(human[i])
        if IC.has_court(faction) then
            local court = IC.load(human[i])
            local empty = true
            for _ in pairs(court.houses) do empty = false break end
            if empty then
                IC.seed(human[i])
            else
                IC.ensure_own_house(human[i])
            end
            IC.stamp_court(human[i])
            IC.reconcile_houses(human[i])
            IC.ensure_leaders(human[i])
            IC.seed_members(human[i])
        end
    end
end

cm:add_first_tick_callback(function() IC.first_tick() end)
