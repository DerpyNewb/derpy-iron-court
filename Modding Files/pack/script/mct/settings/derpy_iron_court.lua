-- MCT registration for The Iron Court.
--
-- MCT loads every .lua under script/mct/settings/, so this file runs only when
-- MCT is installed, and in MCT's own environment: it cannot see IC, and calls
-- nothing in the mod. The campaign reads these values once, at the first tick
-- of a new campaign (or the first load of a save from before this page
-- existed), and freezes them into the save - see IC.freeze_tune - except the
-- switches marked live below, which it reads again at every load and on every
-- Finalize (IC.refresh_live_tune). In multiplayer it does not read them at all.
--
-- EVERY KEY HERE IS REGISTERED TWICE MORE, in IC.TUNE and IC.TUNE_ORDER in
-- zzz_derpy_iron_court.lua. The court harness runs this file and refuses a key
-- missing from either, a default that disagrees, and a preset off its slider.

local mct = get_mct and get_mct()
if not mct then return end

local m = mct:register_mod("derpy_iron_court")
m:set_title("The Iron Court")
m:set_author("derpy")
m:set_description("Parties vie for the offices of your court. The difficulty, the "
    .. "numbers and whether other factions have courts are read once, when a "
    .. "campaign starts, and are then fixed for the life of that save. Change them "
    .. "from the main menu before starting a new campaign. The other switches can be "
    .. "changed at any time. None of it is used in multiplayer, where every player "
    .. "gets the defaults.")

-- MCT HAS NO CAMPAIGN GATING OF ITS OWN: set_context_specific is an empty
-- function. The copy frozen into the save is the real defence; the lock is the
-- notice.
local IN_CAMPAIGN = __game_mode == __lib_type_campaign
local LOCK_REASON = "Fixed for the life of a campaign. Change it from the main "
    .. "menu before starting a new one."
local MP_REASON = "Not used in multiplayer, where every player gets the defaults."
local LIVE_NOTE = " You can change this during a campaign."

-- MULTIPLAYER IS MCT'S ANSWER, NEVER THE GAME'S. This file runs, and its
-- MctInitialized listener fires, while the campaign is still loading, before
-- the model exists. Asking cm:is_multiplayer() there crashed the game on every
-- new campaign (build 226121E7, 2026-09-25) - a null read inside the engine,
-- which no pcall catches. MCT works the answer out itself before the load and
-- hands it over on MctInitialized; until then this reads single player.
local in_mp = false

m:add_new_section("preset", "Difficulty")
m:add_new_section("systems", "Systems")
m:add_new_section("numbers", "Custom numbers")
m:add_new_section("debug", "Debug")

-- ----------------------------------------------------------------- difficulty --
-- ONE DROPDOWN THAT OWNS THE NUMBERS. Pick anything but Custom and it decides
-- all fourteen and greys them; each greyed slider's reason names its number,
-- since MCT cannot write one into a locked slider. The switches are read on
-- every difficulty.
local o_preset = m:add_new_option("preset", "dropdown")
o_preset:set_text("Difficulty")
o_preset:set_tooltip_text("How many rival parties your court starts with, how loyal "
    .. "they are and how quickly they turn. Choose Custom to set each number "
    .. "yourself. The switches under Systems are yours on every difficulty.")
o_preset:set_assigned_section("preset")
o_preset:add_dropdown_value("gentle", "Gentle",
    "One rival party. Parties start more loyal, cool more slowly and give longer "
    .. "warning before they leave. Gifts cost less, and influence comes faster.", false)
o_preset:add_dropdown_value("default", "Default",
    "Two rival parties. The Iron Court as designed.", true)
o_preset:add_dropdown_value("harsh", "Harsh",
    "Three rival parties. Parties start less loyal and leave sooner, a weak Crown "
    .. "loses its rivals sooner, influence comes more slowly and favours cost more.",
    false)
o_preset:add_dropdown_value("ruthless", "Political Chaos",
    "Five rival parties, a full court. Every party is a threat. Loyalty falls "
    .. "fast, a party gives three turns of warning before it leaves, and every "
    .. "favour is dear.", false)
o_preset:add_dropdown_value("custom", "Custom",
    "Set every number under Custom numbers yourself.", false)
o_preset:set_default_value("default")

