"""The Iron Court: DB generator.

Emits every Iron Court DB table and the loc as TSVs in Modding Files/source/iron_court/:
effect bundles and their junctions, traits, event feed rows, missions, campaign groups and
the rebel factions' banner override. The design is 2026-09-11-iron-court-design.md
(docs/design/ in the public repo).

    py tools/gen_iron_court.py --check      # validate, write nothing
    py tools/gen_iron_court.py              # write TSVs
    py tools/gen_iron_court.py --selftest

Needs no RPFM: every vanilla fact it checks against comes out of .skilltree_cache.
"""
import io
import json
import os
import re
import struct
import sys

PACK_NAME = "derpy_iron_court"
CHD_SUBCULTURE = "wh3_dlc23_sc_chd_chaos_dwarfs"
CACHE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     ".skilltree_cache")

# The verified vocabulary.
#
# Every (effect, scope) pair below was read out of vanilla's own
# effect_bundles_to_effects_junctions; is_positive_value_good came from
# effects.json. check() re-reads both and refuses on any drift,
# because an invented effect key or an (effect, scope) pair CA never ships does
# not error - it silently does nothing forever.
#
# The third element is is_positive_value_good. TWO of the nine are False: they are
# load/cost modifiers where the BENEFIT is a NEGATIVE value. Nothing below ever
# writes a raw signed number - see signed_value().
E_ARMAMENTS = ("wh3_dlc23_pooled_resource_chd_armaments_modifier",
               "faction_to_region_own", True)
E_WORKLOAD = ("wh3_dlc23_pooled_resource_chd_workload_modifier",
              "faction_to_province_own", False)
E_RAWMAT = ("wh3_dlc23_pooled_resource_chd_raw_material_efficiency",
            "faction_to_region_own", True)
E_ORDER = ("wh_main_effect_public_order_faction",
           "faction_to_province_own", True)
E_GDP = ("wh_main_effect_economy_gdp_mod_all",
         "faction_to_region_own", True)
# THE SAME EFFECT ON ONE PROVINCE: the governor's runtime bundle adds it.
# Vanilla's province payloads scope it province_to_*.
E_GDP_PROVINCE = ("wh_main_effect_economy_gdp_mod_all",
                  "province_to_region_own", True)
# NO GROWTH: growth is useless to the Chaos Dwarfs. Its five uses became Conclave Influence (the High Priest, the two end bands), CA's
# slave-driven Control (a Priesthood governor) and Workload (every governor).
# THE SLAVES' CONTROL: CA's own effect, on its Dark Elf slave bundles at
# faction_to_province_own, is_positive_value_good True.
E_SLAVE_ORDER = ("wh3_dlc23_effect_public_order_slaves",
                 "faction_to_province_own", True)
E_UPKEEP = ("wh_main_effect_force_all_campaign_upkeep",
            "faction_to_force_own", False)
E_REPLEN = ("wh_main_effect_force_all_campaign_replenishment_rate",
            "faction_to_force_own", True)
E_PB_LABOUR = ("wh3_dlc23_effect_force_chd_campaign_post_battle_labour",
               "faction_to_force_own", True)

E_RESEARCH = ("wh_main_effect_technology_research_rate_mod",
              "faction_to_faction_own", True)
E_MOVEMENT = ("wh_main_effect_force_all_campaign_movement_range",
              "faction_to_force_own", True)
# COST MODIFIERS. is_positive_value_good False - the player's boon is NEGATIVE.
# Never write the sign; declare a magnitude and an intent and let signed_value
# do the arithmetic.
E_CONSTRUCT = ("wh_main_effect_building_construction_cost_mod_all",
               "faction_to_region_own", False)
E_RECRUIT = ("wh_main_effect_force_all_campaign_recruitment_cost_all",
             "faction_to_force_own", False)
E_AGENT = ("wh_main_effect_agent_action_success_chance",
           "faction_to_character_own", True)
E_RAID = ("wh_main_effect_force_all_campaign_raid_income",
          "faction_to_force_own", True)
# CHEAPER HOBGOBLINS, for the Steward of the Ash Fields, in place of growth.
# UPKEEP, not recruitment cost: CA ships the hobgoblin recruit-cost effect only on
# buildings, scoped to one province, and a faction bundle cannot use that scope.
# This one CA ships faction-wide, faction_to_force_own at -15, on the Volary
# (Tomb of Khengai Khan) - an upkeep_mod on unit set
# wh3_dlc23_chd_hobgoblin_units_and_gorduz, is_positive_value_good False.
E_HOBGOBLIN = ("wh3_dlc23_effect_upkeep_hobgoblins",
               "faction_to_force_own", False)

# THE ENVOY'S FOUR: CA's province-bundle shape, every effect
# province_to_province_own_unseen - the scope CA's Higher Quotas and Smoke
# Stacks edicts and its mood bundles give them. Signs measured off the vanilla
# cache: labour loss is the one where less is better.
E_ENVOY_CTL = ("wh_main_effect_public_order_edict",
               "province_to_province_own_unseen", True)
E_ENVOY_ARM = ("wh3_dlc23_pooled_resource_chd_armaments_modifier",
               "province_to_province_own_unseen", True)
E_ENVOY_RAW = ("wh3_dlc23_pooled_resource_chd_raw_material_efficiency",
               "province_to_province_own_unseen", True)
E_ENVOY_LAB = ("wh3_dlc23_pooled_resource_chd_increased_labour_loss",
               "province_to_province_own_unseen", False)
# THE LAWS. Every pair below ships in CA's junction tables and every flag
# matches CA's.
E_LAW_CAPTIVES = ("wh_main_effect_force_all_campaign_captives", "faction_to_force_own_unseen", True)
E_LAW_RUSH = ("wh3_dlc23_effect_rush_construction_cost", "faction_to_province_own", False)
E_LAW_LAB_LD = ("wh3_dlc23_effect_force_stat_leadership_chd_labourers", "faction_to_force_own", True)
E_LAW_LAB_UPKEEP = ("wh3_dlc23_effect_upkeep_chd_labourers", "faction_to_force_own", False)
E_LAW_LAB_RANK = ("wh3_dlc23_effect_recruitment_rank_chd_labourers", "faction_to_force_own", True)
E_LAW_RAW_USED = ("wh3_dlc23_pooled_resources_chd_raw_materials_consumed_mod", "faction_to_province_own", False)
E_LAW_RAZE = ("wh_main_effect_force_all_campaign_razing_income", "faction_to_faction_own_unseen", True)
E_LAW_SACK = ("wh_main_effect_force_all_campaign_sacking_income", "faction_to_faction_own_unseen", True)
E_LAW_CONVOYS = ("wh3_dlc23_effect_technology_chd_convoy_mod_active_convoys", "faction_to_faction_own_unseen", True)
E_LAW_AMBUSH = ("wh3_main_effect_caravan_scouts", "faction_to_character_own_unseen", False)
E_LAW_VASSAL = ("wh_main_effect_modify_vassal_income", "faction_to_faction_own_unseen", True)
E_LAW_TARIFF = ("wh3_dlc23_effect_chd_convoy_trade_tariff_scripted", "faction_to_faction_own_unseen", True)
E_LAW_REFINERY = ("wh3_dlc23_effect_economy_gpd_manufacture", "faction_to_region_own_unseen", True)
E_LAW_CARGO_VALUE = ("wh3_main_effect_caravan_cargo_value", "faction_to_character_own_unseen", True)
E_LAW_MINES = ("wh_main_effect_technology_economy_gdp_mod_mining_dwarfs", "faction_to_region_own_unseen", True)
E_LAW_GOODS = ("wh_main_effect_economy_trade_good_commodity_mod", "faction_to_faction_own_unseen", True)
E_LAW_CARGO_CAP = ("wh3_main_effect_caravan_cargo_capacity", "faction_to_character_own_unseen", True)
E_LAW_OVR_RANK = ("wh3_dlc23_faction_xp_increase_generals_chd_convoy_overseers", "faction_to_faction_own", True)
E_LAW_OVR_XP = ("wh3_dlc23_effect_force_army_campaign_experience_chd_convoy_overseer_per_turn", "faction_to_character_own_unseen", True)
E_LAW_CHD_DIPLO = ("wh3_dlc23_faction_political_diplomacy_mod_chaos_dwarfs", "faction_to_faction_own_unseen", True)
E_LAW_INFLUENCE = ("wh3_dlc23_effect_pooled_resource_conclave_influence_mod_all_sources", "faction_to_faction_own_unseen", True)
E_LAW_CORRUPT = ("wh3_main_effect_corruption_chaos_adjacent_provinces", "faction_to_province_own", True)
E_LAW_TOZ_SEAT = ("wh3_dlc23_effect_toz_chd_conclave_influence_spent_slot_claimed_mod", "faction_to_faction_own_unseen", False)
E_LAW_WOM = ("wh3_dlc23_effect_ability_wom_cost_pct_lore_of_hashut_spells", "faction_to_force_own", False)
E_LAW_COOLDOWN = ("wh3_dlc23_effect_ability_cooldown_lore_of_hashut", "faction_to_force_own", False)
E_LAW_MISCAST = ("wh_main_effect_character_stat_miscast", "faction_to_character_own", False)
E_LAW_KDAAI = ("wh3_dlc23_effect_physical_resist_chd_kdaai", "faction_to_force_own_unseen", True)
E_LAW_TEMPLE_TIME = ("wh3_dlc23_effect_building_construction_time_mod_chd_temple_of_hashut", "faction_to_region_own_unseen", False)
E_LAW_HF_COST = ("wh3_dlc23_chd_ritual_unit_cap_cost_mod_all_toz", "faction_to_faction_own_unseen", False)
E_LAW_HF_CAP = ("wh3_dlc23_effect_chd_hellforge_cap_mod_all", "faction_to_faction_own_unseen", True)
E_LAW_INF_COST = ("wh3_dlc23_effect_force_recruit_cost_chd_chaos_dwarf_infantry", "faction_to_force_own_unseen", False)
E_LAW_INF_RANK = ("wh3_dlc23_effect_force_recruit_rank_chd_chaos_dwarf_infantry", "faction_to_force_own_unseen", True)
E_LAW_ART_UPKEEP = ("wh3_dlc23_effect_upkeep_chd_artillery_warmachines", "faction_to_force_own", False)
E_LAW_DWARF_XP = ("wh3_dlc23_effect_xp_gain_increase_dwarfs", "faction_to_force_own", True)
E_LAW_HOB_UPKEEP = ("wh3_dlc23_effect_upkeep_cost_reduction_chd_labourer_hobgoblin_infantry", "faction_to_force_own_unseen", False)
E_LAW_ART_EXPL = ("wh3_dlc23_effect_force_stat_explosive_damage_chd_artillery", "faction_to_force_own_unseen", True)
E_LAW_ART_RANGE = ("wh3_dlc23_effect_force_stat_range_chd_artillery", "faction_to_force_own_unseen", True)
E_LAW_RANGED_COST = ("wh3_dlc23_effect_recruitment_cost_chd_ranged", "faction_to_province_own", False)
LAW_EFFECTS = [E_LAW_CAPTIVES, E_LAW_RUSH, E_LAW_LAB_LD, E_LAW_LAB_UPKEEP, E_LAW_LAB_RANK,
               E_LAW_RAW_USED, E_LAW_RAZE, E_LAW_SACK, E_LAW_CONVOYS, E_LAW_AMBUSH, E_LAW_VASSAL,
               E_LAW_TARIFF, E_LAW_REFINERY, E_LAW_CARGO_VALUE, E_LAW_MINES, E_LAW_GOODS,
               E_LAW_CARGO_CAP, E_LAW_OVR_RANK, E_LAW_OVR_XP, E_LAW_CHD_DIPLO, E_LAW_INFLUENCE,
               E_LAW_CORRUPT, E_LAW_TOZ_SEAT, E_LAW_WOM, E_LAW_COOLDOWN, E_LAW_MISCAST, E_LAW_KDAAI,
               E_LAW_TEMPLE_TIME, E_LAW_HF_COST, E_LAW_HF_CAP, E_LAW_INF_COST, E_LAW_INF_RANK,
               E_LAW_ART_UPKEEP, E_LAW_DWARF_XP, E_LAW_HOB_UPKEEP, E_LAW_ART_EXPL, E_LAW_ART_RANGE,
               E_LAW_RANGED_COST]
# THE DWARF EFFECTS. Every (effect, scope) pair is one a vanilla Dwarf bundle,
# building or technology ships and every flag is CA's, read out of db.pack; the
# source is named on each line. check() items 1, 2 and 15 re-read all of them.
# An effect with no shipped pair is left out.
E_DWF_OATHGOLD = ("wh2_dlc17_pooled_resource_oathgold_buildings_mod",
                  "faction_to_faction_own_unseen", True)      # bundle wh2_dlc17_lord_trait_dwf_thorek
E_DWF_CRAFT = ("wh3_dlc29_pooled_resource_oathgold_all_crafting_mod",
               "faction_to_faction_own_unseen", False)        # bundle ..._dwarf_forge_assistant, -10
E_DWF_RUNECRAFT = ("wh2_dlc17_pooled_resource_oathgold_runecrafting_mod",
                   "faction_to_faction_own_unseen", False)    # Thorek's trait, -50
# NEGATIVE IS THE BOON: fewer Settled Grudges per Age. CA's script reads it for
# a human faction when the next Age's target is set, so it pays from that Age.
E_DWF_GRUDGE_REQ = ("wh3_dlc25_effect_dwf_book_of_grudges_increase_requirements",
                    "faction_to_faction_own_unseen", False)   # building wh3_main_underdeep_dwf_grudges_1
E_DWF_GRUDGE_ORDER = ("wh_main_effect_public_order_grudges",
                      "faction_to_province_own", True)        # bundle wh3_dlc25_grudge_cycle_1
E_DWF_GROWTH = ("wh_main_effect_province_growth_tech",
                "faction_to_province_own_unseen", True)       # tech wh_main_tech_dwf_civ_3_1
E_DWF_GROWTH_GOV = ("wh_main_effect_province_growth_building",
                    "faction_to_province_own", True)          # building wh2_main_special_underway_hub_dwf_1
E_DWF_LOOT = ("wh_main_effect_force_all_campaign_post_battle_loot_mod",
              "faction_to_faction_own_unseen", True)          # bundle wh_main_faction_trait_dwarfs, -60
E_DWF_TARIFF = ("wh_main_effect_economy_trade_tariff_mod",
                "faction_to_faction_own_unseen", True)        # tech wh_main_tech_dwf_civ_6_1
E_DWF_CULTURE = ("wh_main_effect_technology_economy_gdp_mod_culture_dwarfs",
                 "faction_to_region_own_unseen", True)        # tech wh_main_tech_dwf_civ_4_1
E_DWF_SETTLER_COST = ("wh3_dlc25_effect_recruitment_cost_grudge_settlers",
                      "faction_to_force_own_unseen", False)   # tech wh_main_tech_dwf_mil_1_3, -20
E_DWF_SETTLER_SRC = ("wh3_dlc25_effect_recruitment_source_grudge_settlers",
                     "faction_to_faction_own_unseen", True)   # bundle ..._dwf_eight_peaks_secured, 2
E_DWF_WM_UPKEEP = ("wh3_dlc25_effect_resource_upkeep_cost_reduction_dwf_arty_warmachines",
                   "faction_to_force_own", False)             # Malakai's trait, -15
E_DWF_GT_DMG = ("wh2_dlc11_effect_force_stat_missile_damage_dwf_grudge_thrower_cannon_organ_gun",
                "faction_to_force_own", True)                 # building ..._dwf_blocker_machines_1
E_DWF_THUNDER = ("wh3_dlc25_effect_force_stat_range_dwf_thunderers_pirates",
                 "faction_to_force_own_unseen", True)         # tech wh_main_tech_dwf_mil_2_4
E_DWF_INF_COST = ("wh_main_effect_force_army_campaign_recruitment_cost_infantry",
                  "faction_to_force_own_unseen", False)       # tech wh_main_tech_dwf_mil_1_1, -10
E_DWF_ART_RANK = ("wh3_dlc25_effect_force_recruit_rank_dwf_arty_warmachines",
                  "faction_to_force_own", True)               # Malakai's trait, 3
# THE DWARF ENVOY'S THREE, in CA's province-bundle scopes (Dwarf edicts).
E_ENVOY_OATH = ("wh2_dlc17_pooled_resource_oathgold_buildings_mod",
                "province_to_region_own_unseen", True)        # edict wh_main_edict_dwf_high_kings_tribute
E_ENVOY_GROW = ("wh_main_effect_province_growth_commandment",
                "province_to_province_own_unseen", True)      # edict wh_main_edict_dwf_empower_the_guilds
E_ENVOY_REC = ("wh_main_effect_force_all_campaign_recruitment_cost_all",
               "province_to_province_own_unseen", False)      # edict ..._dwf_masters_of_steel_and_stone
DWF_EFFECTS = [E_DWF_OATHGOLD, E_DWF_CRAFT, E_DWF_RUNECRAFT, E_DWF_GRUDGE_REQ,
               E_DWF_GRUDGE_ORDER, E_DWF_GROWTH, E_DWF_GROWTH_GOV, E_DWF_LOOT,
               E_DWF_TARIFF, E_DWF_CULTURE, E_DWF_SETTLER_COST, E_DWF_SETTLER_SRC,
               E_DWF_WM_UPKEEP, E_DWF_GT_DMG, E_DWF_THUNDER, E_DWF_INF_COST,
               E_DWF_ART_RANK, E_ENVOY_OATH, E_ENVOY_GROW, E_ENVOY_REC]
ENVOY_EFFECT = {"ctl": E_ENVOY_CTL, "arm": E_ENVOY_ARM,
                "raw": E_ENVOY_RAW, "lab": E_ENVOY_LAB}
ENVOY_BLURB = {
    "ctl": "The court's envoy keeps order here.",
    "arm": "The court's envoy drives the forges here.",
    "raw": "The court's envoy drives the mines harder.",
    "lab": "The court's envoy keeps more Labourers alive.",
}
# ONE PAIR CA DOES NOT SHIP, KEPT ON PURPOSE. CA's only province bundle scope for
# raw materials is province_to_province_own_factionwide - every province - so the
# edict's scope is borrowed. Only the game can say it moves; check 2 refuses
# every OTHER unshipped pair.
BORROWED_SCOPES = {
    (E_ENVOY_RAW[0], E_ENVOY_RAW[1]):
        "spec 2026-09-29 section 6: the edict scope, borrowed for one province",
}

ALL_EFFECTS = [E_ARMAMENTS, E_WORKLOAD, E_RAWMAT, E_ORDER, E_GDP, E_SLAVE_ORDER,
               E_UPKEEP, E_REPLEN, E_PB_LABOUR,
               E_RESEARCH, E_MOVEMENT, E_CONSTRUCT, E_RECRUIT, E_AGENT, E_RAID,
               E_HOBGOBLIN,
               E_ENVOY_CTL, E_ENVOY_ARM, E_ENVOY_RAW, E_ENVOY_LAB] + LAW_EFFECTS + DWF_EFFECTS

# THE ZIGGURAT.
#
# Four tiers, narrow at the top: two great offices of state at the apex and five
# lesser posts along the base. Seats per tier and the strength of what a seat
# grants are the same table, so "the higher office is the better office" is true
# BY CONSTRUCTION rather than by having tuned fourteen numbers consistently.
#
# EVERY OFFICE DECLARES ITS TIER-4 MAGNITUDE and the multiplier raises it. That
# is why the numbers in OFFICES look small: the Grand Overseer's armaments base
# of 5 arrives in game as 15. Change a multiplier and the whole tier moves
# together; check() refuses a multiplier table that is not strictly decreasing,
# because a flat one would make the ziggurat a shape and nothing more.
#
# ALL FOURTEEN ARE OPEN FROM TURN 1. Nothing gates a tier.
TIER_MULT = {1: 3.0, 2: 2.0, 3: 1.5, 4: 1.0}
TIER_NAME = {1: "The Apex", 2: "The High Table", 3: "The Broad Step",
             4: "The Lower Step"}


def tier_value(tier, base):
    """A tier-4 magnitude raised to the tier that actually holds the office."""
    assert tier in TIER_MULT, "no such tier: %r" % (tier,)
    assert base > 0, "declare a positive magnitude and an intent, never a sign"
    return int(round(base * TIER_MULT[tier]))

BOON = "boon"
MALUS = "malus"


def signed_value(effect, magnitude, intent):
    """Turn a magnitude plus an intent into the signed value the engine wants.

    This exists so no data row below ever carries a raw sign. On a cost modifier
    (is_positive_value_good False) the player's BOON is a negative number, and a
    reward written +15 arrives in game as a penalty drawn in red. Here the sign
    is arithmetic, not vigilance.
    """
    assert magnitude > 0, "declare a positive magnitude and an intent, not a sign"
    assert intent in (BOON, MALUS), intent
    good = effect[2]
    positive_is_wanted = (good == (intent == BOON))
    return magnitude if positive_is_wanted else -magnitude


# WHERE A MAN IS FROM, which is not who he sits with.
#
# An origin is one trait on a lord recording where he came from, and it carries
# no mechanical weight at all; what he WANTS is his background, and his
# background is what seats him in a party. See PARTIES.
#
# Faction keys are from factions_tables/!!_cr_oldworld_new_factions via
# docs/MOD_STRUCTURE.md - a typo here fails silently forever, so check() greps
# them back out of the staged source. A faction key of None is a PLACE rather
# than a house: where a lord who was never confederated in from anywhere was
# born, and the only kind of origin most of a campaign's lords will ever have.
ORIGINS = [
    # slug,        faction key,                        display
    ("khorakk",    "cr_chd_house_of_khorakk",          "the House of Khorakk"),
    ("uzkulak",    "cr_chd_warfleet_of_uzkulak",       "the Warfleet of Uzkulak"),
    ("artificers", "cr_chd_snakebeards_artificers",    "Snakebeard's Artificers"),
    ("fists",      "cr_chd_fists_of_hashut",           "the Fists of Hashut"),
    ("horns",      "cr_chd_horns_of_hashut",           "the Horns of Hashut"),
    ("baal",       "cr_chd_house_of_baal",             "the House of Baal"),
    ("azeros",     "cr_chd_house_of_azeros",           "the House of Azeros"),
    ("bzaark",     "cr_chd_house_of_bzaark",           "the House of Bzaark"),
    ("blackdwarf", "cr_chd_slaves_of_the_black_dwarf", "the Slaves of the Black Dwarf"),
    ("kraken",     "cr_chd_black_kraken_armada",       "the Black Kraken Armada"),
    ("conclave",   "wh3_dlc23_chd_conclave",           "the Servants of the Conclave"),
    ("astragoth",  "wh3_dlc23_chd_astragoth",          "the Disciples of Hashut"),
    ("azgorh",     "wh3_dlc23_chd_legion_of_azgorh",   "the Legion of Azgorh"),
    ("zhatan",     "wh3_dlc23_chd_zhatan",             "the Warhost of Zharr"),
    ("skullstack", "cr_chd_skullstack",                "the Uzkul Mingol Company"),
    ("zharrduk",   "wh3_dlc23_chd_minor_faction",      "the Overlords of Zharrduk"),
    # AND THE PLACES. A lord raised in your own lands came from none of the
    # above, and before these existed every such man was stamped with his
    # faction's house and the column read the same word for all of them.
    ("zharr",      None,                               "Zharr-Naggrund"),
    ("plain",      None,                               "the Plain of Zharr"),
    ("gorgoth",    None,                               "the Tower of Gorgoth"),
    ("stump",      None,                               "Daemon's Stump"),
    ("zornuzkul",  None,                               "Zorn Uzkul"),
    ("gash",       None,                               "Gash Kadrak"),
    ("mines",      None,                               "the Mines of Mingol"),
    ("wastes",     None,                               "the Howling Wastes"),
]

# Chaos Dwarf factions that are deliberately NOT origins, each one named rather
# than pattern-matched: a rule like "anything with rebels in the key" is a rule
# that quietly swallows the next real faction CA adds.
#
#   _rebels          the rebellion faction every culture has - and since the
#                    secession, the faction a broken-away party BECOMES
#   _qb1 _qb2 _qb3   quest-battle factions, never on a campaign map
#   _invasion        the DLC25 scripted invasion
#   _chaos_dwarfs    CA's generic entry, which flies the Legion of Azgorh's own
#                    flag and leads nothing
NOT_AN_ORIGIN = {
    "wh3_dlc23_chd_chaos_dwarfs",
    "wh3_dlc23_chd_chaos_dwarfs_rebels",
    "wh3_dlc23_chd_chaos_dwarfs_qb1",
    "wh3_dlc23_chd_chaos_dwarfs_qb2",
    "wh3_dlc23_chd_chaos_dwarfs_qb3",
    "wh3_dlc25_chd_chaos_dwarfs_invasion",
}

# WHO SITS IN THE COURT. A party is an interest, not a family - the priesthood,
# the forge guilds, the slavers - and a campaign organises only two to four of
# them. The crown is always seated, is the player's own faction, and takes its
# NAME from that faction rather than from this table; every other party's name
# is rolled at campaign start out of the parts in the model Lua, which is why
# there is a display here at all and why it is generic.
#
# gov_* is the flavour a governor of that party adds on top of the base bundle.
# It moved here from the houses, and that is the point of the whole change:
# which INTEREST holds a province is a decision the player makes, where which
# family held it was a consequence of who they had conquered.
PARTIES = [
    # slug,      display (generic - a rolled name replaces it),  gov effect,  mag
    ("crown",    "The Crown",                                    E_ORDER,     4),
    ("temple",   "The Priesthood",                               E_SLAVE_ORDER, 3),
    ("forge",    "The Forge",                                    E_ARMAMENTS, 6),
    ("chain",    "The Chain",                                    E_PB_LABOUR, 10),
    ("legion",   "The Legion",                                   E_UPKEEP,    6),
    ("ledger",   "The Ledger",                                   E_GDP,       6),
    ("tower",    "The Tower",                                    E_RESEARCH,  5),
    ("road",     "The Road",                                     E_MOVEMENT,  4),
    ("hearth",   "The Hearth",                                   E_REPLEN,    8),
]

# The crown is not rolled and cannot secede: it is the player.
CROWN = "crown"

# A MEMBER TRAIT'S FLAVOUR, ONE PER PARTY, so 140 member traits do not all read
# alike. A party's six rolled names share its line; "confed" is a house that came over by confederation.
MEMBER_FLAVOUR = {
    "crown":  "He answers to you, and the court knows it.",
    "confed": "His house came over whole and still keeps its own counsel.",
    "temple": "He votes the way the priests say Hashut would.",
    "forge":  "He weighs every law by what it does to the furnaces.",
    "chain":  "His party wants more slaves and fewer questions.",
    "legion": "He speaks for the army. The army is listening.",
    "ledger": "He knows what every vote at court is worth in gold.",
    "tower":  "He sides with the sorcerers, who forget no slight.",
    "road":   "His party lives off the convoys and wants the roads open.",
    "hearth": "He speaks for the home kilns and the families that feed them.",
}
DWF_MEMBER_FLAVOUR = {
    "crown":  "He swore to the throne and means to keep his oath.",
    "confed": "His hold joined yours by oath. It keeps its own ways.",
    "temple": "He reminds the king what the ancestors expect.",
    "forge":  "He weighs every law by what it does to the forges.",
    "chain":  "He speaks for the miners, who dig deeper every year.",
    "legion": "He speaks for the clan warriors, who settle grudges with axes.",
    "ledger": "He knows what every hold owes, to the last coin.",
    "tower":  "He keeps the runes' secrets, even from the king.",
    "road":   "He keeps the Underway open, one tunnel at a time.",
    "hearth": "He speaks for the families who keep the holds fed and warm.",
}

PARTY_GOV_BLURB = {
    "crown":   "Your retainers answer for this province.",
    "temple":  "The temples take the province in hand and it grows for Hashut.",
    "forge":   "Forge-guild overseers run the province like a workshop floor.",
    "chain":   "The slavers work the province to the bone and account for every hour.",
    "legion":  "A garrison town under a soldier costs less to keep than it should.",
    "ledger":  "Brokers keep the province's books, and the tribute arrives whole.",
    "tower":   "Tower clerks read everything that passes through, and pass it on.",
    "road":    "The caravan men keep the roads open whatever the season.",
    "hearth":  "The old clans hold it, and men come back to the muster faster.",
}

# WHAT A MAN IS, and therefore who he sits with. Every lord carries exactly one
# of these. A background belongs to one party, and that is the entire membership
# rule - there is no separate party trait and nothing deals men out. A man whose
# party is not organised this campaign falls back to the crown, which is also
# what happens to a party's men after it secedes.
BACKGROUNDS = {
    "crown":  [("household",  "Household Guard"),
               ("blood",      "Blood of the Line"),
               ("sworn",      "Sworn Hand")],
    "temple": [("acolyte",    "Temple Acolyte"),
               ("ashpriest",  "Ash-Priest"),
               ("taurukh",    "Bull Centaur Taurukh")],
    "forge":  [("daemonsmith", "Daemonsmith"),
               ("gunnery",    "Gunnery Master"),
               ("furnace",    "Furnace Master")],
    "chain":  [("overseer",   "Overseer of the Pits"),
               ("driver",     "Slave-Driver"),
               ("wrangler",   "Hobgoblin Wrangler")],
    "legion": [("immortal",   "Immortal of Zharr"),
               ("infernal",   "Infernal Guard"),
               ("siege",      "Siege Captain")],
    "ledger": [("broker",     "Broker of Zharr"),
               ("tribute",    "Tribute-Taker"),
               ("harbour",    "Harbourmaster")],
    "tower":  [("apprentice", "Sorcerer's Apprentice"),
               ("clerk",      "Clerk of the Tower"),
               ("omens",      "Reader of Omens")],
    "road":   [("caravan",    "Caravan Master"),
               ("roadwarden", "Road Warden"),
               ("pathfinder", "Walker of the Wastes")],
    "hearth": [("ashfarmer",  "Ash-Farmer"),
               ("kiln",       "Kiln-Keeper"),
               ("elder",      "Clan Elder")],
}

