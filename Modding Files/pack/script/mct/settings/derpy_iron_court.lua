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
    .. "campaign starts, and are then fixed for the life of that save - change them "
    .. "from the main menu before starting a new one. The other switches can be "
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

local function is_mp()
    if not IN_CAMPAIGN then return false end
    local ok, v = pcall(function() return cm:is_multiplayer() end)
    return ok and v == true
end

m:add_new_section("preset", "Difficulty")
m:add_new_section("systems", "Systems")
m:add_new_section("numbers", "Custom numbers")
m:add_new_section("debug", "Debug")

-- ----------------------------------------------------------------- difficulty --
-- ONE DROPDOWN THAT OWNS THE NUMBERS. Pick anything but Custom and it sets all
-- fourteen and greys them. The switches are read on every difficulty.
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
    "Three rival parties. The Iron Court as designed.", true)
o_preset:add_dropdown_value("harsh", "Harsh",
    "Four rival parties. Parties start less loyal and leave sooner, a weak Crown "
    .. "loses its rivals sooner, influence comes more slowly and favours cost more.",
    false)
o_preset:add_dropdown_value("ruthless", "Ruthless",
    "Five rival parties, a full court. Every party is a threat. Loyalty falls "
    .. "fast, a party gives three turns of warning before it leaves, and every "
    .. "favour is dear.", false)
o_preset:add_dropdown_value("custom", "Custom",
    "Set every number under Custom numbers yourself.", false)
o_preset:set_default_value("default")

-- ------------------------------------------------------------------- systems --
-- key, label, section, tooltip, live. Every switch defaults to on. A LIVE one
-- can be flipped in a running campaign; the six are IC.LIVE_TUNE's.
local SWITCHES = {
    {"parties_act", "Rival parties act on their own", "systems",
     "Parties scheme, feud, make demands and offer deals without being asked. "
     .. "Off, they do none of this; overseers still gain experience and anything "
     .. "already under way still settles.", true},
    {"ai_courts", "Other Chaos Dwarf factions have courts", "systems",
     "Chaos Dwarf factions you do not play run courts of their own, and theirs "
     .. "can split. Off, only your court runs.", false},
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
     "Off, routine news - a seat standing empty, a party joining the court, a "
     .. "feud starting or ending, a party passed over for its own office - is "
     .. "written to the court's Log tab without an event message. Warnings, "
     .. "demands, offers and the results of your own moves always show one.", true},
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
    {"rivals_min", "Fewest rival parties", 3, 1, 5, 1,
     "The fewest rival parties a new court starts with. Set both to the same "
     .. "number for a court of exactly that size."},
    {"rivals_max", "Most rival parties", 3, 1, 5, 1,
     "The most rival parties a new court starts with. Five at most, which fills "
     .. "the court. Only four parties can rise under a banner of their own; one "
     .. "that leaves after that joins a rising already under way."},
    {"term_turns", "Office term, in turns", 10, 2, 20, 1,
     "How many turns an appointment runs. Dismissing a man before his term is up "
     .. "angers his party. When a term ends, the same man cannot take that office "
     .. "again for 3 turns, and his party is not rewarded when he does."},
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

-- -------------------------------------------------------------------- locking --
-- LAST: get_option_by_key answers nil for an option not yet registered, and the
-- loop below would then lock nothing. Every number belongs to the difficulty
-- unless it is Custom. In a campaign only the live switches stay open.
local CUSTOM_ONLY = "Set by the difficulty above. Choose Custom to edit it."

local function relock(custom)
    for i = 1, #NUMBERS do
        local o = m:get_option_by_key(NUMBERS[i][1])
        if o then
            if IN_CAMPAIGN then
                o:set_locked(true, LOCK_REASON)
            elseif not custom then
                o:set_locked(true, CUSTOM_ONLY)
            else
                o:set_locked(false)
            end
        end
    end
    if IN_CAMPAIGN then o_preset:set_locked(true, LOCK_REASON) end
    if not IN_CAMPAIGN then return end
    local mp = is_mp()
    for i = 1, #SWITCHES do
        local o = m:get_option_by_key(SWITCHES[i][1])
        if o then
            if mp then
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
    relock(opt:get_selected_setting() == "custom")
end)
core:add_listener("derpy_ic_mct_ready", "MctFinalized", true, function()
    relock(o_preset:get_finalized_setting() == "custom")
end, false)
-- MCT'S load_game PUTS BACK EVERY LOCK THE SAVE WAS WRITTEN WITH, after this
-- file has run - and every save before 2026-09-25 locked all seven switches.
core:add_listener("derpy_ic_mct_loaded", "MctInitialized", true, function()
    relock(o_preset:get_finalized_setting() == "custom")
end, true)
relock(o_preset:get_finalized_setting() == "custom")
