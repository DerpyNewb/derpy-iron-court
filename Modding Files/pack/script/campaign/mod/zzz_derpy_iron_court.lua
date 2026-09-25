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

IC.MAX_SEATS = #IC.PARTIES
for i = 1, #IC.ORIGINS do
    if IC.ORIGINS[i].faction then IC.MAX_SEATS = IC.MAX_SEATS + 1 end
end

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
    return IC.rebel_faction()
end

function IC.rebel_rename(rebels, name)
    if not rebels or not name or name == "" then return false end
    pcall(function() cm:change_custom_faction_name(rebels, name) end)
    cm:set_saved_value("derpy_ic_risen_" .. rebels, name)
    return true
end

function IC.rebel_rename_all()
    local keys = {}
    for i = 1, #IC.REBEL_POOL do keys[#keys + 1] = IC.REBEL_POOL[i] end
    for i = 1, #IC.ORIGINS do
        if IC.ORIGINS[i].faction then keys[#keys + 1] = IC.ORIGINS[i].faction end
    end
    for i = 1, #keys do
        local name = cm:get_saved_value("derpy_ic_risen_" .. keys[i])
        if name and name ~= "" then
            pcall(function() cm:change_custom_faction_name(keys[i], name) end)
        end
    end
end

function IC.rebel_faction()
    local fallback = nil
    for i = 1, #IC.REBEL_POOL do
        local key = IC.REBEL_POOL[i]
        local ok, f = pcall(function() return cm:get_faction(key) end)
        if ok and f and f ~= false then
            fallback = fallback or key
            local dead = false
            pcall(function() dead = f:is_dead() end)
            if dead then return key, true end
        end
    end
    return fallback, false
end

IC.REBEL_LORD = "wh3_dlc23_chd_overseer"

IC.REBEL_GENERALS = {
    ["wh3_dlc23_chd_lord_convoy_overseer"] = true,
    ["wh3_dlc23_chd_overseer"] = true,
    ["wh3_dlc23_chd_overseer_hobgoblin_spawned_army"] = true,
    ["wh3_dlc23_chd_sorcerer_prophet_death"] = true,
    ["wh3_dlc23_chd_sorcerer_prophet_fire"] = true,
    ["wh3_dlc23_chd_sorcerer_prophet_hashut"] = true,
    ["wh3_dlc23_chd_sorcerer_prophet_metal"] = true,
}
IC.REBEL_ROSTER = {
    "wh3_dlc23_chd_inf_infernal_ironsworn",
    "wh3_dlc23_chd_inf_infernal_guard",
    "wh3_dlc23_chd_inf_infernal_guard_great_weapons",
    "wh3_dlc23_chd_inf_chaos_dwarf_warriors_great_weapons",
    "wh3_dlc23_chd_inf_chaos_dwarf_warriors",
    "wh3_dlc23_chd_inf_hobgoblin_cutthroats",
    "wh3_dlc23_chd_inf_hobgoblin_sneaky_gits",
    "wh3_dlc23_chd_inf_infernal_guard_fireglaives",
    "wh3_dlc23_chd_inf_chaos_dwarf_blunderbusses",
    "wh3_dlc23_chd_inf_hobgoblin_archers",
    "wh3_dlc23_chd_cav_bull_centaurs_greatweapons",
    "wh3_dlc23_chd_cav_bull_centaurs_axe",
    "wh3_dlc23_chd_cav_hobgoblin_wolf_raiders_spears",
    "wh3_dlc23_chd_mon_kdaai_fireborn",
    "wh3_dlc23_chd_mon_great_taurus",
    "wh3_dlc23_chd_veh_iron_daemon",
    "wh3_dlc23_chd_veh_deathshrieker_rocket_launcher",
    "wh3_dlc23_chd_veh_magma_cannon",
    "wh3_main_chd_art_hobgob_bolt_thrower",
}

-- CA's `out` is a callable table, not a function. Keep the call isolated from turns.
function IC.say(text)
    if out then pcall(function() out(tostring(text)) end) end
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
     blurb = "Each office sharpens their appetite for the next.",
     rule = "Nothing at no seat, -1 at one, -2 at two or more",
     n = function(ctx) return -math.min(ctx.held, 2) end},
    {key = "dutiful", name = "Dutiful",
     blurb = "They serve where ordered and ask for little.",
     rule = "+2 with no seat, +1 with one",
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
     blurb = "He wants the Tower, and makes no secret of it."},
    {key = "schemer", name = "Schemer",
     blurb = "Every promise hides another bargain."},
    {key = "brute", name = "Brute",
     blurb = "He settles disputes with threats and iron."},
    {key = "steady", name = "Steady",
     blurb = "Threats do not move him. Flattery fares no better."},
    {key = "shrewd", name = "Shrewd",
     blurb = "He sees which bargains will pay before others do."},
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