BG_COLOUR = {
    "household":  "He stood at your door before he ever stood in a battle line.",
    "blood":      "He knows how close he is to the throne.",
    "sworn":      "He swore to the throne in person. He keeps his word.",
    "acolyte":    "Temple-raised. He still says the words under his breath.",
    "ashpriest":  "He has burned enough offerings to have stopped smelling them.",
    "taurukh":    "Half bull and wholly zealot, like all his kind.",
    "daemonsmith": "He talks to the daemons he binds. Sometimes they answer.",
    "gunnery":    "He can tell you what a barrel will do before it does it.",
    "furnace":    "Twenty years at a furnace mouth. His eyes are not what they were.",
    "overseer":   "He counts a work gang the way other men count coin.",
    "driver":     "He laughs while he works the lash.",
    "wrangler":   "He handles hobgoblins, which means he trusts nothing that moves.",
    "immortal":   "He has stood in the front rank and expects the courtesy of it.",
    "infernal":   "Masked so long that the face underneath is a rumour.",
    "siege":      "He has taken walls down for a living and finds doors insulting.",
    "broker":     "He prices everything, including this conversation.",
    "tribute":    "He collects from those who cannot pay. Coin is only one way.",
    "harbour":    "He knows what every hull on the Sea of Dread is carrying.",
    "apprentice": "Never finished the Tower. Nobody asks him why.",
    "clerk":      "He has read more of the Tower's word than he was meant to.",
    "omens":      "He reads the sky and tells you only what you need to hear.",
    "caravan":    "He has crossed the Wastes enough times to have stopped counting.",
    "roadwarden": "He keeps a road open by making the alternative worse.",
    "pathfinder": "He goes out further than anyone sensible and comes back.",
    "ashfarmer":  "He grows food in ash. His clan doubts it until they eat.",
    "kiln":       "He smells of slag and can judge a firing by the sound.",
    "elder":      "His clan is small. He remembers every slight against it.",
}

# WHAT THE TOOLTIP SAYS AN OFFICE DOES.
#
# The office trait is a MARKER: it records who holds the post, and the mechanical
# effect is delivered by the faction-wide office bundle. That is not a shortcut,
# it is the only thing that works. Measured across all 60,356 (effect, scope)
# pairs vanilla ships in trait_level_effects, effect_bundles_to_effects_junctions,
# building_effects_junction, character_skill_level_to_effects_junctions and
# technology_effects_junction:
#
#   E_WORKLOAD, E_ORDER, E_PB_LABOUR   no character-reaching scope AT ALL
#   E_ARMAMENTS                        character_to_province_own only - one
#                                      province, never the faction
#   E_GDP, E_UPKEEP, E_REPLEN          do have factionwide character scopes
#
# So four of the six offices simply cannot carry their own effect on a trait, and
# a mixed scheme would double-apply the other two unless their bundles were also
# split out. The bundle stays the carrier.
#
# What WAS wrong is that the tooltip said nothing, so an office looked inert. The
# text below is CA's own wording for each effect, pinned here and re-read from
# local_en.pack by check(), which refuses on any drift. The value is substituted
# from the same signed_value() the data rows use, so the tooltip cannot disagree
# with the effect it describes.
EFFECT_TEXT = {
    E_ENVOY_CTL[0]: "Control: %+n",
    E_ENVOY_LAB[0]: "%n% Labour loss per turn (minimum of 5)",
    E_ARMAMENTS[0]: "Armaments output: %+n%",
    E_WORKLOAD[0]:  "Workload requirement for Raw Materials: %+n%",
    # CA writes this one as {{tr:public_order_effect}}, which resolves to
    # "Control". Resolved HERE rather than shipped as a token, because a nested
    # {{tr:}} that does not resolve draws its own braces on screen.
    E_ORDER[0]:     "Control: %+n",
    E_GDP[0]:       "Income from all buildings: %+n%",
    E_UPKEEP[0]:    "Upkeep: %+n%",
    E_REPLEN[0]:    "Casualty replenishment rate: %+n%",
    E_PB_LABOUR[0]: "Labour gained post-battle: %+n%",
    E_SLAVE_ORDER[0]: "Control: %+n",
    E_RAWMAT[0]:    "Raw Materials output: %+n%",
    # CA writes this one as {{tr:effect_technology_research_points_description}}.
    # Resolved here for the same reason E_ORDER is - an unresolved nested token
    # draws its own braces on screen.
    E_RESEARCH[0]:  "Research rate: %+n",
    E_MOVEMENT[0]:  "Campaign movement range: %+n%",
    E_CONSTRUCT[0]: "Construction cost: %+n% for all buildings",
    E_RECRUIT[0]:   "Recruitment cost: %+n%",
    E_AGENT[0]:     "Hero action success chance: %+n%",
    E_RAID[0]:      "Income from raiding: %+n%",
    E_HOBGOBLIN[0]: "Upkeep: %+n% for Hobgoblin units",
    E_LAW_CAPTIVES[0]: "Casualties captured post-battle: %+n%",
    E_LAW_RUSH[0]: "Rush Construction Labour cost: %+n%",
    E_LAW_LAB_LD[0]: "Leadership: %+n for Labourer units",
    E_LAW_LAB_UPKEEP[0]: "Upkeep: %+n% for Labourers units",
    E_LAW_LAB_RANK[0]: "Recruit rank: %+n for Labourer units",
    E_LAW_RAW_USED[0]: "Raw Materials consumed per turn by buildings: %+n%",
    E_LAW_RAZE[0]: "Income from razing settlements: %+n%",
    E_LAW_SACK[0]: "Income from sacking settlements: %+n%",
    E_LAW_CONVOYS[0]: "Maximum number of active Convoys: %+n",
    E_LAW_AMBUSH[0]: "Chance of Caravan intercept battle being an ambush: %+n%",
    E_LAW_VASSAL[0]: "Tribute from [[img:icon_vassal]][[/img]]vassals: %+n%",
    E_LAW_TARIFF[0]: "Income from trade tariffs: %+n% for every completed Convoy route",
    E_LAW_REFINERY[0]: "Income from Refinery buildings: %+n%",
    E_LAW_CARGO_VALUE[0]: "Sale value of cargo: %+n%",
    E_LAW_MINES[0]: "Income from Iron Mines, Gold Mines and Stone Quarries: %+n%",
    E_LAW_GOODS[0]: "Tradable resources produced: %+n%",
    E_LAW_CARGO_CAP[0]: "Maximum Caravan cargo capacity: %+n%",
    E_LAW_OVR_RANK[0]: "Lord recruit rank: %+n for Convoy Overseer",
    E_LAW_OVR_XP[0]: "Experience per turn: %+n for Convoy Overseers",
    E_LAW_CHD_DIPLO[0]: "Diplomatic relations: %+n with Chaos Dwarfs",
    E_LAW_INFLUENCE[0]: "Conclave Influence gained from all sources: %+n% ",
    E_LAW_CORRUPT[0]: "Chaos Undivided corruption in adjacent provinces: %+n",
    E_LAW_TOZ_SEAT[0]: "Conclave Influence cost for Tower of Zharr Seats: %+n%",
    E_LAW_WOM[0]: "Winds of Magic cost: %+n% for Lore of Hashut spells",
    E_LAW_COOLDOWN[0]: "Cooldown: %+n% to Lore of Hashut spells",
    E_LAW_MISCAST[0]: "Miscast base chance: %+n%",
    E_LAW_KDAAI[0]: "Physical resistance: %n% for all K'daai units",
    E_LAW_TEMPLE_TIME[0]: "Construction time: %+n for Temple of Hashut buildings",
    E_LAW_HF_COST[0]: "Armaments cost: %+n% for all unit capacity upgrades in the Hell-Forge",
    E_LAW_HF_CAP[0]: "Maximum active Hell-Forge Forgecraft Options: %+n",
    E_LAW_INF_COST[0]: "Recruitment cost: %+n% for Chaos Dwarf Infantry units",
    E_LAW_INF_RANK[0]: "Recruit rank: %+n for Chaos Dwarf Infantry",
    E_LAW_ART_UPKEEP[0]: "Upkeep: %+n% for Artillery and War Machine units",
    E_LAW_DWARF_XP[0]: "Double experience gain for units when fighting against Dwarfs",
    E_LAW_HOB_UPKEEP[0]: "Upkeep: %+n% for Labourers and Hobgoblin Infantry units",
    E_LAW_ART_EXPL[0]: "Explosive missile damage: %+n% for Iron Daemon and Artillery units",
    E_LAW_ART_RANGE[0]: "Range: %+n% for Iron Daemon and Artillery units",
    E_LAW_RANGED_COST[0]: "Recruitment cost: %+n% for all Missile Infantry, Artillery and War Machine units",
    # THE DWARFS. E_ENVOY_OATH and E_ENVOY_REC share
    # their keys with E_DWF_OATHGOLD and E_RECRUIT, so they need no line.
    E_DWF_OATHGOLD[0]: "Oathgold from buildings: %+n%",
    E_DWF_CRAFT[0]: "Oathgold cost for crafting in the Forge: %+n%",
    E_DWF_RUNECRAFT[0]: "Oathgold cost for crafting Runes: %+n%",
    E_DWF_GRUDGE_REQ[0]: "Increases the number of Settled Grudges required for each Age of Reckoning by %n%",
    E_DWF_GRUDGE_ORDER[0]: "Control: %+n",
    E_DWF_GROWTH[0]: "Growth: %+n",
    E_DWF_GROWTH_GOV[0]: "Growth: %+n",
    E_ENVOY_GROW[0]: "Growth: %+n",
    E_DWF_LOOT[0]: "Income from post-battle loot: %+n%",
    E_DWF_TARIFF[0]: "Income from trade tariffs: %+n%",
    E_DWF_CULTURE[0]: "Income from Gem Cutters and Obsidian Quarries: %+n%",
    E_DWF_SETTLER_COST[0]: "Recruitment cost: %+n% for Grudge Settler units",
    E_DWF_SETTLER_SRC[0]: "%+n Grudge Settler unit capacity per army",
    E_DWF_WM_UPKEEP[0]: "Upkeep: %+n% for Artillery and Flying War Machine units",
    E_DWF_GT_DMG[0]: "Missile strength: %+n% for Bolt Throwers, Grudge Thrower, Cannon, Goblin Hewer and Organ Gun units",
    E_DWF_THUNDER[0]: "Range: %+n% for Thunderer and Slayer Pirate units",
    E_DWF_INF_COST[0]: "Recruitment cost: %+n% for Infantry units",
    E_DWF_ART_RANK[0]: "Recruit rank: %+n for Artillery and Flying War Machine units",
}
# THE CARD'S OWN WORDING, and the only place in this mod that does not use CA's.
#
# An office card is 364px wide and its effect line gets 298 of them; CA's full
# phrasing puts the Grand Overseer's two effects at 331px, which "Never split"
# would cut off mid-word with no warning. These are the same effects with the
# noun phrases trimmed - the VALUE is still computed by signed_value from the
# same table, so a short label can only ever be wrong about wording, never about
# a number. The trait tooltip and the Faction Effects panel still read CA's own
# sentence; check() refuses an effect that has no short form.
EFFECT_SHORT = {
    E_ENVOY_CTL[0]: "Control",
    E_ENVOY_LAB[0]: "Labour loss",
    E_ARMAMENTS[0]: "Armaments",
    E_WORKLOAD[0]:  "Workload",
    E_ORDER[0]:     "Control",
    E_GDP[0]:       "Building income",
    E_UPKEEP[0]:    "Upkeep",
    E_REPLEN[0]:    "Replenishment",
    E_PB_LABOUR[0]: "Post-battle Labour",
    E_SLAVE_ORDER[0]: "Control",
    E_RAWMAT[0]:    "Raw Materials",
    E_RESEARCH[0]:  "Research",
    E_MOVEMENT[0]:  "Movement range",
    E_CONSTRUCT[0]: "Construction cost",
    E_RECRUIT[0]:   "Recruitment cost",
    E_AGENT[0]:     "Hero success",
    E_RAID[0]:      "Raiding income",
    E_HOBGOBLIN[0]: "Hobgoblin upkeep",
    E_LAW_CAPTIVES[0]: "Captives",
    E_LAW_RUSH[0]: "Rush cost",
    E_LAW_LAB_LD[0]: "Labourer leadership",
    E_LAW_LAB_UPKEEP[0]: "Labourer upkeep",
    E_LAW_LAB_RANK[0]: "Labourer rank",
    E_LAW_RAW_USED[0]: "Raw Materials used",
    E_LAW_RAZE[0]: "Razing income",
    E_LAW_SACK[0]: "Sacking income",
    E_LAW_CONVOYS[0]: "Active Convoys",
    E_LAW_AMBUSH[0]: "Convoy ambush",
    E_LAW_VASSAL[0]: "Vassal tribute",
    E_LAW_TARIFF[0]: "Convoy tariffs",
    E_LAW_REFINERY[0]: "Refinery income",
    E_LAW_CARGO_VALUE[0]: "Cargo value",
    E_LAW_MINES[0]: "Mine income",
    E_LAW_GOODS[0]: "Trade goods",
    E_LAW_CARGO_CAP[0]: "Cargo capacity",
    E_LAW_OVR_RANK[0]: "Overseer rank",
    E_LAW_OVR_XP[0]: "Overseer XP a turn",
    E_LAW_CHD_DIPLO[0]: "Chaos Dwarf ties",
    E_LAW_INFLUENCE[0]: "Conclave Influence",
    E_LAW_CORRUPT[0]: "Nearby corruption",
    E_LAW_TOZ_SEAT[0]: "Tower seat cost",
    E_LAW_WOM[0]: "Hashut spell cost",
    E_LAW_COOLDOWN[0]: "Hashut cooldown",
    E_LAW_MISCAST[0]: "Miscast",
    E_LAW_KDAAI[0]: "K'daai resistance",
    E_LAW_TEMPLE_TIME[0]: "Temple build time",
    E_LAW_HF_COST[0]: "Forge upgrade cost",
    E_LAW_HF_CAP[0]: "Forgecraft options",
    E_LAW_INF_COST[0]: "Infantry cost",
    E_LAW_INF_RANK[0]: "Infantry rank",
    E_LAW_ART_UPKEEP[0]: "Artillery upkeep",
    E_LAW_DWARF_XP[0]: "XP vs Dwarfs",
    E_LAW_HOB_UPKEEP[0]: "Labour upkeep",
    E_LAW_ART_EXPL[0]: "Artillery explosive",
    E_LAW_ART_RANGE[0]: "Artillery range",
    E_LAW_RANGED_COST[0]: "Ranged cost",
    E_DWF_OATHGOLD[0]: "Oathgold",
    E_DWF_CRAFT[0]: "Forge Oathgold cost",
    E_DWF_RUNECRAFT[0]: "Rune Oathgold cost",
    E_DWF_GRUDGE_REQ[0]: "Grudges needed",
    E_DWF_GRUDGE_ORDER[0]: "Control",
    E_DWF_GROWTH[0]: "Growth",
    E_DWF_GROWTH_GOV[0]: "Growth",
    E_ENVOY_GROW[0]: "Growth",
    E_DWF_LOOT[0]: "Post-battle loot",
    E_DWF_TARIFF[0]: "Trade tariffs",
    E_DWF_CULTURE[0]: "Gem cutter income",
    E_DWF_SETTLER_COST[0]: "Grudge Settler cost",
    E_DWF_SETTLER_SRC[0]: "Grudge Settler slots",
    E_DWF_WM_UPKEEP[0]: "War machine upkeep",
    E_DWF_GT_DMG[0]: "Artillery damage",
    E_DWF_THUNDER[0]: "Thunderer range",
    E_DWF_INF_COST[0]: "Infantry cost",
    E_DWF_ART_RANK[0]: "Artillery rank",
}

# Which of them are percentages, so the short line does not put a % on Control
# or Growth, which are flat numbers.
EFFECT_PERCENT = {
    E_ENVOY_CTL[0]: False,
    E_ORDER[0]: False,
    E_SLAVE_ORDER[0]: False,
    E_RESEARCH[0]: False,
    E_LAW_LAB_LD[0]: False, E_LAW_LAB_RANK[0]: False, E_LAW_CONVOYS[0]: False,
    E_LAW_OVR_RANK[0]: False, E_LAW_OVR_XP[0]: False, E_LAW_CHD_DIPLO[0]: False,
    E_LAW_CORRUPT[0]: False, E_LAW_TEMPLE_TIME[0]: False, E_LAW_HF_CAP[0]: False,
    E_LAW_INF_RANK[0]: False,
    E_DWF_GRUDGE_ORDER[0]: False, E_DWF_GROWTH[0]: False, E_DWF_GROWTH_GOV[0]: False,
    E_ENVOY_GROW[0]: False, E_DWF_SETTLER_SRC[0]: False, E_DWF_ART_RANK[0]: False,
}


def effect_short(effect, magnitude, intent):
    """One card line: a trimmed label and this row's signed value."""
    label = EFFECT_SHORT[effect[0]]
    value = signed_value(effect, magnitude, intent)
    suffix = "%" if EFFECT_PERCENT.get(effect[0], True) else ""
    return "%s %+d%s" % (label, value, suffix)


# The {{tr:}} tokens resolved above, so check() can prove the resolution rather
# than trust it. ui_text_replacements_localised_text_<key>.
EFFECT_TEXT_TR = {
    E_ENVOY_CTL[0]: ("public_order_effect", "Control"),
    E_ORDER[0]: ("public_order_effect", "Control"),
    E_SLAVE_ORDER[0]: ("public_order_effect", "Control"),
    E_RESEARCH[0]: ("effect_technology_research_points_description",
                    "Research rate"),
    E_LAW_AMBUSH[0]: ("wh3_campaign_notification_caravan", "Caravan"),
    E_LAW_CARGO_CAP[0]: ("wh3_campaign_notification_caravan", "Caravan"),
    E_DWF_GRUDGE_ORDER[0]: ("public_order_effect", "Control"),
}


def effect_line(effect, magnitude, intent):
    """One tooltip line: CA's wording with this row's signed value in it. CA
    writes %+n for a signed value and, on a few effects, %n for a bare one."""
    text = EFFECT_TEXT[effect[0]]
    v = signed_value(effect, magnitude, intent)
    return text.replace("%+n", "%+d" % v).replace("%n", "%d" % v)


# The six offices.
#
# affinity is the house that considers the office theirs. Appointing that house's
# man doubles its standing gain; appointing an outsider costs the affine house
# loyalty. That one field is the whole Rome 2 squeeze.
#
# NOTE ON THE SLAVE PITS: Chaos Dwarfs have no "slaves" pooled resource. The
# vanilla set is labour, armaments, raw_materials, workload, efficiency and
# conclave_influence (read from pooled_resources.json). Slaves are flavour; the
# mechanic is post-battle Labour.
OFFICES = [
    {
        "slug": "priest",
        "name": "High Priest of Hashut",
        "affinity": "temple",
        "tier": 1,
        "blurb": "The Father of Darkness is served loudly, and the people are quiet.",
        "vacant_blurb": "The temples stand unattended and the sermons go unsaid.",
        "effects": [(E_ORDER, 2, BOON), (E_GDP, 4, BOON)],
        "vacancy": [(E_ORDER, 2, MALUS)],
    },
    {
        "slug": "forge",
        "name": "Grand Overseer of the Forge",
        "affinity": "forge",
        "tier": 1,
        "blurb": "The forges of Zharr-Naggrund answer to one voice, and it is his.",
        "vacant_blurb": "No hand guides the forges. Output slips and no one is blamed.",
        "effects": [(E_ARMAMENTS, 5, BOON), (E_RAWMAT, 4, BOON)],
        "vacancy": [(E_ARMAMENTS, 2, MALUS)],
    },
    {
        "slug": "ledger",
        "name": "Keeper of the Black Ledger",
        "affinity": "ledger",
        "tier": 2,
        "blurb": "Every debt in the Dark Lands is written down, and he holds the book.",
        "vacant_blurb": "The books go unbalanced and the tribute arrives light.",
        "effects": [(E_GDP, 6, BOON)],
        "vacancy": [(E_GDP, 3, MALUS)],
    },
    {
        "slug": "warden",
        "name": "Warden of the Marches",
        "affinity": "legion",
        "tier": 2,
        "blurb": "The outer holds are watched, and the watchers are paid on time.",
        "vacant_blurb": "The marches keep themselves, badly and at their own expense.",
        "effects": [(E_UPKEEP, 5, BOON), (E_REPLEN, 5, BOON)],
        "vacancy": [(E_ORDER, 2, MALUS)],
    },
    {
        "slug": "hand",
        "name": "Hand of the Tower",
        "affinity": "tower",
        "tier": 2,
        "blurb": "He carries the Sorcerer-Prophets' word down the Tower, unaltered.",
        "vacant_blurb": "The Tower's word arrives late, and altered on the way.",
        "effects": [(E_RESEARCH, 5, BOON)],
        "vacancy": [(E_RESEARCH, 2, MALUS)],
    },
    {
        "slug": "chains",
        "name": "Keeper of the Chains",
        "affinity": "chain",
        "tier": 3,
        "blurb": "He counts the work gangs, and the gangs know he counts them.",
        "vacant_blurb": "Uncounted, the work gangs move at their own pace.",
        "effects": [(E_WORKLOAD, 10, BOON)],
        "vacancy": [(E_WORKLOAD, 4, MALUS)],
    },
    {
        "slug": "pits",
        "name": "Master of the Pits",
        "affinity": "chain",
        "tier": 3,
        "blurb": "What comes back from a battlefield is his to sort and his to sell.",
        "vacant_blurb": "The spoils are picked over by whoever reaches them first.",
        "effects": [(E_PB_LABOUR, 16, BOON)],
        "vacancy": [(E_PB_LABOUR, 7, MALUS)],
    },
    {
        "slug": "quarry",
        "name": "Master of the Quarries",
        "affinity": "forge",
        "tier": 3,
        "blurb": "The black rock comes up faster when somebody is counting the carts.",
        "vacant_blurb": "The quarries run at the pace of the laziest overseer in them.",
        "effects": [(E_RAWMAT, 6, BOON)],
        "vacancy": [(E_RAWMAT, 3, MALUS)],
    },
    {
        "slug": "roads",
        "name": "Warden of the Caravan Roads",
        "affinity": "road",
        "tier": 3,
        "blurb": "The roads out of Zharr are his, and they are quicker than they were.",
        "vacant_blurb": "The roads are unwatched, and the caravans take the long way round.",
        "effects": [(E_MOVEMENT, 4, BOON)],
        "vacancy": [(E_MOVEMENT, 2, MALUS)],
    },
    {
        "slug": "kilns",
        "name": "Keeper of the Kilns",
        "affinity": "hearth",
        "tier": 4,
        "blurb": "Brick and slag leave his kilns cheaper than anyone can explain.",
        "vacant_blurb": "The kilns burn on unwatched, and the bill still arrives.",
        "effects": [(E_CONSTRUCT, 8, BOON)],
        "vacancy": [(E_CONSTRUCT, 4, MALUS)],
    },
    {
        "slug": "fields",
        "name": "Steward of the Ash Fields",
        "affinity": "hearth",
        "tier": 4,
        "blurb": "The hobgoblin tribes that work the ash fields march cheap for whoever feeds them.",
        "vacant_blurb": "The ash fields go untended, and the hobgoblins want more to march.",
        "effects": [(E_HOBGOBLIN, 15, BOON)],
        "vacancy": [(E_HOBGOBLIN, 5, MALUS)],
    },
    {
        "slug": "scribes",
        "name": "Master of the Scribes",
        "affinity": "tower",
        "tier": 4,
        "blurb": "His clerks know which door to knock on, and when.",
        "vacant_blurb": "The clerks knock on the wrong doors and are turned away.",
        "effects": [(E_AGENT, 8, BOON)],
        "vacancy": [(E_AGENT, 4, MALUS)],
    },
    {
        "slug": "muster",
        "name": "Warden of the Muster",
        "affinity": "legion",
        "tier": 4,
        "blurb": "He knows what a warrior costs, and he pays no more than that.",
        "vacant_blurb": "Every company is hired at whatever it asks for.",
        "effects": [(E_RECRUIT, 8, BOON)],
        "vacancy": [(E_RECRUIT, 4, MALUS)],
    },
    {
        "slug": "banners",
        "name": "Keeper of the Banners",
        "affinity": "legion",
        "tier": 4,
        "blurb": "Raiding is an accounting exercise, and he keeps the account.",
        "vacant_blurb": "The raiders keep their own accounts, and most of the takings.",
        "effects": [(E_RAID, 10, BOON)],
        "vacancy": [(E_RAID, 5, MALUS)],
    },
]

# Traits.
#
# A character's house allegiance and his office are both traits. Save state stays
# the source of truth; the trait is derived, re-added by a reconcile pass at first
# tick. A trait rather than save state alone because it survives on its own, it
# shows on the character panel where a player will look for it, and the game state
# itself then records who holds what.
#
# FOUR tables, not two: character_traits, character_trait_levels, trait_info and
# (optionally) trait_level_effects. trait_info is a single-column table with one
# row per trait - vanilla has 744 of each - and it is exactly the kind of table a
# trace outward never reaches.
#
# ponytail: no trait_level_effects rows. The office's mechanical effect is already
# delivered by the faction-wide office bundle, and a personal effect would mean
# verifying a whole second scope vocabulary (character_to_character_own,
# general_to_force_own) for no mechanical need. 178 of vanilla's 979 trait levels
# carry zero effects, so a marker trait is legal and ordinary. Add them if a
# personal buff is ever wanted.
#
# Single-level traits use the trait key as the level key - CA's own convention,
# read off wh2_dlc09_dummy_trait_dynasty_1.

# EACH KIND OF TRAIT WEARS ITS OWN PICTURE. character_traits.icon names a
# trait_categories row; CA's chaos_dwarfs category is the Chaos Dwarf helmet
# the Trait Gained card blows up into a face. A category is
# two columns, a key and a picture path, and CA points its own at effect-bundle
# art (loyalty, harkon_fractured), so one row of our own per picture is all it
# takes. check() holds every path to a picture that ships.
TRAIT_CATS = {
    # WHERE HE WAS BORN is a place, not a house: eight origins are places, and
    # the cr_chd_* houses' flags ship only with the mod that adds them.
    "derpy_ic_cat_origin": "ui/campaign ui/effect_bundles/settlement.png",
    # A CONFEDERATE PARTY, named by the faction it was.
    "derpy_ic_cat_confed": "ui/campaign ui/effect_bundles/confederation.png",
    "derpy_ic_cat_office": "ui/skins/default/icon_offices.png",
    # The panel's own influence picture (ICUI.COST_ICON).
    "derpy_ic_cat_standing": "ui/skins/default/icon_secure_loyalty.png",
    "derpy_ic_cat_ambition": "ui/campaign ui/effect_bundles/chd_conclave_influence.png",
}


def party_cat(party):
    """A party's own category: its sigil, the one its card and plate wear."""
    return "derpy_ic_cat_party_" + party


for _p in PARTIES:
    TRAIT_CATS[party_cat(_p[0])] = "ui/derpy_ic/party_sigil_%s.png" % _p[0]


def standing_trait_key(tier):
    """The band trait for a man who clears tier `tier`; 0 clears nothing."""
    return "derpy_ic_standing_%d" % tier


# What the band is CALLED, and what it tells the player. Both are about a SEAT
# rather than a number, because the number is already on the court panel and
# what a player wants off a character card is "can he take the job".
def _tier_lc(tier):
    """A tier's name mid-sentence: "the Lower Step", not "The Lower Step"."""
    return "the" + TIER_NAME[tier][3:]


STANDING_BAND = {
    0: ("Unproven at Court",
        "The Iron Court has yet to learn his name.",
        "Too little influence for any seat at court. Influence is earned by "
        "winning battles, taking settlements, gaining ranks and holding a seat."),
    4: ("Noticed at Court",
        "The court has begun to say his name.",
        "Has enough influence for a seat on %s, the lowest tier." % _tier_lc(4)),
    3: ("Spoken For at Court",
        "A party has spoken for him at court.",
        "Has enough influence for a seat on %s." % _tier_lc(3)),
    2: ("Weighed at Court",
        "The old ones have stopped talking over him when he speaks.",
        "Has enough influence for a seat at %s." % _tier_lc(2)),
    1: ("Fit for the Apex",
        "There is no room above him but Hashut's own.",
        "Has enough influence for any seat, %s included." % _tier_lc(1)),
}

AMBITION_BANDS = {
    "cautious": ("Cautious", "He keeps his head down and his claims modest.",
                 "His influence counts 25% less towards his party's."),
    "steady": ("Steady", "He asks for what he is owed, and no more.",
               "His influence counts as usual towards his party's."),
    "ambitious": ("Ambitious", "Every honour becomes another claim on the Iron Court.",
                  "His influence counts 25% more towards his party's."),
}

ORIGIN_COLOUR = {
    "conclave":     "He names the tower that taught him before he gives his own name.",
    "astragoth":    "Old blood and old rites. His back has never bent.",
    "azgorh":       "Azgorh's forges left their smell in his clothes.",
    "zhatan":       "Raised in the Warhost, where a man is his last campaign.",
    "skullstack":   "Company-raised: he prices a man before he greets him.",
    "khorakk":    "Born to the bull-cult. He demands the respect due to it.",
    "uzkulak":    "Raised on a deck, counting other men's cargo.",
    "artificers": "Snakebeard's people take apart anything that holds still.",
    "fists":      "Temple drills left scars he wears with pride.",
    "horns":      "The Horns raise their sons lean and keep them that way.",
    "baal":       "Baal's kin smell of burnt brass and do not apologise for it.",
    "azeros":     "Azeros builds. His people measure a thing before they hate it.",
    "bzaark":     "Few survive Bzaark's household. He did.",
    "blackdwarf": "Sworn to the Black Dwarf, which is not the same as being free.",
    "kraken":     "The Armada raised him. It still expects its due.",
    "zharrduk":   "He learned to run a province on the Plain of Zharrduk.",
    # AND THE PLACES, for a lord who was raised in your own lands rather
    # than confederated in from somebody else's.
    "zharr":      "The Tower loomed over his childhood. Little impresses him now.",
    "plain":      "Plain-bred: he measures everything against a horizon.",
    "gorgoth":    "He learned early to survive Gorgoth's pits.",
    "stump":      "From the Stump, where the ground is still warm.",
    "zornuzkul":  "Born on the Great Skull Land. He does not discuss it.",
    "gash":       "He grew up armed in the orc country of Gash Kadrak.",
    "mines":      "He grew up in the mines. Open sky still makes him uneasy.",
    "wastes":     "Born in the Wastes. He still eats as though food might run out.",
}