-- ------------------------------------------------------------------- systems --
-- key, label, section, tooltip, live. Every switch defaults to on. A LIVE one
-- can be flipped in a running campaign; the eight are IC.LIVE_TUNE's.
local SWITCHES = {
    {"parties_act", "Rival parties act on their own", "systems",
     "Parties scheme, feud, make demands and offer deals without being asked. "
     .. "Off, they do none of this; overseers still gain experience and anything "
     .. "already under way still settles.", true},
    {"ai_courts", "Other Chaos Dwarf and Dwarf factions have courts", "systems",
     "Chaos Dwarf and Dwarf factions you do not play run courts of their own, and "
     .. "theirs can split. Off, only your court runs.", false},
    {"secession", "Parties can secede", "systems",
     "A powerful, angry party counts down and then leaves, taking provinces with "
     .. "it. Off, no party ever leaves, and a countdown already running stops.", true},
    {"pressure", "A weak Crown pushes rivals out", "systems",
     "When your own party's share of the court falls too low, the biggest rival "
     .. "party is pushed to leave. Off, it never is.", true},
    {"crown_split", "Your own party can split", "systems",
     "A Crown whose loyalty runs out splits into a new party. Off, it never does, "
     .. "and a countdown already running stops.", true},
    {"all_cards", "Show routine event messages", "systems",
     "When off, routine news (empty seats, parties joining, feuds starting or "
     .. "ending, a party passed over for its own office) goes only to the court's "
     .. "Record tab. Warnings, demands, offers and the results of your own moves "
     .. "always show an event message.", true},
    {"governments", "Governments", "systems",
     "Each court has a government that changes one of its rules. Off, no court has "
     .. "one, and no government's effects apply.", true},
    {"gov_drift", "Governments change with the court", "systems",
     "A party that leads the court for long enough asks for its own government. "
     .. "Off, your government changes only when you change it.", true},
    {"deeds", "Your deeds move the court", "systems",
     "Victories, the Hell-Forge, the Tower's rites, slaves, convoys and research "
     .. "give the matching party renown, which counts toward its share and fades "
     .. "each turn. A party not in your court that earns enough sends the next lord "
     .. "you recruit. Off, nothing new is earned and nobody is drawn in; renown "
     .. "already earned fades away.", true},
    {"laws", "Laws", "systems",
     "Your court passes laws by a vote of its men: four kinds, five laws each. "
     .. "You and the parties propose them, and you can push, win men or overrule. "
     .. "Off, no law applies and open votes end; the laws in force come back when "
     .. "you turn it on.", true},
    {"dwarf_courts", "Dwarf courts", "systems",
     "Dwarf factions run courts of their own: Dwarf parties, offices, governments "
     .. "and laws. Off, no Dwarf faction has a court, and one already running is "
     .. "taken off the map at its next turn.", true},
    {"detailed_log", "Detailed log", "debug",
     "Writes the court's routine events to script_log.txt. Failures are always "
     .. "written.", true},
}

for i = 1, #SWITCHES do
    local key, label, section, tip, live = unpack(SWITCHES[i])
    local o = m:add_new_option(key, "checkbox")
    o:set_text(label)
    o:set_tooltip_text(live and tip .. LIVE_NOTE or tip)
    o:set_default_value(true)
    o:set_assigned_section(section)
end

-- ------------------------------------------------------------------- numbers --
-- key, label, default, min, max, step, tooltip. The defaults are IC.TUNE's.
local NUMBERS = {
    {"loyalty_start", "Starting loyalty", 55, 30, 80, 1,
     "The loyalty a party has when it first takes its place at court."},
    {"loyalty_drift_none", "Loyalty change each turn for a party with no office",
     -1, -5, 0, 1,
     "What a party that holds no office loses every turn."},
    {"secede_loyalty", "Loyalty at which a party threatens to leave", 20, 0, 40, 1,
     "A party big enough to leave starts counting down at or below this loyalty."},
    {"secede_share", "Share of the court a party needs to leave", 25, 5, 50, 1,
     "The share of the court, in percent, a party must hold before it can leave."},
    {"secede_turns", "Turns of warning before a party leaves", 5, 1, 10, 1,
     "How many turns the countdown runs."},
    {"pressure_below", "Crown share below which rivals are pushed out", 10, 0, 30, 1,
     "When your own party's share of the court falls below this, the biggest "
     .. "rival party can be pushed to leave."},
    {"influence_trickle", "Influence a man earns each turn", 5, 0, 20, 1,
     "The influence a man earns every turn while he is not leading an army."},
    {"settlement_influence", "Influence for taking a settlement", 24, 0, 60, 1,
     "The influence a lord earns for taking a settlement."},
    {"favour_gift_cost", "Price of Send a Gift", 600, 100, 3000, 50,
     "Gold for one gift to a party."},
    {"favour_secure_cost", "Price of Secure Loyalty", 2500, 500, 10000, 100,
     "Gold to hold a party back from leaving for a few turns."},
    {"party_intrigue_line", "Loyalty at which parties start scheming", 55, 20, 80, 1,
     "A party at or below this loyalty spreads rumours about your men and "
     .. "discredits them."},
    {"rivals_min", "Fewest rival parties", 2, 1, 5, 1,
     "The fewest rival parties a new court starts with. Set both to the same "
     .. "number for a court of exactly that size."},
    {"rivals_max", "Most rival parties", 2, 1, 5, 1,
     "The most rival parties a new court starts with. Five at most, which fills "
     .. "the court. Only four parties can rise under a banner of their own; one "
     .. "that leaves after that rises under a fallen house, or joins a rising "
     .. "already under way if every house still stands."},
    {"term_turns", "Office term, in turns", 10, 2, 20, 1,
     "How many turns an appointment runs. Dismissing a man before his term is up "
     .. "angers his party. When a term ends, the same man cannot take that office "
     .. "again for 3 turns, and his party is not rewarded when he does."},
    {"gov_levels_per_weight", "Settlement levels per point of governor weight", 2, 1, 5, 1,
     "A governor's party gains one point of weight per this many settlement "
     .. "levels in his province, rounded up. Every governor is worth at least one."},
    {"gov_pressure_line", "Turns before a leading party asks for its government", 6, 2, 12, 1,
     "How many turns a rival party must lead the court before it asks for its own "
     .. "government."},
    {"gov_hold_cost", "Influence to keep your government", 300, 100, 1000, 50,
     "What refusing a party's government costs the first time. Each refusal after "
     .. "that costs this much more."},
    {"gov_force_cost", "Influence to change your government", 400, 100, 1500, 50,
     "What changing your government by your own choice costs."},
}

