"""The Iron Court - DB generator.

See docs/superpowers/specs/2026-09-11-iron-court-design.md and
docs/mockups/politics_panel.png.

Emits the effect bundles, their effect junctions and the loc for the Chaos Dwarf
political system: six court offices, their vacancy penalties, and the governor
bundles the Overseer agent carries.

    py tools/gen_iron_court.py --check      # validate, write nothing
    py tools/gen_iron_court.py              # write TSVs
    py tools/gen_iron_court.py --selftest

Needs no RPFM: every vanilla fact it checks against comes out of .skilltree_cache.
"""
import io
import json
import os
import re
import sys

PACK_NAME = "derpy_iron_court"
CHD_SUBCULTURE = "wh3_dlc23_sc_chd_chaos_dwarfs"
CACHE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     ".skilltree_cache")

# ---------------------------------------------------------------------------
# The verified vocabulary.
#
# Every (effect, scope) pair below was read out of vanilla's own
# effect_bundles_to_effects_junctions on 2026-09-11; is_positive_value_good came
# from effects.json the same day. check() re-reads both and refuses on any drift,
# because an invented effect key or an (effect, scope) pair CA never ships does
# not error - it silently does nothing forever.
#
# The third element is is_positive_value_good. TWO of the nine are False: they are
# load/cost modifiers where the BENEFIT is a NEGATIVE value. Nothing below ever
# writes a raw signed number - see signed_value().
# ---------------------------------------------------------------------------
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
E_GROWTH = ("wh_main_effect_province_growth_events",
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

ALL_EFFECTS = [E_ARMAMENTS, E_WORKLOAD, E_RAWMAT, E_ORDER, E_GDP, E_GROWTH,
               E_UPKEEP, E_REPLEN, E_PB_LABOUR,
               E_RESEARCH, E_MOVEMENT, E_CONSTRUCT, E_RECRUIT, E_AGENT, E_RAID]

# ---------------------------------------------------------------------------
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
# ---------------------------------------------------------------------------
TIER_SEATS = {1: 2, 2: 3, 3: 4, 4: 5}
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
    reward written +15 arrives in game as a penalty drawn in red. That inversion
    has shipped in this workspace before; here it is arithmetic, not vigilance.
    """
    assert magnitude > 0, "declare a positive magnitude and an intent, not a sign"
    assert intent in (BOON, MALUS), intent
    good = effect[2]
    positive_is_wanted = (good == (intent == BOON))
    return magnitude if positive_is_wanted else -magnitude


# ---------------------------------------------------------------------------
# WHERE A MAN IS FROM - and since 2026-09-12 that is no longer who he sits with.
#
# These were the sixteen HOUSES of the court, and a house was a faction: your
# court was the set of factions whose men served you, so the whole of your
# politics was a consequence of your conquests and nothing you could act on from
# inside. They are ORIGINS now. An origin is one trait on a lord recording where
# he came from and it carries no mechanical weight at all; what he WANTS is his
# background, and his background is what seats him in a party. See PARTIES.
#
# Faction keys are from factions_tables/!!_cr_oldworld_new_factions via
# docs/MOD_STRUCTURE.md - a typo here fails silently forever, so check() greps
# them back out of the staged source. A faction key of None is a PLACE rather
# than a house: where a lord who was never confederated in from anywhere was
# born, and the only kind of origin most of a campaign's lords will ever have.
# ---------------------------------------------------------------------------
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
    ("temple",   "The Priesthood",                               E_GROWTH,    8),
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

PARTY_GOV_BLURB = {
    "crown":   "Your own men hold it, and it is quiet because they are watched.",
    "temple":  "The temples take the province in hand and it grows for Hashut.",
    "forge":   "Forge-guild overseers run the province like a workshop floor.",
    "chain":   "The slavers work the province to the bone and account for every hour.",
    "legion":  "A garrison town under a soldier costs less to keep than it should.",
    "ledger":  "Brokers take the province's books in hand, and the tribute arrives whole.",
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
    "blood":      "Close enough to the line to be dangerous, and he knows it.",
    "sworn":      "He swore to the throne personally, and takes that literally.",
    "acolyte":    "Temple-raised. He still says the words under his breath.",
    "ashpriest":  "He has burned enough offerings to have stopped smelling them.",
    "taurukh":    "Half a bull and entirely a zealot, which is the usual pairing.",
    "daemonsmith": "He talks to what he binds, and it is not clear who is listening.",
    "gunnery":    "He can tell you what a barrel will do before it does it.",
    "furnace":    "Twenty years at a furnace mouth. His eyes are not what they were.",
    "overseer":   "He counts a work gang the way other men count coin.",
    "driver":     "Cheerful, loud, and entirely without a floor.",
    "wrangler":   "He handles hobgoblins, which means he trusts nothing that moves.",
    "immortal":   "He has stood in the front rank and expects the courtesy of it.",
    "infernal":   "Masked so long that the face underneath is a rumour.",
    "siege":      "He has taken walls down for a living and finds doors insulting.",
    "broker":     "He prices everything, including this conversation.",
    "tribute":    "He has collected from people who could not pay, and did anyway.",
    "harbour":    "He knows what every hull on the Sea of Dread is carrying.",
    "apprentice": "Never finished the Tower. Nobody asks him why.",
    "clerk":      "He has read more of the Tower's word than he was meant to.",
    "omens":      "He reads the sky and tells you only the parts you can act on.",
    "caravan":    "He has crossed the Wastes enough times to have stopped counting.",
    "roadwarden": "He keeps a road open by making the alternative worse.",
    "pathfinder": "He goes out further than anyone sensible and comes back.",
    "ashfarmer":  "He has made ash grow something, which nobody believes until they eat.",
    "kiln":       "He smells of slag and can judge a firing by the sound.",
    "elder":      "Old clan, small clan, and a memory for every slight in it.",
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
    E_GROWTH[0]:    "Growth: %+n",
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
    E_ARMAMENTS[0]: "Armaments",
    E_WORKLOAD[0]:  "Workload",
    E_ORDER[0]:     "Control",
    E_GDP[0]:       "Building income",
    E_UPKEEP[0]:    "Upkeep",
    E_REPLEN[0]:    "Replenishment",
    E_PB_LABOUR[0]: "Post-battle Labour",
    E_GROWTH[0]:    "Growth",
    E_RAWMAT[0]:    "Raw Materials",
    E_RESEARCH[0]:  "Research",
    E_MOVEMENT[0]:  "Movement range",
    E_CONSTRUCT[0]: "Construction cost",
    E_RECRUIT[0]:   "Recruitment cost",
    E_AGENT[0]:     "Hero success",
    E_RAID[0]:      "Raiding income",
}

# Which of them are percentages, so the short line does not put a % on Control
# or Growth, which are flat numbers.
EFFECT_PERCENT = {
    E_ORDER[0]: False,
    E_GROWTH[0]: False,
    E_RESEARCH[0]: False,
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
    E_ORDER[0]: ("public_order_effect", "Control"),
    E_RESEARCH[0]: ("effect_technology_research_points_description",
                    "Research rate"),
}


def effect_line(effect, magnitude, intent):
    """One tooltip line: CA's wording with this row's signed value in it."""
    text = EFFECT_TEXT[effect[0]]
    return text.replace("%+n", "%+d" % signed_value(effect, magnitude, intent))


# ---------------------------------------------------------------------------
# The six offices.
#
# affinity is the house that considers the office theirs. Appointing that house's
# man doubles its standing gain; appointing an outsider costs the affine house
# loyalty. That one field is the whole Rome 2 squeeze - see spec section 5.
#
# NOTE ON THE SLAVE PITS: Chaos Dwarfs have no "slaves" pooled resource. The
# vanilla set is labour, armaments, raw_materials, workload, efficiency and
# conclave_influence (read from pooled_resources.json, 2026-09-11). Slaves are
# flavour; the mechanic is post-battle Labour.
# ---------------------------------------------------------------------------
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
        "blurb": "The forges of Zharr Naggrund answer to one voice, and it is his.",
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
        "vacant_blurb": "The kilns burn on regardless, and the bill arrives regardless.",
        "effects": [(E_CONSTRUCT, 8, BOON)],
        "vacancy": [(E_CONSTRUCT, 4, MALUS)],
    },
    {
        "slug": "fields",
        "name": "Steward of the Ash Fields",
        "affinity": "hearth",
        "tier": 4,
        "blurb": "Even ash will grow something, if a Dawi Zharr is made to care.",
        "vacant_blurb": "The ash fields are left to the ash.",
        "effects": [(E_GROWTH, 10, BOON)],
        "vacancy": [(E_GROWTH, 5, MALUS)],
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
        "vacant_blurb": "The raiders keep their own accounts, which is to say they keep the takings.",
        "effects": [(E_RAID, 10, BOON)],
        "vacancy": [(E_RAID, 5, MALUS)],
    },
]

# ---------------------------------------------------------------------------
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
# ---------------------------------------------------------------------------
TRAIT_ICON = "chaos_dwarfs"      # a real trait_categories key; 'dwarf' is the other


def standing_trait_key(tier):
    """The band trait for a man who clears tier `tier`; 0 clears nothing."""
    return "derpy_ic_standing_%d" % tier


# What the band is CALLED, and what it tells the player. Both are about a SEAT
# rather than a number, because the number is already on the court panel and
# what a player wants off a character card is "can he take the job".
STANDING_BAND = {
    0: ("Unproven at Court",
        "He has done nothing the Iron Court thinks worth remembering.",
        "No seat of the court is open to him. Influence is earned in the "
        "field - a victory, a settlement taken, a rank won - and by holding "
        "a seat once he has one."),
    4: ("Noticed at Court",
        "His name has begun to come up, and not only when something breaks.",
        "He has earned enough influence to be seated on %s, the lowest tier "
        "of the ziggurat." % TIER_NAME[4]),
    3: ("Spoken For at Court",
        "A house or two would take him, and one of them says so out loud.",
        "He has earned enough influence to be seated on %s." % TIER_NAME[3]),
    2: ("Weighed at Court",
        "The old ones have stopped talking over him when he speaks.",
        "He has earned enough influence to be seated at %s." % TIER_NAME[2]),
    1: ("Fit for the Apex",
        "There is no room above him but Hashut's own.",
        "He has earned enough influence for any seat in the court, %s "
        "included." % TIER_NAME[1]),
}

AMBITION_BANDS = {
    "cautious": ("Cautious", "His influence carries less weight in the Iron Court.",
                 "His influence counts 25% less towards his party's."),
    "steady": ("Steady", "His influence carries its usual weight in the Iron Court.",
               "His influence counts as usual towards his party's."),
    "ambitious": ("Ambitious", "Every honour becomes another claim on the Iron Court.",
                  "His influence counts 25% more towards his party's."),
}

ORIGIN_COLOUR = {
    "conclave":     "Conclave-raised, and never lets anyone forget which tower taught him.",
    "astragoth":    "Old blood, old rites, and a back that has never once bent.",
    "azgorh":       "Forge-bred in Azgorh, and smells of it at forty paces.",
    "zhatan":       "Raised in the Warhost, where a man is his last campaign.",
    "skullstack":   "Company-raised: he prices a man before he greets him.",
    "khorakk":    "Born to the bull-cult, and it shows in everything he does.",
    "uzkulak":    "Raised on a deck, counting other men's cargo.",
    "artificers": "Snakebeard's people take apart anything that holds still.",
    "fists":      "Temple-drilled, and proud of the scars that took.",
    "horns":      "The Horns raise their sons lean and keep them that way.",
    "baal":       "Baal's kin smell of burnt brass and do not apologise for it.",
    "azeros":     "Azeros builds. His people measure a thing before they hate it.",
    "bzaark":     "Bzaark's household is not known for restraint, or for survivors.",
    "blackdwarf": "Sworn to the Black Dwarf, which is not the same as being free.",
    "kraken":     "The Armada raised him, and the Armada expects its due.",
    "zharrduk":   "Zharrduk-born, and runs a province the way the plain is run.",
    # AND THE PLACES, for a lord who was raised in your own lands rather
    # than confederated in from somebody else's.
    "zharr":      "Raised under the Tower itself, and impossible to impress.",
    "plain":      "Plain-bred: he measures everything against a horizon.",
    "gorgoth":    "Gorgoth raised him, and Gorgoth raises them hard.",
    "stump":      "From the Stump, where the ground is still warm.",
    "zornuzkul":  "Born on the Great Skull Land. He does not discuss it.",
    "gash":       "Gash Kadrak: orc country, and he grew up armed.",
    "mines":      "Born underground and never entirely comfortable above it.",
    "wastes":     "Waste-born, and he still eats like the next meal is theoretical.",
}


# THE KEY KEPT ITS OLD SPELLING ON PURPOSE. These rows were the house
# traits and are the origin traits now; a lord in a campaign started
# before the change is already carrying derpy_ic_house_conclave, which
# reads correctly as an origin and needs no migration. Renaming the key
# would leave every such lord holding a trait with no DB row behind it.
def origin_trait_key(slug):
    return "derpy_ic_house_" + slug


def bg_trait_key(slug):
    return "derpy_ic_bg_" + slug


def office_trait_key(slug):
    return "derpy_ic_title_" + slug


# The governor base bundle. cm:create_new_custom_effect_bundle takes this as its
# base and scales the values by the Overseer's rank at runtime, which is why there
# is one bundle here rather than five rank bundles. A custom effect bundle still
# resolves against a real effect_bundles record, so this row must exist.
GOVERNOR_BASE = [(E_ORDER, 2, BOON), (E_GROWTH, 8, BOON)]

BUNDLE_ICON = "chd_conclave_influence.png"

# effect_bundles_to_effects_junctions.advancement_stage is a FOREIGN KEY into
# effect_bundle_advancement_stages, and vanilla fills it on all 16,430 rows. An
# empty string there is not "no stage", it is an unresolvable reference, and the
# game refuses the whole pack at database load - naming whichever row sorts
# first, which is why the 2026-09-11 crash pointed at House of Baal and not at
# the fault. 'start_turn_completed' is the column's own default and what 16,351
# of vanilla's rows use.
ADVANCEMENT_STAGE = "start_turn_completed"


# ---------------------------------------------------------------------------
# THE EVENT FEED.
#
# The court did everything in silence. Appointments, dismissals, expired terms,
# a plot landing or missing, a party walking into the court - all of it was
# written to IC.log, a forty-entry ring buffer inside the save that is only ever
# drawn on the panel's RECORD tab. A player who did not open the panel and change
# tabs was told nothing at all, which is what the 2026-09-15 session reported as
# "no event log for intrigue success or fail" and "no clear reason why another
# party joined".
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
# THE EVENT TYPE IS NOT A FREE CHOICE EITHER, and this is the part that would
# have shipped broken. The table offers four scripted types, two of them
# "located" variants. Reading the table alone suggests
# scripted_persistent_located_event is ideal - it is the ONLY type vanilla ships
# with instant_open false, i.e. saved to the event history without stealing the
# screen. But grepping all 5,778 of CA's shipped scripts for what they pass to
# the PLAIN cm:show_message_event gives ten distinct indices, and every one of
# them resolves to scripted_persistent_event (persistent=true, instant_open
# true) or scripted_transient_event (persistent=false). The located variants are
# for cm:show_message_event_located and are never used with the plain call. So
# the choice here is between exactly two proven shapes, and "ideal but unproven"
# would have been a silent non-draw nobody could have debugged from in game.
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
# SECONDARY key names the specific seat by reusing the office bundle's own title
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

# slug, persistent, image, sound, title, primary sentence, secondary line.
#
# THE SECONDARY IS THE SMALL PLATE UNDER THE PRIMARY, and passing "" for it
# does not hide the plate - it draws it empty, which is what the 2026-09-17
# report was. None means the event passes its own key at the call site
# instead (office_lost and snub name the seat), so nothing here would be
# read; anything else is emitted as a loc key and used as the default.
#
# Every image key was read out of the vanilla table's own chd/ set; an image key
# the engine does not know is another silent non-draw.
EVENTS = [
    ("plot_ok", True, "chd/diplomacy", "Positive",
     "The Court Moves",
     "Your move succeeded. The court has felt it, and the parties have "
     "adjusted their opinion of you accordingly.",
     "SUCCESS"),
    ("plot_fail", True, "chd/army_morale_down", "Negative",
     "The Court Refuses",
     "Your move failed. What it cost you is spent, and the party it was "
     "aimed at now knows you tried.",
     "FAILURE"),
    # THE ONE THE PLAYER DID NOT DO. A term running out empties a seat with no
    # input from the player at all, which is exactly why it needs telling: the
    # 2026-09-15 report was "no event when officers are removed from office".
    ("office_lost", True, "chd/civilisation_down", "Neutral",
     "A Seat Stands Empty",
     "An officer no longer holds his seat. The office grants nothing while it "
     "stands empty, and its party will not thank you for the vacancy.",
     # NAMES THE SEAT AT THE CALL SITE, out of the office bundle's own key.
     None),
    ("party_joined", True, "chd/faction", "Positive",
     "A Party Enters the Court",
     "A faction you absorbed has brought its men into your court as a party "
     "of its own. It holds weight now, and it will expect seats.",
     "THE COURT GROWS"),
    # THE MOST EXPENSIVE THING THAT CAN HAPPEN, and the panel's alert bar was
    # the only place it was said.
    ("secede_warn", True, "chd/settlement_lost", "Negative",
     "A Party Prepares to Leave",
     "A party has begun counting down to secession. When the count runs out it "
     "takes its provinces with it. Settle with it, or take its seats away "
     "before it can.",
     "SECESSION PENDING"),
    # TRANSIENT, ALONE: six offices can snub six parties in one turn.
    ("snub", False, "chd/army_morale_down", "Negative",
     "A Party Is Slighted",
     "A party is owed a seat it does not hold. Its loyalty falls every turn "
     "the grievance stands.",
     # NAMES THE SEAT AT THE CALL SITE, as office_lost does.
     None),
    # LAST, AND THAT IS DELIBERATE. An event's index is derived from its POSITION
    # in this list, so a row inserted in the middle renumbers everything after it
    # - putting this one above snub moved snub from 2605 to 2606 while the model
    # still said 2605, which the build gate refused. Appending costs nothing and
    # cannot do that.
    #
    # THE THING ITSELF. secede_warn announced a countdown and nothing announced
    # the end of it - and at zero loyalty there is no countdown in front of it at
    # all now, so without this a party takes a province, puts an army on the map
    # and says nothing whatsoever about it.
    ("secede_done", True, "chd/settlement_lost", "Negative",
     "A Party Has Broken With You",
     "A party has left your court. It has taken land with it, and there is an "
     "army of its own people standing on that land. Its seats are empty and its "
     "men have come home to your own house.",
     "SECESSION"),
    # AND THE ONE THAT COMES BEFORE ANY OF THEM. secede_warn fires only when a
    # party has a big enough share of the court to be worth counting down; a
    # small party with nothing to lose rots to the floor without a single card
    # and then leaves on the turn it hits it. This is that party's only notice,
    # and it lands while the player can still buy it off.
    ("loyalty_warn", True, "chd/army_morale_down", "Negative",
     "A Party Turns Against You",
     "A party's loyalty has fallen far enough to be worth watching. Give it a "
     "seat, or buy it off - a party that reaches the bottom does not wait, and "
     "it leaves with whatever land it holds.",
     "DISLOYALTY"),
    # YOUR OWN HOUSE, COMING APART. The Crown cannot secede from itself, so
    # until 2026-09-18 its loyalty was written every turn and read by nothing.
    # This is what it costs now. chd/faction is the same picture party_joined
    # draws, because the thing that happened is the same thing: a party the
    # court did not have yesterday.
    ("splinter", True, "chd/faction", "Negative",
     "Your Own House Splits",
     "Your party's loyalty has run out. The men who will not answer to you any "
     "more have organised as an interest of their own - they hold a share of "
     "the court that used to be yours, and they will expect seats like any "
     "other party.",
     "A NEW PARTY"),
    # THE SECOND NOTICE ON A SECESSION. secede_warn lands at the top of a
    # five-turn clock and nothing was said again until the party was gone - and
    # Provoke, which shortens that clock outright, skipped the opening card too,
    # so the fastest route to losing a province was also the quietest. This
    # fires once, as the count enters its last warn_turns.
    ("secede_soon", True, "chd/settlement_lost", "Negative",
     "The Count Is Nearly Out",
     "A party that began counting down to secession is close to the end of it. "
     "When the count runs out it leaves, and it takes the provinces it holds "
     "with it. There will be no further warning.",
     "SECESSION IMMINENT"),
    # AND THE ONE YOUR OWN HOUSE NEVER GAVE. The split used to happen on the
    # turn the Crown's loyalty crossed the line, with its card arriving in the
    # same frame - which tells the player what has happened, never what is
    # about to. This is the warning that now runs in front of it.
    ("splinter_warn", True, "chd/faction", "Negative",
     "Your Own House Is Turning",
     "Your party's loyalty has run out. The men who will not answer to you any "
     "more are organising as an interest of their own, and when they finish "
     "they will hold a share of the court that is currently yours. Win them "
     "back before it is settled, or lose them.",
     "A SPLIT PENDING"),
    # A PARTY WITH NOTHING TO TAKE. Author, 2026-09-23: a party with nobody in it
    # and no province to its name broke up instead of seceding, where before it
    # "seceded" into another rising's faction, renamed it and started a war.
    ("dissolved", True, "chd/faction", "Neutral",
     "A Party Dissolves",
     "A party with nobody left in it and no province to its name has broken up "
     "rather than walk out. Nobody leaves and nothing is lost; its share of the "
     "court is simply gone.",
     "PARTY DISSOLVED"),
    ("party_plot_warn", True, "chd/army_morale_down", "Negative",
     "A Party Moves Against You",
     "One of the court's parties is preparing to strike at the Crown next turn. "
     "Open the Iron Court: their card names the man and the move, and what "
     "would stop it.",
     "WARNING"),
    ("party_plot_ok", True, "chd/army_morale_down", "Negative",
     "The Court Strikes at the Crown",
     "A party's move against the Crown has landed. The court record says who "
     "did it and what it cost you.",
     "STRUCK"),
    ("party_plot_fail", True, "chd/diplomacy", "Positive",
     "A Plot Is Foiled",
     "A party tried to move against the Crown and failed. What it spent is "
     "gone, and the court record names them.",
     "FOILED"),
    ("party_plot_dropped", True, "chd/diplomacy", "Neutral",
     "A Plot Comes to Nothing",
     "The move a party was preparing against the Crown has fallen apart "
     "before it could land.",
     "ABANDONED"),
    ("party_feud", True, "chd/faction", "Neutral",
     "A Feud in the Court",
     "Two parties have turned on each other. While the feud lasts they strike "
     "at each other rather than at you.",
     "FEUD"),
    ("party_feud_end", True, "chd/faction", "Neutral",
     "A Feud Ends",
     "A feud between two parties is over. Either may turn its attention back "
     "to the Crown.",
     "FEUD OVER"),
    ("party_feud_murder", True, "chd/army_morale_down", "Negative",
     "Blood Between Parties",
     "A feud at court has ended in a killing. One of your men is dead at the hands "
     "of a rival party. The court record names both sides.",
     "KILLED"),
    ("party_demand", True, "chd/diplomacy", "Neutral",
     "A Party Makes a Demand",
     "One of the court's parties demands a post for one of its men. Their card "
     "names the man and the post. Grant it and their loyalty rises; refuse it, "
     "or let the time run out, and it falls.",
     "DEMAND"),
    ("party_demand_refused", True, "chd/army_morale_down", "Negative",
     "A Demand Refused",
     "A party's demand went unmet. They will remember it, and their loyalty "
     "has fallen.",
     "REFUSED"),
    ("party_offer", True, "chd/diplomacy", "Positive",
     "A Party Offers a Favour",
     "A loyal party offers the Crown something for nothing. Their card says "
     "what. Click it to accept or decline, but the offer will not wait long, "
     "and the other parties will notice if you take it.",
     "OFFER"),
]

# THE DEMAND MISSIONS. Issued from Lua as a mission string (IC.demand_string);
# the string route still needs a missions row per key. Field for field the
# Great Guilds bounty row, except: SCRIPTED because the string supplies the
# objective, a real picture (chd/generic is not one), and no manual cancel -
# a cancel is a void, and a void costs nothing, so it would be a free refusal.
DEMAND_REWARD = "derpy_ic_demand_reward"
DEMAND_REWARD_TEXT = "The party's loyalty rises."
DEMANDS = [
    ("derpy_ic_demand_office", "A Party Demands an Office",
     "One of the court's parties wants one of its men seated in a vacant "
     "office. Their party card names the man and the office. Seat him before "
     "the time runs out and their loyalty rises; let it run out, or give the "
     "office to someone else, and it falls.",
     "The office is filled as they asked, and the party is satisfied.",
     "Seat the party's man in the office they named (see their party card)."),
    ("derpy_ic_demand_province", "A Party Demands a Province",
     "One of the court's parties wants one of its men made overseer of a "
     "province. Their party card names the man and the province. Appoint him "
     "before the time runs out and their loyalty rises; let it run out, or "
     "give the province to someone else, and it falls.",
     "The province has the overseer they asked for, and the party is satisfied.",
     "Make the party's man overseer of the province they named (see their "
     "party card)."),
]


def event_key(slug):
    return "derpy_ic_event_" + slug


def event_index(slug):
    """The number the script passes. Derived from position, never typed twice."""
    for i, ev in enumerate(EVENTS):
        if ev[0] == slug:
            return EVENT_INDEX_BASE + i
    raise KeyError(slug)


# ---------------------------------------------------------------------------
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
      (E_GROWTH, 2, BOON)]),
    ("mastery", 60, "Master of the Court",
     "The parties argue, and then they do as they are told.",
     [(E_ORDER, 4, BOON), (E_GDP, 8, BOON), (E_UPKEEP, 10, BOON)]),
    ("command", 40, "In Command of the Court",
     "The Crown is first among the parties, and no more than first.",
     [(E_ORDER, 2, BOON)]),
    ("contested", 10, "A Contested Court",
     "Every decree is a negotiation, and every negotiation has a price.",
     [(E_ORDER, 2, MALUS), (E_UPKEEP, 5, MALUS)]),
    ("lost", 0, "The Court Is Not Yours",
     "The parties rule and the Crown is consulted, when there is time.",
     [(E_ORDER, 8, MALUS), (E_UPKEEP, 20, MALUS), (E_GDP, 15, MALUS),
      (E_GROWTH, 2, MALUS)]),
]


def control_slugs():
    return [b[0] for b in CONTROL_BANDS]


def bundle_key(kind, slug):
    return "derpy_ic_%s_%s" % (kind, slug)


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


def move_result_key(move_key, ok):
    """The loc key IC.move_result_key builds at the other end of the fence."""
    return ("event_feed_strings_text_derpy_ic_move_" + move_key
            + ("_ok" if ok else "_fail"))


def office_by_slug(slug):
    for office in OFFICES:
        if office["slug"] == slug:
            return office
    return None


# ---------------------------------------------------------------------------
# build
# ---------------------------------------------------------------------------
def build():
    bundles = []
    junctions = []
    loc = []

    def emit(key, title, description, target, effects):
        """One bundle: the DB row, its effect junctions, and BOTH loc entries.

        The row text and the loc are written from the same two strings on
        purpose. Row text alone draws an icon with no text in the Faction
        Effects panel - measured 2026-09-05 over 27 bundles that shipped that
        way. CA ships both, 11,710 entries deep.
        """
        bundles.append({
            "key": key,
            "localised_description": description,
            "localised_title": title,
            "bundle_target": target,
            "priority": "1",
            "ui_icon": BUNDLE_ICON,
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
        loc.append({"key": "derpy_ic_control_name_" + slug,
                    "text": name, "tooltip": "false"})

    emit("derpy_ic_gov_base", "Overseer of the Province",
         "An Overseer of the court sits here, and the province knows it.",
         "faction", GOVERNOR_BASE)

    # ONE PER PARTY, and the key kept the "gov_house" stem so a save made
    # before the change still names a bundle that exists when the model
    # takes the old one off. The nine parties replace sixteen houses.
    for slug, display, effect, magnitude in PARTIES:
        emit(bundle_key("gov_house", slug),
             "Overseer: " + display, PARTY_GOV_BLURB[slug],
             "faction", [(effect, magnitude, BOON)])

    # Office and house names are read by the panel at draw time, never from a
    # turn handler - a loc call inside one is a turn-1 CTD that pcall does not
    # catch.
    for office in OFFICES:
        loc.append({"key": "derpy_ic_office_name_" + office["slug"],
                    "text": office["name"], "tooltip": "false"})
    # A PARTY'S NAME IS ROLLED and lives in the save, so this is only the
    # generic fallback - what the panel draws before a court has been
    # rolled, and what the crown would be called if the faction it
    # belongs to somehow has no screen name of its own.
    for slug, display, _effect, _mag in PARTIES:
        loc.append({"key": "derpy_ic_party_name_" + slug,
                    "text": display, "tooltip": "false"})
    # ORIGINS AND BACKGROUNDS IN ROW FORM. The trait carries its own name
    # ("Born: the House of Khorakk"), which is the right shape for a
    # character panel and the wrong one for a column.
    for slug, _faction, display in ORIGINS:
        loc.append({"key": "derpy_ic_origin_name_" + slug,
                    "text": display, "tooltip": "false"})
    for _party, slug, display in backgrounds():
        loc.append({"key": "derpy_ic_bg_name_" + slug,
                    "text": display, "tooltip": "false"})

    # --- traits -----------------------------------------------------------
    trait_info = []
    traits = []
    trait_levels = []

    def emit_trait(key, name, colour, explanation, removal):
        # trait_info is the table a trace outward never reaches: one row per
        # trait, one column, and vanilla's count matches character_traits exactly.
        trait_info.append({"trait": key})
        traits.append({
            "key": key,
            "no_going_back_level": "1",
            "hidden": "false",
            "precedence": "1",
            "icon": TRAIT_ICON,
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
                   "His influence at court has changed.")

    for _slug in ("cautious", "steady", "ambitious"):
        _name, _colour, _explain = AMBITION_BANDS[_slug]
        emit_trait("derpy_ic_ambition_" + _slug, _name, _colour, _explain,
                   "His ambition does not change.")

    # WHERE HE IS FROM. Flavour and nothing else - an origin moves no
    # number in the court. It used to BE his politics, and that was the
    # fault: a lord you recruited yourself wanted what his grandfather's
    # faction wanted, forever, and you could not change it.
    for slug, _faction, display in ORIGINS:
        emit_trait(origin_trait_key(slug),
                   "Born: " + display[0].upper() + display[1:],
                   ORIGIN_COLOUR[slug],
                   "Where he came from. It says nothing about what he wants.",
                   "His origin has been struck from the rolls.")

    # WHAT HE IS, which is the whole of the membership rule. A background
    # belongs to one party; a lord sits with the party his background
    # names, and with the crown when that party is not organised.
    for party, slug, display in backgrounds():
        emit_trait(bg_trait_key(slug),
                   display,
                   BG_COLOUR[slug],
                   "What he did before you had a use for him, and who that "
                   "puts him with at court.",
                   "He has left the trade behind, whatever he says.")

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
                   "He has been stripped of the office, and everyone saw it.")

    # ---- the event feed ---------------------------------------------------
    # FOUR ROWS PER EVENT, and three of the four tables exist only to turn a
    # number into a record. The group and the member are given different names
    # on purpose, the way vanilla does it (wh3_dlc27_event_group_old_gods_curse
    # holds wh3_dlc27_event_feed_scripted_old_gods_curse): they are different
    # things, and a single name for both hides which side a broken link is on.
    groups, members, criteria, feed = [], [], [], []
    for slug, persistent, image, sound, title, primary, secondary in EVENTS:
        key = event_key(slug)
        group_id = key + "_group"
        groups.append({"id": group_id})
        members.append({"group": group_id, "id": key, "priority": "0.0"})
        criteria.append({"member": key, "value": str(event_index(slug))})
        # IN THE DEFINITION'S OWN FIELD ORDER. write_tsvs takes the column order
        # off the first row's keys, so a dict built in a convenient order writes
        # a header CA's definition does not match.
        mine = {
            "event": ("scripted_persistent_event" if persistent
                      else "scripted_transient_event"),
            "group": group_id,
            "image": image,
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
        if secondary is not None:
            loc.append({"key": "event_feed_strings_text_" + key
                               + "_secondary",
                        "text": secondary, "tooltip": "false"})

    # AND THE PER-MOVE LINES THE PLOT CARDS PREFER. The generic SUCCESS
    # and FAILURE rows above stay as the fallback: IC.feed takes the
    # caller's key when it has one, so a move with no row of its own
    # still says something rather than drawing the empty plate.
    #
    # UPPERCASED TO MATCH THE OUTCOME IT IS JOINED TO. The plate carries
    # two things and they are read as one line.
    for move_key, move_name in model_moves():
        loc.append({"key": move_result_key(move_key, True),
                    "text": move_name.upper() + " - SUCCESS",
                    "tooltip": "false"})
        loc.append({"key": move_result_key(move_key, False),
                    "text": move_name.upper() + " - FAILURE",
                    "tooltip": "false"})

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


# ---------------------------------------------------------------------------
# check
# ---------------------------------------------------------------------------
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


def _lua_rebel_generals():
    """IC.REBEL_GENERALS and IC.REBEL_LORD, read out of the shipped Lua."""
    path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "Modding Files", "pack", "script", "campaign", "mod",
        "zzz_derpy_iron_court.lua")
    src = io.open(path, encoding="utf-8").read()
    block = re.search(r"IC\.REBEL_GENERALS = \{(.*?)\n\}", src, re.S)
    keys = set(re.findall(r'\["([^"]+)"\]\s*=\s*true', block.group(1))) \
        if block else set()
    lord = re.search(r'IC\.REBEL_LORD = "([^"]+)"', src)
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
# is a Chaos Dwarf whose key says otherwise, and reading keys shipped him onto
# this list for one revision.
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


def _lua_rebel_heroes():
    """IC.REBEL_HEROES, read out of the shipped Lua."""
    path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "Modding Files", "pack", "script", "campaign", "mod",
        "zzz_derpy_iron_court.lua")
    src = io.open(path, encoding="utf-8").read()
    block = re.search(r"IC\.REBEL_HEROES = \{(.*?)\n\}", src, re.S)
    if not block:
        return None
    return dict(re.findall(r'\["([^"]+)"\]\s*=\s*"([^"]+)"', block.group(1)))


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

def _lua_rebel_roster():
    """IC.REBEL_ROSTER and IC.TUNE.rebel_units, read out of the shipped Lua."""
    path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "Modding Files", "pack", "script", "campaign", "mod",
        "zzz_derpy_iron_court.lua")
    src = io.open(path, encoding="utf-8").read()
    block = re.search(r"IC\.REBEL_ROSTER = \{(.*?)\n\}", src, re.S)
    units = re.findall(r'"([^"]+)"', block.group(1)) if block else []
    want = re.search(r"rebel_units\s*=\s*(\d+)", src)
    return units, (int(want.group(1)) if want else None)


# An army's twenty slots include the general it is created with.
ARMY_SLOTS = 20


def check_rebel_roster():
    out = []
    units, want = _lua_rebel_roster()
    if not units:
        return ["IC.REBEL_ROSTER not found in zzz_derpy_iron_court.lua"]
    seen = set()
    for key in units:
        if key in seen:
            out.append("IC.REBEL_ROSTER lists %s twice" % key)
        seen.add(key)
    table = _cache_table("main_units")
    if table is None:
        out.append("main_units not cached - run "
                   "tools/fetch_vanilla_tables.py main_units")
    else:
        fields, rows = table
        ui = fields.index("unit")
        known = set(r[ui] for r in rows)
        for key in units:
            if key not in known:
                out.append("IC.REBEL_ROSTER lists %s, which is not in "
                           "main_units" % key)
    if want is None:
        out.append("IC.TUNE.rebel_units not found")
    else:
        if want > len(units):
            out.append("IC.TUNE.rebel_units is %d and the roster holds %d, so "
                       "every rebel army is short" % (want, len(units)))
        if want > ARMY_SLOTS - 1:
            out.append("IC.TUNE.rebel_units is %d - an army holds %d including "
                       "its lord, so the roster is %d"
                       % (want, ARMY_SLOTS, ARMY_SLOTS - 1))
    return out

# ---------------------------------------------------------------------------
# The rebel crests: one DB row each, so two rebellions stop sharing a banner.
# ---------------------------------------------------------------------------
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

# TABLES WHOSE CACHED DEFINITION IS KNOWN TO BE WIDER THAN THEIR ROWS, and what
# covers them instead. RPFM patches a definition's unused fields without removing
# them, so a name-to-value zip of the dump misaligns after the first such field.
#
# factions: check_factions() holds all 45 columns of all four rows against the
#           donor RPFM exported out of db.pack, which is stricter than check 14.
CACHE_WIDTH_KNOWN = {"factions"}


def check():
    """Every way this data can be wrong and say nothing about it."""
    out = []
    tables = build()

    # 0. The rebel general whitelist must still be what the DB says. A subtype
    #    key is an unvalidated string, and a wrong one HERE is not the usual
    #    silent no-op - create_force_with_general takes a subtype the faction
    #    cannot field and the game dies, with no Lua error and no minidump
    #    (2026-09-17, derpy_bzaark, 1.4 seconds after the secession).
    out.extend(check_rebel_generals())
    out.extend(check_not_dwarf())
    out.extend(check_rebel_heroes())
    out.extend(check_rebel_roster())
    out.extend(check_factions())
    out.extend(check_demand_keys())

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
        for effect in ALL_EFFECTS:
            if (effect[0], effect[1]) not in pairs:
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
    #
    #     This used to be a harder rule - a faction with no house left a player
    #     leading it with no party of his own at all - and it is not that any
    #     more, because the crown is the player's party whatever faction he
    #     leads. It stays a build failure anyway: checking the keys we DO name
    #     proves nothing about the ones we forgot, and that is how
    #     wh3_dlc23_chd_minor_faction went missing for a month.
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

    # 10c. AND ENOUGH OF THEM TO ROLL. The model rolls two to four rivals and
    #      never the crown, so four rivals have to exist to be drawn without
    #      repeating one. RIVALS_MAX is read out of the model Lua rather than
    #      written down twice.
    _rivals_max = 4
    try:
        _model = io.open(os.path.join(
            root, "Modding Files", "pack", "script", "campaign", "mod",
            "zzz_derpy_iron_court.lua"), encoding="utf-8").read()
        _m = re.search(r"rivals_max\s*=\s*(\d+)", _model)
        if _m:
            _rivals_max = int(_m.group(1))
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

    # 13. The trait icon must be a real trait_categories key. An invented one is a
    #     load-time DB reject, which surfaces in bad_mods_report.txt rather than
    #     as anything the game says out loud.
    vanilla_traits = _cache_table("character_traits")
    if vanilla_traits is not None:
        fields, rows = vanilla_traits
        cats = set(r[fields.index("icon")] for r in rows)
        if TRAIT_ICON not in cats:
            out.append("trait icon %r is not a category vanilla uses" % TRAIT_ICON)

    # 14. No column may be left empty that vanilla never leaves empty. Such a
    #     column is a required foreign key whether or not the schema says so, and
    #     an empty string in one is a load-time database reject that names an
    #     arbitrary row. This is the check that was missing on 2026-09-11: every
    #     junction row shipped with an empty advancement_stage, and the game
    #     rejected the pack while naming House of Baal, which merely sorted first.
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
            for row in tables["event_feed_message_events"]:
                if row["event"] not in ("scripted_persistent_event",
                                        "scripted_transient_event"):
                    out.append("%s is not one of the two types CA raises with "
                               "the plain cm:show_message_event" % row["event"])

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
    # 16g. And every event must carry BOTH its loc keys, or it draws untitled.
    lkeys = set(e["key"] for e in tables["loc"])
    for slug, _p, _i, _s, _t, _pr, _sec in EVENTS:
        parts = ["title", "primary"]
        # AND THE SECONDARY, WHEN IT DECLARES ONE. IC.feed hands the engine
        # this key by default, and a key with no row draws the empty plate
        # the column was added to fill - silently, exactly as before.
        if _sec is not None:
            parts.append("secondary")
        for part in parts:
            k = "event_feed_strings_text_" + event_key(slug) + "_" + part
            if k not in lkeys:
                out.append("event %s has no %s loc key" % (slug, part))
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


# ---------------------------------------------------------------------------
# write
# ---------------------------------------------------------------------------
TSV_META = {
    "effect_bundles": ("effect_bundles_tables", 4),
    "effect_bundles_to_effects_junctions":
        ("effect_bundles_to_effects_junctions_tables", 3),
    # Versions read off the cached vanilla definitions 2026-09-11. A version that
    # does not match the field shape imports a wrong-width TSV.
    "trait_info": ("trait_info_tables", 1),
    "character_traits": ("character_traits_tables", 3),
    "character_trait_levels": ("character_trait_levels_tables", 0),
    # THE EVENT FEED'S FOUR. Versions read off CA's own shipped files on
    # 2026-09-16 - the `definition.version` inside each cached RPFM dump, not
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


# ---------------------------------------------------------------------------
# selftest
# ---------------------------------------------------------------------------
def selftest():
    # DERIVED, not hardcoded. These were pinned at ten and so failed the moment
    # a house was added - which is a selftest reporting on its own literals
    # rather than on the data. What is actually invariant is that the counts
    # AGREE across the five tables, and that nothing is duplicated.
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
    seats = {}
    for office in OFFICES:
        seats[office["tier"]] = seats.get(office["tier"], 0) + 1
    assert seats == TIER_SEATS,         "the court is not a ziggurat: seats per tier %r, wanted %r" % (seats, TIER_SEATS)
    assert len(OFFICES) == sum(TIER_SEATS.values()), "an office outside every tier"
    widths = [TIER_SEATS[t] for t in sorted(TIER_SEATS)]
    assert widths == sorted(widths),         "a tier is narrower than the one above it: %r" % (widths,)

    # And the higher seat must actually BE the better seat. A multiplier table
    # that is not strictly decreasing makes the ziggurat a shape and nothing
    # more - fourteen equal offices drawn in a pyramid.
    mults = [TIER_MULT[t] for t in sorted(TIER_MULT)]
    assert all(a > b for a, b in zip(mults, mults[1:])),         "tier multipliers are not strictly decreasing: %r" % (mults,)
    assert sorted(TIER_MULT) == sorted(TIER_SEATS) == sorted(TIER_NAME),         "the three tier tables disagree about which tiers exist"
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
    assert len(keys) == n_offices * 2 + 1 + n_parties + len(CONTROL_BANDS), \
        ("one office and one vacancy bundle per office, one governor base, and "
         "one governor flavour per PARTY - it was per house, and there were "
         "sixteen of those, plus one per control band: expected %d, got %d"
         % (n_offices * 2 + 1 + n_parties + len(CONTROL_BANDS), len(keys)))

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

    # No bundle description may carry a value placeholder. The Great Guilds
    # shipped 36 that did, with a selftest that asserted the opposite.
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
    n_traits = n_origins + n_backgrounds + n_offices + n_bands + len(AMBITION_BANDS)
    assert len(tables["character_traits"]) == n_traits, \
        ("one trait per origin, per background, per office and per "
         "standing band: expected %d, got %d"
         % (n_traits, len(tables["character_traits"])))
    assert len(tables["trait_info"]) == len(tables["character_traits"]), \
        "trait_info is one row per trait - vanilla has 744 of each"
    assert len(tables["character_trait_levels"]) == len(tables["character_traits"]), \
        "one level per trait"
    for row in tables["character_trait_levels"]:
        assert row["key"] == row["trait"], \
            "single-level traits key the level as the trait - CA's own convention"
    trait_keys = set(r["key"] for r in tables["character_traits"])
    assert len(trait_keys) == n_traits, "trait keys unique"
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

    # --- the checks themselves -------------------------------------------
    # A check nobody has seen fail is not a check. Break each fault in memory and
    # confirm check() names it, then put the data back.
    assert not check(), "the real data must pass before faults are injected"

    def injected(fault, restore, needle):
        problems = check()
        restore()
        assert any(needle in p for p in problems), \
            "check() did not catch %s (said: %s)" % (fault, problems)

    # The tooltip text. Typing CA's wording from memory is exactly how "Raw
    # Materials efficiency" got declared for a string CA writes as "Raw Materials
    # output" - caught by check 15 on its first run, before it shipped.
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

    global TRAIT_ICON
    saved_icon = TRAIT_ICON
    TRAIT_ICON = "not_a_real_category"
    injected("a trait icon that is not a real trait_categories key",
             lambda: globals().__setitem__("TRAIT_ICON", saved_icon),
             "not a category vanilla uses")

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