# THE KEY KEPT ITS OLD SPELLING ON PURPOSE. These rows were the house
# traits and are the origin traits now; a lord in a campaign started
# before the change is already carrying derpy_ic_house_conclave, which
# reads correctly as an origin and needs no migration. Renaming the key
# would leave every such lord holding a trait with no DB row behind it.
def origin_trait_key(slug, race="chd"):
    return bundle_key("house", slug, race)


def bg_trait_key(slug, race="chd"):
    return bundle_key("bg", slug, race)


def office_trait_key(slug, race="chd"):
    return bundle_key("title", slug, race)


# The governor base bundle. cm:create_new_custom_effect_bundle takes this as its
# base and scales the values by the Overseer's rank at runtime, which is why there
# is one bundle here rather than five rank bundles. A custom effect bundle still
# resolves against a real effect_bundles record, so this row must exist.
GOVERNOR_BASE = [(E_ORDER, 2, BOON), (E_WORKLOAD, 5, BOON)]

BUNDLE_ICON = "chd_conclave_influence.png"

# effect_bundles_to_effects_junctions.advancement_stage is a FOREIGN KEY into
# effect_bundle_advancement_stages, and vanilla fills it on all 16,430 rows. An
# empty string there is not "no stage", it is an unresolvable reference, and the
# game refuses the whole pack at database load - naming whichever row sorts
# first, so the crash names an innocent row (House of Baal) and not the fault. 'start_turn_completed' is the column's own default and what 16,351
# of vanilla's rows use.
ADVANCEMENT_STAGE = "start_turn_completed"


# THE EVENT FEED.
#
# IC.log, a forty-entry ring buffer in the save, is drawn only on the panel's
# RECORD tab. Appointments, dismissals, expired terms, plots landing or missing
# and parties joining also raise event cards, so a player who never opens the
# panel still hears of them.
#
# WHY THESE SIX FIELDS ARE WHAT THEY ARE. cm:show_message_event's last argument
# is not a free number: it resolves
#
#     event_feed_message_events.group
#       -> campaign_groups.id
#       -> campaign_group_members (group -> id)
#       -> campaign_group_member_criteria_values.value   <- the number
#
# and an index with no record behind it logs a line and draws NOTHING. The chain
# above was followed end to end through a real vanilla row
# (wh3_dlc27_event_group_old_gods_curse -> 887) rather than taken on trust.
#
# THE EVENT TYPE IS NOT A FREE CHOICE EITHER. The table offers four scripted types, two of them
# "located" variants. Reading the table alone suggests
# scripted_persistent_located_event is ideal - it is the ONLY type vanilla ships
# with instant_open false, i.e. saved to the event history without stealing the
# screen. But grepping all 5,778 of CA's shipped scripts for what they pass to
# the PLAIN cm:show_message_event gives ten distinct indices, and every one of
# them resolves to scripted_persistent_event (persistent=true, instant_open
# true) or scripted_transient_event (persistent=false). The located variants are
# for cm:show_message_event_located and are never used with the plain call. So
# the choice is between exactly two proven shapes; an unproven type is a silent
# non-draw nobody can debug from in game.
#
#   persistent  -> a card, and an entry in the event history the player can
#                  re-read. For things that happened TO the court.
#   transient   -> the feed strip, expires, no card. For the routine per-turn
#                  notice that would be intolerable as a card.
#
# The snub is the only transient one, and it is transient because it is the only
# one that can fire for several houses in a single turn.
#
# NO DYNAMIC TEXT. All three text arguments are LOC KEYS, resolved by the engine
# at draw time - which is also why none of this trips the turn-handler rule that
# a common.get_localised_string from a turn handler is a turn-1 CTD. The engine
# does the lookup, we never do. CA builds keys by concatenation
# ("pooled_resources_display_name_" .. key, wh2_dlc17_thorek.lua:209), so the
# PRIMARY key names the specific seat by reusing the office bundle's own title
# key, which this generator already emits. That is as specific as a scripted
# event can be made without minting a record per office.
#
# Vanilla's highest criteria value is 1960, measured, so these start at 2600.
EVENT_INDEX_BASE = 2600

# event_feed_message_events' thirteen fields IN ORDER, copied off CA's own
# definition (version 1) rather than typed from the columns as they happen to
# print. check() re-reads the cached definition and refuses on any drift.
EVENT_COLS = ["event", "flavour_text", "group", "image", "secondary_detail",
              "target", "layout", "layout_data", "sound_event",
              "context_located", "override_icon", "instant_open",
              "ignore_instant_open_filters"]

# The columns every scripted row shares, read off the 158 vanilla scripted
# rows: all of them use these, with no variation at all.
EVENT_FIXED = {
    "flavour_text": "wh_event_feed_string_all_null",
    "secondary_detail": "wh_event_feed_string_scripted_event_secondary_detail",
    "target": "event_feed_target_faction",
    "layout": "standard",
    "layout_data": "event_feed_none",
    "context_located": "event_feed_none",
    # A BARE FILENAME under ui/campaign ui/message_icons/ at 74x74, and we ship
    # none - so it stays empty and the row falls back to `image`. A name with no
    # file behind it draws a blank square, silently.
    "override_icon": "",
    "ignore_instant_open_filters": "false",
}

# slug, persistent, image, sound, title, primary, secondary.
#
# CA'S SHAPE, measured off vanilla's event_feed_strings: the PRIMARY is the
# large-font subtitle under the title, two to six words, often a bare name; the
# SECONDARY is the body in the dark inset box under it, in full sentences. ""
# for either does not hide the slot - it draws it empty. Every event ships both
# (check 16j). A caller's own key replaces ONE of them, as IC.EVENTS' third
# field says: a seat's or a move's name is the subtitle, a deed's sentence is
# the body. So an event's primary here is the subtitle for when the caller
# has no name to give (two seats at once, say).
#
# Every image key was read out of the vanilla table's own chd/ set; an image key
# the engine does not know is another silent non-draw.
EVENTS = [
    # THE MOVE'S OWN LINE ("Bribe: Success") is the subtitle at the call site.
    ("plot_ok", True, "chd/diplomacy", "Positive",
     "The Court Moves",
     "Your Move Succeeded",
     "Your move has succeeded and taken effect. The Record tab lists what it did."),
    ("plot_fail", True, "chd/army_morale_down", "Negative",
     "The Court Refuses",
     "Your Move Failed",
     "Your move has failed, and its price is spent all the same. If it was "
     "aimed at a party, that party knows who tried and its loyalty falls."),
    # THE ONE THE PLAYER DID NOT DO. A term running out empties a seat with no
    # input from the player at all, which is exactly why it needs telling.
    # ONE SEAT: the call site's subtitle is its name. The one here is for two or more.
    ("office_lost", True, "chd/civilisation_down", "Neutral",
     "A Seat Stands Empty",
     "Several Terms Have Run Out",
     "When a term at court runs out, its officer leaves the seat. An empty "
     "office gives no bonus until you fill it on the Offices tab, and its last "
     "holder cannot take it straight back."),
    ("party_joined", True, "chd/faction", "Positive",
     "A Party Enters the Court",
     "New Men From a Confederation",
     "A faction you confederated has brought its men into your court as a party "
     "of its own. It has strength at court now and will expect seats."),
    # THE MOST EXPENSIVE THING THAT CAN HAPPEN, so it is not left to the panel's
    # alert bar alone.
    ("secede_warn", True, "chd/settlement_lost", "Negative",
     "A Party Prepares to Leave",
     "Its Countdown Has Begun",
     "A party has begun counting down to leave your court. When the count ends, "
     "it leaves and takes provinces with it. Raise its loyalty or cut its share "
     "before then; its card on the Court tab shows the turns left."),
    # TRANSIENT, ALONE: six offices can snub six parties in one turn.
    # The call site's subtitle is the claimed seat's name.
    ("snub", False, "chd/army_morale_down", "Negative",
     "A Party Is Slighted",
     "Its Claimed Seat Is Taken",
     "A rival's man holds an office this party claims as its own. The party "
     "loses loyalty every turn he keeps it."),
    # LAST, AND THAT IS DELIBERATE. An event's index is derived from its POSITION
    # in this list, so a row inserted in the middle renumbers everything after it
    # while the model keeps the old numbers (the build gate refuses that).
    # Append new events.
    #
    # THE THING ITSELF. secede_warn announces a countdown, and at zero loyalty
    # there is no countdown at all, so without this a party takes a province,
    # puts an army on the map and says nothing whatsoever about it.
    ("secede_done", True, "chd/settlement_lost", "Negative",
     "A Party Has Broken With You",
     "Rebels Rise Against You",
     "A party has left your court and risen in rebellion with land and an army "
     "of its own. Its rebels are at war with you. Its seats are empty, and the "
     "men it left behind now serve your own party."),
    # AND THE ONE THAT COMES BEFORE ANY OF THEM. secede_warn fires only when a
    # party has a big enough share of the court to be worth counting down; a
    # small party with nothing to lose rots to the floor without a single card
    # and then leaves on the turn it hits it. This is that party's only notice,
    # and it lands while the player can still buy it off.
    ("loyalty_warn", True, "chd/army_morale_down", "Negative",
     "A Party Turns Against You",
     "Its Loyalty Is Running Low",
     "A rival party's loyalty has fallen low. Give it a seat, or send it a gift "
     "from the Court tab. If its loyalty runs out, it leaves at once and takes "
     "land with it."),
    # YOUR OWN HOUSE, COMING APART. The Crown cannot secede from itself; this is
    # what its loyalty running out costs. chd/faction is the same picture party_joined
    # draws, because the thing that happened is the same thing: a party the
    # court did not have yesterday.
    ("splinter", True, "chd/faction", "Negative",
     "Your Own House Splits",
     "A Rival Party Is Born",
     "Some of your own party's men have broken away to form a rival party, "
     "taking part of your share of the court. Your party's loyalty returns to "
     "its starting level. The new party will expect seats."),
    # THE SECOND NOTICE ON A SECESSION. secede_warn lands at the top of a
    # five-turn clock, and Provoke shortens that clock and skips the opening
    # card, so without this the fastest route to losing a province is also the
    # quietest. This fires once, as the count enters its last warn_turns.
    ("secede_soon", True, "chd/settlement_lost", "Negative",
     "The Count Is Nearly Out",
     "This Is the Last Warning",
     "A party is about to leave your court and take provinces with it. No "
     "further card will warn you. Raise its loyalty or cut its share now."),
    # AND THE CROWN'S OWN WARNING. The split card says what has happened; this
    # one runs in front of it and says what is about to.
    ("splinter_warn", True, "chd/faction", "Negative",
     "Your Own House Is Turning",
     "A Split Is Coming",
     "Your own party's loyalty has fallen too low, and some of its men are "
     "forming a party of their own. Raise its loyalty before they break away."),
    # A PARTY WITH NOTHING TO TAKE. A party with nobody in it and no province to
    # its name breaks up instead of seceding; seceding, it would take over
    # another rising's faction, rename it and start a war.
    ("dissolved", True, "chd/faction", "Neutral",
     "A Party Dissolves",
     "No Men and No Land Left",
     "The party had no men left and no province to take, so it broke up instead "
     "of leaving. Its share of the court is gone, and you lose nothing."),
    ("party_plot_warn", True, "chd/army_morale_down", "Negative",
     "A Party Moves Against You",
     "Its Move Lands Next Turn",
     "A rival party plans to strike at you next turn. The Intrigue tab names the "
     "party and its move. Raise that party's loyalty, or deal with its plotter, "
     "to stop it."),
    ("party_plot_ok", True, "chd/army_morale_down", "Negative",
     "The Court Strikes at the Crown",
     "A Rival's Move Lands",
     "A rival party's move against you has succeeded. The Record tab names the "
     "party and what it did."),
    ("party_plot_fail", True, "chd/diplomacy", "Positive",
     "A Plot Is Foiled",
     "Their Move Failed",
     "A rival party's move against you has failed. Its man lost the influence "
     "he spent on it."),
    ("party_plot_dropped", True, "chd/diplomacy", "Neutral",
     "A Plot Comes to Nothing",
     "The Threat Has Passed",
     "A rival party has given up the move it planned against you."),
    ("party_feud", True, "chd/faction", "Neutral",
     "A Feud in the Court",
     "They Strike at Each Other",
     "Two rival parties have turned on each other. While the feud lasts they "
     "strike at each other and leave you alone. Back one side or make peace on "
     "the Petitions tab to end it."),
    ("party_feud_end", True, "chd/faction", "Neutral",
     "A Feud Ends",
     "Either May Strike at You Now",
     "The feud between two rival parties is over. Neither is busy with the "
     "other, and either may move against you again."),
    ("party_feud_murder", True, "chd/army_morale_down", "Negative",
     "Blood Between Parties",
     "One of Your Men Is Dead",
     "A feud at court has turned to murder: one feuding party has had a man "
     "from the other killed. He was one of your men."),
    ("party_demand", True, "chd/diplomacy", "Neutral",
     "A Party Makes a Demand",
     "A Post for One of Its Men",
     "A party demands a post for one of its men. Its card names the man and the "
     "post. Answer on the Petitions tab: grant it and its loyalty rises; refuse "
     "it or let the time run out and its loyalty falls."),
    ("party_demand_refused", True, "chd/army_morale_down", "Negative",
     "A Demand Refused",
     "Its Loyalty Falls",
     "A party's demand went unmet, and its loyalty has fallen."),
    ("party_offer", True, "chd/diplomacy", "Positive",
     "A Party Offers a Favour",
     "Accepting Angers the Rest",
     "A loyal party offers you a favour. Answer it on the Petitions tab before "
     "it lapses. If you accept, every other rival party loses loyalty."),
    # THE TURN BEFORE office_lost. The call site's subtitle names the seat
    # when only one is ending; the one below is for two or more.
    ("term_soon", True, "chd/civilisation_down", "Neutral",
     "A Term Ends Next Turn",
     "Several Terms End at Once",
     "When a term ends at the start of your next turn, its seat falls vacant "
     "and its holder cannot take it straight back. Pick a successor now on the "
     "Offices tab."),
    ("party_sabotage", True, "chd/army_morale_down", "Negative",
     "An Office Sabotaged",
     "Its Bonus Is Lost for Now",
     "A feuding party has sabotaged an office its rival holds. The office gives "
     "no bonus for a few turns."),
    ("party_withhold", True, "chd/army_morale_down", "Negative",
     "A Party Withholds Its Service",
     "Their Offices Stop Working",
     "A disloyal party's officers have stopped working for you. Their offices "
     "give no bonus for a few turns. Use Secure Loyalty on the Court tab and "
     "they return to work at once."),
    ("realm_secede", False, "chd/army_morale_down", "Negative",
     "A Rival Court Splits",
     "Rebels Take the Field",
     "A party has broken from another Chaos Dwarf court and risen in rebellion "
     "with an army of its own."),
    # Three things the court would otherwise do in silence. A death the court
    # arranged - a plot, a feud - has its own
    # card already and does not raise this one.
    # A SEAT'S NAME is the call site's subtitle; a governor's death uses this one.
    ("officer_died", True, "chd/army_morale_down", "Negative",
     "An Officer Is Dead",
     "A Post Stands Empty",
     "One of your officers has died, and the post he held is empty. Fill it on "
     "the Offices or Governors tab."),
    # BOTH COUNTS: a party's secession and your own house's split.
    ("threat_over", True, "chd/diplomacy", "Positive",
     "A Party Stands Down",
     "The Countdown Stops",
     "A party that was counting down to break with you has stopped, for now. "
     "Keep watch on its loyalty: a new count can start."),
    # The call site's subtitle names the seat when only one is back.
    ("stall_end", True, "chd/diplomacy", "Positive",
     "An Office Is Back at Work",
     "Their Bonuses Apply Again",
     "The stoppage has run its course, and each office it stopped gives its "
     "bonus again."),
    # THE GOVERNMENT.
    ("gov_changed", True, "chd/faction", "Positive",
     "A New Government",
     "A Court Rule Changes",
     "A new government rules the court, with its own court rule and faction "
     "effect. The parties behind it gain loyalty, and those behind the old one "
     "lose some."),
    ("gov_pressure", True, "chd/faction", "Neutral",
     "The Court Pulls Another Way",
     "A Choice Waits",
     "The leading party asks for its own government. On the Petitions tab, "
     "accept it or pay influence to keep your current one. Accepting angers the "
     "old government's party; holding angers the party that asked."),
    # DEEDS. gov_intro is raised once per player court;
    # party_drawn's body is a per-party line (PARTY_DRAWN) naming its deed.
    ("gov_intro", True, "chd/faction", "Neutral",
     "Your Deeds Move the Court",
     "What Raises Each Party",
     "Your deeds strengthen parties at court. Victories raise the Legion; Hell-Forge work raises the Forge; Tower rites and temples raise the Priesthood; slaves and razing raise the Chain; convoys raise the Road; research raises the Tower. A strong party asks for its own government. Your current government is shown in the Crown's box."),
    ("party_drawn", True, "chd/faction", "Positive",
     "A Party Comes to Court",
     "Drawn by Your Deeds",
     "Your deeds have drawn a new party into your court, and your newest lord "
     "has joined it. It has strength at court now and will expect seats."),
    # THE LAWS.
    ("law_proposed", True, "chd/faction", "Neutral",
     "A Law Before the Court",
     "The Court Will Vote",
     "A law is before the court. Each party votes with the influence of its "
     "men. On the Laws tab, push your side, win men over or overrule the vote."),
    ("law_passed", True, "chd/faction", "Positive",
     "A Law Passes",
     "The Law Is Changed",
     "The court has voted the law through, and it is now in force. Parties that "
     "backed it gain loyalty; parties that opposed it lose some."),
    ("law_failed", True, "chd/faction", "Negative",
     "A Law Fails",
     "The Old Law Stands",
     "The court has voted the law down, and the law in force stays. If a rival "
     "party proposed it, that party loses loyalty."),
]

# THE BODY party_drawn PASSES, one per party a deed can draw in. It replaces
# the event's own body, so it carries that body's news as well as the deed.
PARTY_DRAWN = {
    "legion": "Your victories drew the Legion to court. Your newest lord has joined it, and it will expect seats.",
    "forge": "The Hell-Forge's work drew the Forge to court. Your newest lord has joined it, and it will expect seats.",
    "temple": "The Tower's rites drew the Priesthood to court. Your newest lord has joined it, and it will expect seats.",
    "chain": "Your slave-taking drew the Chain to court. Your newest lord has joined it, and it will expect seats.",
    "road": "Your convoys drew the Road to court. Your newest lord has joined it, and it will expect seats.",
    "ledger": "Your convoys drew the Ledger to court. Your newest lord has joined it, and it will expect seats.",
    "tower": "Your research drew the Tower to court. Your newest lord has joined it, and it will expect seats.",
}

# RAISED WITH cm:show_message_event_located. The record type must agree with the
# call - a plain record raised through the located call draws nothing (measured
# for the director, tools/build_director.py). Mirrors IC.LOCATED_EVENTS.
LOCATED_EVENTS = {"realm_secede"}

# THE DEMAND MISSIONS. Issued from Lua as a mission string (IC.demand_string);
# the string route still needs a missions row per key. Field for field the
# Great Guilds bounty row, except: SCRIPTED because the string supplies the
# objective, a real picture (chd/generic is not one), and no manual cancel -
# a cancel is a void, and a void costs nothing, so it would be a free refusal.
DEMAND_REWARD = "derpy_ic_demand_reward"
DEMAND_REWARD_TEXT = "The party's loyalty rises."
DEMANDS = [
    ("derpy_ic_demand_office", "A Party Demands an Office",
     "A party demands a vacant office for one of its men. The party's card names the man and the office. Appoint him in time and its loyalty rises; miss the deadline or appoint someone else and it falls.",
     "The party's man holds the office it demanded.",
     "Appoint the man named on its party card to the office it demands."),
    ("derpy_ic_demand_province", "A Party Demands a Province",
     "A party demands a province for one of its men. The party's card names the man and the province. Make him governor in time and its loyalty rises; miss the deadline or appoint someone else and it falls.",
     "The party's man governs the province it demanded.",
     "Make the man named on its party card governor of the province it demands."),
]


def event_key(slug):
    return "derpy_ic_event_" + slug


# A RUN OF RECORDS PER RACE, because the picture belongs to the record the index
# names; one shared run would give a Dwarf court Chaos Dwarf pictures.
# The Chaos Dwarf run is the original, keys and numbers unchanged; the Dwarf run
# is the same events 200 higher, keyed <event>_dwf, each with the dwf/ picture of
# its twin - vanilla ships a dwf/ version of every one of the five used. The
# model adds DWF.EVENT_OFFSET, which import_iron_court holds to this. 2800-2899
# was free across all 354 installed packs (Mixu holds three in the 2700s).
RACE_EVENT_OFFSET = {"chd": 0, "dwf": 200}


def event_index(slug, race="chd"):
    """The number the script passes. Derived from position, never typed twice."""
    for i, ev in enumerate(EVENTS):
        if ev[0] == slug:
            return EVENT_INDEX_BASE + i + RACE_EVENT_OFFSET[race]
    raise KeyError(slug)


def event_image(image, race):
    """The race's own picture for a Chaos Dwarf one."""
    assert image.startswith("chd/"), image
    return image if race == "chd" else race + "/" + image[len("chd/"):]


# CONTROL OF THE COURT.
#
# The crown's share of the weight, in bands. FLOOR, not a range: a band runs
# from its floor up to the next one's, the list is walked top down, and the
# last floor is 0 - so every possible share lands in exactly one band and no
# arithmetic anywhere has to agree about where a boundary is.
#
# The model carries the same five floors in IC.CONTROL and import_iron_court.py
# refuses to pack when the two disagree: a band the model can reach and the DB
# has no bundle for is a turn in which the player's whole position silently
# stops applying.
#
# THE ENDS ARE STEEP ON PURPOSE. The middle band is nearly free either way -
# most of a campaign is spent there - and the two ends are where the system is
# supposed to be felt: an iron grip pays for itself, and a court that is not
# yours costs more than the offices in it are worth.
CONTROL_BANDS = [
    ("grip", 75, "An Iron Grip on the Court",
     "Nothing moves in Zharr-Naggrund that the Crown did not set moving.",
     [(E_ORDER, 6, BOON), (E_GDP, 12, BOON), (E_UPKEEP, 15, BOON),
      (E_LAW_INFLUENCE, 5, BOON)]),
    ("mastery", 60, "Master of the Court",
     "The parties argue, and then they do as they are told.",
     [(E_ORDER, 4, BOON), (E_GDP, 8, BOON), (E_UPKEEP, 10, BOON)]),
    ("command", 40, "In Command of the Court",
     "The Crown leads the parties but cannot command them.",
     [(E_ORDER, 2, BOON)]),
    ("contested", 10, "A Contested Court",
     "No decree passes without a bargain struck.",
     [(E_ORDER, 2, MALUS), (E_UPKEEP, 5, MALUS)]),
    ("lost", 0, "The Court Is Not Yours",
     "The parties rule. The Crown hears their decisions later.",
     [(E_ORDER, 8, MALUS), (E_UPKEEP, 20, MALUS), (E_GDP, 15, MALUS),
      (E_LAW_INFLUENCE, 5, MALUS)]),
]


# THE GOVERNMENTS, in IC.GOV_ORDER's order:
# slug, name, the rule as the player reads it, the bundle's line, its effects.
# check_governments() holds the order to the model's.
GOVERNMENTS = [
    ("conclave", "The Conclave",
     "Office terms are shorter. A man may take a seat again after 1 turn.",
     "No one rules Zharr-Naggrund. Its Sorcerer-Prophets sit in council.",
     [(E_RESEARCH, 5, BOON)]),
    ("priest", "Rule of the High Priest",
     "Each rank a man gains is worth double influence. Battles are worth less.",
     "The eldest priest rules in Hashut's name.",
     [(E_LAW_INFLUENCE, 10, BOON)]),
    ("forge", "Rule of the Daemonsmiths",
     "Governors earn more income. Men at court earn less influence each turn.",
     "The priest-artificers rule from the forges.",
     [(E_ARMAMENTS, 10, BOON)]),
    ("legion", "Command of the Legion",
     "Battles are worth more influence and loyalty. Men at court earn no "
     "influence each turn.",
     "Rank in the court is won in the field.",
     [(E_UPKEEP, 5, BOON)]),
    ("chain", "Rule of the Slave-Lords",
     "Murder, Purge and Provoke cost less. A failed move costs double loyalty.",
     "Fear holds the court as the chain holds the slave.",
     [(E_PB_LABOUR, 10, BOON)]),
    ("convoy", "The Convoy Concern",
     "Gifts and oaths cost less gold. Embezzling angers the parties twice as much.",
     "Everything in the Dark Lands has a price.",
     [(E_GDP, 5, BOON)]),
]

# THE LAWS, in IC.LAW_ORDER's order and each
# category's IC.LAWS order. check_laws() holds the two together.
LAWS = [
    ("labour", "Labour", "chd_labour.png", [
        ("measure", "The Measure", "Keep the work gangs to their usual quotas.", []),
        ("lash", "The Lash", "More slaves are taken. The lash works them to death.",
         [(E_LAW_CAPTIVES, 15, BOON), (E_LAW_RUSH, 30, BOON), (E_LAW_LAB_LD, 4, MALUS)]),
        ("kept", "The Kept Stock", "Feed the stock. Keep it alive. Take fewer slaves.",
         [(E_LAW_LAB_UPKEEP, 50, BOON), (E_LAW_LAB_RANK, 2, BOON), (E_LAW_CAPTIVES, 10, MALUS)]),
        ("quota", "The Furnace Quota", "The stock pays for every forge's quota.",
         [(E_WORKLOAD, 15, BOON), (E_LAW_RAW_USED, 15, BOON), (E_LAW_LAB_UPKEEP, 25, MALUS)]),
        ("ash", "The Ash Harvest", "Burn what cannot be held, people and all.",
         [(E_LAW_RAZE, 25, BOON), (E_LAW_SACK, 15, BOON), (E_LAW_CAPTIVES, 10, MALUS)]),
    ]),
    ("tribute", "Tribute", "edict_collect_tribute.png", [
        ("tithe", "The Crown's Tithe", "The Crown collects its usual tithe.", []),
        ("roads", "Open Roads", "More convoys use the roads. Vassals pay less tribute.",
         [(E_LAW_CONVOYS, 1, BOON), (E_LAW_AMBUSH, 25, BOON), (E_LAW_VASSAL, 20, MALUS)]),
        ("tariff", "The Ledger's Tariff", "The Ledger takes more from each route. Cargo sells for less.",
         [(E_LAW_TARIFF, 5, BOON), (E_LAW_REFINERY, 10, BOON), (E_LAW_CARGO_VALUE, 10, MALUS)]),
        ("mines", "The Mines Before All", "Supply the mines first. Convoys carry less.",
         [(E_LAW_MINES, 15, BOON), (E_LAW_GOODS, 10, BOON), (E_LAW_CARGO_CAP, 15, MALUS)]),
        ("charter", "The Overseers' Charter", "Charter the convoy overseers. The other houses resent their privilege.",
         [(E_LAW_OVR_RANK, 3, BOON), (E_LAW_OVR_XP, 100, BOON), (E_LAW_CHD_DIPLO, 10, MALUS)]),
    ]),
    ("worship", "Worship", "chd_conclave_influence.png", [
        ("rites", "The Rites Kept", "The priests keep the customary rites.", []),
        ("fires", "The Fires Fed", "Feed Hashut's fires at the expense of building work.",
         [(E_LAW_INFLUENCE, 10, BOON), (E_LAW_CORRUPT, 1, BOON), (E_LAW_RUSH, 15, MALUS)]),
        ("seats", "Seats Bought in the Tower", "Sell seats in the Tower. The priests withhold their favour.",
         [(E_LAW_TOZ_SEAT, 25, BOON), (E_LAW_INFLUENCE, 10, MALUS)]),
        ("lore", "The Lore Taught", "Teach the Lore of Hashut widely, with less care.",
         [(E_LAW_WOM, 10, BOON), (E_LAW_COOLDOWN, 10, BOON), (E_LAW_MISCAST, 15, MALUS)]),
        ("licence", "The Daemonsmiths' Licence", "License the Daemonsmiths. The priests resent their privilege.",
         [(E_LAW_KDAAI, 10, BOON), (E_LAW_TEMPLE_TIME, 1, BOON), (E_LAW_INFLUENCE, 10, MALUS)]),
    ]),
    ("war", "War", "edict_levy_conscripts.png", [
        ("levy", "The Levy", "Raise the customary levy.", []),
        ("hellforge", "The Hell-Forge Unbound", "The Hell-Forge needs no leave to work. Infantry pays the bill.",
         [(E_LAW_HF_COST, 10, BOON), (E_LAW_HF_CAP, 1, BOON), (E_LAW_INF_COST, 10, MALUS)]),
        ("legions", "Standing Legions", "Keep the legions ready. The guns must wait.",
         [(E_LAW_INF_RANK, 1, BOON), (E_LAW_INF_COST, 10, BOON), (E_LAW_ART_UPKEEP, 10, MALUS)]),
        ("grudge", "The Old Grudge", "Pursue the old grudge against the Dwarfs at the labourers' expense.",
         [(E_LAW_DWARF_XP, 100, BOON), (E_LAW_HOB_UPKEEP, 10, MALUS)]),
        ("gunnery", "The Gunnery Doctrine", "Supply the guns first. Shooters cost more to recruit.",
         [(E_LAW_ART_EXPL, 10, BOON), (E_LAW_ART_RANGE, 5, BOON), (E_LAW_RANGED_COST, 15, MALUS)]),
    ]),
]


# THE RACES. `prefix` is the Lua table prefix the race's tables are declared
# under; LUA_OF_PREFIX names the file.
RACES = {
    "chd": {"infix": "", "prefix": "IC",
            "ORIGINS": ORIGINS, "PARTIES": PARTIES, "BACKGROUNDS": BACKGROUNDS,
            "OFFICES": OFFICES, "GOVERNMENTS": GOVERNMENTS, "LAWS": LAWS},
}
LUA_OF_PREFIX = {"IC": "zzz_derpy_iron_court.lua"}