for i = 1, #NUMBERS do
    local key, label, def, lo, hi, step, tip = unpack(NUMBERS[i])
    local o = m:add_new_option(key, "slider")
    o:set_text(label)
    o:set_tooltip_text(tip)
    o:slider_set_min_max(lo, hi)
    o:slider_set_step_size(step)
    o:set_default_value(def)
    o:set_assigned_section("numbers")
end

-- WHAT EACH DIFFICULTY SETS, said on the greyed slider (audit 2026-09-29).
-- MCT will not write a value into a locked option, so the slider goes on
-- showing its own number and the lock's reason carries the difficulty's. A copy
-- of IC.PRESETS, which this file cannot see from the main menu; the court
-- harness holds the two together. Default is each slider's own default.
local PRESET_VALUES = {
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
        secede_share = 15, secede_turns = 3, pressure_below = 15,
        influence_trickle = 3, settlement_influence = 16,
        favour_gift_cost = 1000, favour_secure_cost = 4000,
        party_intrigue_line = 65, rivals_min = 5, rivals_max = 5, term_turns = 10,
        gov_levels_per_weight = 2,
        gov_pressure_line = 4, gov_hold_cost = 500, gov_force_cost = 600,
    },
}

-- -------------------------------------------------------------------- locking --
-- LAST: get_option_by_key answers nil for an option not yet registered, and the
-- loop below would then lock nothing. Every number belongs to the difficulty
-- unless it is Custom. In a campaign only the live switches stay open.
local function relock(preset)
    local custom = preset == "custom"
    for i = 1, #NUMBERS do
        local o = m:get_option_by_key(NUMBERS[i][1])
        if o then
            if IN_CAMPAIGN then
                o:set_locked(true, LOCK_REASON)
            elseif not custom then
                local set = PRESET_VALUES[preset] or {}
                local v = set[NUMBERS[i][1]]
                if v == nil then v = NUMBERS[i][3] end
                o:set_locked(true, string.format("The difficulty above sets this to "
                    .. "%s. Choose Custom to edit it.", tostring(v)))
            else
                o:set_locked(false)
            end
        end
    end
    if IN_CAMPAIGN then o_preset:set_locked(true, LOCK_REASON) end
    if not IN_CAMPAIGN then return end
    for i = 1, #SWITCHES do
        local o = m:get_option_by_key(SWITCHES[i][1])
        if o then
            if in_mp then
                o:set_locked(true, MP_REASON)
            elseif SWITCHES[i][5] then
                o:set_locked(false)
            else
                o:set_locked(true, LOCK_REASON)
            end
        end
    end
end

-- The callback fires BEFORE the value is finalized, so it reads the selected one.
o_preset:add_option_set_callback(function(opt)
    if IN_CAMPAIGN then return end
    relock(opt:get_selected_setting())
end)
core:add_listener("derpy_ic_mct_ready", "MctFinalized", true, function()
    relock(o_preset:get_finalized_setting())
end, false)
-- MCT'S load_game PUTS BACK EVERY LOCK THE SAVE WAS WRITTEN WITH, after this
-- file has run - and every save before 2026-09-25 locked all seven switches.
core:add_listener("derpy_ic_mct_loaded", "MctInitialized", true, function(context)
    in_mp = type(context.is_multiplayer) == "function" and context:is_multiplayer() == true
    relock(o_preset:get_finalized_setting())
end, true)
relock(o_preset:get_finalized_setting())