IC.TIER_SEATS = {}
IC.TIERS = {}
for i = 1, #IC.OFFICES do
    local t = IC.OFFICES[i].tier
    if not IC.TIER_SEATS[t] then IC.TIERS[#IC.TIERS + 1] = t end
    IC.TIER_SEATS[t] = (IC.TIER_SEATS[t] or 0) + 1
end

IC.CHD_SUBCULTURE = "wh3_dlc23_sc_chd_chaos_dwarfs"
IC.MILITARY_DOCTRINE = "wh3_dlc23_edict_chd_armaments"

IC.TUNE = {
    tier_rank           = {30, 20, 12, 5},


    tier_influence      = {400, 300, 200, 100},
    tier_income         = {20, 15, 10, 5},
    governor_income     = 5,
    -- Raised 2026-09-23 (author): a turn-32 save had 2 of 14 seats filled and
    -- 12 of 24 men at 0 influence. Bars unchanged; they are the player's only.
    influence_trickle   = 5,
    influence_trickle_general = 0,
    term_turns          = 5,
    hire_standing       = 100,

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
    favour_secure_cost   = 2500,
    favour_secure_turns  = 5,

    party_trait_scale   = 1,

    weight_start        = 10,   -- a house entering court
    weight_per_office   = 6,
    weight_per_governor = 3,
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


    pressure_below      = IC.CONTROL[#IC.CONTROL - 1].floor,
    pressure_per_point  = 8,    -- chance, in percent, per point below
    pressure_max        = 60,   -- and no higher, ever

    secede_share        = 25,   -- share >= this AND
    secede_loyalty      = 20,   -- loyalty <= this starts the clock
    secede_break        = 0,
    secede_turns        = 5,
    sufferance_share    = 20,   -- the player's own party below this

    rivals_min          = 2,
    rivals_max          = 4,

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
    loyalty_warn        = 35,
    warn_turns          = 3,
    splinter_loyalty    = 25,
    splinter_weight     = 5,
}

IC.AMBITION_ORDER = {"cautious", "steady", "ambitious"}
IC.AMBITION = {
    cautious  = {factor = 75,  roll = 25,
                 trait = "derpy_ic_ambition_cautious"},
    steady    = {factor = 100, roll = 50,
                 trait = "derpy_ic_ambition_steady"},
    ambitious = {factor = 125, roll = 25,
                 trait = "derpy_ic_ambition_ambitious"},
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
        prov     = {},   -- [province key] = loyalty, 0-100
        standing = {},   -- [character cqi] = influence he holds
        ambition = {},   -- [character cqi] = ambition slug
        log      = {},
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
    unseat = true, recall = true, patron = true, kinsman = true,
    pledge = true, audience = true, circuit = true,
    splinter = true,
    pressed = true, dissolve = true,
    party_warn = true, party_dropped = true, party_unseat = true,
    party_recall = true, feud = true, feud_end = true,
    demand = true, demand_met = true, demand_refused = true, demand_void = true,
    offer = true, offer_taken = true,
}

function IC.log(faction_key, kind, slug, key, n)
    if not IC.LOG_KINDS[kind] then return false end
    local court = IC.court(faction_key)
    court.log = court.log or {}
    court.log[#court.log + 1] = {
        turn = cm:model():turn_number(),
        kind = kind, slug = slug, key = key, n = n,
    }
    while #court.log > IC.LOG_MAX do table.remove(court.log, 1) end
    return true
end

IC.EVENTS = {
    plot_ok      = {2600, true, true},
    plot_fail    = {2601, true, true},
    -- False means the office bundle's title key names the seat.
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
}

IC.feed_queue = {}
IC.feed_held = false
-- Bound the deferred feed so a stuck hold cannot release hundreds of cards at once.
IC.FEED_QUEUE_MAX = 10

function IC.hold_feed(on)
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
    -- Hold cards raised behind the open panel until the player can see them.
    if IC.feed_held then
        if #IC.feed_queue < IC.FEED_QUEUE_MAX then
            IC.feed_queue[#IC.feed_queue + 1] = {faction_key, slug, secondary}
        end
        return true
    end
    return IC.raise_feed(faction_key, slug, secondary)
end

function IC.raise_feed(faction_key, slug, secondary)
    local ev = IC.EVENTS[slug]
    if not ev then return false end
    local key = "derpy_ic_event_" .. slug
    local fallback = ev[3]
                     and ("event_feed_strings_text_" .. key .. "_secondary")
                     or ""
    pcall(function()
        cm:show_message_event(
            faction_key,
            "event_feed_strings_text_" .. key .. "_title",
            "event_feed_strings_text_" .. key .. "_primary",
            secondary or fallback,
            ev[2], ev[1])
    end)
    return true
end

function IC.move_result_key(plot_key, ok)
    if not plot_key then return nil end
    return "event_feed_strings_text_derpy_ic_move_" .. plot_key
           .. (ok and "_ok" or "_fail")
end

function IC.office_title_key(office_slug)
    return "effect_bundles_localised_title_" .. IC.office_bundle(office_slug)
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
    return house.weight + (house.gov_weight or 0)
        + IC.member_weight(faction_key, slug)
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

function IC.house_in_court(court, slug)
    return court.houses[slug] ~= nil
end

function IC.house_icon(slug, faction_key)
    if not slug then return nil end
    local sigil = nil
    for i = 1, #IC.PARTIES do
        if IC.PARTIES[i] == slug then
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
    for i = 1, #IC.ORIGINS do
        if IC.ORIGINS[i].slug == slug then return IC.ORIGINS[i].faction end
    end
    return nil
end

function IC.origin_for_faction(faction_key)
    for i = 1, #IC.ORIGINS do
        if IC.ORIGINS[i].faction == faction_key then return IC.ORIGINS[i].slug end
    end
    return nil
end

function IC.party_faction(faction_key, slug)
    if not faction_key or not slug then return nil end
    local house = IC.court(faction_key).houses[slug]
    if not house or not house.confed then return nil end
    return IC.faction_for_origin(slug)
end

function IC.office_by_slug(slug)
    for i = 1, #IC.OFFICES do
        if IC.OFFICES[i].slug == slug then return IC.OFFICES[i] end
    end
    return nil
end

local function join(parts, sep) return table.concat(parts, sep) end

function IC.pack(faction_key)
    local court = IC.court(faction_key)
    local houses, offices, govs, terms = {}, {}, {}, {}
    for slug, h in pairs(court.houses) do
        houses[#houses + 1] = string.format(
            "%s,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d",
            slug, h.weight, h.loyalty, h.clock or 0, h.head or 0, h.tail or 0,
            h.confed and 1 or 0, h.pressed and 1 or 0, h.protected or 0,
            h.t1 or 0, h.t2 or 0,
            h.oath_mine or 0, h.oath_theirs or 0,
            h.snubbed and 1 or 0,
            h.split or 0,
            h.stored and 1 or 0)
    end
    for slug, cqi in pairs(court.offices) do
        offices[#offices + 1] = slug .. "," .. tostring(cqi)
    end
    for province, cqi in pairs(court.govs) do
        govs[#govs + 1] = province .. "," .. tostring(cqi)
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
        logged[#logged + 1] = string.format("%d,%s,%s,%s,%s",
            e.turn or 0, e.kind or "-", e.slug or "-", e.key or "-",
            tostring(e.n or 0))
    end
    local prov, ambition = {}, {}
    for province, n in pairs(court.prov or {}) do
        prov[#prov + 1] = province .. "," .. tostring(n)
    end
    for cqi, slug in pairs(court.ambition or {}) do
        if IC.AMBITION[slug or ""] then
            ambition[#ambition + 1] = tostring(cqi) .. "," .. slug
        end
    end
    return join({join(houses, ";"), join(offices, ";"), join(govs, ";"),
                 join(terms, ";"), join(standing, ";"),
                 join(logged, ";"), join(prov, ";"), join(ambition, ";")}, "|")
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
        if #bits >= 2 then court.govs[bits[1]] = tonumber(bits[2]) end
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
    IC.state[faction_key] = court
    return court
end

function IC.save(faction_key)
    cm:set_saved_value("derpy_ic_" .. faction_key, IC.pack(faction_key))
end

function IC.load(faction_key)
    local packed = cm:get_saved_value("derpy_ic_" .. faction_key)
    if packed and packed ~= "" then IC.unpack(faction_key, packed) end
    return IC.court(faction_key)
end

local function real_faction(faction_key)
    local faction = cm:get_faction(faction_key)
    if not faction then return nil end
    if faction:is_null_interface() then return nil end
    return faction
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
    if not faction or faction:is_null_interface() then return false end
    return faction:subculture() == IC.CHD_SUBCULTURE
end

function IC.present_houses(faction_key)
    local court = IC.court(faction_key)
    local out = {}
    for i = 1, #IC.PARTIES do
        if court.houses[IC.PARTIES[i]] then out[#out + 1] = IC.PARTIES[i] end
    end
    for i = 1, #IC.ORIGINS do
        local slug = IC.ORIGINS[i].slug
        if IC.ORIGINS[i].faction and court.houses[slug]
           and court.houses[slug].confed then
            out[#out + 1] = slug
        end
    end
    return out
end

function IC.is_party(slug)
    for i = 1, #IC.PARTIES do
        if IC.PARTIES[i] == slug then return true end
    end
    return false
end

function IC.court_rolled(faction_key)
    local court = IC.court(faction_key)
    local n = 0
    for slug in pairs(court.houses) do
        if IC.is_party(slug) then n = n + 1 end
    end
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
    court.houses[slug] = nil
    for office_slug, cqi in pairs(court.offices) do
        if IC.house_of_cqi(faction_key, cqi) == slug then
            court.offices[office_slug] = nil
        end
    end
    for province, cqi in pairs(court.govs) do
        if IC.house_of_cqi(faction_key, cqi) == slug then
            court.govs[province] = nil
        end
    end
    IC.save(faction_key)
    return true
end

function IC.origin_of_character(character)
    if not character or character:is_null_interface() then return nil end
    for i = 1, #IC.ORIGINS do
        local slug = IC.ORIGINS[i].slug
        if character:has_trait("derpy_ic_house_" .. slug) then return slug end
    end
    return nil
end

function IC.bg_of_character(character)
    if not character or character:is_null_interface() then return nil end
    for i = 1, #IC.PARTIES do
        local list = IC.BACKGROUNDS[IC.PARTIES[i]]
        for j = 1, #list do
            if character:has_trait("derpy_ic_bg_" .. list[j]) then
                return list[j]
            end
        end
    end
    return nil
end

IC.PARTY_OF_BG = {}
for i = 1, #IC.PARTIES do
    local list = IC.BACKGROUNDS[IC.PARTIES[i]]
    for j = 1, #list do IC.PARTY_OF_BG[list[j]] = IC.PARTIES[i] end
end

function IC.house_of_character(character, faction_key)
    if IC.is_legend(character) then return IC.CROWN end
    local origin = IC.origin_of_character(character)
    if origin and faction_key then
        local came_from = IC.faction_for_origin(origin)
        if came_from and came_from ~= faction_key
           and IC.court(faction_key).houses[origin] then
            return origin
        end
    end
    local bg = IC.bg_of_character(character)
    if not bg then return nil end
    local party = IC.PARTY_OF_BG[bg]
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

function IC.roll_background(faction_key)
    local seated = IC.present_houses(faction_key)
    local pool = {}
    for i = 1, #seated do
        if IC.BACKGROUNDS[seated[i]] then pool[#pool + 1] = seated[i] end
    end
    if #pool == 0 then pool = {IC.CROWN} end
    local party = pool[cm:random_number(#pool, 1)]
    local list = IC.BACKGROUNDS[party]
    if not list or #list == 0 then return nil end
    return list[cm:random_number(#list, 1)]
end

function IC.fixed_history(character)
    if not character or character:is_null_interface() then return nil end
    local ok, key = pcall(function() return character:character_subtype_key() end)
    if not ok or not key then return nil end
    return IC.LORD_HISTORY[key]
end

function IC.origin_for(character)
    local fixed = IC.fixed_history(character)
    if fixed and fixed.origin then return fixed.origin end
    return IC.roll_origin()
end

function IC.background_for(character, faction_key)
    local fixed = IC.fixed_history(character)
    if fixed and fixed.bg then return fixed.bg end
    -- Already stamped: stamp_bg would refuse anyway, and the leader test below
    -- walks the whole court.
    if IC.bg_of_character(character) then return nil end
    local led = IC.leaderless_bg(character, faction_key)
    if led then return led end
    return IC.roll_background(faction_key)
end

-- A PARTY ALWAYS HAS A LEADER (author, 2026-09-23). A lord who could speak for a
-- house goes to one that has nobody to speak for it before anywhere else; a
-- dealt-evenly background left most rivals leaderless at campaign start.
function IC.leaderless_bg(character, faction_key)
    if not faction_key or not IC.is_lordly(character) or IC.is_legend(character) then
        return nil
    end
    local key
    pcall(function() key = character:character_subtype_key() end)
    if key and IC.NOT_DWARF[key] then return nil end
    local pool = {}
    local seated = IC.present_houses(faction_key)
    for i = 1, #seated do
        local slug = seated[i]
        if slug ~= IC.CROWN and IC.BACKGROUNDS[slug]
                and not IC.party_leader(faction_key, slug) then
            pool[#pool + 1] = slug
        end
    end
    if #pool == 0 then return nil end
    local list = IC.BACKGROUNDS[pool[cm:random_number(#pool, 1)]]
    return list[cm:random_number(#list, 1)]
end

-- The generic Chaos Dwarf lords a party may be given, per the author "any lord
-- type". IC.REBEL_GENERALS minus its convoy and hobgoblin-army variants.
IC.STORE_LORDS = {
    "wh3_dlc23_chd_overseer",
    "wh3_dlc23_chd_sorcerer_prophet_death",
    "wh3_dlc23_chd_sorcerer_prophet_fire",
    "wh3_dlc23_chd_sorcerer_prophet_hashut",
    "wh3_dlc23_chd_sorcerer_prophet_metal",
}

-- The Crown lord a leaderless party may take: a lord of any type who holds no
-- office or province, is not the faction leader, not a legend (always the
-- Crown's whatever his trade) and has no fixed history (correct_history would
-- put him back). A lord before a garrison commander (the author's last resort),
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

-- A PARTY ALWAYS HAS A LEADER. First an idle Crown lord moves over - the
-- author's "repair on load", which is what makes an existing save's leaderless
-- parties led at once. Where there is none, a lord is made in the recruitment
-- pool already carrying the party's background, and leads it once recruited.
-- A freshly pooled lord is not in character_list, so `stored` is what stops one
-- being made every turn; it clears as soon as the party has a leader.
-- ponytail: one stored lord per party at a time; one left unrecruited when the
-- party finds a leader elsewhere stays in the pool.
function IC.ensure_leaders(faction_key)
    local court = IC.court(faction_key)
    local made = 0
    -- Men already moved this pass, in case the engine answers has_trait late.
    local taken = {}
    for slug, house in pairs(court.houses) do
        if slug ~= IC.CROWN and IC.BACKGROUNDS[slug] then
            local led = IC.party_leader(faction_key, slug)
            local man = not led and IC.idle_crown_lord(faction_key, taken)
            if led then
                house.stored = nil
            elseif man then
                local list = IC.BACKGROUNDS[slug]
                local lookup = cm:char_lookup_str(man)
                local old = IC.bg_of_character(man)
                if old then cm:force_remove_trait(lookup, "derpy_ic_bg_" .. old) end
                cm:force_add_trait(lookup, "derpy_ic_bg_" .. list[cm:random_number(#list, 1)], false)
                taken[man:command_queue_index()] = true
                house.stored = nil
                IC.say("IRON COURT: " .. slug .. " in " .. faction_key .. " had no leader - "
                       .. "cqi " .. man:command_queue_index() .. " moved over from the Crown")
            elseif not house.stored then
                local subtype = IC.STORE_LORDS[cm:random_number(#IC.STORE_LORDS, 1)]
                local list = IC.BACKGROUNDS[slug]
                local bg = list[cm:random_number(#list, 1)]
                local ok, err = pcall(function()
                    local details = cm:spawn_character_to_pool(faction_key, "", "", "",
                        "", 30, true, "general", subtype, false, "")
                    cm:force_add_trait_to_character_details(details, "derpy_ic_bg_" .. bg)
                end)
                -- Marked even on a failure: a call that fails once fails every
                -- turn, and one log line per party is enough to see it.
                house.stored = true
                if ok then made = made + 1 end
                IC.say("IRON COURT: " .. tostring(slug) .. " in " .. faction_key
                       .. " has no leader - " .. (ok and ("a " .. subtype
                       .. " waits in the lord pool") or ("no lord made: " .. tostring(err))))
            end
        end
    end
    IC.save(faction_key)
    return made
end

function IC.correct_history(character)
    local want = IC.fixed_history(character)
    if not want then return false end
    if not character or character:is_null_interface() then return false end
    local lookup = cm:char_lookup_str(character)
    local moved = false

    local has = IC.origin_of_character(character)
    if want.origin and has ~= want.origin then
        if has then
            cm:force_remove_trait(lookup, "derpy_ic_house_" .. has)
        end
        cm:force_add_trait(lookup, "derpy_ic_house_" .. want.origin, false)
        moved = true
    end

    local trade = IC.bg_of_character(character)
    if want.bg and trade ~= want.bg then
        if trade then
            cm:force_remove_trait(lookup, "derpy_ic_bg_" .. trade)
        end
        cm:force_add_trait(lookup, "derpy_ic_bg_" .. want.bg, false)
        moved = true
    end
    return moved
end

function IC.roll_origin()
    local places = {}
    for i = 1, #IC.ORIGINS do
        if not IC.ORIGINS[i].faction then
            places[#places + 1] = IC.ORIGINS[i].slug
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
    for i = 0, list:num_items() - 1 do
        local character = list:item_at(i)
        if character and not character:is_null_interface() then
            if IC.correct_history(character) then
                stamped = stamped + 1
            end
            -- Use the fixed-history readers so legendary lords are never rerolled.
            if IC.stamp_origin(character, IC.origin_for(character)) then
                stamped = stamped + 1
            end
            if IC.stamp_bg(character,
                           IC.background_for(character, faction_key)) then
                stamped = stamped + 1
            end
            if IC.stamp_ambition(faction_key, character) then
                stamped = stamped + 1
            end
        end
    end
    return stamped
end

function IC.stamp_origin(character, slug)
    if not slug then return false end
    if not character or character:is_null_interface() then return false end
    if IC.origin_of_character(character) then return false end
    cm:force_add_trait(cm:char_lookup_str(character),
                       "derpy_ic_house_" .. slug, true)
    return true
end

function IC.stamp_bg(character, slug)
    if not slug then return false end
    if not character or character:is_null_interface() then return false end
    if IC.bg_of_character(character) then return false end
    cm:force_add_trait(cm:char_lookup_str(character),
                       "derpy_ic_bg_" .. slug, true)
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
    local want = IC.AMBITION[slug].trait
    local lookup = cm:char_lookup_str(character)
    for i = 1, #IC.AMBITION_ORDER do
        local key = IC.AMBITION[IC.AMBITION_ORDER[i]].trait
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

function IC.office_bundle(slug)   return "derpy_ic_office_" .. slug end
function IC.vacancy_bundle(slug)  return "derpy_ic_vacant_" .. slug end
function IC.office_trait(slug)    return "derpy_ic_title_" .. slug end

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
    local has = IC.standing(faction_key, cqi)
    for i = 1, #IC.TIERS do
        if has >= IC.tier_influence(IC.TIERS[i]) then return IC.TIERS[i] end
    end
    return 0
end

function IC.standing_trait(tier)  return "derpy_ic_standing_" .. tier end

function IC.stamp_standing(faction_key, character)
    if not character or character:is_null_interface() then return false end
    local want = IC.standing_trait(
        IC.standing_tier(faction_key, character:command_queue_index()))
    if character:has_trait(want) then return false end
    local lookup = cm:char_lookup_str(character)
    for i = 0, #IC.TIERS do
        local key = IC.standing_trait(i)
        if key ~= want and character:has_trait(key) then
            cm:force_remove_trait(lookup, key)
        end
    end
    cm:force_add_trait(lookup, want, false)
    return true
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

function IC.office_influence(office_slug)
    local office = IC.office_by_slug(office_slug)
    if not office then return 0 end
    return IC.tier_influence(office.tier)
end

function IC.office_rank(office_slug)
    local office = IC.office_by_slug(office_slug)
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

IC.HIRE = {
    {subtype = "wh3_dlc23_chd_infernal_castellan",
     agent = "engineer", name = "Infernal Castellan"},
    {subtype = "wh3_dlc23_chd_bull_centaur_taurruk",
     agent = "champion", name = "Bull Centaur Taurruk"},
    {subtype = "wh3_dlc23_chd_daemonsmith_sorcerer_hashut",
     agent = "wizard", name = "Daemonsmith Sorcerer"},
}

IC.hiring = {}

function IC.hire_cost()
    return IC.TUNE.hire_standing
end

function IC.hire_settlement(faction)
    if not faction or faction:is_null_interface() then return nil end
    local home = faction:home_region()
    if home and not home:is_null_interface() then
        local at = home:settlement()
        if at and not at:is_null_interface() then return at end
    end
    local regions = faction:region_list()
    for i = 0, regions:num_items() - 1 do
        local region = regions:item_at(i)
        if region and not region:is_null_interface() then
            local at = region:settlement()
            if at and not at:is_null_interface() then return at end
        end
    end
    return nil
end

function IC.can_hire(faction_key, office_slug, index)
    local office = IC.office_by_slug(office_slug)
    if not office then return false, "no such office" end
    if not IC.HIRE[index] then return false, "no such officer" end
    local court = IC.court(faction_key)
    if court.offices[office_slug] then
        local left = (court.terms[office_slug] or 0) - cm:model():turn_number()
        return false, "term", math.max(0, left)
    end
    if IC.tier_influence(office.tier) > IC.TUNE.hire_standing then
        return false, "too high"
    end
    if not IC.hire_settlement(real_faction(faction_key)) then
        return false, "no settlement"
    end
    return true
end

function IC.hired(faction_key, character)
    local office_slug = IC.hiring[faction_key]
    if not office_slug then return false end
    if not character or character:is_null_interface() then return false end
    IC.hiring[faction_key] = nil

    local lookup = cm:char_lookup_str(character)
    pcall(function()
        cm:add_agent_experience(lookup, IC.office_rank(office_slug), true)
    end)
    IC.stamp_origin(character, IC.origin_for(character))
    IC.stamp_bg(character, IC.background_for(character, faction_key))
    IC.stamp_ambition(faction_key, character)

    local cqi = character:command_queue_index()
    IC.court(faction_key).standing[cqi] = IC.TUNE.hire_standing
    local done, why, spare = IC.appoint(faction_key, office_slug, cqi)
    if not done then
        IC.save(faction_key)
        return false, why, spare
    end
    IC.log(faction_key, "hire", own, office_slug, 0)
    return true
end

function IC.hire(faction_key, office_slug, index)
    local ok, why, spare = IC.can_hire(faction_key, office_slug, index)
    if not ok then return false, why, spare end
    local faction = real_faction(faction_key)
    local settlement = IC.hire_settlement(faction)
    local recruit = IC.HIRE[index]

    local before = {}
    local list = faction:character_list()
    for i = 0, list:num_items() - 1 do
        local one = list:item_at(i)
        if one and not one:is_null_interface() then
            before[one:command_queue_index()] = true
        end
    end

    IC.hiring[faction_key] = office_slug
    cm:spawn_agent_at_settlement(faction, settlement, recruit.agent,
                                 recruit.subtype)

    list = faction:character_list()
    for i = 0, list:num_items() - 1 do
        local one = list:item_at(i)
        if one and not one:is_null_interface()
                and not before[one:command_queue_index()] then
            local done, reason, over = IC.hired(faction_key, one)
            if done then return true end
            if IC.hiring[faction_key] == nil then return false, reason, over end
        end
    end
    -- Still open: the spawn was asynchronous and the listener will finish it.
    return true
end

function IC.can_appoint(faction_key, office_slug, cqi)
    local court = IC.court(faction_key)
    local office = IC.office_by_slug(office_slug)
    if not office then return false, "no such office" end
    local character = IC.character_by_cqi(faction_key, cqi)
    if not character then return false, "no such character" end
    -- Return the rank shortfall so the panel can explain the refusal.
    local rank_bar = IC.office_rank(office_slug)
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
    return true
end

function IC.appoint(faction_key, office_slug, cqi)
    local ok, why = IC.can_appoint(faction_key, office_slug, cqi)
    if not ok then return false, why end

    local court = IC.court(faction_key)
    local office = IC.office_by_slug(office_slug)
    local character = IC.character_by_cqi(faction_key, cqi)

    IC.dismiss(faction_key, office_slug, true)

    court.offices[office_slug] = cqi
    court.terms[office_slug] = cm:model():turn_number() + IC.TUNE.term_turns
    cm:force_add_trait(cm:char_lookup_str(character), IC.office_trait(office_slug), true)

    local slug = IC.house_of_character(character, faction_key)
    if slug and court.houses[slug] then
        local gain = IC.TUNE.weight_per_office
        if slug == office.affinity then gain = gain * IC.TUNE.weight_affinity_mult end
        court.houses[slug].weight = court.houses[slug].weight + gain
    end
    IC.move_loyalty(faction_key, slug, IC.TUNE.loyalty_appointed)
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
        cm:force_remove_trait(cm:char_lookup_str(character), IC.office_trait(office_slug))
    end
    local slug = IC.house_of_cqi(faction_key, cqi)
    court.offices[office_slug] = nil
    if slug and court.houses[slug] then
        court.houses[slug].weight = math.max(1,
            court.houses[slug].weight - IC.TUNE.weight_per_office)
    end
    if not quiet then
        IC.move_loyalty(faction_key, slug, IC.TUNE.loyalty_dismissed)
    end
    if not quiet then
        IC.log(faction_key, "dismiss", slug, office_slug, 0)
        IC.apply_office_bundles(faction_key)
        IC.save(faction_key)
    end
    return true
end

function IC.apply_office_bundles(faction_key)
    local court = IC.court(faction_key)
    for i = 1, #IC.OFFICES do
        local slug = IC.OFFICES[i].slug
        cm:remove_effect_bundle(IC.office_bundle(slug), faction_key)
        cm:remove_effect_bundle(IC.vacancy_bundle(slug), faction_key)
        if court.offices[slug] then
            cm:apply_effect_bundle(IC.office_bundle(slug), faction_key, -1)
        end
    end
end

function IC.filled_offices(faction_key)
    local court, n = IC.court(faction_key), 0
    for _ in pairs(court.offices) do n = n + 1 end
    return n
end

function IC.gov_bundle_base()      return "derpy_ic_gov_base" end
function IC.gov_bundle_house(slug) return "derpy_ic_gov_house_" .. slug end

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
    -- only kept the early court's provinces empty. The offices still compete
    -- for the best men; a governorship is what the rest of them do.
    court.govs[province_key] = cqi
    IC.log(faction_key, "gov_on", IC.house_of_character(character, faction_key),
           province_key, 0)
    IC.save(faction_key)
    IC.apply_governor_bundles(faction_key)
    return true
end

function IC.release_governor(faction_key, province_key)
    IC.log(faction_key, "gov_off",
           IC.house_of_cqi(faction_key,
                           IC.court(faction_key).govs[province_key] or -1),
           province_key, 0)
    local court = IC.court(faction_key)
    if not court.govs[province_key] then return false end
    court.govs[province_key] = nil
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
    -- ONLY A LORD IN THE FIELD CAN BE AWAY (author, 2026-09-23). A garrison
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

function IC.refresh_gov_weight(faction_key)
    local court = IC.court(faction_key)
    for _, house in pairs(court.houses) do house.gov_weight = 0 end
    for _province_key, cqi in pairs(court.govs) do
        local slug = IC.house_of_cqi(faction_key, cqi)
        local house = slug and court.houses[slug]
        if house then
            house.gov_weight = house.gov_weight + IC.TUNE.weight_per_governor
        end
    end
end

function IC.apply_governor_bundles(faction_key)
    local court = IC.court(faction_key)
    IC.refresh_gov_weight(faction_key)

    for i = 1, #IC.PARTIES do
        cm:remove_effect_bundle(IC.gov_bundle_house(IC.PARTIES[i]), faction_key)
    end
    cm:remove_effect_bundle(IC.gov_bundle_base(), faction_key)

    for province_key, cqi in pairs(court.govs) do
        local character = IC.character_by_cqi(faction_key, cqi)
        local province, region = province_of_character(character)
        if province and province:key() == province_key and region then
            cm:apply_effect_bundle_to_faction_province(IC.gov_bundle_base(), region, -1)
            local slug = IC.house_of_character(character, faction_key)
            if slug and IC.BACKGROUNDS[slug] then
                cm:apply_effect_bundle_to_faction_province(
                    IC.gov_bundle_house(slug), region, -1)
            end
        end
    end
end

function IC.trickle_for(character)
    if not character or character:is_null_interface() then
        return IC.TUNE.influence_trickle_general
    end
    -- A garrison commander's garrison is a force, but he never leaves home.
    if IC.is_colonel(character) then return IC.TUNE.influence_trickle end
    local ok, has = pcall(function() return character:has_military_force() end)
    if not ok or has then return IC.TUNE.influence_trickle_general end
    return IC.TUNE.influence_trickle
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
        local trickle = IC.trickle_for(man)
        add_standing_raw(faction_key, cqi, trickle)
        paid = paid + trickle
    end
    for office_slug, cqi in pairs(court.offices) do
        local office = IC.office_by_slug(office_slug)
        if office and alive[cqi] then
            local wage = IC.tier_income(office.tier)
            add_standing_raw(faction_key, cqi, wage)
            paid = paid + wage
        end
    end
    for _province, cqi in pairs(court.govs) do
        if alive[cqi] then
            add_standing_raw(faction_key, cqi, IC.TUNE.governor_income)
            paid = paid + IC.TUNE.governor_income
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
        IC.log(faction_key, "term", slug, done[i].slug, 0)
    end
    if #done > 0 then
        IC.feed(faction_key, "office_lost",
                #done == 1 and IC.office_title_key(done[1].slug) or nil)
    end
    return #done
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
                    == IC.MILITARY_DOCTRINE then
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
            label = doctrine == 1 and "Military Doctrine"
                    or string.format("Military Doctrine in %d provinces", doctrine),
            n = doctrine * IC.TUNE.loyalty_military_doctrine,
        }
    end

    for i = 1, #IC.OFFICES do
        local office = IC.OFFICES[i]
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
        local trait = IC.PARTY_TRAITS[which or 0]
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
            label = "Blood-oath",
            note = "The oath holds while both men live.",
            n = IC.TUNE.plot_oath_loyalty}
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
                        snub_key and IC.office_by_slug(snub_key)
                        and IC.office_title_key(snub_key) or nil)
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

function IC.control_bundle(slug) return "derpy_ic_control_" .. slug end

function IC.apply_control_bundle(faction_key)
    local want = IC.control_band(faction_key)
    for i = 1, #IC.CONTROL do
        cm:remove_effect_bundle(IC.control_bundle(IC.CONTROL[i].slug),
                                faction_key)
    end
    cm:apply_effect_bundle(IC.control_bundle(want), faction_key, -1)
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
    if not IC.is_human(faction_key) then
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
    local out = {subtype = IC.REBEL_LORD, forename = "", surname = ""}
    if not cqi then return out end
    local man = IC.character_by_cqi(faction_key, cqi)
    if not man then return out end
    pcall(function()
        local key = man:character_subtype_key()
        if key and key ~= "" and IC.REBEL_GENERALS[key] then
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
    local man = nil
    if cqi then man = IC.character_by_cqi(faction_key, cqi) end
    if man then
        local force = nil
        pcall(function() force = man:military_force() end)
        take(force)
    end
    local faction = real_faction(faction_key)
    if faction then
        local forces = nil
        pcall(function() forces = faction:military_force_list() end)
        if forces then
            for i = 0, forces:num_items() - 1 do
                take(forces:item_at(i))
            end
        end
    end
    local at = 1
    while #kit > 0 and #kit < want do
        kit[#kit + 1] = kit[at]
        at = at + 1
    end
    for i = 1, #IC.REBEL_ROSTER do
        if #kit >= want then break end
        kit[#kit + 1] = IC.REBEL_ROSTER[i]
    end
    return kit
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

function IC.rebel_sour(rebels, other)
    if not rebels or not other or rebels == other then return 0 end
    local a, b
    pcall(function() a = cm:get_faction(rebels) end)
    pcall(function() b = cm:get_faction(other) end)
    if not a or a == false or not b or b == false then return 0 end
    local n = 0
    while n < IC.TUNE.rebel_relation_max do
        local now
        pcall(function() now = a:diplomatic_standing_with(b) end)
        if now and now <= IC.TUNE.rebel_relation then break end
        pcall(function()
            cm:apply_dilemma_diplomatic_bonus(rebels, other,
                                              IC.TUNE.rebel_relation_step)
        end)
        n = n + 1
    end
    return n
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

function IC.rebel_force(rebels, region_key, x, y, general, crown, kit)
    if not rebels or not region_key then return false end
    general = general or {subtype = IC.REBEL_LORD, forename = "", surname = ""}
    local units = {}
    if kit and #kit > 0 then
        for i = 1, math.min(IC.TUNE.rebel_units, #kit) do
            units[i] = kit[i]
        end
    else
        for i = 1, math.min(IC.TUNE.rebel_units, #IC.REBEL_ROSTER) do
            units[i] = IC.REBEL_ROSTER[i]
        end
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
        IC.say("IRON COURT: the rebel army did not spawn - " .. tostring(err))
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
                               rise.general, crown, rise.kit)
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
                    pcall(function() cm:kill_character(rise.cqi, false) end)
                    IC.say("IRON COURT: cqi " .. tostring(rise.cqi)
                           .. " taken off the board, his army left standing")
                end
            end
        end
    end

    if rebels and flying then
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
    local court = IC.court(faction_key)
    local crown = court.houses[IC.CROWN]
    if not crown then return nil end
    local backed = {}
    local faction = real_faction(faction_key)
    if faction then
        local list = faction:character_list()
        for i = 0, list:num_items() - 1 do
            local man = list:item_at(i)
            if man and not man:is_null_interface() and not IC.is_legend(man) then
                local bg = IC.bg_of_character(man)
                local party = bg and IC.PARTY_OF_BG[bg]
                if party then backed[party] = true end
            end
        end
    end
    local pool = {}
    for i = 1, #IC.PARTIES do
        local slug = IC.PARTIES[i]
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
    IC.move_loyalty(faction_key, IC.CROWN, IC.TUNE.loyalty_start - keep)
    IC.log(faction_key, "splinter", slug, nil, house.weight)
    IC.feed(faction_key, "splinter")
    IC.save(faction_key)
    return slug
end

function IC.at_breaking_point(faction_key, slug)
    if not slug or slug == IC.CROWN then return false end
    local house = IC.court(faction_key).houses[slug]
    if not house then return false end
    return (house.loyalty or IC.TUNE.loyalty_start) <= IC.TUNE.secede_break
end

function IC.tick_secession(faction_key)
    local court = IC.court(faction_key)
    local own = IC.CROWN
    local warned = {}
    -- Collect first because mutating a table during pairs() traversal is undefined.
    local seceding = {}
    for slug, house in pairs(court.houses) do
        local angry = false
        local breaking = false
        if slug ~= own then
            local share = IC.share(faction_key, slug)
            angry = share >= IC.TUNE.secede_share
                and house.loyalty <= IC.TUNE.secede_loyalty
            if house.pressed then angry = true end
            if IC.protected_for(faction_key, slug) > 0 then angry = false end
            breaking = IC.at_breaking_point(faction_key, slug)
        end
        if breaking then
            seceding[#seceding + 1] = slug
            house.clock = 0
        elseif angry then
            if (house.clock or 0) <= 0 then
                house.clock = IC.TUNE.secede_turns
                IC.log(faction_key, "warn", slug, nil, house.clock)
                IC.feed(faction_key, "secede_warn")
            else
                house.clock = house.clock - 1
                if house.clock <= 0 then
                    seceding[#seceding + 1] = slug
                elseif house.clock == IC.TUNE.warn_turns then
                    IC.feed(faction_key, "secede_soon")
                end
            end
            warned[#warned + 1] = {slug = slug, turns = house.clock}
        else
            if (house.clock or 0) > 0 then
                IC.log(faction_key, "snub_off", slug, nil, 0)
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

-- NOBODY IN IT AND NO PROVINCE TO TAKE. Seen live 2026-09-23: such a party
-- "seceded" from a rebel faction with 0 provinces and 0 armies, and all it did
-- was rename another rising's faction (the rebel pool was full) and start a war
-- between the two. The author: it dissolves instead, with a card.
function IC.nothing_to_take(faction_key, slug)
    local _, members = IC.party_lords(faction_key, slug)
    if (members or 0) > 0 then return false end
    return #(IC.defecting_provinces(faction_key, slug) or {}) == 0
end

function IC.dissolve(faction_key, slug)
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

function IC.ai_fill_offices(faction_key)
    if IC.is_human(faction_key) then return 0 end
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
    local used, seated = {}, 0
    for i = 1, #IC.OFFICES do
        local office = IC.OFFICES[i]
        if not court.offices[office.slug] then
            -- THE CLAIMED PARTY, and nobody else while it sits in this court.
            -- An outsider in a claimed seat costs that party loyalty_snubbed at
            -- once and loyalty_affinity_snub every turn after, and the AI has no
            -- move that can ever pay either back. The outsider was nearly always
            -- a Crown man already at or near 100, so the seat bought nothing.
            -- Live saves, 2026-09-23: every AI party still falling was one whose
            -- claimed seat had gone to an outsider, because it was empty or its
            -- men were under the rank bar. A seat claimed by a party that is not
            -- in this court goes to anybody.
            local passes = court.houses[office.affinity] and 1 or 2
            for pass = 1, passes do
                local done = false
                for j = 1, #pool do
                    local cqi = pool[j].cqi
                    local affine = pool[j].slug == office.affinity
                    if not used[cqi] and ((pass == 1) == affine)
                            and IC.appoint(faction_key, office.slug, cqi) then
                        used[cqi] = true
                        seated = seated + 1
                        done = true
                        break
                    end
                end
                if done then break end
            end
        end
    end
    return seated
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
    {key = "house",  name = "Against a House"},
    {key = "bond",   name = "Bonds"},
    {key = "errand", name = "Errands"},
}

function IC.plots_in(cat)
    local out = {}
    for i = 1, #IC.PLOTS do
        if IC.PLOTS[i].cat == cat then out[#out + 1] = IC.PLOTS[i] end
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
     blurb = "Gold and labourers buy favour."},
    {key = "discredit", name = "Discredit",
     icon = "ui/campaign ui/skills/campaign_chaos_corruption.png",
     cat = "man",
     cost = "plot_discredit_cost",
     effect = string.format(
         "-%d influence for him. -%d influence from his party.",
         IC.TUNE.plot_discredit_standing,
         IC.TUNE.plot_discredit_weight),
     blurb = "His ore comes up short and his contracts are challenged. His party falls with him."},
    {key = "rumour", name = "Spread Rumours",
     icon = "ui/campaign ui/skills/wh3_main_lord_passive_whispers_in_the_darkness.png",
     cat = "man",
     cost = "plot_rumour_cost",
     effect = string.format(
         "-%d influence for him. His party is unaffected.",
         IC.TUNE.plot_rumour_damage),
     blurb = "A few paid tongues can ruin one name without starting a feud."},
    {key = "murder", name = "A Forge Accident",
     icon = "ui/campaign ui/skills/wh3_dlc23_character_ability_reforge.png",
     cat = "man",
     cost = "plot_murder_cost",
     effect = string.format(
         "He dies. -%d loyalty from his house.",
         IC.TUNE.plot_murder_loyalty),
     blurb = "The Tower claims another victim. His party will know who arranged it."},
    -- Rome II-style actions against an entire party.
    -- PROVOKE AND PURGE ARE cat "party", which IC.PLOT_CATS does not list, so
    -- the Intrigue grid never draws them. They are the court tab's action bar:
    -- the player picks the party on its card and the move is aimed at the man
    -- who speaks for it (author, 2026-09-24).
    {key = "provoke", name = "Provoke",
     icon = "ui/campaign ui/skills/wh3_dlc23_character_ability_malign_authority.png",
     cat = "party",
     cost = "plot_provoke_cost",
     effect = string.format(
         "-%d loyalty. Sets their secession countdown to %d turns.",
         IC.TUNE.plot_provoke_loyalty,
         IC.TUNE.plot_provoke_clock),
     blurb = "Give them an insult they cannot ignore, then choose when the reckoning begins."},
    {key = "purge", name = "Purge the House",
     icon = "ui/campaign ui/skills/wh3_dlc23_character_abilities_skjalandirs_fall.png",
     cat = "party",
     cost = "plot_purge_cost",
     effect = string.format(
         "Removes the party. -%d loyalty to all others. Failure: another -%d to the target.",
         IC.TUNE.plot_purge_witness,
         IC.TUNE.plot_purge_backfire),
     blurb = "Erase their name. The court remembers."},
    {key = "unseat", name = "Strike Their Seats",
     icon = "ui/campaign ui/skills/wh2_dlc11_forgery.png",
     cat = "house",
     cost = "plot_unseat_cost",
     effect = string.format(
         "Empties every office they hold. -%d loyalty.",
         IC.TUNE.plot_unseat_loyalty),
     blurb = "Strip every title from them in one sitting. They keep only their name."},
    {key = "recall", name = "Recall Their Governors",
     icon = "ui/campaign ui/skills/wh3_dlc24_hero_passive_assume_command.png",
     cat = "house",
     cost = "plot_recall_cost",
     effect = string.format(
         "Recalls every governor from their party. -%d loyalty.",
         IC.TUNE.plot_recall_loyalty),
     blurb = "Call their overseers home. The provinces answer to the Tower again."},
    {key = "oath", name = "Blood-Oath on the Anvil",
     icon = "ui/campaign ui/skills/wh3_dlc23_character_abilities_by_our_blood.png",
     cat = "bond",
     cost = "plot_oath_cost",
     effect = string.format(
         "+%d loyalty each turn while both men live. Requires %d loyalty.",
         IC.TUNE.plot_oath_loyalty,
         IC.TUNE.plot_oath_min_loyalty),
     blurb = "Score two names into hot iron. They must trust you before they swear."},
    {key = "patron", name = "Stand His Patron",
     icon = "ui/campaign ui/skills/character_diplomacy.png",
     cat = "bond",
     cost = "plot_patron_cost",
     effect = string.format(
         "+%d influence for him. +%d loyalty for his party.",
         IC.TUNE.plot_patron_standing,
         IC.TUNE.plot_patron_loyalty),
     blurb = "Put your name behind his and an office within reach. He will remember."},
    {key = "kinsman", name = "Name Him Kinsman",
     icon = "ui/campaign ui/ancillaries/wh3_dlc23_anc_banner_chd_standard_of_zharr.png",
     cat = "bond",
     cost = "plot_kinsman_cost",
     effect = string.format(
         "Moves up to %d influence to the Crown. Requires %d loyalty.",
         IC.TUNE.plot_kinsman_weight,
         IC.TUNE.plot_kinsman_min_loyalty),
     blurb = "Take him under your standard. His party loses influence."},
    {key = "pledge", name = "Pledge of the Forge",
     icon = "ui/campaign ui/skills/mount_anvil_of_doom.png",
     cat = "bond",
     cost = "plot_pledge_cost",
     effect = string.format(
         "+%d loyalty. Stops their secession countdown. Costs the Crown %d influence.",
         IC.TUNE.plot_pledge_loyalty,
         IC.TUNE.plot_pledge_weight),
     blurb = "Promise them the next work of the forge."},
    {key = "embezzle", name = "Embezzle from the Vaults", aimed = false,
     icon = "ui/campaign ui/ancillaries/wh_main_anc_human_spy.png",
     cat = "errand",
     cost = "plot_embezzle_cost",
     effect = string.format(
         "+%d gold. -%d loyalty across the whole court.",
         IC.TUNE.plot_embezzle_gold,
         IC.TUNE.plot_embezzle_loyalty),
     blurb = "The ledgers will balance before the audit. The court will still smell theft."},
    {key = "feast", name = "A Feast of Ash", aimed = false,
     icon = "ui/campaign ui/skills/wh3_main_unit_passive_gorefeast.png",
     cat = "errand",
     cost = "plot_feast_cost",
     effect = string.format(
         "+%d influence to the man you send. -%d loyalty across "
         .. "the court.",
         IC.TUNE.plot_feast_standing,
         IC.TUNE.plot_feast_loyalty),
     blurb = "Labourers, fire, and a long feast. The court learns his name."},
    {key = "audience", name = "Hold the Ash Court", aimed = false,
     icon = "ui/campaign ui/skills/campaign_public_order.png",
     cat = "errand",
     cost = "plot_audience_cost",
     effect = string.format(
         "+%d loyalty to every house in the court.",
         IC.TUNE.plot_audience_loyalty),
     blurb = "Hear every grievance through a day of smoke. The court leaves less bitter."},
    {key = "circuit", name = "Ride the Circuit", aimed = false,
     icon = "ui/campaign ui/ancillaries/wh3_dlc23_anc_follower_convoy_enforcer.png",
     cat = "errand",
     cost = "plot_circuit_cost",
     effect = string.format(
         "+%d control in every province you hold.",
         IC.TUNE.plot_circuit_prov),
     blurb = "Inspect the provinces with a ledger and an armed escort. Order improves."},
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
     blurb = "Send labourers, ore, and strong drink. A small payment buys a little patience."},
    {key = "secure", name = "Secure Loyalty",
     cost = "favour_secure_cost",
     blurb = "Take hostages and bind the party by oath. This delays rebellion but cannot save loyalty at zero."},
}

function IC.favour_by_key(key)
    for i = 1, #IC.FAVOURS do
        if IC.FAVOURS[i].key == key then return IC.FAVOURS[i] end
    end
    return nil
end

function IC.favour_cost(key)
    local favour = IC.favour_by_key(key)
    if not favour then return 0 end
    return IC.TUNE[favour.cost] or 0
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
    local cost = IC.favour_cost(key)
    local gold = IC.treasury(faction_key)
    if gold < cost then return false, "gold", cost - gold end
    if key == "gift" and (house.loyalty or 0) >= 100 then
        return false, "content"
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
    local cost = IC.favour_cost(key)
    cm:treasury_mod(faction_key, -cost)

    if key == "gift" then
        IC.move_loyalty(faction_key, slug, IC.TUNE.favour_gift_loyalty)
    elseif key == "secure" then
        house.protected = cm:model():turn_number() + IC.TUNE.favour_secure_turns
        house.clock = 0
        house.pressed = nil
    end

    IC.log(faction_key, key, slug, nil, cost)
    IC.save(faction_key)
    return true
end

function IC.plot_by_key(key)
    for i = 1, #IC.PLOTS do
        if IC.PLOTS[i].key == key then return IC.PLOTS[i] end
    end
    return nil
end

function IC.plot_cost(key)
    local plot = IC.plot_by_key(key)
    if not plot then return 0 end
    return IC.TUNE[plot.cost] or 0
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

function IC.is_legend(character)
    if not character or character:is_null_interface() then return false end
    if IC.is_unique(character) then return true end
    local key = nil
    pcall(function() key = character:character_subtype_key() end)
    return key ~= nil and IC.LEGEND_SUBTYPES[key] == true
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
    if not IC.plot_is_aimed(plot_key) then return true end
    local victim = IC.character_by_cqi(faction_key, tonumber(cqi))
    if not victim then return false, "no such target" end
    if plot_key == "murder" and IC.is_legend(victim) then
        return false, "unique"
    end
    if IC.house_of_character(victim, faction_key) == IC.CROWN then
        return false, "own party"
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
    local ok, why = IC.may_target(faction_key, plot_key, target)
    if not ok then return false, why end
    local actor = IC.character_by_cqi(faction_key, actor_cqi)
    if not actor then return false, "no such character" end
    if not IC.may_plot_as(faction_key, actor_cqi) then
        return false, "not yours"
    end
    if IC.is_civil_mission(plot_key) and actor:has_military_force() then
        return false, "commands"
    end
    if not IC.plot_is_aimed(plot_key) then
        local cost0 = IC.plot_cost(plot_key)
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

    local cost = IC.plot_cost(plot_key)
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
    local cost = IC.plot_cost(plot_key)
    local slug = IC.house_of_cqi(faction_key, actor_cqi)
    local cqi = tonumber(target)
    local against = IC.house_of_cqi(faction_key, cqi)

    IC.add_standing(faction_key, actor_cqi, -cost)

    local chance = IC.plot_chance(faction_key, plot_key, actor_cqi, target)
    if chance and cm:random_number(100, 1) > chance then
        if against then
            IC.move_loyalty(faction_key, against, -IC.TUNE.plot_fail_loyalty)
            if plot_key == "purge" then
                IC.move_loyalty(faction_key, against,
                                -IC.TUNE.plot_purge_backfire)
            end
        end
        IC.log(faction_key, "plot_failed", slug, against, cost)
        IC.feed(faction_key, "plot_fail",
                IC.move_result_key(plot_key, false))
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
        if house then
            house.clock = 0
            house.snubbed = nil
            house.snub_key = nil
        end
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
        local house = IC.house_of_victim(faction_key, cqi)
        if house then
            local now = house.clock or 0
            if now <= 0 or now > IC.TUNE.plot_provoke_clock then
                house.clock = IC.TUNE.plot_provoke_clock
                if house.clock <= IC.TUNE.warn_turns
                   and (now <= 0 or now > IC.TUNE.warn_turns) then
                    IC.feed(faction_key, "secede_soon")
                end
            end
            if house.oath_mine then
                house.oath_mine, house.oath_theirs = nil, nil
                IC.log(faction_key, "oath_broken", against or "", "provoked", 0)
            end
        end
    elseif plot_key == "purge" then
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
        IC.mood_of_the_court(faction_key, -IC.TUNE.plot_embezzle_loyalty)
    elseif plot_key == "feast" then
        IC.add_standing(faction_key, actor_cqi, IC.TUNE.plot_feast_standing)
        IC.mood_of_the_court(faction_key, -IC.TUNE.plot_feast_loyalty)
    elseif plot_key == "unseat" then
        for _, office_slug in ipairs(IC.offices_of_house(faction_key, against)) do
            IC.dismiss(faction_key, office_slug, true)
        end
        IC.move_loyalty(faction_key, against, -IC.TUNE.plot_unseat_loyalty)
    elseif plot_key == "recall" then
        for _, province_key in ipairs(IC.provinces_of_house(faction_key,
                                                            against)) do
            IC.release_governor(faction_key, province_key)
        end
        IC.move_loyalty(faction_key, against, -IC.TUNE.plot_recall_loyalty)
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
        if house then
            house.clock = 0
            house.snubbed = nil
            house.snub_key = nil
        end
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
    elseif plot_key == "murder" then
        local victim = IC.character_by_cqi(faction_key, cqi)
        IC.move_loyalty(faction_key, against, -IC.TUNE.plot_murder_loyalty)
        cm:kill_character(cm:char_lookup_str(victim), false)
    end

    IC.log(faction_key, plot_key, slug, against, cost)
    IC.feed(faction_key, "plot_ok", IC.move_result_key(plot_key, true))
    IC.enforce_bars(faction_key)
    IC.apply_office_bundles(faction_key)
    IC.save(faction_key)
    return true, "landed"
end

function IC.enforce_bars(faction_key)
    -- The other half of the exemption in IC.can_appoint: seating an AI officer
    -- under the bar and then unseating him on the next turn start would be
    -- worse than never seating him, because a dismissal is a loyalty event.
    if not IC.is_human(faction_key) then return end
    local court = IC.court(faction_key)
    local fallen = {}
    for office_slug, cqi in pairs(court.offices) do
        local office = IC.office_by_slug(office_slug)
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

function IC.turn(faction_key)
    IC.load(faction_key)
    -- Roll the court before backgrounds, as IC.seed does, or an AI faction's
    -- first turn deals every starting man to the Crown and every rival party
    -- is born empty. Only the player's court went through IC.seed.
    IC.roll_court(faction_key)
    IC.stamp_court(faction_key)
    IC.reconcile_houses(faction_key)
    IC.ensure_leaders(faction_key)
    IC.reconcile_governors(faction_key)
    IC.tick_provinces(faction_key)
    IC.income(faction_key)
    IC.expire_terms(faction_key)
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
    IC.tick_pressure(faction_key)
    if not IC.feed_held then IC.flush_feed() end
    if IC.party_turn then IC.party_turn(faction_key) end
    local warned = IC.tick_secession(faction_key)
    IC.splinter(faction_key)
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
    if IC.court_rolled(faction_key) then return false end
    IC.add_house(faction_key, IC.CROWN)
    local pool = {}
    for i = 1, #IC.PARTIES do
        if IC.PARTIES[i] ~= IC.CROWN then pool[#pool + 1] = IC.PARTIES[i] end
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
    IC.save(faction_key)
    return true
end

function IC.name_party(faction_key, slug)
    local court = IC.court(faction_key)
    local house = court.houses[slug]
    if not house then return false end
    local tails = IC.NAME_TAILS[slug]
    if not tails or #tails == 0 then return false end
    house.head = cm:random_number(#IC.NAME_HEADS, 1)
    house.tail = cm:random_number(#tails, 1)
    return true
end

function IC.roll_party_traits(faction_key, slug)
    local house = IC.court(faction_key).houses[slug]
    if not house then return false end
    local n = #IC.PARTY_TRAITS
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

-- THE LAST RESORT, a garrison commander (author, 2026-09-23): a court whose
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
                                       agent = IC.REBEL_HEROES[key]}
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
    return key ~= nil and IC.REBEL_HEROES[key] ~= nil
end

function IC.can_defect(character)
    if not IC.is_lordly(character) then return false end
    if IC.is_legend(character) then return false end
    local key = nil
    pcall(function() key = character:character_subtype_key() end)
    return key ~= nil and IC.REBEL_GENERALS[key] == true
end

function IC.is_lordly(character)
    local kind = IC.kind_of_character(character)
    return kind == "general" or kind == "lord"
end

function IC.party_traits(faction_key, slug)
    local out = {}
    local house = IC.court(faction_key).houses[slug or ""]
    if not house then return out end
    for _, which in ipairs({house.t1 or 0, house.t2 or 0}) do
        local trait = IC.PARTY_TRAITS[which]
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
    local cqi = IC.party_leader(faction_key, slug)
    if not cqi then return nil end
    return IC.LEADER_TRAITS[(cqi % #IC.LEADER_TRAITS) + 1]
end

function IC.party_name(faction_key, slug)
    local house = IC.court(faction_key).houses[slug]
    if not house or not house.head or not house.tail then return nil end
    local tails = IC.NAME_TAILS[slug]
    if not tails or #tails == 0 then return nil end
    -- Wrapped, not indexed: a save rolled against the older, longer head list
    -- still names every party.
    local head = IC.NAME_HEADS[(house.head - 1) % #IC.NAME_HEADS + 1]
    local tail = tails[(house.tail - 1) % #tails + 1]
    return head .. " of " .. tail
end

function IC.reconcile_houses(faction_key)
    local court = IC.court(faction_key)
    local dead = {}
    for slug, house in pairs(court.houses) do
        if not IC.is_party(slug) and not house.confed then
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

function IC.stamp_incoming(faction_key, slug, attempts, before)
    attempts = attempts or 0
    local faction = real_faction(faction_key)
    if not faction then return end
    local list = faction:character_list()
    before = before or {}
    local stamped = 0
    for i = 0, list:num_items() - 1 do
        local man = list:item_at(i)
        if man and not man:is_null_interface()
           and not before[man:command_queue_index()] then
        local fixed = IC.fixed_history(man)
        if IC.stamp_origin(man, fixed and fixed.origin or slug) then
            stamped = stamped + 1
        end
        IC.stamp_bg(man, IC.background_for(man, faction_key))
        end
    end
    if stamped > 0 and IC.add_house(faction_key, slug, true) then
        IC.log(faction_key, "join", slug, nil, stamped)
        IC.feed(faction_key, "party_joined")
        IC.save(faction_key)
    end
    if stamped == 0 and attempts < 6 then
        cm:callback(function()
            IC.stamp_incoming(faction_key, slug, attempts + 1, before)
        end, 3)
    end
end

function IC.register()
    core:add_listener("ic_turn", "FactionTurnStart", true, function(context)
        local faction = context:faction()
        if not IC.is_chd(faction) then return end
        IC.turn(faction:name())
    end, true)

    core:add_listener("ic_confed", "FactionJoinsConfederation", true, function(context)
        local host = context:confederation()
        local joined = context:faction()
        if not IC.is_chd(host) then return end
        local slug = IC.origin_for_faction(joined:name())
        if not slug then return end
        local host_key = host:name()
        local before = {}
        local own = host:character_list()
        for i = 0, own:num_items() - 1 do
            local man = own:item_at(i)
            if man and not man:is_null_interface() then
                before[man:command_queue_index()] = true
            end
        end
        IC.stamp_incoming(host_key, slug, 0, before)
    end, true)


    core:add_listener("ic_born", "CharacterCreated", true, function(context)
        local character = context:character()
        if not character or character:is_null_interface() then return end
        local faction = character:faction()
        if not faction or faction:is_null_interface() then return end
        local faction_key = faction:name()
        IC.hired(faction_key, character)
        if IC.is_chd(faction) and IC.court_rolled(faction_key) then
            IC.stamp_origin(character, IC.origin_for(character))
            IC.stamp_bg(character, IC.background_for(character, faction_key))
        end
    end, true)

    core:add_listener("ic_battle", "CharacterCompletedBattle", true, function(context)
        local character = context:character()
        if not character or character:is_null_interface() then return end
        if not character:won_battle() then return end
        local faction = character:faction()
        if not faction or faction:is_null_interface() then return end
        if not IC.is_chd(faction) then return end
        local battle = context:pending_battle()
        if not battle or battle:is_null_interface() then return end
        local result = battle:attacker_battle_result()
        if not IC.TUNE.battle_influence[result] then
            result = battle:defender_battle_result()
        end
        local gain = IC.TUNE.battle_influence[result]
        if not gain then return end
        local faction_key = faction:name()
        IC.move_loyalty(faction_key,
                        IC.house_of_character(character, faction_key),
                        IC.TUNE.loyalty_battle_won)
        IC.add_standing(faction_key, character:command_queue_index(), gain)
    end, true)

    core:add_listener("ic_took", "GarrisonOccupiedEvent", true, function(context)
        local character = context:character()
        if not character or character:is_null_interface() then return end
        local faction = character:faction()
        if not faction or faction:is_null_interface() then return end
        if not IC.is_chd(faction) then return end
        IC.add_standing(faction:name(), character:command_queue_index(),
                        IC.TUNE.settlement_influence)
    end, true)

    core:add_listener("ic_rank", "CharacterRankUp", true, function(context)
        local character = context:character()
        if not character or character:is_null_interface() then return end
        local faction = character:faction()
        if not faction or faction:is_null_interface() then return end
        if not IC.is_chd(faction) then return end
        local gained = context:ranks_gained() or 1
        IC.add_standing(faction:name(), character:command_queue_index(),
                        gained * IC.TUNE.rank_influence)
    end, true)

    core:add_listener("ic_dead", "CharacterConvalescedOrKilled", true, function(context)
        local character = context:character()
        if not character or character:is_null_interface() then return end
        if character:is_alive() ~= false then return end
        local faction = character:faction()
        if not IC.is_chd(faction) then return end
        local faction_key = faction:name()
        local cqi = character:command_queue_index()
        local court = IC.court(faction_key)
        for office_slug, holder in pairs(court.offices) do
            if holder == cqi then
                local slug = IC.house_of_character(character, faction_key)
                court.offices[office_slug] = nil
                if slug and court.houses[slug] then
                    court.houses[slug].weight = math.max(1,
                        court.houses[slug].weight - IC.TUNE.weight_per_office)
                end
            end
        end
        for province_key, holder in pairs(court.govs) do
            if holder == cqi then court.govs[province_key] = nil end
        end
        IC.move_loyalty(faction_key,
                        IC.house_of_character(character, faction_key),
                        IC.TUNE.loyalty_member_died)
        for slug2, house2 in pairs(court.houses) do
            if house2.oath_mine == cqi or house2.oath_theirs == cqi then
                house2.oath_mine, house2.oath_theirs = nil, nil
                IC.log(faction_key, "oath_broken", slug2, "died", 0)
            end
        end
        IC.apply_office_bundles(faction_key)
        IC.save(faction_key)
    end, true)
end

cm:add_first_tick_callback(function()
    IC.register()
    IC.rebel_rename_all()
    local human = cm:get_human_factions()
    for i = 1, #human do
        local faction = real_faction(human[i])
        if IC.is_chd(faction) then
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
        end
    end
end)