# THE DWARFS. The model's tables are in zzz_derpy_iron_court_dwarf.lua as DWF.X; check_dwf() holds the
# two together. Slugs are the Chaos Dwarf slots; every key carries "dwf_".
DWF_ORIGINS = [
    ("karaz",     "wh_main_dwf_dwarfs",                "Karaz-a-Karak"),
    ("kadrin",    "wh_main_dwf_karak_kadrin",          "Karak Kadrin"),
    ("angrund",   "wh_main_dwf_karak_izor",            "Clan Angrund"),
    ("throng",    "wh3_main_dwf_the_ancestral_throng", "the Ancestral Throng"),
    ("ironbrow",  "wh2_dlc17_dwf_thorek_ironbrow",     "Ironbrow's Expedition"),
    ("malakai",   "wh3_dlc25_dwf_malakai",             "the Masters of Innovation"),
    ("barakvarr", "wh_main_dwf_barak_varr",            "Barak Varr"),
    ("zhufbar",   "wh_main_dwf_zhufbar",               "Zhufbar"),
    ("krakadrak", "wh_main_dwf_kraka_drak",            "Kraka Drak"),
    ("azorn",     "wh3_main_dwf_karak_azorn",          "Karak Azorn"),
    ("norn",      "wh_main_dwf_karak_norn",            "Karak Norn"),
    ("hirn",      "wh_main_dwf_karak_hirn",            "Karak Hirn"),
    ("azul",      "wh_main_dwf_karak_azul",            "Karak Azul"),
    ("ziflin",    "wh_main_dwf_karak_ziflin",          "Karak Ziflin"),
    ("rangers",   None,                                "the Ranger clans"),
    ("deeps",     None,                                "the Deeps"),
    ("grey",      None,                                "the Grey Mountains"),
    ("black",     None,                                "the Black Mountains"),
]

# Dwarf factions deliberately NOT origins, each named.
DWF_NOT_AN_ORIGIN = {
    "wh_main_dwf_dwarf_rebels",              # the engine's rebels
    "wh_main_dwf_dwarfs_qb1",                # CA's convoy ambushes, Worldroots, Sayl
    "wh_main_dwf_dwarfs_qb2",                # the rising pool
    "wh_main_dwf_dwarfs_qb3",
    "wh_main_dwf_dwarfs_qb4",
    "wh_main_dwf_dwarfs_seperatists_qb1",    # quest battles (CA's spelling)
    "wh_main_dwf_dwarfs_seperatists_qb2",
    "wh_main_dwf_dwarfs_seperatists_qb3",
    "wh_main_dwf_dwarfs_seperatists_qb4",
    "wh3_dlc26_dwf_dwarfs_invasion",         # Arbaal's challenge
    "wh2_dlc15_dwf_clan_helhein",            # in the DB, unconfirmed on the map
    "wh2_main_dwf_karak_zorn",
    "wh2_main_dwf_greybeards_prospectors",
    "wh2_main_dwf_spine_of_sotek_dwarfs",
}

DWF_ORIGIN_COLOUR = {
    "karaz":     "He grew up hearing the High King's judgements in the great hall.",
    "kadrin":    "He grew up in Kadrin among Slayers sworn to seek their deaths.",
    "angrund":   "Clan Angrund taught him the loss of Eight Peaks. He means to reclaim it.",
    "throng":    "He marched with the Throng to places named in the oldest clan tales.",
    "ironbrow":  "Ironbrow's people go further from home than any dwarf should.",
    "malakai":   "He trusts Malakai's flying machines. His elders disapprove.",
    "barakvarr": "He learned his trade among the ships at Barak Varr.",
    "zhufbar":   "Zhufbar-born: he knows an engine by its sound.",
    "krakadrak": "He learned to endure the northern winters at Kraka Drak.",
    "azorn":     "Azorn taught him to watch the east.",
    "norn":      "He judges stonework against the halls of Karak Norn.",
    "hirn":      "He knows the sound of wind in Karak Hirn's caverns.",
    "azul":      "He learned his craft at Azul's anvils.",
    "ziflin":    "Ziflin-born, from a small hold with a long memory.",
    "rangers":   "Ranger clans taught him to watch the passes for greenskins.",
    "deeps":     "He grew up in the Deeps. He knows the stone above him is sound.",
    "grey":      "He knows the passes between the holds of the Grey Mountains.",
    "black":     "From the Black Mountains, where the greenskins are never far.",
}

DWF_PARTIES = [
    # slug,      display,                  gov effect,          mag
    ("crown",    "The Throne-Sworn",       E_ORDER,             4),
    ("temple",   "The Ancestor Priesthood", E_DWF_GRUDGE_ORDER, 3),
    ("forge",    "The Forgewrights",       E_DWF_OATHGOLD,      6),
    ("chain",    "The Deepdelvers",        E_DWF_LOOT,          10),
    ("legion",   "The Clan Warriors",      E_UPKEEP,            6),
    ("ledger",   "The Reckoners",          E_GDP,               6),
    ("tower",    "The Runesmiths",         E_RESEARCH,          5),
    ("road",     "The Underway Wardens",   E_MOVEMENT,          4),
    ("hearth",   "The Hearth Clans",       E_REPLEN,            8),
]

DWF_PARTY_GOV_BLURB = {
    "crown":  "The king's retainers answer for this province.",
    "temple": "The priests tend its clan shrines and keep its old grudges alive.",
    "forge":  "The Forgewrights collect Oathgold from the province's workshops.",
    "chain":  "The Deepdelvers weigh the spoils brought home by their warriors.",
    "legion": "A thane knows what his clan needs to defend the hold.",
    "ledger": "The Reckoners collect every debt owed to the hold.",
    "tower":  "The Runesmiths put the hold's old lore to use.",
    "road":   "The Underway Wardens clear safe routes beneath the mountains.",
    "hearth": "The Hearth Clans care for wounded warriors until they can march again.",
}

DWF_BACKGROUNDS = {
    "crown":  [("kinguard",     "Household Warrior"),
               ("lineblood",    "Blood of the Line"),
               ("oathsworn",    "Oath-Sworn Hand")],
    "temple": [("shrinekeeper", "Shrine-Keeper"),
               ("valayan",      "Priest of Valaya"),
               ("tombwarden",   "Warden of the Tombs")],
    "forge":  [("smith",        "Gromril Smith"),
               ("engineer",     "Engineer"),
               ("foundry",      "Foundry Master")],
    "chain":  [("miner",        "Miner"),
               ("prospector",   "Prospector"),
               ("tunneller",    "Tunneller")],
    "legion": [("longbeard",    "Longbeard"),
               ("ironbreaker",  "Ironbreaker"),
               ("thane",        "Thane of a Clan")],
    "ledger": [("reckoner",     "Reckoner of Debts"),
               ("trader",       "Hold Trader"),
               ("goldsmith",    "Goldsmith")],
    "tower":  [("runesmith",    "Runesmith"),
               ("loremaster",   "Loremaster"),
               ("scribe",       "Grudge-Scribe")],
    "road":   [("ranger",       "Ranger"),
               ("wayfinder",    "Wayfinder"),
               ("underwarden",  "Underway Sentry")],
    "hearth": [("farmer",       "Holdfarmer"),
               ("brewer",       "Brewer"),
               ("clanelder",        "Clan Elder")],
}

DWF_BG_COLOUR = {
    "kinguard":     "The king trusted him to guard his household before taking him to war.",
    "lineblood":    "His clan can trace its kinship to the royal line.",
    "oathsworn":    "The Ancestors witnessed his oath to the king. He will keep it.",
    "shrinekeeper": "He tends the ancestor shrines. He knows every name in the stone.",
    "valayan":      "Valaya's priest. The hearth is his altar and the hold his charge.",
    "tombwarden":   "He has kept watch over the clan tombs for years.",
    "smith":        "A tap of his hammer tells him whether gromril is sound.",
    "engineer":     "He checks every gun himself before the warriors trust it.",
    "foundry":      "Twenty years at the foundry have scorched his beard.",
    "miner":        "He has dug further down than most dwarfs have ever been.",
    "prospector":   "His claims on new seams have made his clan wealthy.",
    "tunneller":    "He can hear rock about to give before it gives.",
    "longbeard":    "He remembers better days and expects the young to listen.",
    "ironbreaker":  "He has held the underways against things that never come up to the light.",
    "thane":        "He answers for his clan's honour, however few its warriors.",
    "reckoner":     "He remembers every debt owed to his clan.",
    "trader":       "He checks every coin a foreign trader offers.",
    "goldsmith":    "He weighs gold by eye and is never more than a grain out.",
    "runesmith":    "His master entrusted him with runes he will never teach outsiders.",
    "loremaster":   "He knows which old records still matter to the hold.",
    "scribe":       "He leaves no wrong out of the Book.",
    "ranger":       "He spots a greenskin trail where others see bare rock.",
    "wayfinder":    "He knows the old roads the maps have forgotten.",
    "underwarden":  "He guards the crossings where greenskins enter the Underway.",
    "farmer":       "He brings in the hold's barley before the mountain frosts.",
    "brewer":       "He knows a spoiled barrel before anyone lifts a tankard.",
    "clanelder":        "He hears every clan dispute, however petty.",
}

# THE FOURTEEN SEATS, tier-4 magnitudes raised by TIER_MULT.
DWF_OFFICES = [
    {"slug": "priest", "name": "High Priest of the Ancestors", "affinity": "temple", "tier": 1,
     "blurb": "He tends the clan shrines and settles disputes in their names.",
     "vacant_blurb": "The shrines stand unattended and the old names go unspoken.",
     "effects": [(E_ORDER, 2, BOON), (E_GDP, 4, BOON)],
     "vacancy": [(E_ORDER, 2, MALUS)]},
    {"slug": "forge", "name": "Master Forgewright", "affinity": "forge", "tier": 1,
     "blurb": "The master smiths accept his judgement at the anvil.",
     "vacant_blurb": "The smiths dispute each other's work. No master settles the matter.",
     "effects": [(E_DWF_OATHGOLD, 5, BOON), (E_DWF_CRAFT, 4, BOON)],
     "vacancy": [(E_DWF_OATHGOLD, 2, MALUS)]},
    {"slug": "ledger", "name": "Keeper of the Reckoning", "affinity": "ledger", "tier": 2,
     "blurb": "He makes each debtor pay what the hold is owed.",
     "vacant_blurb": "Unpaid debts gather in the hold's books.",
     "effects": [(E_GDP, 6, BOON)],
     "vacancy": [(E_GDP, 3, MALUS)]},
    {"slug": "warden", "name": "Warden of the Gate", "affinity": "legion", "tier": 2,
     "blurb": "He assigns the gate watch and keeps the garrison supplied.",
     "vacant_blurb": "The clans dispute who owes the gate watch.",
     "effects": [(E_UPKEEP, 5, BOON), (E_REPLEN, 5, BOON)],
     "vacancy": [(E_ORDER, 2, MALUS)]},
    {"slug": "hand", "name": "Keeper of the Grudge-Book", "affinity": "tower", "tier": 2,
     "blurb": "Every wrong is written in his hand. From the next Age of Reckoning, fewer grudges need settling.",
     "vacant_blurb": "The Book goes unkept. From the next Age of Reckoning, more grudges need settling.",
     "effects": [(E_DWF_GRUDGE_REQ, 5, BOON)],
     "vacancy": [(E_DWF_GRUDGE_REQ, 2, MALUS)]},
    {"slug": "roads", "name": "Warden of the Underway", "affinity": "road", "tier": 2,
     "blurb": "He keeps the old routes through the Underway clear.",
     "vacant_blurb": "Blocked tunnels force traders over the mountain passes.",
     "effects": [(E_MOVEMENT, 4, BOON)],
     "vacancy": [(E_MOVEMENT, 2, MALUS)]},
    {"slug": "chains", "name": "Overseer of the Mines", "affinity": "chain", "tier": 3,
     "blurb": "He inspects each seam and accounts for every ore cart.",
     "vacant_blurb": "The mining clans quarrel over their claims.",
     "effects": [(E_LAW_MINES, 10, BOON)],
     "vacancy": [(E_LAW_MINES, 4, MALUS)]},
    {"slug": "pits", "name": "Master of the Delvings", "affinity": "chain", "tier": 3,
     "blurb": "He sees that spoils reach the hold's vaults.",
     "vacant_blurb": "Warriors take spoils before the hold receives its share.",
     "effects": [(E_DWF_LOOT, 16, BOON)],
     "vacancy": [(E_DWF_LOOT, 7, MALUS)]},
    {"slug": "quarry", "name": "Master of the Stonecutters", "affinity": "forge", "tier": 3,
     "blurb": "His stonecutters waste little when they widen the halls.",
     "vacant_blurb": "The clans cannot agree whose halls to cut first.",
     "effects": [(E_CONSTRUCT, 6, BOON)],
     "vacancy": [(E_CONSTRUCT, 3, MALUS)]},
    {"slug": "muster", "name": "Thane of the Muster", "affinity": "legion", "tier": 3,
     "blurb": "He ensures each clan equips its warriors at a fair price.",
     "vacant_blurb": "Each clan asks its own price to send warriors.",
     "effects": [(E_RECRUIT, 8, BOON)],
     "vacancy": [(E_RECRUIT, 4, MALUS)]},
    {"slug": "kilns", "name": "Brewmaster of the Hold", "affinity": "hearth", "tier": 4,
     "blurb": "Traders come for his ale and buy the hold's fine work beside it.",
     "vacant_blurb": "Poor ale drives traders away from the hold's wares.",
     "effects": [(E_DWF_CULTURE, 8, BOON)],
     "vacancy": [(E_DWF_CULTURE, 4, MALUS)]},
    {"slug": "fields", "name": "Steward of the Holdfarms", "affinity": "hearth", "tier": 4,
     "blurb": "He brings in enough grain to feed new households.",
     "vacant_blurb": "The holdfarms lack hands to feed new households.",
     "effects": [(E_DWF_GROWTH, 5, BOON)],
     "vacancy": [(E_DWF_GROWTH, 2, MALUS)]},
    {"slug": "scribes", "name": "Keeper of the Lore", "affinity": "tower", "tier": 4,
     "blurb": "He finds old designs the smiths can put to work.",
     "vacant_blurb": "The smiths repeat work from neglected old books.",
     "effects": [(E_RESEARCH, 5, BOON)],
     "vacancy": [(E_RESEARCH, 2, MALUS)]},
    {"slug": "banners", "name": "Keeper of the Clan Banners", "affinity": "legion", "tier": 4,
     "blurb": "He gathers supplies for the Grudge Settlers from each clan.",
     "vacant_blurb": "The Grudge Settlers must buy their own supplies.",
     "effects": [(E_DWF_SETTLER_COST, 10, BOON)],
     "vacancy": [(E_DWF_SETTLER_COST, 5, MALUS)]},
]

# THE GOVERNMENTS, in DWF.GOV_ORDER's order: slug, name, rule, blurb, effects.
DWF_GOVERNMENTS = [
    ("conclave", "The Council of Elders",
     "Office terms are shorter. A man may take a seat again after 1 turn.",
     "The king hears each clan elder before the council decides.",
     [(E_RESEARCH, 5, BOON)]),
    ("priest", "The Ancestors' Writ",
     "Each rank a man gains is worth double influence. Battles are worth less.",
     "The priests judge the hold by the laws of its Ancestors.",
     [(E_DWF_GRUDGE_ORDER, 2, BOON)]),
    ("forge", "The Forge-Throne",
     "Governors earn more income. Men at court earn less influence each turn.",
     "The master smiths govern the hold between shifts at the forge.",
     [(E_DWF_OATHGOLD, 10, BOON)]),
    ("legion", "The War-King",
     "Battles are worth more influence and loyalty. Men at court earn no "
     "influence each turn.",
     "The king leads the shield wall. Clan thanes must fight beside him.",
     [(E_UPKEEP, 5, BOON)]),
    ("chain", "The Iron Law",
     "Ancestor Oath, Stand His Patron and Oath on the Anvil cost a third less. "
     "A broken oath costs 10 more loyalty.",
     "An oath sworn in the hold is kept, or it is written down.",
     [(E_DWF_SETTLER_SRC, 1, BOON)]),
    ("convoy", "The Reckoning-Throne",
     "Gifts and oaths cost less gold. Skimming the Tally angers the parties twice as much.",
     "The king demands an account of every debt.",
     [(E_DWF_TARIFF, 10, BOON)]),
]

# THE LAWS, in DWF.LAW_ORDER and each category's order.
DWF_LAWS = [
    ("labour", "Craft", "edict_masters_of_steel_and_stone.png", [
        ("measure", "The Old Ways", "The clans work as their fathers worked.", []),
        ("lash", "Deep Seams", "Send more miners into the deep seams. The holdfarms lose hands.",
         [(E_LAW_MINES, 15, BOON), (E_DWF_GROWTH, 3, MALUS)]),
        ("kept", "Hearth and Holdfarm", "The holdfarms get the hands they need before the mines.",
         [(E_DWF_GROWTH, 8, BOON), (E_LAW_MINES, 10, MALUS)]),
        ("quota", "The Master's Mark", "Master smiths inspect every piece. Warriors wait for their equipment.",
         [(E_DWF_CRAFT, 15, BOON), (E_REPLEN, 5, MALUS)]),
        ("ash", "Raise the Halls", "Widen the halls at the counting-houses' expense.",
         [(E_CONSTRUCT, 15, BOON), (E_GDP, 5, MALUS)]),
    ]),
    ("tribute", "Tribute", "edict_collect_tribute.png", [
        ("tithe", "The King's Tithe", "Each clan owes the king its customary tithe.", []),
        ("roads", "Open Underways", "Clear the Underway for traders. Vassal holds owe less tribute.",
         [(E_DWF_TARIFF, 15, BOON), (E_MOVEMENT, 5, BOON), (E_LAW_VASSAL, 20, MALUS)]),
        ("tariff", "The Reckoners' Tariff", "Every hall pays the Reckoners. Traders pay at the gate and come less often.",
         [(E_GDP, 5, BOON), (E_DWF_TARIFF, 10, MALUS)]),
        ("mines", "The Oathgold Hoard", "Gather Oathgold for the hold. Repairs to the roads must wait.",
         [(E_DWF_OATHGOLD, 15, BOON), (E_MOVEMENT, 5, MALUS)]),
        ("charter", "Hold Charters", "Charter the holds to sell their craft. Warriors cost more to maintain.",
         [(E_DWF_CULTURE, 15, BOON), (E_LAW_GOODS, 10, BOON), (E_UPKEEP, 5, MALUS)]),
    ]),
    ("worship", "Ancestors", "edict_venerate_the_ancestors.png", [
        ("rites", "The Ancestors' Rites", "The clans honour their Ancestors.", []),
        ("fires", "Valaya's Hearth", "Supply Valaya's hearths before the loremasters' work.",
         [(E_DWF_GRUDGE_ORDER, 2, BOON), (E_DWF_GROWTH, 3, BOON), (E_RESEARCH, 5, MALUS)]),
        ("seats", "Rune-Lore", "Give the runesmiths leave to work. The shrines receive less.",
         [(E_DWF_RUNECRAFT, 15, BOON), (E_DWF_GRUDGE_ORDER, 1, MALUS)]),
        ("lore", "The Lore of the Book", "Call clansmen from the holdfarms to study the old books.",
         [(E_RESEARCH, 10, BOON), (E_DWF_GROWTH, 3, MALUS)]),
        ("licence", "The Anvil's Licence", "The forge is licensed to work without the priests' leave.",
         [(E_DWF_CRAFT, 10, BOON), (E_DWF_GRUDGE_ORDER, 1, MALUS)]),
    ]),
    ("war", "War", "edict_levy_conscripts.png", [
        ("levy", "The Muster", "Each clan sends its customary muster.", []),
        ("grudge", "Grudge Settlers", "The king funds the Grudge Settlers from the counting-houses.",
         [(E_DWF_SETTLER_COST, 15, BOON), (E_DWF_SETTLER_SRC, 1, BOON), (E_GDP, 5, MALUS)]),
        ("hellforge", "Batteries of the Hold", "Guns come first. Infantry costs more to recruit.",
         [(E_DWF_WM_UPKEEP, 10, BOON), (E_DWF_GT_DMG, 5, BOON), (E_DWF_INF_COST, 10, MALUS)]),
        ("legions", "Clan Hosts", "Equip the clan hosts. The gun batteries must wait.",
         [(E_DWF_INF_COST, 10, BOON), (E_DWF_WM_UPKEEP, 10, MALUS)]),
        ("gunnery", "Thunder and Iron", "Engineers train the gun crews and Thunderers. Recruits cost more.",
         [(E_DWF_THUNDER, 10, BOON), (E_DWF_ART_RANK, 1, BOON), (E_RECRUIT, 5, MALUS)]),
    ]),
]

DWF_CONTROL_BANDS = [
    ("grip", 75, "An Iron Grip on the Court",
     "Every clan accepts the king's authority.",
     [(E_ORDER, 6, BOON), (E_GDP, 12, BOON), (E_UPKEEP, 15, BOON),
      (E_DWF_OATHGOLD, 5, BOON)]),
    ("mastery", 60, "Master of the Court",
     "The elders grumble but honour the king's decisions.",
     [(E_ORDER, 4, BOON), (E_GDP, 8, BOON), (E_UPKEEP, 10, BOON)]),
    ("command", 40, "In Command of the Court",
     "The king must hear the clans before he rules.",
     [(E_ORDER, 2, BOON)]),
    ("contested", 10, "A Contested Court",
     "The clans bargain over each royal decree.",
     [(E_ORDER, 2, MALUS), (E_UPKEEP, 5, MALUS)]),
    ("lost", 0, "The Court Is Not Yours",
     "The clan elders decide matters without the king.",
     [(E_ORDER, 8, MALUS), (E_UPKEEP, 20, MALUS), (E_GDP, 15, MALUS),
      (E_DWF_OATHGOLD, 5, MALUS)]),
]

DWF_TIER_NAME = {1: "The First Seats", 2: "The Elders' Bench", 3: "The Long Hall",
                 4: "The Hall Doors"}

DWF_STANDING_BAND = {
    0: ("Unproven at Court",
        "The court has yet to learn his name.",
        "Too little influence for any seat at court. Influence is earned by "
        "winning battles, taking settlements, gaining ranks and holding a seat."),
    4: ("Noticed at Court",
        "The court has begun to say his name.",
        "Has enough influence for a seat at the Hall Doors, the lowest tier."),
    3: ("Spoken For at Court",
        "A clan elder has spoken for him at court.",
        "Has enough influence for a seat in the Long Hall."),
    2: ("Weighed at Court",
        "The longbeards have stopped talking over him when he speaks.",
        "Has enough influence for a seat on the Elders' Bench."),
    1: ("Fit for the First Seats",
        "There is no seat above him but the throne's own.",
        "Has enough influence for any seat, the First Seats included."),
}

RACES["dwf"] = {
    "infix": "dwf_",
    "prefix": "DWF",
    "ORIGINS": DWF_ORIGINS,
    "NOT_AN_ORIGIN": DWF_NOT_AN_ORIGIN,
    "ORIGIN_COLOUR": DWF_ORIGIN_COLOUR,
    "PARTIES": DWF_PARTIES,
    "PARTY_GOV_BLURB": DWF_PARTY_GOV_BLURB,
    "BACKGROUNDS": DWF_BACKGROUNDS,
    "BG_COLOUR": DWF_BG_COLOUR,
    "OFFICES": DWF_OFFICES,
    "GOVERNMENTS": DWF_GOVERNMENTS,
    "LAWS": DWF_LAWS,
    "CONTROL_BANDS": DWF_CONTROL_BANDS,
    "GOVERNOR_BASE": [(E_ORDER, 2, BOON), (E_DWF_GROWTH_GOV, 5, BOON)],
    "ENVOY_EFFECT": {"ctl": E_ENVOY_CTL, "oath": E_ENVOY_OATH,
                     "grow": E_ENVOY_GROW, "rec": E_ENVOY_REC},
    "ENVOY_BLURB": {
        "ctl": "The king's envoy settles disputes here.",
        "oath": "The king's envoy collects Oathgold from the forges.",
        "grow": "The king's envoy sees to the holdfarms.",
        "rec": "The king's envoy reduces the cost of the clan muster.",
    },
    "TIER_NAME": DWF_TIER_NAME,
    "STANDING_BAND": DWF_STANDING_BAND,
    # THE BODY party_drawn PASSES, one per party a Dwarf deed draws.
    "PARTY_DRAWN": {
        "legion": "Your victories drew the Clan Warriors to court. Your newest lord has joined them, and they will expect seats.",
        "tower": "Your research drew the Runesmiths to court. Your newest lord has joined them, and they will expect seats.",
    },
    # THE EVENTS IN DWF.EVENT_LOC: title, primary (subtitle), secondary (body).
    "EVENT_TEXT": {
        "gov_intro": (
            "Your Deeds Move the Court",
            "Victory and Research Count",
            "Victory strengthens the Clan Warriors at court. Research strengthens the Runesmiths. A strong party asks for its own government. The throne's box shows who rules the court."),
        "realm_secede": (
            "A Rival Court Splits",
            "Oathbreakers in Arms",
            "A party has broken from another hold's court and risen in rebellion "
            "with an army of its own."),
    },
    "BUNDLE_ICON": "trait_dwarf.png",
}
# THE DWARF TABLES' FILE: race_lua("DWF") / lua_table(name, "DWF") read it.
LUA_OF_PREFIX["DWF"] = "zzz_derpy_iron_court_dwarf.lua"
_MOD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "Modding Files", "pack", "script", "campaign", "mod")


def tier_seats(race="chd"):
    """{tier: seats}, counted off the race's own OFFICES - the shape, never typed."""
    out = {}
    for office in RACES[race]["OFFICES"]:
        out[office["tier"]] = out.get(office["tier"], 0) + 1
    return out


def race_lua(prefix="IC"):
    """The text of the file that declares `prefix`'s tables."""
    return io.open(os.path.join(_MOD_DIR, LUA_OF_PREFIX[prefix]), encoding="utf-8").read()


def lua_table(name, prefix="IC", src=None):
    """The body of `<prefix>.<name> = {` up to its column-0 `}`, or None."""
    m = re.search(r"^%s\.%s = \{(.*?)\n\}" % (re.escape(prefix), name),
                  race_lua(prefix) if src is None else src, re.S | re.M)
    return m.group(1) if m else None


def model_law_icons(prefix="IC"):
    """{(category, option): bare effect_bundles picture} from <prefix>.LAWS."""
    body = lua_table("LAWS", prefix)
    out = {}
    if body is None:
        return out
    for cm in re.finditer(r"\n    (\w+) = \{icon = \"[^\"]+\",\s*\n\s*order = \{[^}]*\},\s*\n\s*opts = \{(.*?)\n    \}\}",
                          body, re.S):
        for om in re.finditer(r"(\w+)\s*=\s*\{icon = \"([^\"]+)\"", cm.group(2)):
            out[(cm.group(1), om.group(1))] = om.group(2)
    return out


def control_slugs():
    return [b[0] for b in CONTROL_BANDS]


def bundle_key(kind, slug, race="chd"):
    return "derpy_ic_%s_%s%s" % (kind, RACES[race]["infix"], slug)


def origin_slugs():
    return [h[0] for h in ORIGINS]


def party_slugs():
    return [p[0] for p in PARTIES]


def backgrounds():
    """(party slug, background slug, display), in PARTIES order."""
    out = []
    for party, _d, _e, _m in PARTIES:
        for bg, display in BACKGROUNDS[party]:
            out.append((party, bg, display))
    return out


# THE MOVES, READ OUT OF THE SHIPPED LUA. IC.PLOTS is declared in the model
# and nowhere else, and it is the list the panel draws, the list the player
# clicks and the list IC.plot rolls against - so a copy here would be a fourth
# list that agrees with the other three only until somebody adds a move.
#
# RAISES RATHER THAN FALLING BACK. check()'s rivals_max read can shrug off an
# unreadable file because it only relaxes a check; this one feeds build(), and a
# silent empty list is sixteen missing loc keys and sixteen blank plates.
def model_moves():
    """(key, name) for every IC.PLOTS entry, in the order the model declares."""
    path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "Modding Files", "pack", "script", "campaign", "mod",
        "zzz_derpy_iron_court.lua")
    src = io.open(path, encoding="utf-8").read()
    block = re.search(r"IC\.PLOTS = \{(.*?)\n\}", src, re.S)
    if not block:
        raise RuntimeError("the model Lua declares no IC.PLOTS")
    moves = re.findall(r'\{key = "(\w+)", name = "([^"]+)"', block.group(1))
    if not moves:
        raise RuntimeError("IC.PLOTS parsed to no moves at all")
    return moves


def _model_lua():
    return race_lua("IC")


# RAISES RATHER THAN FALLING BACK, like model_moves: these feed build(), and a
# silent default is a bundle whose value is not the card's.
def model_tune(name):
    """IC.TUNE[name] as the shipped Lua declares it."""
    m = re.search(r"\n\s+%s\s*=\s*(\d+)\s*," % re.escape(name), _model_lua())
    if not m:
        raise RuntimeError("the model Lua declares no IC.TUNE.%s" % name)
    return int(m.group(1))


def model_gov_icons(prefix="IC"):
    """{government slug: bare effect_bundles picture} from <prefix>.GOVS."""
    body = lua_table("GOVS", prefix)
    if body is None:
        raise RuntimeError("the model Lua declares no %s.GOVS" % prefix)
    return dict(re.findall(r'(\w+)\s*=\s*\{icon = "([^"]+)"', body))


def model_envoy_tasks():
    """[(code, name, knob, bundle, icon)] from IC.ENVOY_TASKS, in its order."""
    block = re.search(r"IC\.ENVOY_TASKS = \{(.*?)\n\}", _model_lua(), re.S)
    if not block:
        raise RuntimeError("the model Lua declares no IC.ENVOY_TASKS")
    tasks = re.findall(
        r'\{code = "(\w+)", name = "([^"]+)", knob = "(\w+)", fmt = "[^"]*",\s*'
        r'bundle = "(\w+)", icon = "([^"]+)"\}', block.group(1))
    if len(tasks) != 4:
        raise RuntimeError("IC.ENVOY_TASKS parsed to %d tasks, not 4" % len(tasks))
    return tasks


# THE PARTY NAME TAILS, READ OUT OF THE SHIPPED LUA for the same reason as the
# moves: IC.NAME_TAILS is what the roll lands on and what the panel draws, and a
# party trait is keyed by the tail's position in it (IC.member_trait).
def model_tails(prefix="IC"):
    """{interest slug: [tail, ...]} in the order the model declares them."""
    body = lua_table("NAME_TAILS", prefix)
    if body is None:
        raise RuntimeError("the model Lua declares no %s.NAME_TAILS" % prefix)
    tails = {slug: re.findall(r'"([^"]+)"', b)
             for slug, b in re.findall(r"(\w+)\s*=\s*\{(.*?)\}", body, re.S)}
    if not tails:
        raise RuntimeError("%s.NAME_TAILS parsed to no parties at all" % prefix)
    return tails


# THE DWARF RACE'S TABLES, READ OUT OF ITS OWN FILE
# the way the Chaos Dwarf ones are read out of the model. Raises rather than
# falling back: these feed build().
DWF_LUA = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "Modding Files", "pack", "script", "campaign", "mod",
    "zzz_derpy_iron_court_dwarf.lua")

# WHAT emit_dwf WROTE, by kind, for check_dwf; refilled by every build().
DWF_ROWS = {}


def _dwf_src():
    return io.open(DWF_LUA, encoding="utf-8").read()


def _dwf_block(name):
    """The body of a column-0 DWF.<name> = { ... } - lua_table, the one
    scraper (anchored at column 0); never a second regex."""
    body = lua_table(name, "DWF")
    if body is None:
        raise RuntimeError("the Dwarf Lua declares no DWF.%s" % name)
    return body


def _dwf_list(name):
    """A one-line DWF.<name> = {"a", "b"} list."""
    m = re.search(r"^DWF\.%s = \{([^}]*)\}" % re.escape(name), _dwf_src(), re.M)
    if not m:
        raise RuntimeError("the Dwarf Lua declares no DWF.%s" % name)
    return re.findall(r'"(\w+)"', m.group(1))


def dwf_origins():
    return [(s, f) for s, f in re.findall(
        r'\{slug = "(\w+)"(?:,\s*faction = "(\w+)")?\}', _dwf_block("ORIGINS"))]


def dwf_offices():
    return [(s, a, int(t)) for s, a, t in re.findall(
        r'\{slug = "(\w+)",\s*affinity = "(\w+)",\s*tier = (\d)\}', _dwf_block("OFFICES"))]










def dwf_envoy_tasks():
    tasks = re.findall(
        r'\{code = "(\w+)", name = "([^"]+)", knob = "(\w+)", fmt = "[^"]*",\s*'
        r'bundle = "(\w+)", icon = "([^"]+)"\}', _dwf_block("ENVOY_TASKS"))
    if len(tasks) != 4:
        raise RuntimeError("DWF.ENVOY_TASKS parsed to %d tasks, not 4" % len(tasks))
    return tasks




def dwf_start_gov():
    return dict(re.findall(r'(\w+) = "(\w+)"', _dwf_block("START_GOV")))


def dwf_plot_names():
    return dict(re.findall(r'\n    (\w+) = \{name = "([^"]+)"', _dwf_block("PLOT_TEXT")))


def emit_dwf(emit, emit_trait, emit_member, loc):
    """Every Dwarf bundle, trait and loc row. Each key is bundle_key(kind, slug,
    "dwf"), the Lua's IC.key with the dwf_ infix."""
    R = RACES["dwf"]
    icon = R["BUNDLE_ICON"]

    def K(kind, slug):
        return bundle_key(kind, slug, "dwf")

    def text(key, value):
        loc.append({"key": key, "text": value, "tooltip": "false"})

    for office in R["OFFICES"]:
        up = [(e, tier_value(office["tier"], b), i) for e, b, i in office["effects"]]
        down = [(e, tier_value(office["tier"], b), i) for e, b, i in office["vacancy"]]
        emit(K("office", office["slug"]), office["name"], office["blurb"], "faction", up, icon=icon)
        emit(K("vacant", office["slug"]), office["name"] + " (Vacant)",
             office["vacant_blurb"], "faction", down, icon=icon)
        text(K("office_name", office["slug"]), office["name"])
        emit_trait(K("title", office["slug"]), office["name"], office["blurb"],
                   ", ".join(effect_line(e, m, i) for e, m, i in up),
                   "He no longer holds the office.", "derpy_ic_cat_office")
    for slug, _floor, name, blurb, effects in R["CONTROL_BANDS"]:
        emit(K("control", slug), name, blurb, "faction", effects, icon=icon)
        text(K("control_name", slug), name)
    gov_icons = model_gov_icons("DWF")
    for slug, name, rule, blurb, effects in R["GOVERNMENTS"]:
        emit(K("doctrine", slug), name, blurb, "faction", effects, icon=gov_icons.get(slug))
        text(K("doctrine_name", slug), name)
        text(K("doctrine_rule", slug), rule)
    law_icons = model_law_icons("DWF")
    for cat, cat_name, _icon, options in R["LAWS"]:
        text(K("law_cat", cat), cat_name)
        for opt, name, blurb, effects in options:
            emit(K("law", cat + "_" + opt), name, blurb, "faction", effects,
                 icon=law_icons.get((cat, opt)))
            text(K("law_name", cat + "_" + opt), name)
            for n, (e, m, intent) in enumerate(effects, start=1):
                text(K("law_fx%d" % n, cat + "_" + opt), effect_line(e, m, intent))
    emit(K("gov", "base"), "Governor of the Province",
         "The king's governor answers for this province.",
         "faction", R["GOVERNOR_BASE"], icon=icon)
    for slug, display, effect, magnitude in R["PARTIES"]:
        emit(K("gov_house", slug), "Governor: " + display, R["PARTY_GOV_BLURB"][slug],
             "faction", [(effect, magnitude, BOON)], icon=icon)
        text(K("party_name", slug), display)
    for code, name, knob, bundle, b_icon in dwf_envoy_tasks():
        emit(bundle, "Envoy: " + name, R["ENVOY_BLURB"][code], "province",
             [(R["ENVOY_EFFECT"][code], model_tune(knob), BOON)], icon=b_icon)
    for slug, _faction, display in R["ORIGINS"]:
        text(K("origin_name", slug), display)
        emit_trait(K("house", slug), "Born: " + display[0].upper() + display[1:],
                   R["ORIGIN_COLOUR"][slug], "Where he was born. It has no effect at court.",
                   "His origin has been struck from the rolls.", "derpy_ic_cat_origin")
    for party, _d, _e, _m in R["PARTIES"]:
        for slug, display in R["BACKGROUNDS"][party]:
            text(K("bg_name", slug), display)
            emit_trait(K("bg", slug), display, R["BG_COLOUR"][slug],
                       "His former trade. It decides which party he sits with.",
                       "He no longer follows this trade.", party_cat(party))
    for tier in [0] + sorted(R["TIER_NAME"]):
        name, colour, explain = R["STANDING_BAND"][tier]
        emit_trait(K("standing", str(tier)), name, colour, explain,
                   "His influence at court has changed.", "derpy_ic_cat_standing")
    for slug in ("cautious", "steady", "ambitious"):
        name, colour, explain = AMBITION_BANDS[slug]
        emit_trait(K("ambition", slug), name, colour, explain,
                   "His ambition does not change.", "derpy_ic_cat_ambition")
    emit_member(K("member", CROWN), "the Throne-Sworn", party_cat(CROWN),
                DWF_MEMBER_FLAVOUR[CROWN])
    for slug, _faction, display in R["ORIGINS"]:
        emit_member(K("member", slug), display, "derpy_ic_cat_confed",
                    DWF_MEMBER_FLAVOUR["confed"])
    tails = model_tails("DWF")
    for party, _d, _e, _m in R["PARTIES"]:
        if party != CROWN:
            for n, tail in enumerate(tails[party], 1):
                emit_member("%s_%d" % (K("member", party), n), tail, party_cat(party),
                            DWF_MEMBER_FLAVOUR[party])
    for slug, (title, primary, secondary) in sorted(R["EVENT_TEXT"].items()):
        stem = "event_feed_strings_text_" + K("event", slug)
        text(stem + "_title", title)
        text(stem + "_primary", primary)
        text(stem + "_secondary", secondary)
    for party, line in sorted(R["PARTY_DRAWN"].items()):
        text("event_feed_strings_text_" + K("event_party_drawn", party), line)
    keys = set(re.findall(r'"(\w+)"', _dwf_block("PLOT_KEYS")))
    names = dwf_plot_names()
    for move_key, move_name in model_moves():
        if move_key in keys:
            name = names.get(move_key, move_name)
            text("event_feed_strings_text_" + K("move", move_key) + "_ok", name + ": Success")
            text("event_feed_strings_text_" + K("move", move_key) + "_fail", name + ": Failure")
def member_trait_key(slug, index=None, race="chd"):
    """The key IC.member_trait builds: the Crown, a confederate origin, or a tail."""
    key = bundle_key("member", slug, race)
    return key if index is None else "%s_%d" % (key, index)


def move_result_key(move_key, ok):
    """The loc key IC.move_result_key builds at the other end of the fence."""
    return ("event_feed_strings_text_derpy_ic_move_" + move_key
            + ("_ok" if ok else "_fail"))


def office_by_slug(slug):
    for office in OFFICES:
        if office["slug"] == slug:
            return office
    return None


def build():
    bundles = []
    junctions = []
    loc = []

    def emit(key, title, description, target, effects, icon=None):
        """One bundle: the DB row, its effect junctions, and BOTH loc entries.

        The row text and the loc are written from the same two strings on
        purpose. Row text alone draws an icon with no text in the Faction
        Effects panel (measured over 27 bundles). CA ships both, 11,710
        entries deep.
        """
        bundles.append({
            "key": key,
            "localised_description": description,
            "localised_title": title,
            "bundle_target": target,
            "priority": "1",
            "ui_icon": icon or BUNDLE_ICON,
            # A live bundle with is_global_effect false is hidden from the
            # Faction Effects panel. These are all meant to be read.
            "is_global_effect": "true",
            "show_in_3d_space": "false",
            "owner_only": "true",
        })
        for effect, magnitude, intent in effects:
            junctions.append({
                "effect_bundle_key": key,
                "effect_key": effect[0],
                "effect_scope": effect[1],
                "value": "%.1f" % signed_value(effect, magnitude, intent),
                "advancement_stage": ADVANCEMENT_STAGE,
            })
        # A bundle description is a plain sentence. %+n works on an EFFECT
        # description because the engine substitutes that effect's value; a
        # bundle names a whole set and has no single value, so a placeholder
        # renders literally. 1 of 5,855 vanilla bundle descriptions has one.
        assert "%+n" not in description, "bundle descriptions take no placeholder"
        loc.append({"key": "effect_bundles_localised_title_" + key,
                    "text": title, "tooltip": "false"})
        loc.append({"key": "effect_bundles_localised_description_" + key,
                    "text": description, "tooltip": "false"})
        # NO LINE FOR A BUNDLE WITH NO EFFECTS (a law's start option): a blank
        # value draws nothing, and the panel says "No effects" itself.
        if effects:
            loc.append({"key": "derpy_ic_effects_" + key,
                        "text": ", ".join(effect_short(e, m, i)
                                          for e, m, i in effects),
                        "tooltip": "false"})

    def scaled(office, which):
        """Tier-4 magnitudes raised to the tier that holds the office."""
        return [(e, tier_value(office["tier"], base), intent)
                for e, base, intent in office[which]]

    for office in OFFICES:
        emit(bundle_key("office", office["slug"]),
             office["name"], office["blurb"], "faction",
             scaled(office, "effects"))
        emit(bundle_key("vacant", office["slug"]),
             office["name"] + " (Vacant)", office["vacant_blurb"],
             "faction", scaled(office, "vacancy"))

    # ONE PER BAND, and the model puts exactly one of them on the faction.
    for slug, floor, name, blurb, effects in CONTROL_BANDS:
        emit(bundle_key("control", slug), name, blurb, "faction", effects)
        # The band's own name, for the panel: it is drawn at the top of the
        # court every turn and a loc call from a turn handler is a turn-1 CTD.
        loc.append({"key": bundle_key("control_name", slug),
                    "text": name, "tooltip": "false"})

    # ONE PER GOVERNMENT, and the model puts exactly one of them on the faction.
    # "doctrine", not "gov": the governors' bundles already use derpy_ic_gov_.
    gov_icons = model_gov_icons()
    for slug, name, rule, blurb, effects in GOVERNMENTS:
        emit(bundle_key("doctrine", slug), name, blurb, "faction", effects,
             icon=gov_icons.get(slug))
        # Name and rule for the panel, read at draw time and never from a turn
        # handler (a loc call there is a turn-1 CTD).
        loc.append({"key": bundle_key("doctrine_name", slug),
                    "text": name, "tooltip": "false"})
        loc.append({"key": bundle_key("doctrine_rule", slug),
                    "text": rule, "tooltip": "false"})

    # ONE PER LAW, and the model puts one per category on
    # a player faction. The start options have no effects: a bundle so the
    # Faction Effects panel still names the law in force.
    law_icons = model_law_icons()
    for cat, cat_name, _icon, options in LAWS:
        loc.append({"key": bundle_key("law_cat", cat), "text": cat_name, "tooltip": "false"})
        for opt, name, blurb, effects in options:
            key = bundle_key("law", "%s_%s" % (cat, opt))
            emit(key, name, blurb, "faction", effects, icon=law_icons.get((cat, opt)))
            loc.append({"key": bundle_key("law_name", "%s_%s" % (cat, opt)), "text": name,
                        "tooltip": "false"})
            for i, (e, m, intent) in enumerate(effects, start=1):
                loc.append({"key": bundle_key("law_fx%d" % i, "%s_%s" % (cat, opt)),
                            "text": effect_line(e, m, intent), "tooltip": "false"})

    emit("derpy_ic_gov_base", "Governor of the Province",
         "The court's governor rules this province.",
         "faction", GOVERNOR_BASE)

    # ONE PER PARTY, and the key kept the "gov_house" stem so a save made
    # before the change still names a bundle that exists when the model
    # takes the old one off. The nine parties replace sixteen houses.
    for slug, display, effect, magnitude in PARTIES:
        emit(bundle_key("gov_house", slug),
             "Governor: " + display, PARTY_GOV_BLURB[slug],
             "faction", [(effect, magnitude, BOON)])

    # THE ENVOY'S FOUR: one province, for
    # IC.TUNE.mission_turns, in CA's province-bundle shape. The value is the
    # model's own knob.
    for code, name, knob, bundle, icon in model_envoy_tasks():
        emit(bundle, "Envoy: " + name, ENVOY_BLURB[code], "province",
             [(ENVOY_EFFECT[code], model_tune(knob), BOON)], icon=icon)

    # Office and house names are read by the panel at draw time, never from a
    # turn handler - a loc call inside one is a turn-1 CTD that pcall does not
    # catch.
    for office in OFFICES:
        loc.append({"key": bundle_key("office_name", office["slug"]),
                    "text": office["name"], "tooltip": "false"})
    # A PARTY'S NAME IS ROLLED and lives in the save, so this is only the
    # generic fallback - what the panel draws before a court has been
    # rolled, and what the crown would be called if the faction it
    # belongs to somehow has no screen name of its own.
    for slug, display, _effect, _mag in PARTIES:
        loc.append({"key": bundle_key("party_name", slug),
                    "text": display, "tooltip": "false"})
    # ORIGINS AND BACKGROUNDS IN ROW FORM. The trait carries its own name
    # ("Born: the House of Khorakk"), which is the right shape for a
    # character panel and the wrong one for a column.
    for slug, _faction, display in ORIGINS:
        loc.append({"key": bundle_key("origin_name", slug),
                    "text": display, "tooltip": "false"})
    for _party, slug, display in backgrounds():
        loc.append({"key": bundle_key("bg_name", slug),
                    "text": display, "tooltip": "false"})

    # Traits.
    trait_info = []
    traits = []
    trait_levels = []

    def emit_trait(key, name, colour, explanation, removal, cat):
        # trait_info is the table a trace outward never reaches: one row per
        # trait, one column, and vanilla's count matches character_traits exactly.
        trait_info.append({"trait": key})
        traits.append({
            "key": key,
            "no_going_back_level": "1",
            "hidden": "false",
            "precedence": "1",
            "icon": cat,
            "ui_priority": "1",
            "pre_battle_speech_parameter": "",
            "remove_on_skill_reset": "false",
        })
        # Single level, keyed the same as the trait - CA's own convention.
        trait_levels.append({
            "key": key,
            "level": "1",
            "trait": key,
            "threshold_points": "1",
        })
        # All four trait loc keys hang off the LEVEL key, and all of them live in
        # character_trait_levels__.loc. There is no character_traits__.loc at all.
        for suffix, text in (("onscreen_name", name),
                             ("colour_text", colour),
                             ("explanation_text", explanation),
                             ("removal_text", removal)):
            loc.append({"key": "character_trait_levels_%s_%s" % (suffix, key),
                        "text": text, "tooltip": "false"})

    # ONE BAND PER TIER, plus the man who clears none. Emitted from the same
    # tier tables the ziggurat is built from, so a tier added or removed carries
    # its band with it instead of leaving a key nothing ever stamps.
    for _tier in [0] + sorted(TIER_NAME):
        _name, _colour, _explain = STANDING_BAND[_tier]
        emit_trait(standing_trait_key(_tier), _name, _colour, _explain,
                   "His influence at court has changed.", "derpy_ic_cat_standing")

    for _slug in ("cautious", "steady", "ambitious"):
        _name, _colour, _explain = AMBITION_BANDS[_slug]
        emit_trait("derpy_ic_ambition_" + _slug, _name, _colour, _explain,
                   "His ambition does not change.", "derpy_ic_cat_ambition")

    # WHERE HE IS FROM. Flavour and nothing else - an origin moves no
    # number in the court. Were it his politics, a lord you recruited
    # yourself would want what his grandfather's faction wanted, forever.
    for slug, _faction, display in ORIGINS:
        emit_trait(origin_trait_key(slug),
                   "Born: " + display[0].upper() + display[1:],
                   ORIGIN_COLOUR[slug],
                   "Where he was born. It has no effect at court.",
                   "His origin has been struck from the rolls.", "derpy_ic_cat_origin")

    # WHAT HE IS, which is the whole of the membership rule. A background
    # belongs to one party; a lord sits with the party his background
    # names, and with the crown when that party is not organised.
    for party, slug, display in backgrounds():
        emit_trait(bg_trait_key(slug),
                   display,
                   BG_COLOUR[slug],
                   "His former trade. It decides which party he sits with.",
                   "He no longer follows this trade.", party_cat(party))

    # WHICH PARTY HE SITS WITH, shown on the character panel. Kept in step by IC.stamp_members at
    # the end of every turn. A rolled party is named by its tail, the part of
    # "Covenant of the Cold Anvil" that tells two parties apart; a confederate
    # party by the faction it was.
    def emit_member(key, party, cat, flavour):
        emit_trait(key, "Party: " + party[0].upper() + party[1:],
                   flavour,
                   "His party at court. Changes when parties form, break away or dissolve.",
                   "He sits with another party now.", cat)

    emit_member(member_trait_key(CROWN), "the Crown", party_cat(CROWN),
                MEMBER_FLAVOUR[CROWN])
    for slug, _faction, display in ORIGINS:
        emit_member(member_trait_key(slug), display, "derpy_ic_cat_confed",
                    MEMBER_FLAVOUR["confed"])
    tails = model_tails()
    for party, _d, _e, _m in PARTIES:
        if party != CROWN:
            for i, tail in enumerate(tails[party], 1):
                emit_member(member_trait_key(party, i), tail, party_cat(party),
                            MEMBER_FLAVOUR[party])

    for office in OFFICES:
        # ONE LINE, and deliberately so. Vanilla does put doubled newlines in
        # trait explanation_text (16 of them, all wh3_main_trait_realm_*), but a
        # newline inside a TSV FIELD splits the row - the gate caught exactly that,
        # counting 174 rows where build() made 161 - and TSV has no portable escape
        # for one. A single line needs no escaping at all.
        #
        # The effects and nothing else. "He was raised to this office by your word"
        # said what the title already says; the effects are what the tooltip was
        # missing, and what a player actually scans a trait for.
        emit_trait(office_trait_key(office["slug"]),
                   office["name"],
                   office["blurb"],
                   ", ".join(effect_line(e, m, i)
                             for e, m, i in scaled(office, "effects")),
                   "He no longer holds the office.",
                   "derpy_ic_cat_office")

    # The event feed.
    # FOUR ROWS PER EVENT, and three of the four tables exist only to turn a
    # number into a record. The group and the member are given different names
    # on purpose, the way vanilla does it (wh3_dlc27_event_group_old_gods_curse
    # holds wh3_dlc27_event_feed_scripted_old_gods_curse): they are different
    # things, and a single name for both hides which side a broken link is on.
    groups, members, criteria, feed = [], [], [], []
    for slug, persistent, image, sound, title, primary, secondary in EVENTS:
        key = event_key(slug)
        # THE RECORDS, ONE RUN PER RACE (RACE_EVENT_OFFSET). The loc is the
        # model's to pick by race (IC.event_stem), so it is written once.
        for race in ("chd", "dwf"):
            rkey = key if race == "chd" else key + "_" + race
            group_id = rkey + "_group"
            groups.append({"id": group_id})
            members.append({"group": group_id, "id": rkey, "priority": "0.0"})
            criteria.append({"member": rkey, "value": str(event_index(slug, race))})
            # IN THE DEFINITION'S OWN FIELD ORDER. write_tsvs takes the column
            # order off the first row's keys, so a dict built in a convenient
            # order writes a header CA's definition does not match.
            mine = {
                "event": ("scripted_transient_located_event" if slug in LOCATED_EVENTS
                          else "scripted_persistent_event" if persistent
                          else "scripted_transient_event"),
                "group": group_id,
                "image": event_image(image, race),
                "sound_event": "UI_CAM_POPUP_Message_Event_" + sound,
                # instant_open MUST agree with the event type. All 93 vanilla
                # persistent rows are true and all 4 transient rows are false;
                # this is not a preference, it is what the type means.
                "instant_open": "true" if persistent else "false",
            }
            row = {}
            for col in EVENT_COLS:
                row[col] = mine.get(col, EVENT_FIXED.get(col))
                assert row[col] is not None, "no value for event column " + col
            feed.append(row)
        loc.append({"key": "event_feed_strings_text_" + key + "_title",
                    "text": title, "tooltip": "false"})
        loc.append({"key": "event_feed_strings_text_" + key + "_primary",
                    "text": primary, "tooltip": "false"})
        loc.append({"key": "event_feed_strings_text_" + key + "_secondary",
                    "text": secondary, "tooltip": "false"})
    for party, text in sorted(PARTY_DRAWN.items()):
        loc.append({"key": "event_feed_strings_text_derpy_ic_event_party_drawn_" + party,
                    "text": text, "tooltip": "false"})

    # AND THE PER-MOVE LINES THE PLOT CARDS PREFER, as their subtitle. The
    # generic plot_ok and plot_fail subtitles above stay as the fallback:
    # IC.raise_feed takes the caller's key when it has one.
    #
    # CA'S OWN FORM, "Scout Ruins - Success!": title case, never capitals (CA
    # ships 0 event feed strings in capitals of 910).
    for move_key, move_name in model_moves():
        loc.append({"key": move_result_key(move_key, True),
                    "text": move_name + ": Success",
                    "tooltip": "false"})
        loc.append({"key": move_result_key(move_key, False),
                    "text": move_name + ": Failure",
                    "tooltip": "false"})

    # THE DWARFS, after every Chaos Dwarf row so none
    # of those moves; what they wrote is kept for check_dwf.
    _was = (len(bundles), len(traits), len(loc))
    emit_dwf(emit, emit_trait, emit_member, loc)
    DWF_ROWS["bundles"] = [r["key"] for r in bundles[_was[0]:]]
    DWF_ROWS["traits"] = [r["key"] for r in traits[_was[1]:]]
    DWF_ROWS["loc"] = [r["key"] for r in loc[_was[2]:]]
    missions = []
    for key, title, desc, done, objective in DEMANDS:
        missions.append({
            "key": key, "mission_type": "SCRIPTED",
            "localised_title": title, "localised_description": desc,
            "ui_image": "chd/diplomacy", "ui_icon": "rom_event_mission.png",
            "generate": "false", "prioritised": "false",
            "event_category": "Quest", "set_piece_battle": "",
            "location_x": "0", "location_y": "0",
            "quest_mission": "false", "quest_mission_final": "false",
            "trigger_radius": "0.0000", "quest_character": "",
            "sticky_by_default": "false",
            "localised_mission_completed_text": done,
            "can_be_manually_cancelled": "false",
        })
        for field, text in (("title", title), ("description", desc),
                            ("mission_completed_text", done)):
            loc.append({"key": "missions_localised_%s_%s" % (field, key),
                        "text": text, "tooltip": "false"})
        loc.append({"key": "mission_text_text_" + key, "text": objective,
                    "tooltip": "false"})
    payload_ui = [{"component": DEMAND_REWARD,
                   "icon": "ui/skins/default/icon_check.png",
                   "state": "positive", "sort_order": "0"}]
    loc.append({"key": "campaign_payload_ui_details_description_" + DEMAND_REWARD,
                "text": DEMAND_REWARD_TEXT, "tooltip": "false"})

    return {"effect_bundles": bundles,
            "effect_bundles_to_effects_junctions": junctions,
            "trait_info": trait_info,
            "character_traits": traits,
            "character_trait_levels": trait_levels,
            "trait_categories": [{"category": k, "icon_path": v}
                                 for k, v in sorted(TRAIT_CATS.items())],
            "campaign_groups": groups,
            "campaign_group_members": members,
            "campaign_group_member_criteria_values": criteria,
            "event_feed_message_events": feed,
            # CA's OWN ROWS, four of them, with flags_path repointed at a crest
            # this pack ships. build_factions is defined below because it reads
            # the donor TSV rather than being written out here - forty-five
            # columns of CA's values are data, not code.
            "factions": build_factions(),
            "missions": missions,
            "campaign_payload_ui_details": payload_ui,
            "loc": loc}


def _cache_table(name):
    path = os.path.join(CACHE, name + ".json")
    if not os.path.isfile(path):
        return None
    with io.open(path, encoding="utf-8") as fh:
        blob = json.load(fh)
    table = blob["VecRFile"][0]["data"]["Decoded"]["DB"]["table"]
    fields = [f["name"] for f in table["definition"]["fields"]]
    rows = [[list(cell.values())[0] for cell in row] for row in table["table_data"]]
    return fields, rows


# The Lua reads these; the check below re-derives them from the DB so a patch
# that moves them fails the build rather than the campaign.
REBEL_POOL = [
    "wh3_dlc23_chd_chaos_dwarfs_qb1",
    "wh3_dlc23_chd_chaos_dwarfs_qb2",
    "wh3_dlc23_chd_chaos_dwarfs_qb3",
    "wh3_dlc25_chd_chaos_dwarfs_invasion",
]


def _lua_rebel_generals(prefix="IC"):
    """<prefix>.REBEL_GENERALS and IC.REBEL_LORD, read out of the shipped Lua."""
    body = lua_table("REBEL_GENERALS", prefix)
    keys = set(re.findall(r'\["([^"]+)"\]\s*=\s*true', body)) if body is not None else set()
    lord = re.search(r'IC\.REBEL_LORD = "([^"]+)"', _model_lua())
    return keys, (lord.group(1) if lord else None)


def _lua_not_dwarf():
    """IC.NOT_DWARF and IC.LORD_HISTORY's keys, read out of the shipped Lua."""
    path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "Modding Files", "pack", "script", "campaign", "mod",
        "zzz_derpy_iron_court.lua")
    src = io.open(path, encoding="utf-8").read()
    block = re.search(r"IC\.NOT_DWARF = \{(.*?)\n\}", src, re.S)
    keys = set(re.findall(r'\["([^"]+)"\]\s*=\s*true', block.group(1))) \
        if block else set()
    hist = set(re.findall(r"^\s{4}(\w+)\s*=\s*\{origin", src, re.M))
    return keys, hist, block is not None


# THE TOKENS THAT MEAN GREENSKIN, matched against the VOICE and the unit and
# never against the subtype key - wh3_dlc23_chd_overseer_hobgoblin_spawned_army
# is a Chaos Dwarf whose key says otherwise.
_GREEN = ("hobgoblin", "goblin", "greenskin", "_grn_", "_orc_")


def check_not_dwarf():
    out = []
    perm = _cache_table("faction_agent_permitted_subtypes")
    agents = _cache_table("agent_subtypes")
    if perm is None or agents is None:
        return ["faction_agent_permitted_subtypes / agent_subtypes not cached - "
                "run tools/fetch_vanilla_tables.py for both"]
    pf, pr = perm
    fi, si = pf.index("faction"), pf.index("subtype")
    di = pf.index("mod_disabled") if "mod_disabled" in pf else None
    af, ar = agents
    ki = af.index("key")
    vi = af.index("audio_voiceover_actor_group")
    ui = af.index("associated_unit_override")
    sub = {r[ki]: (str(r[vi]).lower(), str(r[ui]).lower()) for r in ar}

    have, hist, found = _lua_not_dwarf()
    if not found:
        return ["IC.NOT_DWARF not found in zzz_derpy_iron_court.lua"]
    if not hist:
        return ["IC.LORD_HISTORY read back empty - the check cannot run"]

    # EVERY LORD A CHAOS DWARF FACTION CAN PUT IN FRONT OF A HOUSE.
    cand = set(hist)
    for r in pr:
        if "chd" not in str(r[fi]):
            continue
        if di is not None and r[di]:
            continue
        cand.add(str(r[si]))

    want = set()
    for key in cand:
        vo, unit = sub.get(key, ("", ""))
        if any(g in vo for g in _GREEN) or any(g in unit for g in _GREEN):
            want.add(key)

    for key in sorted(want - have):
        out.append("IC.NOT_DWARF is missing %s, which a Chaos Dwarf faction may "
                   "field and which is a greenskin by its voice or its unit"
                   % key)
    for key in sorted(have - want):
        out.append("IC.NOT_DWARF lists %s, which the DB does not call a "
                   "greenskin - a Chaos Dwarf lord struck off this list cannot "
                   "speak for his own house" % key)
    return out


def check_rebel_generals():
    out = []
    table = _cache_table("faction_agent_permitted_subtypes")
    if table is None:
        return ["faction_agent_permitted_subtypes not cached - run "
                "tools/fetch_vanilla_tables.py faction_agent_permitted_subtypes"]
    fields, rows = table
    fi, ai = fields.index("faction"), fields.index("agent")
    si = fields.index("subtype")
    di = fields.index("mod_disabled") if "mod_disabled" in fields else None
    per = {}
    for r in rows:
        if r[fi] in REBEL_POOL and r[ai] == "general":
            if di is not None and r[di]:
                continue
            per.setdefault(r[fi], set()).add(r[si])
    missing = [f for f in REBEL_POOL if f not in per]
    if missing:
        return ["no permitted general subtypes in the DB for: %s"
                % ", ".join(missing)]
    # EVERY pool faction, not any: the pool is walked in order and a fifth
    # secession reuses it from the top, so a subtype only three of them accept
    # is a crash waiting for the fourth party to leave.
    want = set.intersection(*per.values())
    have, lord = _lua_rebel_generals()
    if not have:
        return ["IC.REBEL_GENERALS not found in zzz_derpy_iron_court.lua"]
    for key in sorted(have - want):
        out.append("IC.REBEL_GENERALS lists %s, which not every faction in "
                   "REBEL_POOL may field as a general" % key)
    for key in sorted(want - have):
        out.append("IC.REBEL_GENERALS is missing %s, which all four pool "
                   "factions permit" % key)
    # THE FALLBACK IS THE HALF THAT WAS ALREADY WRONG. The Castellan is
    # permitted for all four - as an engineer - and was the fallback anyway.
    if lord not in want:
        out.append("IC.REBEL_LORD is %s, which no faction in REBEL_POOL may "
                   "field as a general (permitted generals: %s)"
                   % (lord, ", ".join(sorted(want))))
    return out


def _lua_rebel_heroes(prefix="IC"):
    """<prefix>.REBEL_HEROES, read out of the shipped Lua."""
    body = lua_table("REBEL_HEROES", prefix)
    if body is None:
        return None
    return dict(re.findall(r'\["([^"]+)"\]\s*=\s*"([^"]+)"', body))


# THE TWO PAIRS THE LIST LEAVES OUT ON PURPOSE, and why. Named here rather than
# subtracted silently, so a future pass that wonders where they went finds the
# answer beside the check instead of rediscovering it from a crash.
REBEL_HERO_EXCLUDED = {
    ("colonel", "wh3_dlc23_chd_overseer"):
        "a lord's subtype wearing a hero's agent type; he is in "
        "IC.REBEL_GENERALS",
    ("spy", "wh3_dlc23_chd_gorduz_backstabber"):
        "a legendary lord; IC.is_legend bars him and a second copy of that "
        "rule here is a second place to get it wrong",
}


def check_rebel_heroes():
    out = []
    table = _cache_table("faction_agent_permitted_subtypes")
    if table is None:
        return ["faction_agent_permitted_subtypes not cached - run "
                "tools/fetch_vanilla_tables.py faction_agent_permitted_subtypes"]
    fields, rows = table
    fi, ai = fields.index("faction"), fields.index("agent")
    si = fields.index("subtype")
    di = fields.index("mod_disabled") if "mod_disabled" in fields else None
    per = {}
    for r in rows:
        if r[fi] in REBEL_POOL and r[ai] != "general":
            if di is not None and r[di]:
                continue
            per.setdefault(r[fi], set()).add((r[ai], r[si]))
    missing = [f for f in REBEL_POOL if f not in per]
    if missing:
        return ["no permitted hero subtypes in the DB for: %s"
                % ", ".join(missing)]
    # EVERY pool faction, not any - the pool is walked in order and reused.
    want = set.intersection(*per.values())
    want = set(p for p in want if p not in REBEL_HERO_EXCLUDED)
    have = _lua_rebel_heroes()
    if have is None:
        return ["IC.REBEL_HEROES not found in zzz_derpy_iron_court.lua"]
    for subtype, agent in sorted(have.items()):
        if (agent, subtype) not in want:
            out.append("IC.REBEL_HEROES pairs %s with %s, which not every "
                       "faction in REBEL_POOL permits" % (subtype, agent))
    for agent, subtype in sorted(want):
        if subtype not in have:
            out.append("IC.REBEL_HEROES is missing %s, which all four pool "
                       "factions permit as a %s" % (subtype, agent))
    # NO OVERLAP TEST. One was written here - a subtype on both lists would be
    # killed as a lord and made again as an agent - and it is unreachable: the
    # only CHD subtype that carries both a general and a non-general agent type
    # is wh3_dlc23_chd_overseer, which REBEL_HERO_EXCLUDED already removes, so
    # anything on both lists is reported by the pairing test above first.
    # Watched for, could not be made to fire, removed rather than left green.
    return out

def _lua_rebel_roster(prefix="IC"):
    """<prefix>.REBEL_POOLS (role -> unit keys), <prefix>.REBEL_DRAFT (the roles in
    slot order) and IC.TUNE.rebel_units, read out of the shipped Lua."""
    src = race_lua(prefix)
    pools = {}
    body = lua_table("REBEL_POOLS", prefix, src)
    if body is not None:
        for role, b in re.findall(r"(\w+) = \{(.*?)\n    \},", body, re.S):
            pools[role] = re.findall(r'\{"([^"]+)", (\d+)\}', b)
    draft = lua_table("REBEL_DRAFT", prefix, src)
    roles = re.findall(r'"(\w+)"', draft) if draft is not None else []
    want = re.search(r"rebel_units\s*=\s*(\d+)", _model_lua())
    return pools, roles, (int(want.group(1)) if want else None)


# An army's twenty slots include the general it is created with.
ARMY_SLOTS = 20


def check_rebel_roster():
    out = []
    pools, roles, want = _lua_rebel_roster()
    if not pools:
        return ["IC.REBEL_POOLS not found in zzz_derpy_iron_court.lua"]
    if not roles:
        return ["IC.REBEL_DRAFT not found in zzz_derpy_iron_court.lua"]
    seen = {}
    for role, units in pools.items():
        if not units:
            out.append("IC.REBEL_POOLS.%s lists no unit" % role)
        for key, weight in units:
            if key in seen:
                out.append("%s is in both the %s and %s pools"
                           % (key, seen[key], role))
            seen[key] = role
            if int(weight) <= 0:
                out.append("%s has weight %s in the %s pool" % (key, weight, role))
    for role in roles:
        if role not in pools:
            out.append("IC.REBEL_DRAFT names %s, which has no pool" % role)
    table = _cache_table("main_units")
    if table is None:
        out.append("main_units not cached - run "
                   "tools/fetch_vanilla_tables.py main_units")
    else:
        fields, rows = table
        ui = fields.index("unit")
        known = set(r[ui] for r in rows)
        for key in seen:
            if key not in known:
                out.append("IC.REBEL_POOLS lists %s, which is not in "
                           "main_units" % key)
    if want is None:
        out.append("IC.TUNE.rebel_units not found")
    else:
        if want > len(roles):
            out.append("IC.TUNE.rebel_units is %d and the draft holds %d slots"
                       % (want, len(roles)))
        if want > ARMY_SLOTS - 1:
            out.append("IC.TUNE.rebel_units is %d - an army holds %d including "
                       "its lord, so the roster is %d"
                       % (want, ARMY_SLOTS, ARMY_SLOTS - 1))
    return out

# The rebel crests: one DB row each, so two rebellions stop sharing a banner.
# CA's own rows, exported by RPFM out of db.pack, kept verbatim so the override
# changes exactly one column. See tools/make_ic_rebel_flags.py for why a crest
# cannot be set at runtime and why four is the ceiling.
DONOR_FACTIONS = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "Modding Files", "source", "iron_court", "_donor_factions.tsv")
FACTIONS_COLS = 45
FACTIONS_VERSION = 6


def _donor_rows():
    """(columns, [row dicts]) straight out of the donor TSV."""
    if not os.path.isfile(DONOR_FACTIONS):
        return None, []
    lines = io.open(DONOR_FACTIONS, encoding="utf-8").read().split("\n")
    cols = lines[0].split("\t")
    rows = []
    for line in lines[2:]:
        if not line.strip():
            continue
        cells = line.split("\t")
        rows.append(dict(zip(cols, cells)))
    return cols, rows


def build_factions():
    """The four pool factions, each pointed at its own crest."""
    import make_ic_rebel_flags as F
    cols, rows = _donor_rows()
    if not cols:
        return []
    want = {key: folder for key, folder, _slug, _shape in F.CREST}
    out = []
    for row in rows:
        folder = want.get(row.get("key"))
        if not folder:
            continue
        row = dict(row)
        # A BACKSLASH PATH, which is what every other row in this column holds.
        # The engine takes it either way, and matching CA means a diff of this
        # table shows one changed value rather than forty-five.
        row["flags_path"] = "ui\\flags\\%s" % folder
        out.append(row)
    return out


def check_factions():
    """Every way a row override of CA's table can be wrong and say nothing."""
    import make_ic_rebel_flags as F
    out = []
    if not os.path.isfile(DONOR_FACTIONS):
        return ["missing %s - re-export it from db.pack with RPFM open"
                % DONOR_FACTIONS]
    lines = io.open(DONOR_FACTIONS, encoding="utf-8").read().split("\n")
    cols = lines[0].split("\t")
    meta = lines[1] if len(lines) > 1 else ""
    if len(cols) != FACTIONS_COLS:
        out.append("the donor has %d columns, not %d - RPFM's export shape "
                   "moved and the rows must be re-exported"
                   % (len(cols), FACTIONS_COLS))
    if cols and cols.index("flags_path") != 8:
        out.append("flags_path is column %d, not 9"
                   % (cols.index("flags_path") + 1))
    if not meta.startswith("#factions_tables;%d;" % FACTIONS_VERSION):
        out.append("the donor's metadata line is %r, not version %d - a "
                   "version change means CA moved the field shape"
                   % (meta.strip(), FACTIONS_VERSION))
    rows = build_factions()
    if len(rows) != len(F.CREST):
        out.append("the donor yields %d row(s) for %d crest(s)"
                   % (len(rows), len(F.CREST)))
    if set(r["key"] for r in rows) != set(REBEL_POOL):
        out.append("the override covers %s and IC.REBEL_POOL is %s"
                   % (sorted(r["key"] for r in rows), sorted(REBEL_POOL)))
    for row in rows:
        if len(row) != FACTIONS_COLS:
            out.append("%s has %d columns, not %d"
                       % (row.get("key"), len(row), FACTIONS_COLS))
        # AND THE ROW MUST STILL BE CA'S EXCEPT FOR THE CREST. This is the one
        # that matters: a donor edited by hand, or a generator that touched a
        # second column, silently replaces a faction's name group or its
        # military generator config with whatever was typed.
        _cols, donor = _donor_rows()
        for d in donor:
            if d.get("key") != row.get("key"):
                continue
            for col in row:
                if col == "flags_path":
                    continue
                if row[col] != d[col]:
                    out.append("%s.%s was changed from %r to %r - this "
                               "override may only touch flags_path"
                               % (row["key"], col, d[col], row[col]))
    # AND THE CREST IT POINTS AT MUST SHIP. A flags_path with no folder behind
    # it is a blank square with nothing in the log.
    have = set(F.paths())
    for row in rows:
        folder = row["flags_path"].replace("\\", "/").rsplit("/", 1)[-1]
        for name, _size in F.FILES:
            want = "ui/flags/%s/%s" % (folder, name)
            if want not in have:
                out.append("%s points at %s, which this pack does not ship"
                           % (row["key"], want))
    out.extend(F.check())
    return out


def check_demand_keys():
    """The Lua and the DB must name the same missions, and the tables must be
    the versions CA's own files declare. A key is an unvalidated string: a
    mismatch issues a mission with no row, which fails in silence."""
    out = []
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    lua = io.open(os.path.join(root, "Modding Files", "pack", "script",
                               "campaign", "mod",
                               "zzz_derpy_iron_court_parties.lua"),
                  encoding="utf-8").read()
    for key in [d[0] for d in DEMANDS] + [DEMAND_REWARD, "derpy_ic_demand"]:
        if '"%s"' % key not in lua:
            out.append("the parties Lua never names %s" % key)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import read_vanilla_cache as R
    for table in ("missions", "campaign_payload_ui_details"):
        if not R.have(table):
            out.append("%s not cached - run tools/fetch_vanilla_tables.py %s"
                       % (table, table))
        elif R.version(table) != TSV_META[table][1]:
            out.append("%s is version %d in CA's files, TSV_META says %d"
                       % (table, R.version(table), TSV_META[table][1]))
        else:
            _rows, fields = R.load(table)
            built = build()[table][0]
            if list(built.keys()) != fields:
                out.append("%s columns %s differ from CA's %s"
                           % (table, list(built.keys()), fields))
    return out


# LORD RECRUIT RANK. A lord made by create_force_with_general arrives at rank 1
# whatever the faction's lord recruit rank (measured under a +10 bundle), so a
# party leader put in the field is raised by IC.recruit_rank off
# IC.RECRUIT_RANK. That table is EVERY source in CA's DB, with no race filter: a
# Chaos Dwarf can hold a captured landmark's `_other` variant, and the slot walk
# costs the same whatever the table holds. Derived here so a patch that moves a
# source fails the build, never the campaign.
RANK_EFFECTS = ("wh_main_faction_xp_increase_generals",
                "wh2_main_effect_agent_recruitment_xp_all_agents_and_lords",
                "wh3_dlc25_faction_xp_increase_heroes_generals")
# NOT WHERE A LORD IS RECRUITED: a force or army already raised, a foreign
# building, a preview. The `_hidden` twin of each effect is left out by name -
# it carries the same number to the force and would count every source twice.
RANK_SKIP = ("force", "army", "foreign", "non_functional")
# Reaches only the province it stands in; every other scope reaches them all.
RANK_LOCAL = ("building_to_province_own", "province_to_province_own",
              "province_to_province_own_unseen")
RANK_SOURCES = (("building_effects_junction_tables", "building", "effect", "building"),
                ("technology_effects_junction_tables", "technology", "effect",
                 "technology"),
                ("character_skill_level_to_effects_junctions_tables",
                 "character_skill_key", "effect_key", "skill"),
                ("effect_bundles_to_effects_junctions_tables", "effect_bundle_key",
                 "effect_key", "bundle"))


def recruit_rank_rows():
    """[(kind, key, ranks, reach)], sorted, exactly as IC.RECRUIT_RANK holds them."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from read_vanilla_db import load, DB_PACK
    total = {}
    for table, key_col, effect_col, kind in RANK_SOURCES:
        for _path, _version, rows in load(DB_PACK, table):
            for r in rows:
                scope = r["effect_scope"]
                if r[effect_col] not in RANK_EFFECTS or any(s in scope for s in RANK_SKIP):
                    continue
                # A skill's later levels would need its level read off the man.
                if kind == "skill" and r["level"] != 1:
                    continue
                # A CONDITION THE SCRIPT CANNOT TEST (corruption at 50, a Dechala
                # ritual): 10 building rows as of 9.0, none of them Chaos Dwarf.
                if r.get("context_requirement"):
                    continue
                reach = "province" if scope in RANK_LOCAL else "faction"
                at = (kind, r[key_col], reach)
                total[at] = total.get(at, 0) + r["value"]
    return sorted((kind, key, int(round(n)), reach)
                  for (kind, key, reach), n in total.items() if n > 0)


def recruit_rank_lua(rows):
    return "IC.RECRUIT_RANK = {\n%s}\n" % "".join(
        '    {"%s", "%s", %d, "%s"},\n' % row for row in rows)


def _lua_recruit_rank():
    path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "Modding Files", "pack", "script", "campaign", "mod",
        "zzz_derpy_iron_court.lua")
    src = io.open(path, encoding="utf-8").read()
    block = re.search(r"IC\.RECRUIT_RANK = \{\n(.*?)\n\}", src, re.S)
    if not block:
        return None
    return [(k, key, int(n), reach) for k, key, n, reach in re.findall(
        r'\{"(\w+)", "([^"]+)", (\d+), "(\w+)"\}', block.group(1))]


def check_gov_rank_constants():
    """IC.GOV_* in the Lua must be what this generator ships: the governor's base bundle is rebuilt at runtime from them."""
    lua = io.open(os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "Modding Files", "pack", "script", "campaign", "mod",
        "zzz_derpy_iron_court.lua"), encoding="utf-8").read()
    out = []
    want = {"IC.GOV_BASE_ORDER":
                str([v for e, v, _ in GOVERNOR_BASE if e is E_ORDER][0]),
            "IC.GOV_ORDER_EFFECT": '"%s"' % E_ORDER[0],
            "IC.GOV_INCOME_EFFECT": '"%s"' % E_GDP_PROVINCE[0],
            "IC.GOV_INCOME_SCOPE": '"%s"' % E_GDP_PROVINCE[1]}
    for name, value in want.items():
        m = re.search(r"^%s = (.+)$" % re.escape(name), lua, re.M)
        if not m or m.group(1).strip() != value:
            out.append("%s is %s in the Lua, %s here"
                       % (name, m and m.group(1), value))
    return out


def sound_registry():
    """Every Wwise event name the game knows, lowercased - the `event_data__core.dat`
    list in audio_base_bnk.pack (docs/SOUNDS.md section 2). Names are hashed
    lowercased, so the match is case-insensitive."""
    import read_pack_index
    from read_vanilla_db import DB_PACK
    hits = read_pack_index.read(os.path.join(os.path.dirname(DB_PACK),
                                             "audio_base_bnk.pack"),
                                "event_data__core.dat")
    if not hits:
        return None
    d = hits[0][2]
    n, = struct.unpack_from("<I", d, 0)
    pos, names = 4, set()
    for _ in range(n):
        size, = struct.unpack_from("<I", d, pos)
        pos += 4
        names.add(d[pos:pos + size].decode("ascii").lower())
        pos += size + 4
    return names


def unknown_sounds(lua_text, names):
    """Every UI_ sound literal in the Lua that is not an event. A hook key from
    sound_settings.xml, or a made-up name, plays nothing and raises nothing."""
    found = set(re.findall(r'"((?:UI|ui)_[A-Za-z0-9_]+)"', lua_text))
    return sorted(s for s in found if s.lower() not in names)


def check_governments(race="chd"):
    """The model's governments and this file's are one list, in one order, and
    the bundle the model applies is one this file builds."""
    prefix = RACES[race]["prefix"]
    lua = race_lua(prefix)
    out = []
    m = re.search(r"%s\.GOV_ORDER\s*=\s*\{([^}]*)\}" % re.escape(prefix), lua)
    model_govs = re.findall(r'"(\w+)"', m.group(1)) if m else []
    mine = [g[0] for g in RACES[race]["GOVERNMENTS"]]
    if model_govs != mine:
        out.append("%s.GOV_ORDER is %s and GOVERNMENTS is %s" % (prefix, model_govs, mine))
    m = re.search(r'function IC\.gov_bundle\(slug, faction_key\) return '
                  r'IC\.key\("(\w+)", slug, faction_key\) end', _model_lua())
    kind = m.group(1) if m else "?"
    built = {r["key"]: r for r in build()["effect_bundles"]}
    icons = model_gov_icons(prefix)
    for slug in mine:
        key = bundle_key(kind, slug, race)
        row = built.get(key)
        if not row:
            out.append("the model applies %s and no such bundle is built" % key)
        elif not icons.get(slug) or row["ui_icon"] != icons[slug]:
            out.append("%s wears %s, not the model's picture %s"
                       % (row["key"], row["ui_icon"], icons.get(slug)))
    return out


# THE PLAIN-WORDS RULE for player text: none of these as a word.
JARGON = ("cap", "caps", "accrue", "accrues", "rep", "AI", "HUD", "standing")


def check_laws(race="chd"):
    """The model's laws and this file's are one catalogue, in one order, each
    option's bundle built and wearing the model's picture."""
    prefix = RACES[race]["prefix"]
    lua = race_lua(prefix)
    out = []
    for r in build()["loc"]:
        if r["key"].startswith(("derpy_ic_law_", "derpy_ic_effects_derpy_ic_law_")):
            for w in JARGON:
                if re.search(r"\b%s\b" % w, r["text"]):
                    out.append("%s says %r, which the plain-words rule bans" % (r["key"], w))
    m = re.search(r"%s\.LAW_ORDER\s*=\s*\{([^}]*)\}" % re.escape(prefix), lua)
    model_cats = re.findall(r'"(\w+)"', m.group(1)) if m else []
    mine = [c[0] for c in RACES[race]["LAWS"]]
    if model_cats != mine:
        out.append("%s.LAW_ORDER is %s and LAWS is %s" % (prefix, model_cats, mine))
    built = {r["key"]: r for r in build()["effect_bundles"]}
    loc = {r["key"]: r["text"] for r in build()["loc"]}
    body = lua_table("LAWS", prefix, lua) or ""
    for cat, _name, _icon, options in RACES[race]["LAWS"]:
        cm = re.search(r"\n    %s = \{.*?order = \{([^}]*)\}" % cat, body, re.S)
        order = re.findall(r'"(\w+)"', cm.group(1)) if cm else []
        if order != [o[0] for o in options]:
            out.append("%s: the model's order is %s, here %s" % (cat, order, [o[0] for o in options]))
        for opt, name, _blurb, effects in options:
            key = bundle_key("law", "%s_%s" % (cat, opt), race)
            im = re.search(r"\n\s+%s\s*=\s*\{icon = \"([^\"]+)\"" % opt, body)
            row = built.get(key)
            if not row:
                out.append("no bundle %s" % key)
            elif not im or row["ui_icon"] != im.group(1):
                out.append("%s wears %s, not the model's %s"
                           % (key, row["ui_icon"], im.group(1) if im else None))
            if loc.get(bundle_key("law_name", "%s_%s" % (cat, opt), race)) != name:
                out.append("no name loc for %s" % key)
            if len(effects) > 3:
                out.append("%s has %d effects; a card holds three" % (key, len(effects)))
            if opt == options[0][0] and effects:
                out.append("%s is its category's start and has effects" % key)
    return out


def check_party_drawn(prefix="IC"):
    """Every party <prefix>.DEEDS can name has a party_drawn line."""
    body = lua_table("DEEDS", prefix)
    named = set(re.findall(r'(?:party|alt|also) = "(\w+)"', body)) if body is not None else set()
    missing = sorted(named - set(PARTY_DRAWN))
    out = ["party_drawn has no line for %s" % p for p in missing] + (
        [] if named else ["the model Lua declares no %s.DEEDS" % prefix])
    # EACH LINE NAMES ITS PARTY AS THE PANEL DOES: the
    # generic display, not the government's name - "the Daemonsmiths" is a
    # government, "the Forge" is the party the card says arrived.
    display = {slug: name for slug, name, _e, _m in PARTIES}
    for party, text in PARTY_DRAWN.items():
        name = display.get(party, "")
        bare = name[4:] if name.startswith("The ") else name
        if bare and ("the %s to court" % bare) not in text:
            out.append("party_drawn line for %s does not name %s: %s" % (party, name, text))
    return out


def check_sound_names():
    names = sound_registry()
    if not names:
        return ["audio_base_bnk.pack has no event_data__core.dat - the sound check cannot run"]
    mod = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "Modding Files", "pack", "script", "campaign", "mod")
    out = []
    for fn in sorted(os.listdir(mod)):
        if fn.startswith("zzz_derpy_iron_court") and fn.endswith(".lua"):
            text = io.open(os.path.join(mod, fn), encoding="utf-8").read()
            for s in unknown_sounds(text, names):
                out.append("%s plays %s, which is not a sound event - silent"
                           % (fn, s))
    return out


def check_recruit_rank():
    have = _lua_recruit_rank()
    if have is None:
        return ["IC.RECRUIT_RANK not found in zzz_derpy_iron_court.lua"]
    want = recruit_rank_rows()
    if not want:
        return ["CA's DB read back no lord recruit rank source - the check cannot run"]
    out = []
    for row in sorted(set(want) - set(have)):
        out.append("IC.RECRUIT_RANK is missing %s, which CA's DB has" % (row,))
    for row in sorted(set(have) - set(want)):
        out.append("IC.RECRUIT_RANK has %s, which CA's DB does not" % (row,))
    if out:
        out.append("paste this over IC.RECRUIT_RANK:\n" + recruit_rank_lua(want))
    return out

def check_seed_price():
    """IC.SEED_PRICE holds every lord the seeding can make at CA's own price.

    A starting lord is hired out of the pool for nothing - the engine prices a
    scripted pool lord at zero - so the model charges agent_subtypes.cost once
    at his hire, the normal recruit price once. There is no
    script call for a character's price, so the number is typed; this holds it
    to the DB, and a store lord with no price would be hired free, silently.
    """
    import read_vanilla_cache as R
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    mod = os.path.join(here, "Modding Files", "pack", "script", "campaign", "mod")
    src = {n: io.open(os.path.join(mod, n), encoding="utf-8").read()
           for n in ("zzz_derpy_iron_court.lua", "zzz_derpy_iron_court_dwarf.lua")}
    m = re.search(r"IC\.SEED_PRICE = \{([^}]*)\}", src["zzz_derpy_iron_court.lua"])
    if not m:
        return ["IC.SEED_PRICE not found in zzz_derpy_iron_court.lua"]
    have = {k: int(v) for k, v in re.findall(r'\["(\w+)"\]\s*=\s*(\d+)', m.group(1))}
    lords = set()
    for name, prefix in (("zzz_derpy_iron_court.lua", "IC"),
                         ("zzz_derpy_iron_court_dwarf.lua", "DWF")):
        b = re.search(prefix + r"\.STORE_LORDS = \{([^}]*)\}", src[name])
        if not b:
            return ["%s.STORE_LORDS not found in %s" % (prefix, name)]
        lords |= set(re.findall(r'"(\w+)"', b.group(1)))
    rows = [r for part in R.load("agent_subtypes") if isinstance(part, list)
            for r in part if isinstance(r, dict)]
    cost = {r["key"]: r["cost"] for r in rows if "cost" in r}
    if not cost:
        return ["agent_subtypes read back no cost column - the check cannot run"]
    out = []
    for k in sorted(lords | set(have)):
        if k not in lords:
            out.append("IC.SEED_PRICE prices %s, which no STORE_LORDS can make" % k)
        elif k not in have:
            out.append("IC.SEED_PRICE has no price for %s - he is hired free" % k)
        elif cost.get(k) != have[k]:
            out.append("IC.SEED_PRICE says %s costs %d, CA's agent_subtypes %s"
                       % (k, have[k], cost.get(k)))
    return out


# TABLES WHOSE CACHED DEFINITION IS KNOWN TO BE WIDER THAN THEIR ROWS, and what
# covers them instead. RPFM patches a definition's unused fields without removing
# them, so a name-to-value zip of the dump misaligns after the first such field.
#
# factions: check_factions() holds all 45 columns of all four rows against the
#           donor RPFM exported out of db.pack, which is stricter than check 14.
CACHE_WIDTH_KNOWN = {"factions"}


def check_race_effects():
    """Every effect a Dwarf row names is in ALL_EFFECTS, so checks 1, 2 and 15
    (the vanilla key, its sign, its scope and CA's own words) reach it. An
    effect used and not listed would ship unverified."""
    R = RACES.get("dwf")
    if not R:
        return ["RACES has no dwf entry"]
    used = set()
    for office in R["OFFICES"]:
        used |= set(e for e, _m, _i in office["effects"] + office["vacancy"])
    for _s, _f, _n, _b, fx in R["CONTROL_BANDS"]:
        used |= set(e for e, _m, _i in fx)
    for _s, _n, _r, _b, fx in R["GOVERNMENTS"]:
        used |= set(e for e, _m, _i in fx)
    for _c, _n, _i, options in R["LAWS"]:
        for _o, _n2, _b, fx in options:
            used |= set(e for e, _m, _i in fx)
    used |= set(e for e, _m, _i in R["GOVERNOR_BASE"])
    used |= set(e for _s, _d, e, _m in R["PARTIES"])
    used |= set(R["ENVOY_EFFECT"].values())
    have = set(ALL_EFFECTS)
    return ["%s / %s is used by a Dwarf row and is not in ALL_EFFECTS" % (e[0], e[1])
            for e in sorted(used - have)]
# WHY EACH DWARF SUBTYPE ALL THREE POOL FACTIONS PERMIT IS LEFT OUT.
DWF_REBEL_GEN_EXCLUDED = {
    "wh_main_dwf_thorgrim_grudgebearer": "a legendary lord; IC.is_legend bars him",
    "wh_dlc06_dwf_belegar": "a legendary lord; IC.is_legend bars him",
    "wh3_dlc25_dwf_daemon_slayer": "a Slayer has forsworn his hold and leads no rising",
    "wh3_dlc25_dwf_daemon_slayer_spawned_army": "a Slayer, and CA's scripted spawn",
}
DWF_REBEL_HERO_EXCLUDED = {
    ("dignitary", "wh3_dlc25_dwf_dragon_slayer"): "a Slayer has forsworn his hold",
    ("colonel", "wh_main_dwf_lord"): "a lord's subtype on a hero's agent type",
    ("minister", "wh_main_dwf_lord"): "a lord's subtype on a hero's agent type",
}
# THE CHAOS DWARFS' OWN WORDS, which no Dwarf string may carry.
CHD_WORDS = re.compile(r"hashut|zharr|hell-?forge|slave|labourer|hobgoblin|convoy|"
                       r"ziggurat|daemon|chaos dwarf", re.I)
DWF_SUBCULTURE = "wh_main_sc_dwf_dwarfs"


def great_guild_dwarf_names():
    """The Great Guilds Dwarf names, off that mod's own leader bundles."""
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "Modding Files", "source", "great_guilds", "effect_bundles.tsv")
    names = set()
    for line in io.open(path, encoding="utf-8"):
        cells = line.rstrip("\n").split("\t")
        if len(cells) > 2 and re.match(r"derpy_gg_lead_\w+_dwf$", cells[0]):
            names.add(cells[2].split(" - ")[0])
    return names


def _bare(name):
    name = name.strip().lower()
    return name[4:] if name.startswith("the ") else name


def check_dwf():
    """The Dwarf race: Lua and Python one race, every key against the DB, its
    words its own."""
    out = []
    R = RACES.get("dwf")
    if not R:
        return ["RACES has no dwf entry"]
    tables = build()
    if not DWF_ROWS.get("bundles"):
        return ["build() emitted no Dwarf bundle"]

    # 1. THE LUA AND THIS FILE ARE ONE RACE.
    if dwf_origins() != [(s, f or "") for s, f, _d in R["ORIGINS"]]:
        out.append("DWF.ORIGINS and RACES dwf ORIGINS disagree")
    if dwf_offices() != [(o["slug"], o["affinity"], o["tier"]) for o in R["OFFICES"]]:
        out.append("DWF.OFFICES and RACES dwf OFFICES disagree")
    if tier_seats("dwf") != {1: 2, 2: 4, 3: 4, 4: 4}:
        out.append("the Dwarf tiers are %s, not 2/4/4/4" % (tier_seats("dwf"),))
    # The order, bundles and pictures of the governments and laws: the
    # race-taking checks, run for the Dwarfs.
    out.extend(check_governments("dwf"))
    out.extend(check_laws("dwf"))
    for cat, _n, _i, options in R["LAWS"]:
        for opt, _name, _blurb, effects in options:
            if opt == options[0][0] and effects:
                out.append("%s.%s is its category's start and has effects" % (cat, opt))
            if len(effects) > 3:
                out.append("%s.%s has %d effects; a card holds three" % (cat, opt, len(effects)))
    origin_factions = set(f for _s, f, _d in R["ORIGINS"] if f)
    for fk, gov in dwf_start_gov().items():
        if gov not in _dwf_list("GOV_ORDER"):
            out.append("%s starts on %s, which is no government" % (fk, gov))
        if fk not in origin_factions:
            out.append("%s has a start government and is no origin" % fk)
    for party in set(re.findall(r'(?:party|alt) = "(\w+)"', _dwf_block("DEEDS"))):
        if party not in R["PARTY_DRAWN"]:
            out.append("a Dwarf deed draws %s and party_drawn has no line for it" % party)
    display = dict((s, d) for s, d, _e, _m in R["PARTIES"])
    for party, line in R["PARTY_DRAWN"].items():
        if ("the %s to court" % display[party][4:]) not in line:
            out.append("party_drawn line for %s does not name %s" % (party, display[party]))
    if set(re.findall(r"(\w+) = true", _dwf_block("EVENT_LOC"))) != set(R["EVENT_TEXT"]):
        out.append("DWF.EVENT_LOC and EVENT_TEXT name different events")
    for slug in R["EVENT_TEXT"]:
        if slug not in [e[0] for e in EVENTS]:
            out.append("the Dwarfs word %s, which is no event" % slug)

    # 2. THE HOLDS, against factions_tables both ways.
    vf = _cache_table("factions")
    if vf is None:
        out.append("factions not cached")
    else:
        f, rows = vf
        ki, si = f.index("key"), f.index("subculture")
        sub = dict((r[ki], r[si]) for r in rows)
        for fk in sorted(origin_factions):
            if sub.get(fk) != DWF_SUBCULTURE:
                out.append("origin faction %s is subculture %s" % (fk, sub.get(fk)))
        for fk in sorted(k for k, s in sub.items() if s == DWF_SUBCULTURE):
            if fk not in origin_factions and fk not in R["NOT_AN_ORIGIN"]:
                out.append("Dwarf faction %s is neither an origin nor named as not one" % fk)

    # 3. THE RISINGS, against faction_agent_permitted_subtypes and main_units.
    pool = re.findall(r'"(\w+)"', _dwf_block("REBEL_POOL"))
    perm = _cache_table("faction_agent_permitted_subtypes")
    if perm is None:
        out.append("faction_agent_permitted_subtypes not cached")
    else:
        f, rows = perm
        fi, ai, si = f.index("faction"), f.index("agent"), f.index("subtype")
        di = f.index("mod_disabled") if "mod_disabled" in f else None
        gens, heroes = {}, {}
        for r in rows:
            if r[fi] in pool and not (di is not None and r[di]):
                if r[ai] == "general":
                    gens.setdefault(r[fi], set()).add(r[si])
                else:
                    heroes.setdefault(r[fi], set()).add((r[ai], r[si]))
        if sorted(gens) != sorted(pool) or sorted(heroes) != sorted(pool):
            out.append("a Dwarf pool faction permits no general or no hero")
        else:
            want = set.intersection(*gens.values()) - set(DWF_REBEL_GEN_EXCLUDED)
            have = set(re.findall(r'\["(\w+)"\]', _dwf_block("REBEL_GENERALS")))
            if have != want:
                out.append("DWF.REBEL_GENERALS is %s, the DB permits %s"
                           % (sorted(have), sorted(want)))
            lord = re.search(r'DWF\.REBEL_LORD = "(\w+)"',
                             io.open(DWF_LUA, encoding="utf-8").read())
            if not lord or lord.group(1) not in want:
                out.append("DWF.REBEL_LORD is no general every pool faction permits")
            want_h = set.intersection(*heroes.values()) - set(DWF_REBEL_HERO_EXCLUDED)
            have_h = set((a, s) for s, a in re.findall(r'\["(\w+)"\]\s*=\s*"(\w+)"',
                                                        _dwf_block("REBEL_HEROES")))
            if have_h != want_h:
                out.append("DWF.REBEL_HEROES is %s, the DB permits %s"
                           % (sorted(have_h), sorted(want_h)))
    mu = _cache_table("main_units")
    roles = re.findall(r'"(\w+)"', _dwf_block("REBEL_DRAFT"))
    pools = dict((role, re.findall(r'\{"(\w+)", \d+\}', body)) for role, body in
                 re.findall(r"(\w+) = \{(.*?)\n    \},", _dwf_block("REBEL_POOLS"), re.S))
    if mu is None:
        out.append("main_units not cached")
    else:
        f, rows = mu
        known = set(r[f.index("unit")] for r in rows)
        for role, units in pools.items():
            for u in units:
                if u not in known:
                    out.append("DWF.REBEL_POOLS.%s lists %s, which is not in main_units" % (role, u))
    for role in roles:
        if role not in pools:
            out.append("DWF.REBEL_DRAFT names %s, which has no pool" % role)
    if len(roles) < model_tune("rebel_units"):
        out.append("the Dwarf draft holds %d slots" % len(roles))

    # 3b. EVERY OTHER DWARF KEY THE MODEL HANDS THE ENGINE, re-read here so a game
    #     patch that drops one fails the build.
    src = io.open(DWF_LUA, encoding="utf-8").read()

    def one(name):
        m = re.search(r'^DWF\.%s = "(\w+)"' % name, src, re.M)
        return m.group(1) if m else None
    if mu is not None:
        f, rows = mu
        known = set(r[f.index("unit")] for r in rows)
        troops = re.findall(r'(\w+)\s*=\s*"(\w+)"', _dwf_block("PARTY_TROOPS"))
        if len(troops) != 8:
            out.append("DWF.PARTY_TROOPS holds %d parties, not 8" % len(troops))
        for party, unit in troops + [("default", one("TROOPS_DEFAULT"))]:
            if unit not in known:
                out.append("the Dwarf %s troops %s are not in main_units" % (party, unit))
    if perm is not None:
        f, rows = perm
        fi, ai, si = f.index("faction"), f.index("agent"), f.index("subtype")
        lords = re.findall(r'"(\w+)"', _dwf_block("STORE_LORDS"))
        for fk in sorted(origin_factions):
            allowed = set(r[si] for r in rows if r[fi] == fk and r[ai] == "general")
            for lord in lords:
                if lord not in allowed:
                    out.append("%s does not permit the Dwarf store lord %s" % (fk, lord))
    for table, col, keys, what in [
            ("cai_personalities", "key", [one("REBEL_PERSONALITY")], "rebel personality"),
            ("agent_subtypes", "key", re.findall(r'\["(\w+)"\] = true', _dwf_block("LEGEND_SUBTYPES")),
             "legend subtype")]:
        t = _cache_table(table)
        if t is None:
            out.append("%s not cached" % table)
            continue
        f, rows = t
        have = set(r[f.index(col)] for r in rows)
        if not keys:
            out.append("the Dwarf Lua names no %s" % what)
        for k in keys:
            if k not in have:
                out.append("the Dwarf %s %s is not in %s" % (what, k, table))

    # 4. THE WORDS: no Chaos Dwarf word, no Guild, no jargon in a Dwarf row.
    dwf_loc = set(DWF_ROWS["loc"])
    for r in tables["loc"]:
        if r["key"] in dwf_loc:
            if CHD_WORDS.search(r["text"]):
                out.append("%s says %r" % (r["key"], r["text"]))
            if "guild" in r["text"].lower():
                out.append("%s says Guild: %r" % (r["key"], r["text"]))
            for w in JARGON:
                if re.search(r"\b%s\b" % w, r["text"]):
                    out.append("%s says %r, which the plain-words rule bans" % (r["key"], w))
    for r in tables["effect_bundles"]:
        if r["key"] in set(DWF_ROWS["bundles"]):
            for text in (r["localised_title"], r["localised_description"]):
                if CHD_WORDS.search(text) or "guild" in text.lower():
                    out.append("%s says %r" % (r["key"], text))

    # 5. NO DWARF PARTY IS A GREAT GUILD.
    guilds = set(_bare(n) for n in great_guild_dwarf_names())
    # A FLOOR, not a count: the Great Guilds mod adds guilds on its own schedule
    # (a seventh, the Ancestor Temples, was added later). Fewer than six is a
    # scraper that read nothing.
    if len(guilds) < 6:
        out.append("read %d Great Guilds Dwarf names, fewer than 6" % len(guilds))
    for _s, d, _e, _m in R["PARTIES"]:
        if _bare(d) in guilds:
            out.append("the Dwarf party %s is a Great Guilds name" % d)

    # 6. EVERY DWARF ROW IS A DWARF KEY, and no key is emitted twice.
    for kind, keys in sorted(DWF_ROWS.items()):
        for key in keys:
            if "dwf_" not in key:
                out.append("Dwarf %s row %s carries no dwf_ infix" % (kind, key))
    for table, col in (("effect_bundles", "key"), ("character_traits", "key"), ("loc", "key")):
        keys = [r[col] for r in tables[table]]
        for key in sorted(set(k for k in keys if keys.count(k) > 1)):
            out.append("duplicate %s key: %s" % (table, key))
    return out
def check():
    """Every way this data can be wrong and say nothing about it."""
    out = []
    tables = build()

    # 0. The rebel general whitelist must still be what the DB says. A subtype
    #    key is an unvalidated string, and a wrong one HERE is not the usual
    #    silent no-op - create_force_with_general takes a subtype the faction
    #    cannot field and the game dies, with no Lua error and no minidump
    #    (seen 1.4 seconds after a secession).
    out.extend(check_rebel_generals())
    out.extend(check_not_dwarf())
    out.extend(check_rebel_heroes())
    out.extend(check_rebel_roster())
    out.extend(check_factions())
    out.extend(check_demand_keys())
    out.extend(check_recruit_rank())
    out.extend(check_seed_price())
    out.extend(check_gov_rank_constants())
    out.extend(check_sound_names())
    out.extend(check_governments())
    out.extend(check_laws())
    out.extend(check_party_drawn())
    out.extend(check_race_effects())
    out.extend(check_dwf())

    # 1. Effect keys must exist in vanilla, and the declared is_positive_value_good
    #    must match. A wrong sign flag silently inverts a reward into a penalty.
    effects = _cache_table("effects")
    if effects is None:
        out.append("effects not cached - run tools/fetch_vanilla_tables.py effects")
    else:
        fields, rows = effects
        ki, gi = fields.index("effect"), fields.index("is_positive_value_good")
        good = {r[ki]: r[gi] for r in rows}
        for effect in ALL_EFFECTS:
            if effect[0] not in good:
                out.append("effect key not in vanilla: %s" % effect[0])
            elif bool(good[effect[0]]) != bool(effect[2]):
                out.append("is_positive_value_good disagrees for %s: vanilla %s, declared %s"
                           % (effect[0], good[effect[0]], effect[2]))

    # 2. Every (effect, scope) pair must be one CA actually ships. A scope the
    #    engine does not pair with that effect applies nothing, with no error.
    junc = _cache_table("effect_bundles_to_effects_junctions")
    if junc is None:
        out.append("effect_bundles_to_effects_junctions not cached")
    else:
        fields, rows = junc
        ei, si = fields.index("effect_key"), fields.index("effect_scope")
        pairs = set((r[ei], r[si]) for r in rows)
        # AND THE BUILDING AND TECHNOLOGY TABLES. A scope is the same scope
        # whichever table carries the row: faction_to_force_own on a landmark is
        # the effect applied at faction level to every force, which is what an
        # office's faction bundle does. The Steward's hobgoblin upkeep has its
        # one precedent there - the Volary, a shipped landmark, at -15.
        for table in ("building_effects_junction", "technology_effects_junction"):
            more = _cache_table(table)
            if more is None:
                continue
            f2, r2 = more
            if "effect" in f2 and "effect_scope" in f2:
                e2, s2 = f2.index("effect"), f2.index("effect_scope")
                pairs |= set((r[e2], r[s2]) for r in r2)
        for effect in ALL_EFFECTS:
            if ((effect[0], effect[1]) not in pairs
                    and (effect[0], effect[1]) not in BORROWED_SCOPES):
                out.append("(effect, scope) pair not shipped by CA: %s / %s"
                           % (effect[0], effect[1]))

    # 3. No duplicate bundle keys. The game drops a duplicate silently.
    keys = [r["key"] for r in tables["effect_bundles"]]
    for key in sorted(set(k for k in keys if keys.count(k) > 1)):
        out.append("duplicate effect_bundles key: %s" % key)

    # 4. Every junction points at a bundle this pack defines.
    defined = set(keys)
    for row in tables["effect_bundles_to_effects_junctions"]:
        if row["effect_bundle_key"] not in defined:
            out.append("junction for undefined bundle: %s" % row["effect_bundle_key"])

    # 4b. EVERY BUNDLE'S ICON EXISTS. ui_icon is a bare name
    #     under ui/campaign ui/effect_bundles/; a wrong one draws a blank square
    #     with no error.
    try:
        import gen_iron_court_emitter as _EU
        assets = _EU._game_assets()
    except Exception as exc:
        out.append("game ui assets unreadable, cannot verify bundle icons: %r" % (exc,))
    else:
        for row in tables["effect_bundles"]:
            path = "ui/campaign ui/effect_bundles/" + row["ui_icon"]
            if path.lower() not in assets and path not in assets:
                out.append("bundle %s wears an icon the game does not have: %s"
                           % (row["key"], row["ui_icon"]))

    # 5. Every bundle has both loc entries, and no loc key is duplicated.
    lockeys = [r["key"] for r in tables["loc"]]
    for key in sorted(set(k for k in lockeys if lockeys.count(k) > 1)):
        out.append("duplicate loc key: %s" % key)
    have = set(lockeys)
    for key in defined:
        for prefix in ("effect_bundles_localised_title_",
                       "effect_bundles_localised_description_"):
            if prefix + key not in have:
                out.append("missing loc: %s%s" % (prefix, key))

    # 6. No empty loc text. A blank value is a valid key that draws nothing,
    #    which is indistinguishable in game from a tooltip that failed.
    for row in tables["loc"]:
        if not row["text"].strip():
            out.append("empty loc text for %s" % row["key"])

    # 7. Pipes in a loc value draw verbatim. Only literal attribute text splits.
    for row in tables["loc"]:
        if "||" in row["text"]:
            out.append("loc value contains || which draws literally: %s" % row["key"])

    # 8. Uppercase anywhere in a shipped path crashes since 6.1. The pack name is
    #    the only path this generator decides.
    if PACK_NAME != PACK_NAME.lower():
        out.append("pack name must be lowercase: %s" % PACK_NAME)

    # 9. Every house faction key must resolve, and to a CHAOS DWARF faction. They
    #    are unvalidated strings: a typo does nothing, forever.
    #
    #    Two populations, two sources of truth. A VANILLA key is checked against
    #    the cached factions table, which also proves its subculture - a stronger
    #    check than existence, and the one that would catch pointing a house at,
    #    say, a Dwarf faction whose key reads plausibly. A MODDED key cannot be in
    #    that table at all, so it is grepped back out of the staged source, which
    #    is the only place it is written down.
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    vanilla_factions = _cache_table("factions")
    known, chd = {}, set()
    if vanilla_factions is not None:
        fields, rows = vanilla_factions
        ki, si = fields.index("key"), fields.index("subculture")
        for r in rows:
            known[r[ki]] = r[si]
            if r[si] == CHD_SUBCULTURE:
                chd.add(r[ki])

    staged = []
    doc = os.path.join(root, "docs", "MOD_STRUCTURE.md")
    if os.path.isfile(doc):
        staged.append(doc)
    script_dir = os.path.join(root, "Modding Files", "pack", "script")
    for dirpath, _dirs, files in os.walk(script_dir):
        for name in files:
            if name.endswith(".lua"):
                staged.append(os.path.join(dirpath, name))
    source_text = []
    for path in staged:
        try:
            with io.open(path, encoding="utf-8", errors="replace") as fh:
                source_text.append(fh.read())
        except IOError:
            pass
    source_text = "\n".join(source_text)

    for slug, faction, _d in ORIGINS:
        if faction is None:
            continue          # a place, not a house: nothing to resolve
        if faction in known:
            if faction not in chd:
                out.append("origin %s points at %s, which is subculture %s, not %s"
                           % (slug, faction, known[faction], CHD_SUBCULTURE))
        elif faction not in source_text:
            out.append("origin faction key resolves nowhere - not in the vanilla "
                       "factions table and not in the staged source: %s (%s)"
                       % (faction, slug))

    # 9b. AND THE OTHER DIRECTION: every Chaos Dwarf faction a player can lead
    #     must have an ORIGIN, so that its men read as having come from
    #     somewhere when you confederate them rather than as locally born.
    #     A build failure, because checking the keys we DO name proves nothing
    #     about the ones we forgot (wh3_dlc23_chd_minor_faction, for one).
    for faction in sorted(chd):
        if faction in NOT_AN_ORIGIN:
            continue
        if faction not in set(h[1] for h in ORIGINS):
            out.append("Chaos Dwarf faction %s has no origin - its lords would "
                       "arrive at court with no record of where they came from"
                       % faction)

    # 10. Every office affinity names a real party.
    slugs = set(party_slugs())
    for office in OFFICES:
        if office["affinity"] not in slugs:
            out.append("office %s has unknown affinity %s"
                       % (office["slug"], office["affinity"]))

    # 10b. THE PARTIES THEMSELVES. Each needs a background set, a governor
    #      blurb and a distinct name; a background belongs to exactly one party,
    #      because the party a lord sits with is looked up FROM his background
    #      and a background in two parties would seat him in whichever came
    #      first out of a dict.
    seen_bg = {}
    for party, bg, _display in backgrounds():
        if bg in seen_bg:
            out.append("background %s belongs to both %s and %s"
                       % (bg, seen_bg[bg], party))
        seen_bg[bg] = party
    for party in party_slugs():
        if not BACKGROUNDS.get(party):
            out.append("party %s has no backgrounds, so nobody can ever sit "
                       "in it" % party)
        if party not in PARTY_GOV_BLURB:
            out.append("party %s has no governor blurb" % party)
    for party in BACKGROUNDS:
        if party not in set(party_slugs()):
            out.append("backgrounds declared for unknown party %s" % party)
    for party in PARTY_GOV_BLURB:
        if party not in set(party_slugs()):
            out.append("governor blurb for unknown party %s" % party)
    if CROWN not in set(party_slugs()):
        out.append("the crown %s is not in PARTIES" % CROWN)

    # 10c. AND ENOUGH OF THEM TO ROLL. The model rolls up to rivals_max rivals
    #      and never the crown, so that many have to exist to be drawn without
    #      repeating one. Read out of the model Lua rather than written down
    #      twice - and the LARGEST of every rivals_max in it, since the
    #      difficulties set their own (Ruthless five) and the first one in the
    #      file is only Default's.
    _rivals_max = 5
    try:
        _model = io.open(os.path.join(
            root, "Modding Files", "pack", "script", "campaign", "mod",
            "zzz_derpy_iron_court.lua"), encoding="utf-8").read()
        _all = [int(v) for v in re.findall(r"rivals_max\s*=\s*(\d+)", _model)]
        if _all:
            _rivals_max = max(_all)
    except IOError:
        pass
    if len(PARTIES) - 1 < _rivals_max:
        out.append("%d parties beside the crown cannot fill a roll of %d rivals"
                   % (len(PARTIES) - 1, _rivals_max))

    # 10d. Every origin and every background has its flavour line. A missing one
    #      is a KeyError at build time rather than a silent blank, but the
    #      reverse - a line for a slug that no longer exists - is silent, and is
    #      how a renamed slug leaves its old prose behind.
    for slug in ORIGIN_COLOUR:
        if slug not in set(origin_slugs()):
            out.append("origin colour text for unknown origin %s" % slug)
    for slug in BG_COLOUR:
        if slug not in seen_bg:
            out.append("background colour text for unknown background %s" % slug)

    # 11. The trait chain must be complete in all three tables. A trait present in
    #     character_traits but missing from trait_info is the failure this check
    #     exists for - vanilla has 744 of each, exactly.
    trait_keys = set(r["key"] for r in tables["character_traits"])
    info_keys = set(r["trait"] for r in tables["trait_info"])
    level_traits = set(r["trait"] for r in tables["character_trait_levels"])
    for key in sorted(trait_keys - info_keys):
        out.append("trait has no trait_info row: %s" % key)
    for key in sorted(info_keys - trait_keys):
        out.append("trait_info row for undefined trait: %s" % key)
    for key in sorted(trait_keys - level_traits):
        out.append("trait has no character_trait_levels row: %s" % key)
    for row in tables["character_trait_levels"]:
        if row["trait"] not in trait_keys:
            out.append("trait level points at undefined trait: %s" % row["trait"])

    # 12. All four trait loc keys, per LEVEL key, or the trait draws nameless.
    for row in tables["character_trait_levels"]:
        for suffix in ("onscreen_name", "colour_text",
                       "explanation_text", "removal_text"):
            key = "character_trait_levels_%s_%s" % (suffix, row["key"])
            if key not in have:
                out.append("missing trait loc: %s" % key)

    # 13. Every trait's icon is a trait_categories key, this pack's or vanilla's.
    #     An invented one is a load-time DB reject, which surfaces in
    #     bad_mods_report.txt rather than as anything the game says out loud.
    #     And every category of ours points at a picture that ships - CA's, or
    #     art this pack writes - since a path to nothing draws an empty frame.
    ours = dict((r["category"], r["icon_path"]) for r in tables["trait_categories"])
    known = set(ours)
    vanilla_traits = _cache_table("character_traits")
    if vanilla_traits is not None:
        fields, rows = vanilla_traits
        known |= set(r[fields.index("icon")] for r in rows)
    for row in tables["character_traits"]:
        if row["icon"] not in known:
            out.append("trait %s wears %r, a category neither this pack nor "
                       "vanilla has" % (row["key"], row["icon"]))
        elif row["icon"] not in ours:
            out.append("trait %s wears vanilla's %r - the generic Chaos Dwarf "
                       "picture every trait here used to wear" % (row["key"], row["icon"]))
    import gen_ic_ui as _UI
    _ship = set(_UI.art_paths()) | set(_UI._assets())
    for cat, path in sorted(ours.items()):
        if path not in _ship:
            out.append("trait category %s points at no picture: %s" % (cat, path))

    # 14. No column may be left empty that vanilla never leaves empty. Such a
    #     column is a required foreign key whether or not the schema says so, and
    #     an empty string in one is a load-time database reject that names an
    #     arbitrary row: an empty advancement_stage on the junctions makes the
    #     game reject the pack while naming House of Baal, which merely sorts first.
    for table, rows in tables.items():
        if table == "loc" or not rows:
            continue
        vanilla = _cache_table(table)
        if vanilla is None:
            continue
        fields, vrows = vanilla
        # THE CACHED DEFINITION CAN BE WIDER THAN THE CACHED ROWS. RPFM's dump
        # of factions_tables has 61 fields, 34 of them patched `unused: true`,
        # against rows of 45 cells - so fields.index(column) hands back an
        # index past the end of every row and this loop raises IndexError. It
        # did, the moment factions joined the pack.
        #
        # NAMED RATHER THAN SKIPPED. A check that quietly stops checking is
        # worse than one that fails. The tables covered here are covered by
        # name elsewhere - factions by check_factions(), which compares every
        # column of every row against the donor RPFM exported and is stricter
        # than this is.
        if vrows and len(fields) != len(vrows[0]):
            if table not in CACHE_WIDTH_KNOWN:
                out.append("%s: the cached definition has %d fields and its "
                           "rows %d cells, so column 14 cannot be checked by "
                           "name" % (table, len(fields), len(vrows[0])))
            continue
        for column in rows[0].keys():
            if column not in fields:
                out.append("%s: column %s is not in the vanilla definition"
                           % (table, column))
                continue
            if not any(row[column] == "" for row in rows):
                continue
            at = fields.index(column)
            if not any(r[at] == "" for r in vrows):
                out.append("%s.%s is empty in this pack and in none of vanilla's "
                           "%d rows - it is a required reference"
                           % (table, column, len(vrows)))

    # 15. The tooltip must use CA'S OWN WORDS for each effect. EFFECT_TEXT is
    #     pinned above and re-read from local_en.pack here, so a patch that
    #     rewords an effect makes this refuse instead of shipping a trait whose
    #     tooltip disagrees with the Faction Effects panel beside it.
    #
    #     This is also the only check that can catch a %+n that stopped being a
    #     %+n: substitution is a plain string replace, and a miss leaves the
    #     literal "%+n" on screen rather than a number.
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import read_vanilla_loc as _L
        vloc = _L.load("effects")
        ui = _L.load("ui_text_replacements")
    except Exception as exc:
        out.append("vanilla loc unreadable, cannot verify tooltip text: %r" % (exc,))
    else:
        for effect in ALL_EFFECTS:
            key = effect[0]
            if key not in EFFECT_TEXT:
                out.append("no tooltip text declared for %s" % key)
                continue
            want = vloc.get("effects_description_" + key)
            if want is None:
                out.append("no vanilla loc for effect %s" % key)
                continue
            got = EFFECT_TEXT[key]
            if key in EFFECT_TEXT_TR:
                token, resolved = EFFECT_TEXT_TR[key]
                real = ui.get("ui_text_replacements_localised_text_" + token)
                if real != resolved:
                    out.append("{{tr:%s}} resolves to %r, declared %r"
                               % (token, real, resolved))
                want = want.replace("{{tr:%s}}" % token, resolved)
            if got != want:
                out.append("tooltip text drifted for %s: vanilla %r, declared %r"
                           % (key, want, got))
        # THE TRAIT MUST QUOTE THE BUNDLE. Re-derived from the junction rows,
        # which is the only copy of the number that reaches the game, so a
        # scaling step that stops being applied to one of the two shows up here
        # rather than as a tooltip that quietly undersells the office.
        tables = build()
        values = {}
        for row in tables["effect_bundles_to_effects_junctions"]:
            values.setdefault(row["effect_bundle_key"], []).append(row["value"])
        texts = {r["key"]: r["text"] for r in tables["loc"]}
        for office in OFFICES:
            key = bundle_key("office", office["slug"])
            said = texts.get("character_trait_levels_explanation_text_"
                             + office_trait_key(office["slug"]), "")
            for value in values.get(key, []):
                shown = "%+d" % int(float(value))
                if shown not in said:
                    out.append("office %s grants %s and its trait says %r"
                               % (office["slug"], shown, said))

        # A SHORT FORM FOR EVERY EFFECT. effect_short indexes EFFECT_SHORT
        # directly, so a missing entry is a KeyError at build time rather than a
        # blank card - but only if something builds, which is what this is.
        for effect in ALL_EFFECTS:
            if effect[0] not in EFFECT_SHORT:
                out.append("no short card label for %s" % effect[0])
            elif len(EFFECT_SHORT[effect[0]]) > 20:
                out.append("the short label for %s is %d characters, which is "
                           "not short" % (effect[0], len(EFFECT_SHORT[effect[0]])))

        # Every office line must have had its value substituted.
        for office in OFFICES:
            for e, m, intent in office["effects"]:
                line = effect_line(e, m, intent)
                if "%+n" in line:
                    out.append("unsubstituted %%+n in %s tooltip: %r"
                               % (office["slug"], line))

    # 16. THE EVENT FEED, against vanilla's own table.
    #
    #     Every value in a scripted event row is a foreign key or an enum, and
    #     every one of them fails the same way: the engine logs that it showed an
    #     event and draws nothing. There is no error to read and no way to tell
    #     from in game which of the thirteen columns was wrong, which is exactly
    #     the class of fault that must not reach a launch.
    feed_cache = _cache_table("event_feed_message_events")
    crit_cache = _cache_table("campaign_group_member_criteria_values")
    if feed_cache is None or crit_cache is None:
        out.append("event feed tables not cached - run tools/fetch_vanilla_tables.py "
                   "event_feed_message_events campaign_group_member_criteria_values")
    else:
        vfields, vrows = feed_cache
        # 16a. The field order this file writes IS the definition's.
        if vfields != EVENT_COLS:
            out.append("event_feed_message_events fields are %s in vanilla and "
                       "%s here - the TSV would import into the wrong columns"
                       % (vfields, EVENT_COLS))
        else:
            col = {n: i for i, n in enumerate(vfields)}
            # 16b. Every enum value must be one vanilla actually uses. An
            #      invented image key or sound event is a silent non-draw.
            for name in ("event", "image", "sound_event", "target", "layout",
                         "layout_data", "context_located", "flavour_text",
                         "secondary_detail"):
                known = set(str(r[col[name]]) for r in vrows)
                for row in tables["event_feed_message_events"]:
                    if str(row[name]) not in known:
                        out.append("event_feed_message_events.%s = %r is a value "
                                   "vanilla never uses" % (name, row[name]))
            # 16c. instant_open must agree with the event type, because that is
            #      what the type MEANS: all 93 vanilla persistent rows are true
            #      and all 4 transient rows are false.
            for row in tables["event_feed_message_events"]:
                want = "true" if row["event"] == "scripted_persistent_event" else "false"
                if row["instant_open"] != want:
                    out.append("%s row has instant_open %s, and every vanilla "
                               "row of that type is %s"
                               % (row["event"], row["instant_open"], want))
            # 16d. ONLY THE TWO TYPES CA USES WITH THE PLAIN CALL. The located
            #      variants are for cm:show_message_event_located; none of CA's
            #      ten plain-call indices resolves to one.
            #      EXCEPT LOCATED_EVENTS, which are raised with the located
            #      call and must carry the located type - and only they may.
            located = {event_key(s) + suf + "_group" for s in LOCATED_EVENTS
                       for suf in ("", "_dwf")}
            for row in tables["event_feed_message_events"]:
                if row["event"] not in ("scripted_persistent_event",
                                        "scripted_transient_event",
                                        "scripted_transient_located_event"):
                    out.append("%s is not one of the two types CA raises with "
                               "the plain cm:show_message_event" % row["event"])
                elif ((row["event"] == "scripted_transient_located_event")
                        != (row["group"] in located)):
                    out.append("%s is %s, and it is %sraised with the located call"
                               % (row["group"], row["event"],
                                  "" if row["group"] in located else "not "))
            # 16d2. THE LUA RAISES THE SAME SET with the located call.
            lua = io.open(os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "Modding Files", "pack", "script", "campaign", "mod",
                "zzz_derpy_iron_court.lua"), encoding="utf-8").read()
            block = re.search(r"IC\.LOCATED_EVENTS = \{([^}]*)\}", lua)
            lua_located = (set(re.findall(r"(\w+)\s*=\s*true", block.group(1)))
                           if block else set())
            if lua_located != LOCATED_EVENTS:
                out.append("IC.LOCATED_EVENTS is %s in the Lua, %s here"
                           % (sorted(lua_located), sorted(LOCATED_EVENTS)))

        # 16e. The index must be above every vanilla one, or it collides with a
        #      record that already exists and draws CA's message instead of ours.
        vcrit = crit_cache[1]
        vmax = max(int(r[1]) for r in vcrit if str(r[1]).lstrip("-").isdigit())
        for row in tables["campaign_group_member_criteria_values"]:
            if int(row["value"]) <= vmax:
                out.append("event index %s is not above vanilla's highest (%d)"
                           % (row["value"], vmax))

    # 16f. The four tables must line up with each other. A member whose group
    #      has no row, or a criteria value naming a member that does not exist,
    #      breaks the chain from the number the script passes to the record -
    #      and breaks it silently.
    gids = set(r["id"] for r in tables["campaign_groups"])
    mids = set(r["id"] for r in tables["campaign_group_members"])
    for r in tables["campaign_group_members"]:
        if r["group"] not in gids:
            out.append("event group member %s names group %s, which has no row"
                       % (r["id"], r["group"]))
    for r in tables["campaign_group_member_criteria_values"]:
        if r["member"] not in mids:
            out.append("criteria value %s names member %s, which has no row"
                       % (r["value"], r["member"]))
    for r in tables["event_feed_message_events"]:
        if r["group"] not in gids:
            out.append("event row names group %s, which has no row" % r["group"])
    # 16g. And every event must carry ALL THREE loc keys. IC.raise_feed hands
    #     the engine its own _primary and _secondary whenever the caller names
    #     nothing, and a key with no row draws that slot empty, silently.
    lkeys = set(e["key"] for e in tables["loc"])
    for slug, _p, _i, _s, _t, _pr, _sec in EVENTS:
        for part in ("title", "primary", "secondary"):
            k = "event_feed_strings_text_" + event_key(slug) + "_" + part
            if k not in lkeys:
                out.append("event %s has no %s loc key" % (slug, part))
    # 16j. AND EACH SLOT HOLDS ITS OWN SHAPE, CA's: the primary is a short
    #      subtitle, the secondary the body. Reversed, the large-font line is a
    #      paragraph and the inset box under it says "Failure". Every race's
    #      run, and the runtime keys that fill a slot: a move's result line and
    #      an office's name are subtitles, a party_drawn line is a body.
    ltext = dict((e["key"], e["text"]) for e in tables["loc"])
    stems = ([event_key(e[0]) for e in EVENTS]
             + [bundle_key("event", s, r) for r in RACES if r != "chd"
                for s in RACES[r].get("EVENT_TEXT", {})])
    subtitles, bodies = [], []
    for stem in stems:
        base = "event_feed_strings_text_" + stem
        if ltext.get(base + "_primary") == ltext.get(base + "_title"):
            out.append("event %s's subtitle repeats its title" % stem)
        subtitles.append(base + "_primary")
        bodies.append(base + "_secondary")
    for k in ltext:
        if k.startswith(("event_feed_strings_text_derpy_ic_move_",
                         "effect_bundles_localised_title_derpy_ic_office_")):
            subtitles.append(k)
        elif (k.startswith("event_feed_strings_text_derpy_ic_event_party_drawn_")
              and not k.endswith(("_title", "_primary", "_secondary"))):
            bodies.append(k)
    for k in subtitles:
        t = ltext.get(k) or ""
        if not t or len(t) > 36 or t.endswith("."):
            out.append("%s is not a subtitle (1-36 characters, no full stop): %r" % (k, t))
    for k in bodies:
        t = ltext.get(k) or ""
        if not t.endswith("."):
            out.append("%s is not a body (sentences ending in a full stop): %r" % (k, t))
    # 16h. Indices must be unique. Two events on one number is one of them
    #      drawing the other's card.
    _vals = [r["value"] for r in tables["campaign_group_member_criteria_values"]]
    if len(set(_vals)) != len(_vals):
        out.append("two events share an index: %s" % sorted(_vals))
    # 16i. AND EVERY MOVE HAS BOTH ITS RESULT LINES. IC.move_result_key
    #      builds these from IC.PLOTS with no guard of its own, on the
    #      strength of this check - a move added to the model and not
    #      regenerated here draws the blank plate the lines replaced,
    #      silently, which is the one failure mode nothing else sees.
    for _mkey, _mname in model_moves():
        for _ok in (True, False):
            k = move_result_key(_mkey, _ok)
            if k not in lkeys:
                out.append("move %s has no %s result line"
                           % (_mkey, "success" if _ok else "failure"))

    return out


TSV_META = {
    "effect_bundles": ("effect_bundles_tables", 4),
    "effect_bundles_to_effects_junctions":
        ("effect_bundles_to_effects_junctions_tables", 3),
    # Versions read off the cached vanilla definitions. A version that
    # does not match the field shape imports a wrong-width TSV.
    "trait_info": ("trait_info_tables", 1),
    "character_traits": ("character_traits_tables", 3),
    "character_trait_levels": ("character_trait_levels_tables", 0),
    # Two fields, category and icon_path, read off CA's own data__ v0.
    "trait_categories": ("trait_categories_tables", 0),
    # THE EVENT FEED'S FOUR. Versions read off CA's own shipped files - the
    # `definition.version` inside each cached RPFM dump, not
    # RPFM's default for the table, which is allowed to differ and would import
    # a wrong-width TSV. Field counts there too: 1, 3, 2, 13.
    "campaign_groups": ("campaign_groups_tables", 0),
    "campaign_group_members": ("campaign_group_members_tables", 1),
    "campaign_group_member_criteria_values":
        ("campaign_group_member_criteria_values_tables", 0),
    "event_feed_message_events": ("event_feed_message_events_tables", 1),
    # CA's OWN TABLE, four rows overridden. Version and field
    # shape come from RPFM's export of db.pack, not from a guess:
    # check_factions() refuses if either moves.
    "factions": ("factions_tables", 6),
    # Versions pinned against CA's own shipped files by check_demand_keys().
    # missions declared 6 once and crashed the game at load (docs/MISSIONS.md).
    "missions": ("missions_tables", 0),
    "campaign_payload_ui_details": ("campaign_payload_ui_details_tables", 2),
    "loc": ("Loc", 1),
}


def container_path(table):
    if table == "loc":
        return "text/db/%s.loc" % PACK_NAME
    return "db/%s/%s" % (TSV_META[table][0], PACK_NAME)


def write_tsvs(outdir):
    if not os.path.isdir(outdir):
        os.makedirs(outdir)
    written = []
    for table, rows in build().items():
        if not rows:
            continue
        cols = list(rows[0].keys())
        path = os.path.join(outdir, table + ".tsv")
        name, version = TSV_META[table]
        pad = "\t" * (len(cols) - 1)
        with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\t".join(cols) + "\n")
            fh.write("#%s;%d;%s%s\n" % (name, version, container_path(table), pad))
            for row in rows:
                for c in cols:
                    # A TSV row IS a line and a TSV field IS tab-delimited, so
                    # neither character can travel inside a value. Refusing here
                    # beats writing a file whose rows no longer match build().
                    assert "\n" not in row[c] and "\t" not in row[c], (
                        "%s.%s cannot hold a newline or tab: %r"
                        % (table, c, row[c]))
                fh.write("\t".join(row[c] for c in cols) + "\n")
        written.append(path)
    return written


def selftest():
    # THE RACE SEAM. The tiers are counted off the
    # race's own offices, a key carries the race's infix, and a scraper reads
    # the prefix it is given and no other.
    assert tier_seats("chd") == {1: 2, 2: 3, 3: 4, 4: 5}, tier_seats("chd")
    RACES["tst"] = dict(RACES["chd"], infix="tst_", prefix="TST")
    try:
        assert bundle_key("office", "priest", "tst") == "derpy_ic_office_tst_priest"
        assert bundle_key("office", "priest") == "derpy_ic_office_priest"
    finally:
        del RACES["tst"]
    _src = ('IC.OFFICES = {\n    {slug = "a"},\n}\n'
            'DWF.OFFICES = {\n    {slug = "b"},\n}\n')
    assert '"b"' in lua_table("OFFICES", "DWF", _src)
    assert '"a"' not in lua_table("OFFICES", "DWF", _src)
    assert lua_table("LAWS", "DWF", _src) is None
    # Only a column-0 definition counts: not a longer prefix, not an indented copy.
    assert lua_table("OFFICES", "IC", 'XIC.OFFICES = {\n    {slug = "x"},\n}\n') is None
    assert lua_table("OFFICES", "IC", 'do\n    IC.OFFICES = {\n    {slug = "x"},\n}\n') is None

    # DERIVED, not hardcoded. These were pinned at ten and so failed the moment
    # a house was added - which is a selftest reporting on its own literals
    # rather than on the data. What is actually invariant is that the counts
    # AGREE across the five tables, and that nothing is duplicated.
    # THE SOUND CHECK REPORTS A HOOK KEY and passes a real event in any case.
    _names = {"ui_click_recruitment_cancel"}
    assert unknown_sounds('play("UI_CAMPAIGN_RECRUITMENT_CANCEL")', _names) \
        == ["UI_CAMPAIGN_RECRUITMENT_CANCEL"], "a hook key passed the sound check"
    assert unknown_sounds('play("UI_CLICK_Recruitment_Cancel")', _names) == [], \
        "a real event failed the sound check on case"

    n_origins = len(ORIGINS)
    n_offices = len(OFFICES)
    assert n_origins >= 10, "the ten modded houses are the floor, got %d" % n_origins
    assert len(set(origin_slugs())) == n_origins, "origin slugs unique"
    _keys = [h[1] for h in ORIGINS if h[1] is not None]
    assert len(set(_keys)) == len(_keys), "faction keys unique"
    assert len(set(o["slug"] for o in OFFICES)) == len(OFFICES), "office slugs unique"

    # THE ZIGGURAT. Pinning a total would be the same literal that made this
    # selftest report on itself when a house was added; what is invariant is the
    # SHAPE - narrow at the top, wide at the base - so the shape is what is
    # asserted and the total falls out of it.
    seats = tier_seats()
    assert len(OFFICES) == sum(seats.values()), "an office outside every tier"
    widths = [seats[t] for t in sorted(seats)]
    assert widths == sorted(widths),         "a tier is narrower than the one above it: %r" % (widths,)

    # And the higher seat must actually BE the better seat. A multiplier table
    # that is not strictly decreasing makes the ziggurat a shape and nothing
    # more - fourteen equal offices drawn in a pyramid.
    mults = [TIER_MULT[t] for t in sorted(TIER_MULT)]
    assert all(a > b for a, b in zip(mults, mults[1:])),         "tier multipliers are not strictly decreasing: %r" % (mults,)
    assert sorted(TIER_MULT) == sorted(seats) == sorted(TIER_NAME),         "the three tier tables disagree about which tiers exist"
    assert tier_value(1, 4) > tier_value(4, 4), "a tier-1 seat grants no more than a tier-4 one"
    assert tier_value(4, 7) == 7, "tier 4 is the base: its magnitude is what is declared"

    slugs = set(party_slugs())
    affinities = [o["affinity"] for o in OFFICES]
    for office in OFFICES:
        assert office["affinity"] in slugs,             "%s wants party %r, which is not in PARTIES" % (office["slug"], office["affinity"])
    # OFFICES MAY SHARE A PARTY NOW, and fourteen of them across eight parties
    # have to. What may not happen is a party with no office at all: the snub is
    # the only pressure the court applies, and a party that is owed nothing can
    # never be snubbed, so its loyalty would be a number that only ever drifts.
    # THE CROWN FIRST. This and the equality below it are one rule split in
    # two, and with the equality first an office owed to the crown reported
    # an EMPTY list of parties owed nothing - which reads as "nothing is
    # wrong" and names the other half of the rule.
    assert CROWN not in affinities,         "the crown is the player - an office owed to it could never be snubbed"
    assert set(affinities) == slugs - {CROWN},         "every party but the crown must be owed an office: %r" % (
            sorted(slugs - {CROWN} - set(affinities)),)

    # The sign rule, in both directions, on both kinds of effect. This is the
    # whole reason magnitudes are declared without signs.
    assert signed_value(E_ORDER, 4, BOON) == 4, "good effect, boon, stays positive"
    assert signed_value(E_ORDER, 4, MALUS) == -4, "good effect, malus, goes negative"
    assert signed_value(E_UPKEEP, 10, BOON) == -10, \
        "COST effect, boon, must be NEGATIVE - this is the inversion that ships as a red penalty"
    assert signed_value(E_UPKEEP, 10, MALUS) == 10, "cost effect, malus, is positive"
    assert signed_value(E_WORKLOAD, 15, BOON) == -15, "workload is a load modifier"

    try:
        signed_value(E_ORDER, -4, BOON)
        raise AssertionError("a pre-signed magnitude must be refused")
    except AssertionError as exc:
        assert "not a sign" in str(exc), exc

    # THE BANDS ARE FLOORS, walked top down, and the last one has to be 0 or a
    # court below it lands in no band at all - which is a turn with no bundle
    # on the faction and nothing anywhere saying so.
    assert CONTROL_BANDS[-1][1] == 0, \
        ("the lowest control band starts at %d, so a share below that is in no "
         "band at all" % CONTROL_BANDS[-1][1])
    floors = [b[1] for b in CONTROL_BANDS]
    assert floors == sorted(floors, reverse=True), \
        "the control bands must run high to low, got %r" % (floors,)
    assert len(set(floors)) == len(floors), \
        "two control bands share a floor: %r" % (floors,)

    tables = build()
    keys = [r["key"] for r in tables["effect_bundles"]]
    assert len(keys) == len(set(keys)), "no duplicate bundle keys"
    n_parties = len(PARTIES)
    # AND ONE PER ENVOY TASK.
    n_envoy = len(model_envoy_tasks())
    # AND ONE PER LAW, start options included.
    n_laws = sum(len(options) for _cat, _name, _icon, options in LAWS)
    want = (n_offices * 2 + 1 + n_parties + len(CONTROL_BANDS) + n_envoy
            + len(GOVERNMENTS) + n_laws)
    # PER RACE: the Dwarfs keep the skeleton, so each
    # race builds the same count; a Dwarf key carries "_dwf_".
    chd_keys = [k for k in keys if "_dwf_" not in k]
    assert len(chd_keys) == want, \
        ("one office and one vacancy bundle per office, one governor base, and "
         "one governor flavour per PARTY - it was per house, and there were "
         "sixteen of those, plus one per control band, one per envoy task, "
         "one per government and one per law: expected %d, got %d" % (want, len(chd_keys)))
    assert len(keys) - len(chd_keys) == want, \
        "the Dwarfs build %d bundles, not the skeleton's %d" % (len(keys) - len(chd_keys), want)

    # Every office's boon and its vacancy penalty must land on opposite sides of
    # zero. A vacancy that helps you is the sign bug wearing a different hat.
    signs = {}
    for row in tables["effect_bundles_to_effects_junctions"]:
        signs.setdefault(row["effect_bundle_key"], []).append(float(row["value"]))
    for office in OFFICES:
        values = (signs[bundle_key("office", office["slug"])]
                  + signs[bundle_key("vacant", office["slug"])])
        assert all(v != 0 for v in values), "no zero-value junction"

    for office in OFFICES:
        for effect, magnitude, intent in office["effects"]:
            assert intent == BOON, "an office's own effects are boons"
            assert magnitude > 0, "magnitudes are positive"
        for effect, magnitude, intent in office["vacancy"]:
            assert intent == MALUS, "a vacancy is a penalty"

    # An effect and its vacancy counterpart must produce opposite signs when they
    # are the same effect, whatever that effect's polarity.
    for office in OFFICES:
        shared = set(e[0][0] for e in office["effects"]) & \
                 set(e[0][0] for e in office["vacancy"])
        for effect_key in shared:
            boon = [signed_value(e[0], e[1], e[2]) for e in office["effects"]
                    if e[0][0] == effect_key][0]
            malus = [signed_value(e[0], e[1], e[2]) for e in office["vacancy"]
                     if e[0][0] == effect_key][0]
            assert boon * malus < 0, \
                "%s: office and vacancy must oppose on %s" % (office["slug"], effect_key)

    # No bundle description may carry a value placeholder.
    for row in tables["effect_bundles"]:
        assert "%+n" not in row["localised_description"], row["key"]

    for row in tables["loc"]:
        assert row["text"].strip(), row["key"]
        assert "||" not in row["text"], row["key"]

    assert PACK_NAME == PACK_NAME.lower(), "lowercase pack name"

    # The trait chain: one row in each of the three tables, per trait.
    # DERIVED, not a literal: one band per tier plus the man who clears none.
    n_bands = len(TIER_NAME) + 1
    n_backgrounds = len(backgrounds())
    # AND ONE PER PARTY A MAN CAN SIT WITH: the Crown, each confederate party,
    # and each rolled party's tails.
    _tails = model_tails()
    n_members = 1 + len(ORIGINS) + sum(len(_tails[p[0]]) for p in PARTIES if p[0] != CROWN)
    n_traits = (n_origins + n_backgrounds + n_offices + n_bands + len(AMBITION_BANDS)
                + n_members)
    chd_traits = [r for r in tables["character_traits"] if "_dwf_" not in r["key"]]
    assert len(chd_traits) == n_traits, \
        ("one trait per origin, per background, per office, per standing band "
         "and per party: expected %d, got %d"
         % (n_traits, len(chd_traits)))
    # THE SAME COUNT FOR THE DWARFS, off their own tables.
    D = RACES["dwf"]
    d_tails = model_tails("DWF")
    d_members = 1 + len(D["ORIGINS"]) + sum(len(d_tails[p[0]]) for p in D["PARTIES"] if p[0] != CROWN)
    d_want = (len(D["ORIGINS"]) + sum(len(v) for v in D["BACKGROUNDS"].values()) + len(D["OFFICES"])
              + len(D["TIER_NAME"]) + 1 + len(AMBITION_BANDS) + d_members)
    d_got = len(tables["character_traits"]) - len(chd_traits)
    assert d_got == d_want, "the Dwarfs build %d traits, not %d" % (d_got, d_want)
    # AND EACH WEARS A PICTURE OF ITS OWN KIND, not the generic Chaos Dwarf one.
    cats = set(r["category"] for r in tables["trait_categories"])
    assert all(r["icon"] in cats for r in tables["character_traits"]), \
        "a trait wears a category this pack does not ship"
    assert len(set(r["icon"] for r in tables["character_traits"])) == len(cats), \
        "a trait category nothing wears"
    assert len(tables["trait_info"]) == len(tables["character_traits"]), \
        "trait_info is one row per trait - vanilla has 744 of each"
    assert len(tables["character_trait_levels"]) == len(tables["character_traits"]), \
        "one level per trait"
    for row in tables["character_trait_levels"]:
        assert row["key"] == row["trait"], \
            "single-level traits key the level as the trait - CA's own convention"
    trait_keys = set(r["key"] for r in tables["character_traits"])
    assert len(trait_keys) == len(tables["character_traits"]), "trait keys unique"
    assert all(k == k.lower() for k in trait_keys), "lowercase trait keys"

    ambition_keys = {"derpy_ic_ambition_" + slug for slug in AMBITION_BANDS}
    for key in ambition_keys:
        assert sum(row["key"] == key for row in tables["character_traits"]) == 1, \
            "ambition trait is emitted once: %s" % key
        assert sum(row["trait"] == key for row in tables["character_trait_levels"]) == 1, \
            "ambition trait level is emitted once: %s" % key
        assert sum(row["trait"] == key for row in tables["trait_info"]) == 1, \
            "ambition trait info is emitted once: %s" % key
        assert sum(row["key"].endswith("_" + key) for row in tables["loc"]) == 4, \
            "ambition trait has four loc rows: %s" % key
    assert not any(row.get("trait") in ambition_keys
                   for row in tables.get("trait_level_effects", [])), \
        "ambition marker traits have no effects"

    # EVERY BAND A TIER COULD ASK FOR. The Lua builds this key from whichever
    # tier a man clears, so a tier without a band is a force_add_trait against a
    # key that does not exist - which fails silently and leaves the character
    # panel saying nothing at all about his standing.
    for _tier in [0] + sorted(TIER_NAME):
        assert standing_trait_key(_tier) in trait_keys, \
            "tier %r has no standing band" % (_tier,)
        assert _tier in STANDING_BAND, "tier %r has no band text" % (_tier,)
    assert len(STANDING_BAND) == n_bands, \
        "STANDING_BAND declares a band for a tier the ziggurat has not got"
    # And each band names a DIFFERENT seat, or two of them read identically on
    # the character panel and the player cannot tell which way he is moving.
    _names = [STANDING_BAND[t][0] for t in STANDING_BAND]
    assert len(set(_names)) == len(_names), "two standing bands share a name"

    # The checks themselves.
    # A check nobody has seen fail is not a check. Break each fault in memory and
    # confirm check() names it, then put the data back.
    assert not check(), "the real data must pass before faults are injected"

    def injected(fault, restore, needle):
        problems = check()
        restore()
        assert any(needle in p for p in problems), \
            "check() did not catch %s (said: %s)" % (fault, problems)

    # THE SLOTS REVERSED, the shape every event shipped in before 2026-10-10:
    # the body sentence in the subtitle and a one-word label in the body.
    _ev = EVENTS[1]
    EVENTS[1] = _ev[:5] + (_ev[6], _ev[5])
    injected("an event whose subtitle and body are swapped",
             lambda: EVENTS.__setitem__(1, _ev), "is not a subtitle")
    EVENTS[1] = _ev[:5] + (_ev[6], _ev[5])
    injected("an event whose subtitle and body are swapped",
             lambda: EVENTS.__setitem__(1, _ev), "is not a body")

    # The tooltip text. CA's wording typed from memory goes wrong ("Raw Materials
    # efficiency" for CA's "Raw Materials output"); check 15 must catch it.
    _t = EFFECT_TEXT[E_GDP[0]]
    EFFECT_TEXT[E_GDP[0]] = "Income from every building: %+n%"
    injected("reworded tooltip text",
             lambda: EFFECT_TEXT.__setitem__(E_GDP[0], _t), "tooltip text drifted")

    EFFECT_TEXT[E_GDP[0]] = "Income from all buildings: +12%"
    injected("a tooltip line with no %+n to substitute",
             lambda: EFFECT_TEXT.__setitem__(E_GDP[0], _t), "tooltip text drifted")

    _tr = EFFECT_TEXT_TR[E_ORDER[0]]
    EFFECT_TEXT_TR[E_ORDER[0]] = ("public_order_effect", "Public Order")
    injected("a {{tr:}} token resolved to the wrong string",
             lambda: EFFECT_TEXT_TR.__setitem__(E_ORDER[0], _tr), "resolves to")

    saved = ALL_EFFECTS[3]
    ALL_EFFECTS[3] = ("wh_main_effect_public_order_faction_TYPO",
                      "faction_to_province_own", True)
    injected("an invented effect key",
             lambda: ALL_EFFECTS.__setitem__(3, saved), "not in vanilla")

    ALL_EFFECTS[3] = ("wh_main_effect_public_order_faction", "faction_to_force_own", True)
    injected("a scope CA never pairs with that effect",
             lambda: ALL_EFFECTS.__setitem__(3, saved), "not shipped by CA")

    # A BUNDLE ICON THE GAME DOES NOT SHIP. emit() reads the
    # module's BUNDLE_ICON at build time, and check() builds afresh.
    _icon = BUNDLE_ICON
    globals()["BUNDLE_ICON"] = "no_such_icon.png"
    injected("a bundle icon the game does not ship",
             lambda: globals().__setitem__("BUNDLE_ICON", _icon),
             "an icon the game does not have")

    # THE BORROWED SCOPE IS EXEMPT BY PAIR, NOT BY EFFECT: the
    # same effect on any other unshipped scope is still refused.
    _i = ALL_EFFECTS.index(E_ENVOY_RAW)
    ALL_EFFECTS[_i] = (E_ENVOY_RAW[0], "province_to_region_own_unseen_TYPO", True)
    injected("the borrowed scope's exemption stretched to another scope",
             lambda: ALL_EFFECTS.__setitem__(_i, E_ENVOY_RAW), "not shipped by CA")

    ALL_EFFECTS[3] = ("wh_main_effect_public_order_faction",
                      "faction_to_province_own", False)
    injected("a wrong is_positive_value_good, which inverts the reward",
             lambda: ALL_EFFECTS.__setitem__(3, saved), "disagrees")

    _dropped = [h for h in ORIGINS if h[1] == "wh3_dlc23_chd_minor_faction"]
    assert _dropped, "the origin this injection drops is no longer in ORIGINS"
    ORIGINS.remove(_dropped[0])
    injected("a playable Chaos Dwarf faction with no origin",
             lambda: ORIGINS.append(_dropped[0]),
             "has no origin")

    saved_faction = ORIGINS[0]
    ORIGINS[0] = ("khorakk", "cr_chd_house_of_khorrak", "the House of Khorakk")
    injected("a typo'd faction key, which fails silently forever",
             lambda: ORIGINS.__setitem__(0, saved_faction), "resolves nowhere")

    # The other half of check 9, and the reason it reads the factions table rather
    # than merely grepping for the string: a REAL key that belongs to the wrong
    # culture greps clean and is wrong anyway. wh_main_dwf_dwarfs exists, and a
    # Dwarf faction is not a Chaos Dwarf house.
    ORIGINS[0] = ("khorakk", "wh_main_dwf_dwarfs", "the House of Khorakk")
    injected("a real faction key from the wrong subculture",
             lambda: ORIGINS.__setitem__(0, saved_faction), "not wh3_dlc23_sc_chd")

    saved_affinity = OFFICES[0]["affinity"]
    OFFICES[0]["affinity"] = "nosuchparty"
    injected("an office pointing at a party that does not exist",
             lambda: OFFICES[0].__setitem__("affinity", saved_affinity),
             "unknown affinity")

    # A BACKGROUND IN TWO PARTIES seats its man in whichever the lookup reaches
    # first, which is a dict order and not a decision.
    BACKGROUNDS["temple"].append(("daemonsmith", "Daemonsmith"))
    injected("one background claimed by two parties",
             lambda: BACKGROUNDS["temple"].pop(), "belongs to both")

    _saved_bgs = BACKGROUNDS["road"]
    BACKGROUNDS["road"] = []
    injected("a party nobody can ever belong to",
             lambda: BACKGROUNDS.__setitem__("road", _saved_bgs),
             "has no backgrounds")

    BG_COLOUR["a_slug_that_went_away"] = "Left behind by a rename."
    injected("flavour text left behind by a renamed background",
             lambda: BG_COLOUR.pop("a_slug_that_went_away"),
             "unknown background")

    saved_icon = TRAIT_CATS.pop("derpy_ic_cat_office")
    injected("a trait icon that is not a real trait_categories key",
             lambda: TRAIT_CATS.__setitem__("derpy_ic_cat_office", saved_icon),
             "a category neither this pack nor vanilla has")

    TRAIT_CATS["derpy_ic_cat_office"] = "ui/skins/default/icon_no_such_picture.png"
    injected("a trait category pointing at a picture nothing ships",
             lambda: TRAIT_CATS.__setitem__("derpy_ic_cat_office", saved_icon),
             "points at no picture")

    global ADVANCEMENT_STAGE
    saved_stage = ADVANCEMENT_STAGE
    ADVANCEMENT_STAGE = ""
    injected("an empty advancement_stage, the 2026-09-11 database reject",
             lambda: globals().__setitem__("ADVANCEMENT_STAGE", saved_stage),
             "required reference")

    saved_origin = ORIGIN_COLOUR.pop("khorakk")
    try:
        build()
        raise AssertionError("a missing trait colour string must not build silently")
    except KeyError:
        pass
    finally:
        ORIGIN_COLOUR["khorakk"] = saved_origin

    saved_bg = BG_COLOUR.pop("daemonsmith")
    try:
        build()
        raise AssertionError("a missing background colour must not build silently")
    except KeyError:
        pass
    finally:
        BG_COLOUR["daemonsmith"] = saved_bg

    assert not check(), "the injected faults must all have been restored"

    print("selftest: ok (%d bundles, %d junctions, %d traits, %d loc)"
          % (len(tables["effect_bundles"]),
             len(tables["effect_bundles_to_effects_junctions"]),
             len(tables["character_traits"]),
             len(tables["loc"])))


def main(argv):
    if "--selftest" in argv:
        selftest()
        return 0

    problems = check()
    for problem in problems:
        sys.stderr.write("FAIL %s\n" % problem)
    if problems:
        return 1

    tables = build()
    print("ok: %d bundles, %d junctions, %d traits, %d loc rows"
          % (len(tables["effect_bundles"]),
             len(tables["effect_bundles_to_effects_junctions"]),
             len(tables["character_traits"]),
             len(tables["loc"])))
    if "--check" in argv:
        return 0

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    outdir = os.path.join(root, "Modding Files", "source", "iron_court")
    for path in write_tsvs(outdir):
        print("wrote %s" % path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
