# -*- coding: utf-8 -*-
"""Break the Iron Court's rules one at a time and prove the harness notices.

WHY THIS EXISTS. tools/_iron_court_harness.lua is the only tool in this workspace
with no --selftest of its own, and it is the one that decides whether the model
and the panel are correct. A green harness is worth exactly as much as its
weakest check, and a check nobody has watched fail proves nothing at all: an
assertion quietly becomes unbreakable when the code it was aimed at moves out
from under it.

WHAT A MUTANT IS. Not a typo - the compiler finds those. Each entry below is a
plausible IMPLEMENTATION mistake: the guard somebody forgets, the sweep somebody
narrows, the clamp somebody thinks is redundant, the early return somebody
deletes while tidying. If the harness is green with one of them applied, the
harness is not testing that rule, whatever its check name says.

HOW IT RUNS. The mutation is written into the SHIPPED Lua, the harness is run
against it, and the file is restored in a finally - so an interrupt mid-run
leaves the tree clean. The harness is run green before and after, and the run
refuses to report anything if either of those fails.

AN ANCHOR THAT NO LONGER MATCHES IS A FINDING, not a maintenance chore to be
silently skipped: it means the code this mutant was aimed at has moved, and
nobody has checked whether the check aimed at it moved too. It is reported
exactly like a survivor.

    py tools/mutate_iron_court.py            # every mutant
    py tools/mutate_iron_court.py oath purge # only mutants whose name matches
    py tools/mutate_iron_court.py --selftest

Exit 1 on a survivor, a stale anchor, or a harness that was not green to start.
"""
import io
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOD = os.path.join(ROOT, "Modding Files", "pack", "script", "campaign", "mod")
M = os.path.join(MOD, "zzz_derpy_iron_court.lua")
U = os.path.join(MOD, "zzz_derpy_iron_court_ui.lua")
UM = os.path.join(MOD, "zzz_derpy_iron_court_ui_map.lua")
P = os.path.join(MOD, "zzz_derpy_iron_court_parties.lua")
D = os.path.join(MOD, "zzz_derpy_iron_court_dwarf.lua")
S = os.path.join(ROOT, "Modding Files", "pack", "script", "mct", "settings",
                 "derpy_iron_court.lua")
HARNESS = os.path.join(ROOT, "tools", "_iron_court_harness.lua")
LUA = r"C:\Program Files (x86)\Lua\5.1\lua.exe"

# (what it breaks, which file, the code as it ships, what a mistake would leave)
#
# Grouped by the rule each one attacks, not by the check meant to catch it: the
# whole point is that this file does not know which check is watching.
#
# Anchor on CODE lines, never a comment line: a comment pass on the Lua stales
# an anchor whose code has not moved at all.
# THE CONTRACT'S SIGNATURES (docs/superpowers/plans/2026-10-04-iron-court-dwarfs-CONTRACT.md).
# The "both races" mutants anchor on these and not on lines inside them: the
# bodies change, the contract fixes the names. Each renames the real function
# to a body and wraps it, which is how a mistake AROUND a function (a cache
# keyed by nothing, the wrong faction, a guard nobody runs) is written without
# knowing what the function says inside.
_SIG_R = "function IC.R(faction_key)\n"
_SIG_KEY = "function IC.key(kind, slug, faction_key)\n"
_SIG_HAS = "function IC.has_court(faction)\n"
_SIG_GRUDGES = "function IC.grudges(faction_key, slug)\n"
_SIG_WRITE = "function IC.grudge_write(faction_key, slug, code)\n"
_SIG_TURN = "function IC.turn(faction_key)\n"


def _holder(sig):
    """The one court Lua file that defines `sig`. None or two: M, and the run then
    reports a stale anchor, which is a finding."""
    hits = [p for p in (M, D, P, U) if os.path.isfile(p)
            and io.open(p, encoding="utf-8").read().count(sig) == 1]
    return hits[0] if len(hits) == 1 else M


def _as_dwarf(call):
    """Lua that runs `call` with every race accessor answering Dwarf - the race guard
    forgotten, wherever inside it sat - and puts them back before any error is
    re-raised. Leaves the first result in `out`."""
    return ("    local keep = {IC.race_key, IC.R, IC.race_of, IC.is_chd}\n"
            "    IC.race_key = function() return \"dwf\" end\n"
            "    IC.R = function() return IC.RACES.dwf end\n"
            "    IC.race_of = function() return IC.RACES.dwf end\n"
            "    IC.is_chd = function() return false end\n"
            "    local ok, out = pcall(%s)\n"
            "    IC.race_key, IC.R, IC.race_of, IC.is_chd = keep[1], keep[2], keep[3], keep[4]\n"
            "    if not ok then error(out, 0) end\n" % call)

MUTANTS = [
    # What your house can break into.
    # THE ROLL BACK OVER EVERY UNSEATED INTEREST. A man joins a party when his
    # background maps to it, so an interest nobody in the faction has the
    # background for is seated with weight, a name, traits, a card - and nobody
    # in it, under a card saying the men who will not answer to you any more
    # have organised as an interest of their own. Invisible from inside
    # IC.splinter, which never looks at a character.
    ("a house splitting into an interest nobody belongs to", M,
     """        if slug ~= IC.CROWN and not court.houses[slug] and backed[slug] then""",
     """        if slug ~= IC.CROWN and not court.houses[slug] then"""),

    # AND THE LEGEND COUNTED. house_of_character answers the Crown for a legend
    # first and whatever else is true of him, so his background can never move
    # him - counting it makes his interest eligible and then he does not join
    # it, which is the empty party again by a longer route.
    ("a legend's background making an interest eligible", M,
     """            if man and not man:is_null_interface() and not IC.is_legend(man)
                    and not IC.is_ruler(man, faction_key) then""",
     """            if man and not man:is_null_interface()
                    and not IC.is_ruler(man, faction_key) then"""),

    # AND THE RULER'S, who sits with the Crown whatever his background.
    ("the ruler's background making an interest eligible", M,
     """            if man and not man:is_null_interface() and not IC.is_legend(man)
                    and not IC.is_ruler(man, faction_key) then""",
     """            if man and not man:is_null_interface() and not IC.is_legend(man) then"""),

    # What a secession would cost.
    # THE PANEL DOING ITS OWN ARITHMETIC. "How many provinces would go" looks
    # like it should be the party's share of the court, and it is not -
    # defecting_provinces floors it at what the party already governs and at
    # what has rotted past prov_defect_floor. A tooltip that recomputes it is a
    # second owner of the rule, and the two agree until the day they do not.
    ("a tooltip counting provinces for itself", U,
     """        "If this party walks out it takes %d of your %d provinces: %s%s.",
        #doomed, #seats, table.concat(names, ", "), more)""",
     """        "If this party walks out it takes %d of your %d provinces: %s%s.",
        math.ceil(#seats * (IC.share(faction, slug) or 0) / 100), #seats,
        table.concat(names, ", "), more)"""),

    # THE KEY ON SCREEN. province_name() is documented as returning a key, so
    # skipping the lookup puts "wh3_main_combi_province_gash_kadrak" in front
    # of the player.
    ("a province at risk printed as its key", U,
     """        names[i] = loc("provinces_onscreen_" .. doomed[i], doomed[i])""",
     """        names[i] = doomed[i]"""),

    # THE CROWN HANDED THE RIVAL SENTENCE. IC.splinter moves weight and men and
    # never touches a province, so this tells the player his own house is about
    # to take land off him - a threat the model does not make and he cannot act
    # on.
    ("the player's own card threatening him with his own provinces", U,
     """    if slug == IC.CROWN then
        -- YOUR OWN HOUSE TAKES NO LAND.""",
     """    if false then
        -- YOUR OWN HOUSE TAKES NO LAND."""),

    # THE CAP TRIMMING THE WRONG END. defecting_provinces returns its answer in
    # the order the land is actually taken, so keeping the tail names the
    # provinces least likely to go and drops the ones already lost. Identical
    # in every fixture with fewer provinces than the cap.
    ("a long list of doomed provinces cut at the front", U,
     """    for i = 1, math.min(#doomed, ICUI.TIP_PROVINCES) do
        names[i] = loc("provinces_onscreen_" .. doomed[i], doomed[i])
    end""",
     """    local first = math.max(1, #doomed - ICUI.TIP_PROVINCES + 1)
    for i = first, #doomed do
        names[#names + 1] = loc("provinces_onscreen_" .. doomed[i], doomed[i])
    end"""),

    # The record's two halves.
    # A kind missing from the whitelist. IC.log drops a kind that is not in this
    # table at its first line, so the model writes the entry, the whitelist eats
    # it, and the sentence waiting in the panel can never draw.
    ("the record's whitelist missing a kind the court writes", M,
     """    pressed = true, dissolve = true,""",
     """"""),

    # AND THE OTHER SIDE OF IT. A kind the whitelist accepts and the renderer
    # has no branch for returns nil, and the row is skipped - the entry is in
    # the save, counts against the forty-line ring buffer, and shows nothing.
    ("a kind written to the record with no sentence to draw it", U,
     """    elseif e.kind == "pressed" then""",
     """    elseif e.kind == "pressed_not" then"""),

    # The last warning, on both things that end a house.
    # THE CARD NOBODY RAISES. secede_warn fires at the top of a five-turn clock
    # and this is the only other thing said before a province changes hands;
    # without it the player has four silent turns and then a secession. The
    # clock still runs correctly, which is why nothing else notices.
    ("a secession that goes quiet after its first warning", M,
     """                elseif house.clock == math.min(IC.TUNE.warn_turns,""",
     """                elseif false and math.min(IC.TUNE.warn_turns,"""),

    # THE TEST THAT READS BETTER AND IS WRONG. "<=" is the natural way to write
    # "inside the last three turns" and it is true on every turn beneath the
    # line, so one secession cards the player warn_turns times. The first card
    # still lands at exactly the right distance, so a check that only measures
    # the warning's timing passes this happily.
    ("a last warning repeated every turn to the door", M,
     """                elseif house.clock == math.min(IC.TUNE.warn_turns,""",
     """                elseif house.clock <= math.min(IC.TUNE.warn_turns,"""),

    # AND A TURN OUT. Off-by-one against a tuning value is the classic form of
    # this bug and it is invisible without counting to the event itself: the
    # card still arrives, still once, still near the end.
    ("a last warning a turn later than it promises", M,
     """                elseif house.clock == math.min(IC.TUNE.warn_turns,""",
     """                elseif house.clock == -1 + math.min(IC.TUNE.warn_turns,"""),

    # THE SECOND CALL SITE. Provoke sets the clock outright rather than going
    # through the branch above, so it skips secede_warn AND the crossing. Without
    # this, the one move meant to shorten a countdown puts a house on one in
    # silence, while every ordinary secession still warns correctly.
    ("provoke putting a house on a silent clock", M,
     """                if house.clock <= IC.TUNE.warn_turns
                   and (now <= 0 or now > IC.TUNE.warn_turns) then
                    IC.feed(faction_key, "secede_soon")
                end""",
     """"""),

    # THE CLOCK TREATED AS COSMETIC. Raise the warning and then split anyway in
    # the same call, which looks right in the log because both the warning and
    # the split are recorded.
    ("a split warning that lands with the split itself", M,
     """    if (crown.split or 0) <= 0 then
        crown.split = IC.TUNE.warn_turns
        IC.feed(faction_key, "splinter_warn")
        IC.save(faction_key)
        return nil
    end""",
     """    if (crown.split or 0) <= 0 then
        crown.split = IC.TUNE.warn_turns
        IC.feed(faction_key, "splinter_warn")
    end"""),

    # AND THE SAME COUNT, TOO LONG. The warning arrives, once, and the split
    # arrives - just not when the player was told. Only a check that counts to
    # the event can see it.
    ("a split count longer than the notice it gave", M,
     """        crown.split = IC.TUNE.warn_turns
        IC.feed(faction_key, "splinter_warn")""",
     """        crown.split = IC.TUNE.warn_turns + 2
        IC.feed(faction_key, "splinter_warn")"""),

    # THE COUNT THAT PAUSES INSTEAD OF CANCELLING. A player who buys his own
    # house back above the line stops the split today and is split anyway the
    # moment it dips again, from wherever the count had got to - with no second
    # warning, because the count never restarted. The secession clock cancels,
    # so this is the court answering one question two ways.
    ("a split count that pauses rather than cancelling", M,
     """            crown.split = 0
""",
     """"""),

    # The save string.
    # string.find(packed, "%|", from) works in Lua 5.1.5 and finds nothing in
    # WH3, which loses every section after the houses on load. The harness runs
    # stock Lua and cannot see that; check_lua_api.py refuses the init argument.
    # What the harness CAN see is the other half of the same contract: a walk
    # that eats empty fields shifts every section after the first gap.
    ("the save walk back on the field-eating form of gmatch", M,
     """    for field in string.gmatch(packed .. "|", "([^|]*)|") do""",
     """    for field in string.gmatch(packed, "([^|]+)") do"""),

    # What a move says it does.
    # THE ODDS PUT BACK ON THE CARD. The picker already draws them on each
    # candidate's button, LIVE - base plus the actor's standing edge - so a card
    # can only ever carry the base and the two disagree for every aimed move.
    # The player is never shown both at once, which is why this is invisible in
    # a screenshot and needs a check.
    ("a move card quoting odds the picker already shows live", M,
     """         "He dies. -%d loyalty from his party.",
         IC.TUNE.plot_murder_loyalty - IC.TUNE.loyalty_member_died)""",
     """         "%d%% odds. He dies. -%d loyalty from his party.",
         IC.TUNE.plot_chance_murder, IC.TUNE.plot_murder_loyalty - IC.TUNE.loyalty_member_died)"""),

    # Feedback for a click the player made.
    # A PULSE NOTHING TURNS OFF. pulse_uicomponent has no duration: it runs until
    # something stops it, so dropping the callback leaves every seat the player
    # has ever appointed to flashing for the rest of the campaign. It looks
    # correct on the first click, which is the only one anybody tests by hand.
    ("a confirmation pulse that never stops", U,
     """        if again then
            pcall(function() pulse_uicomponent(again, false, 0, false) end)
        end""",
     """"""),
    # THE STOP THROUGH THE OLD HANDLE. The court can shut inside
    # those seconds, and a destroyed component's handle is not an error a
    # pcall catches.
    ("the pulse stopped through a handle its court may have destroyed", U,
     """        if again then
            pcall(function() pulse_uicomponent(again, false, 0, false) end)
        end""",
     """        pcall(function() pulse_uicomponent(c, false, 0, false) end)"""),

    # ONE SOUND FOR BOTH OUTCOMES, which is a sound that says nothing. Sacking a
    # man and seating one are opposite acts and the confirmation is the only
    # thing that distinguishes them at the moment of the click.
    ("the same sound for seating a man and sacking one", U,
     """ICUI.SOUND_BAD = "UI_CAM_POPUP_Message_Event_Negative\"""",
     """ICUI.SOUND_BAD = "UI_CAM_POPUP_Message_Event_Positive\""""),

    # The event feed.
    # THE VACANCY THAT TELLS NOBODY. A term running out is the one way a seat
    # empties with no input from the player, which is exactly why it is the one
    # that has to reach him. Removing the call leaves the record line in place,
    # so the panel still knows and only the player does not.
    ("a term running out that reaches the record but not the player", M,
     """    if #done > 0 then
        IC.feed(faction_key, "office_lost",
                #done == 1 and IC.office_title_key(done[1].slug, faction_key) or nil)
    end""",
     """    if #done > 0 then
    end"""),

    # EVERY COURT ON THE MAP TALKING. The model runs for all fourteen Chaos
    # Dwarf factions; without the guard the player is shown a card for every
    # appointment, dismissal and expired term in every AI court in the campaign.
    ("the event feed without its human guard", M,
     """    if not IC.is_human(faction_key) then return false end""",
     """    if false then return false end"""),

    # THE GARRISON TAKEN FOR AN ARMY: every garrison commander back at 0 a turn.
    ("a garrison commander paid a field general's trickle", M,
     "    if IC.is_colonel(character) then return IC.tune(faction_key, \"influence_trickle\") end",
     ""),

    # AN OLD SAVE'S INDEX READ STRAIGHT: the head list got shorter, so a party
    # rolled in an older save names nothing, or errors.
    ("an old save's name index read without wrapping", M,
     '    return R.NAME_HEADS[(head - 1) % #R.NAME_HEADS + 1] .. " of "',
     '    return R.NAME_HEADS[head] .. " of "'),

    ("an event card with the empty plate back under its sentence", M,
     '    local primary, secondary = stem .. "_primary", stem .. "_secondary"',
     '    local primary, secondary = stem .. "_primary", ""'),
    # THE SLOTS THE CALLER'S KEY TAKES. A seat's name or a move's result is the
    # subtitle and a deed's sentence is the body; one rule for both is either
    # a seat's name in the body's box or a paragraph in the subtitle's font.
    ("an event card with a seat's name in the body's box", M,
     "    if line and ev[3] then secondary = line elseif line then primary = line end",
     "    if line then secondary = line end"),
    ("an event card with a deed's sentence as its subtitle", M,
     "    if line and ev[3] then secondary = line elseif line then primary = line end",
     "    if line then primary = line end"),

    # THE CALL SITE GIVING UP ON THE MOVE. IC.feed still raises the card
    # and the plate is still filled - by the generic SUCCESS line - so
    # nothing is blank, nothing errors, and the only thing lost is which of
    # sixteen moves the player just paid for. A screenshot cannot tell the
    # two apart, which is the whole reason this one is written down.
    ("a plot card that stops naming the move it reports", M,
     '    IC.feed(faction_key, "plot_ok", IC.move_result_key(plot_key, true, faction_key))',
     '    IC.feed(faction_key, "plot_ok")'),

    # THE FOURTEENTH FIELD, DROPPED. house.snubbed is what drift_loyalty's
    # transition gate compares against. Unpacked, IC.load builds a fresh court
    # every turn, the comparison runs against nil, and a grievance that has not
    # changed is written to the record as though it had just started.
    # THE COUNT LEFT OUT OF THE SAVE. IC.turn opens with IC.load, so a field that
    # does not round-trip is reset on every single turn - the player gets his
    # warning, the count restarts from the top each turn and the split he was
    # promised never arrives. It looks correct in one session of a live game and
    # correct in every check that does not reload.
# THE CROWN'S CARD BACK TO A WORD WITHOUT A NUMBER. A rival on the way out
# reads "SECEDES 3"; a bare "SPLINTERING" on the Crown states the same
# situation with the number missing from the card the player is standing in.
# Looks correct in a screenshot.
    ("the Crown's split count taken off its own card", U,
     """            if (house.split or 0) > 0 then
                return string.format("SPLITS %d", house.split)
            end""",
     """"""),

    ("the split's count left out of the save", M,
     """            h.split or 0,
            h.stored""",
     """            0,
            h.stored"""),

    ("the snub flag left out of the save again", M,
     """            h.snubbed and 1 or 0,""",
     """            0,"""),

    # AN ABSENT FIELD IS "-", NEVER "": split() drops an empty piece, so a record
    # entry aimed at nobody comes back four fields long and is thrown away on the
    # next load.
    ("a record entry with no target written as an empty field again", M,
     """            e.turn or 0, e.kind or "-", e.slug or "-", e.key or "-",""",
     """            e.turn or 0, e.kind or "-", e.slug or "-", e.key or "","""),

    # A CONFEDERATION'S POLL BRANDING THE WHOLE LIST. stamp_origin refuses a man
    # who already has one, so this only ever catches lords recruited since the
    # last turn start, which makes it look intermittent rather than like a rule.
    ("a confederation branding every unstamped man in the faction", M,
     """        if man and not man:is_null_interface()
           and not before[man:command_queue_index()] then""",
     """        if man and not man:is_null_interface() then"""),

    # The clocks, the witnesses and the sweeps.
    ("provoke lengthens a clock it should only shorten", M,
     """               and (now <= 0 or now > count) then""",
     """               and true then"""),

    ("a purge charges the Crown as a witness to itself", M,
     """            if slug2 ~= IC.CROWN then
                IC.move_loyalty(faction_key, slug2,
                                -IC.TUNE.plot_purge_witness)
            end""",
     """            IC.move_loyalty(faction_key, slug2, -IC.TUNE.plot_purge_witness)"""),

    ("the Crown pays for its own embezzlement", M,
     """        if slug ~= IC.CROWN then
            IC.move_loyalty(faction_key, slug, delta)
            moved = moved + 1
        end""",
     """        IC.move_loyalty(faction_key, slug, delta)
        moved = moved + 1"""),

    # Only a lord speaks, and only a lord leaves.

    # THE LORDS-ONLY FILTER DROPPED. The man who speaks for a party leads its
    # rebellion, so a party whose best-standing member is a Daemonsmith secedes
    # under a general the ENGINE invents (an orc shaman).
    ("a party spoken for by a hero who cannot lead an army", M,
     """            if IC.is_lordly(man) then""",
     """            if true then"""),

    # THE PAIR COLLAPSED TO ITS FIRST HALF. kind_of_character splits a lord by
    # whether he has a force TODAY, so this looks like the tighter rule and it
    # quietly disqualifies every lord between armies - a party whose men are all
    # unattached has nobody to speak for it and secedes leaderless.
    ("a lord between armies who no longer counts as a lord", M,
     '''    return kind == "general" or kind == "lord"''',
     '''    return kind == "general"'''),

    # THE CAP SET TO ONE. "The faction leader will be leading a rebel army" reads
    # like the leader and nobody else, and this is what that costs: the party's
    # other lords carry on serving the man they just rebelled against.
    ("a secession the party's other lords sit out", M,
     """    local leaving = math.min(#defectors, want_lords, IC.TUNE.rebel_lords_max)""",
     """    local leaving = math.min(#lords, 1)"""),

    # THE CAP TAKEN OFF. The honest rule with no brake on it: a party of nine
    # lords puts nine full stacks on the map in a single turn, which is not a
    # political crisis, it is a loss screen.
    ("a secession that ends the campaign in one turn", M,
     """    local leaving = math.min(#defectors, want_lords, IC.TUNE.rebel_lords_max)""",
     """    local leaving = #lords"""),

    # THE SCALE THROWN AWAY, so every party sends the same number whatever it
    # was: a two-man splinter and a faction-within-the-faction eight strong put
    # identical armies on the map.
    ("a two-man splinter that rebels as hard as a faction-within-a-faction", M,
     """    local leaving = math.min(#defectors, want_lords, IC.TUNE.rebel_lords_max)""",
     """    local leaving = math.min(#lords, IC.TUNE.rebel_lords_max)"""),

    # THE HEROES TAKEN BACK OUT OF THE COUNT. They cannot lead an army, so
    # counting only the men who can looks like the tighter rule, and it drops the
    # heroes the count includes on purpose. A party with a long tail of
    # hangers-on is a bigger thing to lose than its lords alone.
    ("a party sized by its lords when the author asked for its members", M,
     """            members = members + 1
            if IC.can_defect_hero(man) then""",
     """            if IC.can_defect_hero(man) then"""),
    # AND AGAIN WITH THE COUNTER PUT BACK, one line lower, where only the lords
    # reach it. The mutant above deletes the count; this one MOVES it, which is
    # the mistake somebody actually makes.
    ("a party sized by its lords with the count merely moved", M,
     """            if IC.is_lordly(man) then
                local cqi = man:command_queue_index()""",
     """            if IC.is_lordly(man) then
                members = members + 1
                local cqi = man:command_queue_index()"""),

    # ROUNDED DOWN. floor is the more natural-looking of the two beside a
    # division and it quietly costs every party a lord: at rebel_lords_per = 3 a
    # party of five sends one instead of two, and only the explicit clamp below
    # keeps a party of two sending anything at all.
    ("a split rounded in the player's favour every time", M,
     """    local want_lords = math.ceil(members / IC.TUNE.rebel_lords_per)""",
     """    local want_lords = math.floor(members / IC.TUNE.rebel_lords_per)"""),

    # A PARTY WITH NO LORDS THAT GOES QUIETLY. `math.max(leaving, 1)` reads as
    # belt and braces beside a loop bound that is already a count. Without it a
    # party of nothing but agents walks out and the map does not move. It has
    # nobody who can lead an army; it is still a party that has left, and the
    # Castellan fallback is there for exactly this.
    ("a party of agents that secedes without a shot", M,
     """    for i = 1, math.max(leaving, 1) do""",
     """    for i = 1, leaving do"""),

    # THE PARTY'S OWN LORD COUNT DROPPED FROM THE CLAMP. The scale reads the
    # size off every member, heroes included, so without this a party of one lord
    # and a crowd of hangers-on asks for more armies than it has men to lead
    # them - and lords[2] is nil, so the extra rising gets the fallback general.
    # That is the orc shaman arriving by a different road.
    ("a party fielding more lords than it has", M,
     """    local leaving = math.min(#defectors, want_lords, IC.TUNE.rebel_lords_max)""",
     """    local leaving = math.min(want_lords, IC.TUNE.rebel_lords_max)"""),

    # THE SUBTYPE HALF OF THE LEGEND TEST DROPPED, leaving is_unique on its own.
    # A live campaign answers is_unique = false for derpy_bzaark, so every rule
    # built on it goes quiet: he sits in a rival party, the secession kills him,
    # and the game crashes.
    ("a legend the engine does not flag, and nothing notices", M,
     """    if IC.is_unique(character) then return true end
    local key = nil
    pcall(function() key = character:character_subtype_key() end)
    return in_any_race("LEGEND_SUBTYPES", key) == true""",
     """    return IC.is_unique(character)"""),

    # AND THE SAFETY NET UNDER IT. Whether a man may be killed and made again is
    # a whitelist question, and without it any subtype at all goes over, which
    # turns a political event into a deleted legendary lord.
    ("a lord killed to defect into a faction that cannot field him", M,
     """    return in_any_race("REBEL_GENERALS", key) == true
end""",
     """    return true
end"""),

    # THE TWO TESTS BACK IN THEIR OLD ORDER. In that order "a legendary lord IS
    # the faction" can only reach a legend who was NOT confederated, which is the
    # one case it changes nothing in, so every absorbed legend goes to his old
    # house and Bzaark sits with the legion in a Conclave campaign.
    ("an absorbed legend seated with the house he came from", M,
     """    if IC.is_legend(character) or IC.is_ruler(character, faction_key) then return IC.CROWN end
    local origin = IC.origin_of_character(character)""",
     """    if IC.is_ruler(character, faction_key) then return IC.CROWN end
    local origin = IC.origin_of_character(character)"""),

    # AND THE LEGEND GUARD PUT BACK BEHIND THE OWN-BLOC TEST. Every legend is a
    # Crown man, so the own-bloc test answers first every time and a guard on an
    # irreversible act silently stops firing while still reading like a guard.
    ("a legend refused for where he sits rather than for what he is", M,
     """    if plot_key == "murder" and IC.is_legend(victim) then
        return false, "unique"
    end
    if IC.house_of_character(victim, faction_key) == IC.CROWN then""",
     """    if IC.house_of_character(victim, faction_key) == IC.CROWN then"""),

    # EVERY ARMY CROWNING ITS GENERAL: three characters each made faction leader
    # of the same faction inside one tick, each deposing the last, which crashes
    # at Warhammer3.exe+0x268CE1F. A ONE-army secession is unharmed, which is
    # why it reads as harmless.
    ("every rebel army crowning its own general as faction leader", M,
     """            local crown = waking and i == 1""",
     """            local crown = waking"""),

    # AND THE CROWN GIVEN OVER A REBELLION THAT ALREADY HAS ONE. The pool is
    # reused once every faction in it is awake, so a fifth party would depose the
    # leader of the rebellion it is joining.
    ("a fifth secession deposing the rebellion it joins", M,
     """            local crown = waking and i == 1""",
     """            local crown = (i == 1)"""),

    # AND NOBODY CROWNED AT ALL. The other way round: a dormant faction woken
    # with make_faction_leader false has a leader INVENTED for it, which is the
    # orc shaman.
    ("a woken faction left to invent its own leader", M,
     """            local crown = waking and i == 1""",
     """            local crown = false"""),

    # THE STEPS RUN INLINE AGAIN, all in the frame the turn handler is already
    # in, which crashes at Warhammer3.exe+0x268CE1F. It reads like a
    # simplification, since the callback does nothing you cannot do by calling
    # the function. What it does is give the engine a frame between waking a
    # faction, moving twenty regions and killing three of the player's generals.
    ("a secession that changes the whole world in one frame", M,
     """    pcall(steps[i])
    cm:callback(function() IC.secede_step(steps, i + 1) end,
                IC.TUNE.secede_step)""",
     """    for n = i, #steps do pcall(steps[n]) end"""),

    # AND THE GAP CLOSED TO NOTHING, which is the same thing wearing a tuning
    # knob: cm:callback with a zero delay runs in the same frame.
    ("a stagger with no gap in it", M,
     """    secede_step         = 0.1,""",
     """    secede_step         = 0,"""),

    # THE WHITELIST DROPPED, so the departing lord's subtype goes over whatever
    # it is. derpy_bzaark handed to qb2, which may not field him, crashes the
    # game about a second later with no Lua error and no minidump. He belongs to
    # the PLAYER's faction, so he can be anything at all.
    ("a rebel general the rebels are not allowed to field", M,
     """        if key and key ~= "" and R.REBEL_GENERALS[key] then
            out.subtype = key
        end""",
     """        if key and key ~= "" then
            out.subtype = key
        end"""),

    # AND THE LEGEND ALLOWED TO DEFECT. A defection is a kill and a respawn, so
    # this deletes a legendary lord from the player's campaign for good, which
    # IC.plot also refuses to do.
    ("a legendary lord killed off for a party he merely belonged to", M,
     """                             defects = IC.can_defect(man)}""",
     """                             defects = true}"""),

    # THE COUNT BACK ON EVERY LORD rather than on the ones who can actually go.
    # A party of one legend and one ordinary lord asks for two and has one, and
    # the second rising gets defectors[2] = nil - a rebellion under a general
    # the engine picked, which is the orc shaman once more.
    ("a secession counting lords who cannot change sides", M,
     """    local leaving = math.min(#defectors, want_lords, IC.TUNE.rebel_lords_max)""",
     """    local leaving = math.min(#lords, want_lords, IC.TUNE.rebel_lords_max)"""),

    # NOBODY IS ACTUALLY TAKEN OFF YOUR SIDE. The army spawns, it is the right
    # faction, it is led by a man with the right name - and the same man is also
    # still sitting in your court, so the player sees his lord twice.
    ("a lord who leads the rebellion and stays in your court", M,
     """                pcall(function() cm:kill_character(rise.cqi, false) end)""",
     """                local _ = rise.cqi"""),

    # AND HIS ARMY DELETED WITH HIM. "An army whose lord has changed sides has
    # changed sides" reads better, and it is the prime suspect for the null
    # dereference at Warhammer3.exe+0x268CE1F: these lords stand in provinces
    # handed to the rebels a moment later.
    ("a secession that deletes the player's armies as well as his lords", M,
     """                pcall(function() cm:kill_character(rise.cqi, false) end)""",
     """                pcall(function() cm:kill_character(rise.cqi, true) end)"""),

    # THE OTHER DIRECTION, on the other caller. A murder in the Tower passing
    # true deletes the dead man's army: a stack of the player's own soldiers
    # gone because somebody lost a vote. The harness checks this on the murder,
    # not in the stub, because secession is a caller that needs true.
    ("a knife in the Tower that takes his whole army with him", M,
     """        cm:kill_character(cm:char_lookup_str(victim), false)""",
     """        cm:kill_character(cm:char_lookup_str(victim), true)"""),

    # THE DEFECTOR ARRIVES AS A STOCK CASTELLAN. The fallback is for a party
    # with nobody left who can lead, and using it for everybody throws away the
    # only thing that makes a secession read as YOUR lord turning on you.
    ("a rebellion led by a stranger rather than by your own lord", M,
     """        if key and key ~= "" and R.REBEL_GENERALS[key] then
            out.subtype = key
        end""",
     """        if key and key ~= "" and R.REBEL_GENERALS[key] then
            out.subtype = IC.REBEL_LORD
        end"""),

    # The secession actually bites.

    # THE FLOOR PUT BACK ON THE ORDINARY CLOCK. Zero forces the anger and then
    # queues behind the same five turns as every other grievance, so the most
    # final state in the model gets five turns of warning. A party at zero
    # leaves at once.
    ("a party at zero put back on the five-turn countdown", M,
     """        if breaking then
            seceding[#seceding + 1] = slug
            house.clock = 0
        elseif angry then""",
     """        if breaking then
            angry = true
        end
        if angry then"""),

    # The fallback lives in the floor under `want`, so this mistake is written
    # as letting the count reach zero: a party that governs nothing in a loyal
    # realm walks out with nothing and the whole secession is a row leaving a
    # table, with no settlements seized.
    ("a secession that moves no land when the party built nothing", M,
     """    if want < 1 then want = 1 end""",
     """    if false then want = 1 end"""),

    # THE ARMY HANDED TO THE PLAYER'S OWN FACTION. One argument, and it is the
    # argument the whole call exists for: force_rebellion_in_region has no
    # faction parameter at all, so a Chaos Dwarf secession through it at
    # Nagashizzar raises skaven. A rebellion the player owns is not a rebellion.
    ("a rebel army that belongs to the faction it is rebelling against", M,
     """            rebels, table.concat(units, ","), region_key, x, y,""",
     """            "wh3_dlc23_chd_conclave", table.concat(units, ","), region_key, x, y,"""),

    # THE LAND MOVED FIRST AND THE ARMY SECOND. This reads better - take the
    # province, then raise the army on it - and it is wrong twice over: the site
    # is read out of the PLAYER'S region list, which no longer contains a
    # province that has changed hands, and the transfers need the rebel faction
    # to exist, which is what creating the force does.
    #
    # Written against the per-lord loop: asking for a province the player does
    # not hold is what reading the site after the transfer amounts to (rebel_site
    # walks his region_list and finds nothing), so the mutant says it that way
    # rather than by reordering thirty lines.
    ("an army raised after the ground it was going to stand on changed hands", M,
     """        local name, x, y = IC.rebel_site(faction_key, where)""",
     """        local name, x, y = IC.rebel_site(faction_key, where .. "_gone")"""),

    # AND NOBODY IS TOLD. The record line stays, so the Record tab still has it -
    # which is exactly what makes this easy to do and hard to notice: the
    # information is technically somewhere.
    ("a party that leaves without a word on the feed", M,
     """    IC.feed(faction_key, "secede_done")""",
     """    local _ = faction_key"""),

    # THE ROSTER EMPTIED TO A LORD ON HIS OWN. rebel_units is a tuning number and
    # this is what reading it as an index rather than a count looks like: an
    # army spawns, the faction is right, the lord is right, and the crisis is one
    # man standing in a field.
    ("a rebellion of one lord and no soldiers", M,
     """        for i = 1, math.min(IC.TUNE.rebel_units, #kit) do
            units[i] = kit[i]
        end""",
     """        units[1] = kit[IC.TUNE.rebel_units]"""),

    # THE ARMY ASKED OF CA's WRAPPER AGAIN. It is the obvious thing to write:
    # `cm` is what every other call in this file uses. Its
    # create_force_with_general refuses a faction that is not on the campaign
    # map, the rebels never are, and the refusal lands inside a pcall, so the
    # army silently never spawns and the province transfer that was waiting on
    # the faction existing does nothing either.
    ("a rebel army asked of the wrapper that refuses off-map factions", M,
     """        cm.game_interface:create_force_with_general(""",
     """        cm:create_force_with_general("""),

    # THE SHARE DROPPED OUT OF THE COUNT. Back to "what it governs plus what has
    # rotted", which is a floor with nothing on top of it, so a party holding
    # half the court walks out with whatever it happened to be governing. The
    # land a party takes reflects its share of the court.
    ("a secession whose size has nothing to do with the party's", M,
     """    local want = math.ceil(#pool * share / 100)""",
     """    local want = 0"""),

    # AND THE FLOOR DROPPED OUT OF IT. A small party with three angry provinces
    # walks out leaving two of them behind, because its share only entitled it
    # to one - the share is about how much MORE it takes, never about handing
    # back ground that had already gone over.
    ("a share that takes ground back off a party that already held it", M,
     """    if want < must then want = must end""",
     """    if false then want = must end"""),

    # THE ROUNDING TURNED DOWN. Every party under half a province's worth of
    # court takes nothing at all; this line is the fallback that catches that.
    ("a share rounded down, so a small party leaves with nothing", M,
     """    local want = math.ceil(#pool * share / 100)""",
     """    local want = math.floor(#pool * share / 100)"""),

    # BACK TO THE REBEL FACTION. It is the key anybody would pick:
    # wh3_dlc23_chd_chaos_dwarfs_rebels is the canonical
    # Chaos Dwarf rebels and the only is_rebel row in the subculture. Asked of a
    # live campaign it answers FALSE - every is_rebel faction does, because the
    # engine makes them per rebellion - so the transfer and the spawn both do
    # nothing and say nothing, and the secession reports success either way.
    ("a party that secedes into a faction the campaign has never heard of", M,
     """    local rebels, waking = IC.rebel_faction_for(faction_key, slug)""",
     """    local rebels, waking = "wh3_dlc23_chd_chaos_dwarfs_rebels", true"""),

    # THE DORMANT ONE PREFERRED OVER THE FREE ONE, so every secession after the
    # first joins the faction the first became. It looks like a simplification -
    # one rebel faction, one civil war - and it costs the player the ability to
    # tell two rebellions apart on the map.
    ("every party that leaves joining the same rebel faction", M,
     """        local dead = false
        pcall(function() dead = f:is_dead() end)
        return dead""",
     """        return true"""),
    # A FULL POOL JOINING A RISING WHILE A HOUSE LIES DEAD.
    ("a full pool joining a running rising while a dead house is free", M,
     """        if key and key ~= exclude and dead_one(key) then return key, true end""",
     """        if false then return key, true end"""),

    # AND THE WAR DROPPED. The land still changes hands and the army still
    # stands on it, and the faction holding your provinces is at peace with you -
    # which is not a civil war, it is a gift.
    ("a rebellion that takes your provinces and stays friendly", M,
     """            pcall(function()
                cm:force_declare_war(rebels, faction_key, false, false)
            end)""",
     """            pcall(function() local _ = rebels end)"""),

    # THE GENERAL NOT LEADING THE FACTION HE WAS SPAWNED INTO. It reads like the
    # safe value: don't touch the faction's leadership. A dormant faction woken
    # with no leader has one INVENTED for it (an orc shaman); the Infernal
    # Castellan is permitted for all four of these factions, so the shaman was
    # never this army's general, it was the leader nobody set.
    ("a rebel army whose general does not lead the rebellion", M,
     """            crown == true, true, false)""",
     """            false, true, false)"""),

    # The feed waits for the panel.

    # The card raised under the panel. The panel is priority 60 and covers the
    # screen while CA's events layout is 50, so a card raised the moment the
    # plot resolves opens underneath it and the player never sees one. The
    # engine logs the call either way.
    ("a feed that raises a card straight into the back of the panel", M,
     """    if IC.feed_held then
        if #IC.feed_queue < IC.FEED_QUEUE_MAX then
            IC.feed_queue[#IC.feed_queue + 1] = {faction_key, slug, secondary}
        end
        return true
    end
    return IC.raise_feed(faction_key, slug, secondary)""",
     """    return IC.raise_feed(faction_key, slug, secondary)"""),

    # THE FLUSH WALKED BACKWARDS, which is the shape somebody reaches for when
    # emptying a list in place - and the hold exists precisely so that two moves
    # made in one sitting arrive in the order they happened. Reversed, a failed
    # plot and the seat it cost read as cause and effect the wrong way round.
    ("a queue emptied from the end, so the cards arrive backwards", M,
     """    for i = 1, #queued do
        IC.raise_feed(queued[i][1], queued[i][2], queued[i][3])
    end""",
     """    for i = #queued, 1, -1 do
        IC.raise_feed(queued[i][1], queued[i][2], queued[i][3])
    end"""),

    # THE DRAIN TIDIED OUT OF THE TURN. It looks like dead code - the panel
    # always releases the hold on close - and what it actually guards is the
    # case where the flag was cleared without a flush, where the difference
    # between having this line and not is a card that is late and a card that
    # is gone.
    ("a turn that walks past a queue nothing else will empty", M,
     """    if not IC.feed_held then IC.flush_feed() end""",
     """    if false then IC.flush_feed() end"""),

    # THE HOLD NEVER SET. Everything else about the panel is unchanged and the
    # model is still perfectly capable of holding - it is simply never asked to,
    # which puts the mod back exactly where the player found it.
    ("a court that opens without telling the feed to wait", U,
     """        IC.hold_feed(true)""",
     """        local _ = IC.hold_feed"""),

    # THE HOLD HOISTED UP BESIDE THE CREATE, where it reads as part of "open
    # the court" rather than part of "the court opened". It is the same ordering
    # fault as a HUD hidden before creation succeeds and costs more: a hold set
    # on a panel that never appeared is a hold nothing will ever release, and
    # the event feed is silent from then until the player reloads.
    ("a hold set before the panel is known to exist", U,
     """    if ok and comp(ICUI.PANEL) then
        -- AFTER creation, never before: a failed CreateComponent must not be able
        -- to leave the player with a hidden HUD and no panel to close.
        ICUI.show_hud(false)
        -- AND THE FEED WAITS, under the same guard and for the same reason. This
        -- panel is priority 60 and covers the screen while CA's events layout is
        -- 50, so a card raised from a click inside it opens underneath it and is
        -- never seen. A hold set on a panel that failed to open would be a hold
        -- nothing ever releases.
        IC.hold_feed(true)
        ICUI.hold_esc()
        ICUI.refresh()""",
     """    IC.hold_feed(true)
    if ok and comp(ICUI.PANEL) then
        ICUI.show_hud(false)
        ICUI.hold_esc()
        ICUI.refresh()"""),

    # AND THE RELEASE NEVER MADE. This is the worse half of the same fault: the
    # first time the player opens the court, the feed goes quiet for the rest of
    # the campaign, and nothing on screen says why.
    ("a court that closes and leaves the feed held forever", U,
     """    IC.hold_feed(false)
    -- AND THE ESCAPE KEY""",
     """    -- AND THE ESCAPE KEY"""),

    # The breaking point.

    # TESTED BEFORE THE OATH INSTEAD OF AFTER IT. This reads better (the two
    # ways a party can be held, one after the other) and breaks the rule that
    # nothing holds a party at zero, so the oath has to be cleared first and the
    # floor tested last. Written this way, the expensive button still saves a
    # party that has hit bottom.
    #
    # The floor is its own flag, read first and acted on before the anger is
    # looked at, so the version of this mistake that still compiles is an oath
    # that clears that flag.
    ("an oath that holds a party at zero after all", M,
     """            if IC.protected_for(faction_key, slug) > 0 then angry = false end
            breaking = IC.at_breaking_point(faction_key, slug)""",
     """            breaking = IC.at_breaking_point(faction_key, slug)
            if IC.protected_for(faction_key, slug) > 0 then
                angry = false
                breaking = false
            end"""),

    # THE FLOOR DELETED: a party at zero loyalty sits in court forever, because
    # five equal parties are 20 per cent each and secede_share is 25, so the
    # loyalty half of the gate is unreachable. The line looks redundant beside
    # the gate two lines up.
    ("a court where zero loyalty is just another low number", M,
     """            breaking = IC.at_breaking_point(faction_key, slug)""",
     """            breaking = false"""),

    # THE OATH SOLD AT THE FLOOR AND DOING NOTHING. The refusal looks like a
    # restriction on the player, so removing it looks like a kindness; what it
    # actually does is take full price for an oath that stops the clock this
    # turn and watches it start again the next.
    ("an oath sold to a party nothing can hold", M,
     """        if IC.at_breaking_point(faction_key, slug) then
            return false, "breaking"
        end""",
     """        if false then
            return false, "breaking"
        end"""),

    # AND THE TOOLTIP PUT BACK TO PROMISING IT. "They cannot break with you for
    # another 5 turns" off protected_for alone is false at the floor, and Secure
    # Loyalty's tooltip (the favour screen's line) is exactly where a player
    # goes when a party is about to leave.
    ("a Secure Loyalty tooltip that still promises an oath holds them", U,
     """    if IC.at_breaking_point(faction, slug) then""",
     """    if false then"""),

    # The oath.
    ("the oath's loyalty gate", M,
     """        if (house.loyalty or IC.TUNE.loyalty_start)
                < IC.TUNE.plot_oath_min_loyalty then
            return false, "cold"
        end""",
     """"""),

    ("an oath survives the death of YOUR half of it", M,
     """        for slug2, house2 in pairs(court.houses) do
            if house2.oath_mine == cqi or house2.oath_theirs == cqi then""",
     """        for slug2, house2 in pairs(court.houses) do
            if house2.oath_theirs == cqi and false then"""),

    # The odds.
    ("an errand's odds measured against a victim that is not there", M,
     """    local edge = 0
    if IC.plot_is_aimed(plot_key) then""",
     """    local edge = 0
    if true then"""),

    ("the odds clamp, which is the only thing keeping a plot fallible", M,
     """    if chance < IC.TUNE.plot_chance_min then chance = IC.TUNE.plot_chance_min end
    if chance > IC.TUNE.plot_chance_max then chance = IC.TUNE.plot_chance_max end""",
     """"""),

    # Who may move, and against whom.
    ("a general sent on a civil mission", M,
     """    if IC.is_civil_mission(plot_key) and actor:has_military_force() then
        return false, "commands"
    end""",
     """"""),

    ("a knife aimed at your own party", M,
     """    if IC.house_of_character(victim, faction_key) == IC.CROWN then""",
     """    if false then"""),

    ("a legendary lord murdered and never coming back", M,
     """    if plot_key == "murder" and IC.is_legend(victim) then
        return false, "unique"
    end""",
     """"""),

    # What a move costs, and what a miss costs.
    ("a plot that is never paid for", M,
     """    IC.add_standing(faction_key, actor_cqi, -cost)""",
     """"""),

    ("the purge's backfire folded into the ordinary penalty", M,
     """            if plot_key == "purge" then
                IC.move_loyalty(faction_key, against,
                                -IC.TUNE.plot_purge_backfire)
            end""",
     """"""),

    ("loyalty running past the ends of its own scale", M,
     """    house.loyalty = math.max(0, math.min(100, was + delta))""",
     """    house.loyalty = was + delta"""),

    # The save.
    ("an older save refused instead of migrated", M,
     """        if #bits >= 3 then""",
     """        if #bits >= 13 then"""),

    # The seven moves that fill out the columns.
    ("a strike that charges the insult once per seat", M,
     """            IC.dismiss(faction_key, office_slug, true)""",
     """            IC.dismiss(faction_key, office_slug)"""),

    ("a strike aimed at a house that holds nothing to strike", M,
     """    if plot_key == "unseat" then
        local slug = IC.house_of_character(victim, faction_key)
        if #IC.offices_of_house(faction_key, slug) == 0 then
            return false, "no seats"
        end
    end""",
     """    if plot_key == "unseat" then
        local _slug = IC.house_of_character(victim, faction_key)
    end"""),

    ("a recall that calls every overseer home, not one house's", M,
     """        for _, province_key in ipairs(IC.provinces_of_house(faction_key,
                                                            against)) do""",
     """        for _, province_key in ipairs(IC.seats(faction_key)) do"""),

    ("a patronage that hands over more than it charged", M,
     """        IC.add_standing(faction_key, cqi, IC.TUNE.plot_patron_standing)""",
     """        IC.add_standing(faction_key, cqi, IC.plot_cost(plot_key) + 50)"""),

    ("a kinsman added to the Crown without leaving his house", M,
     """            house.weight = (house.weight or 0) - moved
            crown.weight = (crown.weight or 0) + moved""",
     """            crown.weight = (crown.weight or 0) + moved"""),

    ("a pledge the Crown never pays for", M,
     """        local crown = IC.court(faction_key).houses[IC.CROWN]
        if crown then
            crown.weight = math.max(1, (crown.weight or 0)
                                    - IC.TUNE.plot_pledge_weight)
        end""",
     """        local _crown = IC.court(faction_key).houses[IC.CROWN]"""),

    ("an audience that cools the court it was held to warm", M,
     """        IC.mood_of_the_court(faction_key, IC.TUNE.plot_audience_loyalty)""",
     """        IC.mood_of_the_court(faction_key, -IC.TUNE.plot_audience_loyalty)"""),

    ("a circuit that pushes a province past the top of its scale", M,
     """            court.prov[province_key] = math.min(IC.TUNE.prov_loyalty_max,
                IC.province_loyalty(faction_key, province_key)
                + IC.TUNE.plot_circuit_prov)""",
     """            court.prov[province_key] =
                IC.province_loyalty(faction_key, province_key)
                + IC.TUNE.plot_circuit_prov"""),

    # The grid the categories derive.
    ("a category quietly one move deeper than the rest", M,
     """    {key = "circuit", name = "Ride the Circuit", aimed = false,
     icon = "ui/campaign ui/ancillaries/wh3_dlc23_anc_follower_convoy_enforcer.png",
     cat = "errand",""",
     """    {key = "circuit", name = "Ride the Circuit", aimed = false,
     icon = "ui/campaign ui/ancillaries/wh3_dlc23_anc_follower_convoy_enforcer.png",
     cat = "bond","""),

    ("a move with no odds, which can therefore never miss", M,
     """    plot_chance_circuit   = 80,""",
     """    plot_chance_cicruit   = 80,"""),

    # Who speaks for your own house.
    ("the Crown led by the richest courtier instead of the man on the throne", M,
     """    if slug == IC.CROWN then
        local seated = IC.faction_leader_cqi(faction_key)
        if seated and IC.house_of_cqi(faction_key, seated) == IC.CROWN then
            return seated
        end
    end""",
     """"""),

    ("the throne's own fallback deleted, so a faction between rulers has nobody", M,
     """        local seated = IC.faction_leader_cqi(faction_key)
        if seated and IC.house_of_cqi(faction_key, seated) == IC.CROWN then
            return seated
        end""",
     """        return IC.faction_leader_cqi(faction_key)"""),

    ("the Crown's block back on its own second source for who leads", U,
     """    local cqi = IC.party_leader(faction, IC.CROWN)""",
     """    local cqi = IC.faction_leader_cqi(faction)"""),

    # The panel.
    # THE CARD IS THE CONTROL: once to choose, again for its members. A handler
    # that only ever chooses leaves the roster unreachable.
    ("a second click on a chosen card choosing it again, not opening its men", U,
     """    if ICUI.sel == slug then""",
     """    if false then"""),

    ("the selection frame drawn on every card", U,
     """        card:SetImagePath(ICUI.sel == slug and ICUI.PARTY_SELECTED
                          or ICUI.MASK_NONE, ICUI.PARTY_SEL_INDEX)""",
     """        card:SetImagePath(ICUI.PARTY_SELECTED, ICUI.PARTY_SEL_INDEX)"""),

    ("the action bar drawn for your own house", U,
     """    local rival = slug ~= nil and slug ~= IC.CROWN and court.houses[slug] ~= nil""",
     """    local rival = slug ~= nil and court.houses[slug] ~= nil"""),

    ("Provoke and Purge aimed at your own house's leader", U,
     """    local target = IC.party_leader(faction, slug)
    if not target then""",
     """    local target = IC.party_leader(faction, IC.CROWN)
    if not target then"""),

    ("a demand granted without seating the man it names", P,
     """        if not IC.appoint(faction_key, d.key, d.cqi) then return false, "no" end""",
     """        if false then return false, "no" end"""),

    ("a demand for a man already in office drawn as grantable", P,
     """    for _, cqi in pairs(court.offices) do
        if cqi == d.cqi then return false, "busy" end
    end""",
     """"""),

    ("REFUSE on the Petitions tab routed to ACCEPT", U,
     """                ICUI.on_petition_click(context, false)""",
     """                ICUI.on_petition_click(context, true)"""),

    # A roster row offers Find, but only for a man the camera can go to. The
    # mistake is wiring the rest.
    ("a roster row wired to a man the camera cannot go to", U,
     """            ICUI.pick_rows[#lines] = ICUI.map_spot(cand.character)
                                     and cand.cqi or nil""",
     """            ICUI.pick_rows[#lines] = cand.cqi"""),

    ("the roster listing every house's men, not your own", U,
     """      if not roster or cand.slug == ICUI.pick.slug then""",
     """      if true then"""),

    ("a civil mission opening the victim picker anyway", U,
     """    elseif IC.plot_is_aimed(move.plot) then
        ICUI.pick = {kind = "plot_target", plot = move.plot}
    else
        ICUI.pick = {kind = "plot", plot = move.plot, key = nil}
    end""",
     """    else
        ICUI.pick = {kind = "plot_target", plot = move.plot}
    end"""),

    ("a move's icon painted into the porthole's layer, not the icon cell's", U,
     """            ICUI.set_crest(card, "ic_plot_icon", plot.icon, ICUI.PLOT_ICON_PX)""",
     """            ICUI.set_face(card, "ic_plot_icon", plot.icon)"""),

    ("a seat nobody can take drawn as though somebody could", U,
     """        if not cand.busy and IC.can_appoint(faction, office_slug, cand.cqi) then
            return true
        end
    end
    return false""",
     """        if not cand.busy and IC.can_appoint(faction, office_slug, cand.cqi) then
            return true
        end
    end
    return true"""),
    # The Crown's block says what each line is.
    ("the share line drawn bare", U,
     """string.format(
             "[[img:%s]][[/img]]%d%% of the court", ICUI.COST_ICON, IC.control(faction))""",
     """string.format(
             "%d%% of the court", IC.control(faction))"""),
    ("the band line drawn bare", U,
     """string.format(
             "[[img:%s]][[/img]]%s", ICUI.BAND_ICON, ICUI.band_name(band))""",
     """ICUI.band_name(band)"""),
    ("an effect line drawn bare", U,
     """    if not (label and ICUI.FX_ICONS[label]) then return line end""",
     """    if true then return line end"""),
    ("the Crown's party drawn without its crest", U,
     """    set_text(comp("ic_leader_party", panel), ICUI.crest(IC.CROWN) and string.format(""",
     """    set_text(comp("ic_leader_party", panel), false and string.format("""),
    ("the Crown's rules left on every tab", U,
     """"ic_crown_box",
                    "ic_crown_rule_l", "ic_crown_rule_r", "ic_crown_rule_v"}""",
     """"ic_crown_box"}"""),
    ("a recruit arrives with nothing", M,
     """    court.standing[cqi] = IC.recruit_influence(character:rank(), faction_key)""",
     """    court.standing[cqi] = 0"""),
    ("the ladder flat between its bars", M,
     """            return a[2] + math.floor((b[2] - a[2]) * (rank - a[1]) / (b[1] - a[1]))""",
     """            return a[2]"""),
    ("a second CharacterCreated resets what he earned", M,
     """    if court.standing[cqi] ~= nil then return end
    court.standing[cqi] = IC.recruit_influence""",
     """    court.standing[cqi] = IC.recruit_influence"""),
    ("a man priced into a court with no parties", M,
     """    if not IC.court_rolled(faction_key) then return end
    local cqi = character:command_queue_index()
    local court = IC.court(faction_key)""",
     """    local cqi = character:command_queue_index()
    local court = IC.court(faction_key)"""),

    # Sorting.
    # A copy of the court's list. The court draws the model's own list, and the
    # pie, the grid and the pager all index it, so a copy taken here (the obvious
    # "don't hand callers your internals" reflex) leaves the grid drawing one
    # order while the pie and the click read another. The standing bar is
    # positional too: IC.present_houses appends confederates rather than
    # interleaving them, so seating one does not move a colour already on screen.
    ("a court grid handed a copy the pie and the clicks are not", U,
     """function ICUI.court_slugs(faction_key)
    return IC.present_houses(faction_key)
end""",
     """function ICUI.court_slugs(faction_key)
    local out = {}
    for _, slug in ipairs(IC.present_houses(faction_key)) do
        table.insert(out, 1, slug)
    end
    return out
end"""),

    # A COMPARATOR THAT CAN ANSWER "EQUAL" BOTH WAYS. table.sort is not stable
    # in Lua, so two parties on the same loyalty come back in whatever order the
    # partition happened to leave them - measured, not assumed: five equal
    # elements sort to a,d,c,b,e one way round and e,b,c,d,a the other. The grid
    # then reshuffles on every refresh of one unchanged save.
    ("a sort comparator with nothing to break a tie on", U,
     """local function by(cmp, tie)
    return function(a, b)
        local x, y = cmp(a), cmp(b)
        if x ~= y then return x < y end
        return tie(a) < tie(b)
    end
end""",
     """local function by(cmp, tie)
    return function(a, b) return cmp(a) < cmp(b) end
end"""),

    # THE LISTS SCROLL: every list is drawn whole, with no pager. Each rule the
    # drawn-whole list rests on, broken once.
    ("the Court's cards never put in a list", U,
     """        ICUI.list_build(panel, "party", #slugs)
        ICUI.list_items(panel, "party", #slugs)""",
     """        local _ = 0"""),
    ("the rows never put in a list", U,
     """        ICUI.list_build(panel, "row", total)
        ICUI.list_items(panel, "row", total)""",
     """        local _ = 0"""),
    ("the items left behind when the list scrolls", U,
     """    if hy ~= by then holder:MoveTo(hx, by) end
end

-- THE POLL, on the Governors""",
     """end

-- THE POLL, on the Governors"""),
    ("the last view's list left over this one", U,
     """    if not ICUI.list_used then ICUI.list_drop(panel) end
""", ""),
    ("a list kept at its old length", U,
     """    local key = table.concat({view, kind, n, ICUI.list_gens[view] or 0}, "|")""",
     """    local key = table.concat({view, kind, ICUI.list_gens[view] or 0}, "|")"""),
    ("a re-sort that leaves the list scrolled", U,
     """    ICUI.list_rescroll(view)
    return true""",
     """    return true"""),
    ("a list whose bar shows when it fits", U,
     """        show(slider, lines > s.lines)""",
     """        show(slider, true)"""),
    ("a governor pick on the map that draws a row list over it", U,
     """    if ICUI.view == "govs" and ICUI.pick.kind == "gov" then return "" end
""", ""),
    ("a picker click that adds a window offset back", U,
     """    local chosen = ICUI.pick_rows[row]""",
     """    local chosen = ICUI.pick_rows[row + 10]"""),

    # THE SORT NEVER RUN. The picker's setting then cycles, relabels itself and
    # moves nothing at all - which on screen is indistinguishable from a control
    # that works on a list that happened to be in that order already.
    ("a character picker that never sorts", U,
     """    ICUI.sort_rows("pick", lines, ICUI.pick_rows, #lines)""",
     """"""),

    # THE DRAWN ROWS PERMUTED AND THE CLICK KEYS LEFT BEHIND. `lines` and
    # ICUI.pick_rows are parallel by index and on_pick_click reads nothing else,
    # so this offers one man and appoints another - silently, and only for a
    # player who has touched the sort.
    ("a picker reordered on screen but not where the click reads", U,
     """    for i = 1, n do
        lines[i] = was_lines[order[i]]
        rows[i] = was_rows[order[i]]
    end""",
     """    for i = 1, n do
        lines[i] = was_lines[order[i]]
    end"""),

    # WRITTEN STRAIGHT BACK INTO THE LIST IT IS READING. The copies look like
    # ceremony and are the whole thing: a permutation applied in place overwrites
    # an entry it has not read yet, so men are duplicated and men are lost.
    ("a picker permutation written over the rows it has not read yet", U,
     """    local was_lines, was_rows = {}, {}
    for i = 1, n do was_lines[i], was_rows[i] = lines[i], rows[i] end
    for i = 1, n do
        lines[i] = was_lines[order[i]]
        rows[i] = was_rows[order[i]]
    end""",
     """    for i = 1, n do
        lines[i] = lines[order[i]]
        rows[i] = rows[order[i]]
    end"""),

    # AVAILABLE BUILT FROM A SECOND COPY OF THE RULES. `affordable` is only one
    # of the four things that decide whether the click will take a man - rank,
    # a seat he already holds and the model's own plot gates are the others - so
    # this lifts a rich officer who is already Keeper of the Chains to the top of
    # the list and the button then refuses him.
    ("an AVAILABLE order that answers a different question than the click", U,
     """        lines[#lines].sort.ready = ICUI.pick_rows[#lines] ~= nil""",
     """        lines[#lines].sort.ready = affordable"""),

    # A CARD CELL BACK ON set_text. It is the obvious tidy-up - fit_cut looks
    # like ceremony beside four plain set_texts on the same card - and the cell
    # is 170px against a party name that reaches about 285. The string does not
    # clip at the cell edge, it draws out through the side of the card and across
    # the card beside it, and no build-time measurement can see it: the name is
    # rolled in the campaign and does not exist when the generator runs.
    ("a card cell that stops cutting the name it cannot measure", U,
     """            ICUI.fit_cut(comp("ic_card_holder", card),
                         holder and ICUI.character_name(holder) or "Vacant")""",
     """            set_text(comp("ic_card_holder", card),
                     holder and ICUI.character_name(holder) or "Vacant")"""),

    # THE TWO ENGINE CALLS IN THE OTHER ORDER. It reads better this way round -
    # "has an army, therefore a general" - and it is wrong for the one case the
    # label exists to distinguish: has_military_force is documented as "Does
    # this character command a military force?" and a hero riding inside a stack
    # is a character the engine has every reason to answer yes for. Asked first,
    # a wizard embedded in an army is drawn as a General.
    #
    # With four kinds it also means a Retainer can never be produced, so that
    # kind never appears and the feature looks like it had been built.
    ("a man's kind decided by his army before his type", M,
     """    local ok, general = pcall(function()
        return character:character_type("general")
    end)
    if not ok then return nil end
    local held, force = pcall(function()
        return character:has_military_force()
    end)""",
     """    local held, force = pcall(function()
        return character:has_military_force()
    end)
    if held and force then return "general" end
    local ok, general = pcall(function()
        return character:character_type("general")
    end)
    if not ok then return nil end"""),

    # THE TITLE TIDIED OFF THE FRONT OF THE NAME. The shorter line still reads
    # correctly, which is exactly why somebody would write it: the feature is
    # then gone with no error anywhere and a column that looks like it always
    # did.
    ("a character cell that stops saying what kind of man he is", U,
     """            ICUI.titled(cand.kind, man),""",
     """            man,"""),

    # THE SORT KEYED ON WHAT THE CELL DRAWS. It looks like the tightening this
    # panel keeps making - one source for the cell and the order - and it is the
    # one place that rule is wrong: the cell draws a WORD in front of the name,
    # so a list ordered on it comes back grouped by kind - every General, then
    # every Hero, then every Lord - under a heading that says Character.
    #
    # It lives on the name cell because the rank cell is a bare number and
    # cannot be made to carry a word.
    ("a name order keyed on the label instead of the name", U,
     """            sort = {name = man, standing = has, rank = cand.rank,""",
     """            sort = {name = ICUI.titled(cand.kind, man), standing = has, rank = cand.rank,"""),

    # THE CARD THAT DRAWS A BARE NAME. The title belongs in the lists AND on
    # the cards, and the card is the easier half to forget: it is a
    # different function, in a different file section, and the line it changes
    # reads perfectly well without it.
    ("an office card whose second line goes back to spelling out the party", U,
     """            local kind = holder and IC.kind_of_character(holder) or nil
            ICUI.fit_cut(comp("ic_card_house", card),
                         (kind and ICUI.KIND_NAME[kind]) or "")""",
     """            ICUI.fit_cut(comp("ic_card_house", card),
                         slug and ICUI.house_name(slug) or "")"""),

    # THE WORD LEFT ON A SEAT NOBODY HOLDS. Cards are RECYCLED: the component
    # that drew the last officer draws the vacancy, so writing the cell only
    # when there IS a man reads like a guard and is the opposite of one.
    #
    # NOT "or nil": fit_cut's own first line is tostring(text or ""), so nil and
    # "" reach the cell as the same empty string and that mutant changes
    # nothing.
    ("a vacated card that keeps the last man's position", U,
     """            ICUI.fit_cut(comp("ic_card_house", card),
                         (kind and ICUI.KIND_NAME[kind]) or "")""",
     """            if kind then
                ICUI.fit_cut(comp("ic_card_house", card), ICUI.KIND_NAME[kind])
            end"""),

    # A RECYCLED CARD WITH ONE OF ITS TWO LAYERS LEFT ON. The plate and the
    # colour mask are separate images and a vacant seat has to have BOTH taken
    # off it - "no call" leaves the last holder's art where it was, and a seat
    # nobody holds flying a party's colour reads as a seat that party holds.
    ("a vacant card that clears one layer and not the other", U,
     """        ic:SetImagePath(ICUI.MASK_NONE, ICUI.PLATE_INDEX)
        ic:SetImagePath(ICUI.MASK_NONE, ICUI.MASK_INDEX)""",
     """        ic:SetImagePath(ICUI.MASK_NONE, ICUI.PLATE_INDEX)"""),

    # CLEARED WITH NOTHING, WHICH IS NOT THE SAME AS CLEARED. An empty path and
    # a path that resolves to nothing both draw a BLANK WHITE SQUARE, silently.
    # ICUI.MASK_NONE is a real fully transparent png shipped for exactly this.
    ("a vacant card that clears its plate with nothing at all", U,
     """        ic:SetImagePath(ICUI.MASK_NONE, ICUI.PLATE_INDEX)""",
     """        ic:SetImagePath("", ICUI.PLATE_INDEX)"""),

    # NO WAY BACK TO THE ORDER THE LIST ALREADY HAD. A control whose every
    # setting is a sort cannot return the player to the arrangement he has
    # learnt, and nothing on screen tells him what he has lost.
    ("a sort control with no setting for the list's own order", U,
     """    pick = {
        {key = "default",  name = "ROSTER ORDER"},
        {key = "name",     name = "NAME",      col = 1},""",
     """    pick = {
        {key = "name",     name = "NAME",      col = 1},"""),

    # Who a rebellion is.
    # THE POOL FOR EVERYBODY, which is defensible right up until you look at the
    # map: four dormant factions all called "Chaos Dwarfs" over the generic rebel
    # flag, and a confederated House of Bzaark rising again as "Chaos Dwarfs
    # (2)". A faction's crest is a factions_tables column with no runtime setter,
    # so being the right faction is the ONLY way to fly the right one.
    ("every rebellion back in the dormant pool, crest and all", M,
     """    local own = IC.faction_for_origin(slug)
    if own and own ~= faction_key then""",
     """    local own = IC.faction_for_origin(slug)
    if false then"""),

    # THE GUARD DROPPED. faction_for_origin("conclave") answers
    # wh3_dlc23_chd_conclave, so a Conclave party in a Conclave campaign secedes
    # into the player himself: his own provinces handed to him, and a war
    # declared between him and him. force_confederation(X,X) already crashes the
    # game for the same reason.
    ("a party seceding into the very faction it is leaving", M,
     """    if own and own ~= faction_key then""",
     """    if own then"""),

    # What it is called.
    # THE RENAME APPLIED AND NOT REMEMBERED. change_custom_faction_name is not
    # documented as persistent and this is exactly the line somebody removes as
    # redundant - the name is visibly right for the whole session it was set in,
    # and wrong the next time the player loads.
    ("a rebellion's name forgotten the moment the save is reloaded", M,
     """    pcall(function() cm:change_custom_faction_name(rebels, name) end)
    cm:set_saved_value("derpy_ic_risen_" .. rebels, name)""",
     """    pcall(function() cm:change_custom_faction_name(rebels, name) end)"""),

    # THE FACTION'S OWN KEY FOR ITS NAME. rebels is in scope, is a string, and
    # reads like a name in the log line two lines below - and the whole point
    # was that the key is what the player was seeing already.
    ("a rebellion renamed to the faction key it already was", M,
     """            IC.rebel_rename(rebels, flying)""",
     """            IC.rebel_rename(rebels, rebels)"""),

    # Who minds.
    # NO THREAT SCORE. The war is declared, so the secession looks complete, and
    # a rebellion against an AI court is on friendly terms with the player.
    ("a rebellion everybody else is perfectly happy about", M,
     """                if f and f ~= false then
                    cm:set_base_strategic_threat_score(f, IC.TUNE.rebel_threat)
                end""",
     """                if f and f ~= false then
                    local _ = IC.TUNE.rebel_threat
                end"""),

    # Edicts need a governor.
    # THE GREY THAT DID NOT HOLD: the state alone, which the
    # engine moves back to "active" by itself.
    ("an ungoverned province's edicts greyed by state alone", U,
     """                c:SetDisabled(true)
                ICUI.grey_look(c, true)""",
     """                c:SetDisabled(true)"""),
    ("a governed province's edicts left shaded grey", U,
     """                c:SetDisabled(false)
                ICUI.grey_look(c, false)""",
     """                c:SetDisabled(false)"""),
    # Three ways the edict lookup finds nothing in game.
    ("the edict stack looked for under the layout file's spelling", U,
     """ICUI.EDICT_STACK = {"hud_campaign", "BL_parent", "stack_incentives"}""",
     """ICUI.EDICT_STACK = {"hud_campaign", "bl_parent", "stack_incentives"}"""),
    ("only the edict stack's own children taken for buttons", U,
     """                else
                    walk(k)
                end""",
     """                end"""),
    ("every child of the edict stack taken for a button", U,
     """                if string.sub(tostring(k:Id()), 1, 7) == "button_" then""",
     """                if true then"""),
    ("an ungoverned province's edicts left clickable, only drawn grey", U,
     """                if to then c:SetState(to) end
                c:SetDisabled(true)""",
     """                if to then c:SetState(to) end"""),
    ("the running edict greyed into the plain inactive state", U,
     """                   selected = "selected_inactive", down_off = "selected_inactive"}""",
     """                   selected = "inactive", down_off = "inactive"}"""),
    ("a governed province never given its edicts back", U,
     """        return "live"
    end)""",
     """        return nil
    end)"""),
    ("an incomplete province's edicts lit by the court", U,
     """            if list:item_at(i):owning_faction():name() ~= me then return nil end""",
     """            local _ = list:item_at(i)"""),
    ("another faction's settlement judged by this court", U,
     """        if region:owning_faction():name() ~= me then return nil end
        local province""",
     """        local province"""),
    # The branch guard is redundant (a false memo throws inside the pcall), so
    # the rule lives per button.
    ("buttons the engine greyed lit by the court", U,
     """                if not mine[c:Id()] then return end
                local to = ICUI.EDICT_LIVE[c:CurrentState()]""",
     """                local to = ICUI.EDICT_LIVE[c:CurrentState()]"""),
    ("asking about edicts makes a court", U,
     """    local court = IC.state[me]
    if not court or not IC.court_rolled(me) then return nil end""",
     """    local court = IC.court(me)
    if not IC.court_rolled(me) then return nil end"""),
    ("closing the court leaves the edicts as they were", U,
     """    ICUI.refresh_edicts()
end""",
     """end"""),
    ("a selected settlement's edicts never judged", U,
     """        cm:callback(function() ICUI.apply_edict_lock(region) end, delay)""",
     """        cm:callback(function() end, delay)"""),
    # No persist argument: the engine drops the listener after the first
    # settlement the player selects.
    ("the settlement listener registered once-only", U,
     """        cm:callback(function() ICUI.apply_edict_lock(region) end, delay)
    end
end, true)""",
     """        cm:callback(function() ICUI.apply_edict_lock(region) end, delay)
    end
end)"""),
    # THE REASON beside the grey buttons.
    ("no note beside the grey edicts", U,
     """    ICUI.edict_note(verdict == "grey")
""",
     ""),
    ("the governor note left up on a settlement the court has no say in", U,
     """    ICUI.edict_note(verdict == "grey")
""",
     """    if verdict then ICUI.edict_note(verdict == "grey") end
"""),
    ("the governor note made and never shown", U,
     """        note:SetVisible(true)
    end)
    return note""",
     """    end)
    return note"""),
    ("a second governor note made on every selection", U,
     """    local note = comp(ICUI.EDICT_NOTE, stack)
    if not show then""",
     """    local note = nil
    if not show then"""),
    ("the governor note sized to the plate, not its words", U,
     """    ICUI.resize(c, tw + side * 2, h)""",
     """    ICUI.resize(c, ICUI.STANDING_W, h)"""),
    ("the governor note back on the standing plate", U,
     """        pcall(function() stack:CreateComponent(ICUI.EDICT_NOTE, ICUI.PATH_EDICT_NOTE) end)""",
     """        pcall(function() stack:CreateComponent(ICUI.EDICT_NOTE, ICUI.PATH_STANDING) end)"""),
    ("the governor note at the standing plate's height", U,
     """        ICUI.fit_words(note, ICUI.EDICT_NOTE_TEXT, ICUI.EDICT_NOTE_H)""",
     """        ICUI.fit_words(note, ICUI.EDICT_NOTE_TEXT, ICUI.STANDING_H)"""),
    # The note's width comes from WidthOfTextLine; TextDimensionsForText runs its
    # edges too long.
    ("the governor note sized off TextDimensionsForText", U,
     """    local tw = c:WidthOfTextLine(text)""",
     """    local tw = c:TextDimensionsForText(text)"""),
    ("the governor note's words left to the engine's centring", U,
     """    c:SetTextHAlign("left")
    c:SetTextXOffset(side, side)
""",
     ""),
    # THE INFLUENCE PLATE: its background fits its words, and it follows the
    # panel's man, not the map's selection.
    ("the influence plate reads the map's selection, not the panel's man", U,
     """    local cqi = ICUI.standing_cqi()""",
     """    local cqi = ICUI.selected_cqi"""),
    ("the influence plate with no fallback when the panel says nothing", U,
     """        if cqi then return cqi end
    end
    return ICUI.selected_cqi""",
     """        if cqi then return cqi end
    end
    return nil"""),
    ("the influence plate not redrawn when the panel's man changes", U,
     """        cm:callback(function() ICUI.show_standing() end, delay)""",
     """        cm:callback(function() end, delay)"""),
    ("the influence plate's switch listener registered once-only", U,
     """        cm:callback(function() ICUI.show_standing() end, delay)
    end
end, true)""",
     """        cm:callback(function() ICUI.show_standing() end, delay)
    end
end)"""),
    ("the influence plate left at its file width", U,
     """    pcall(ICUI.fit_words, plate, ICUI.standing_text(faction, cqi), ICUI.STANDING_H)""",
     """    set_text(plate, ICUI.standing_text(faction, cqi))"""),
    # The governor note at any screen resolution.
    ("the governor note pinned where the stack sits at 1920x1080", U,
     """        note:MoveTo(x + w + ICUI.EDICT_NOTE_GAP, y + math.floor((h - ICUI.EDICT_NOTE_H) / 2))""",
     """        note:MoveTo(314, 1036)"""),
    ("the governor note left a gap from the edict frame", U,
     """ICUI.EDICT_NOTE_GAP = -2""",
     """ICUI.EDICT_NOTE_GAP = 6"""),

    # Only a seat somebody can take pulses.
    ("every empty seat pulses the button again", U,
     '''        offices = s.fillable > 0 or #s.ending > 0,''',
     '''        offices = s.empty > 0 or #s.ending > 0,'''),
    ("every empty seat listed as waiting", U,
     '    if s.fillable > 0 then\n        waiting[#waiting + 1] = string.format("Seats ready to fill: %d. See Offices.",',
     '    if s.empty > 0 then\n        waiting[#waiting + 1] = string.format("Seats ready to fill: %d. See Offices.",'),
    ("the summary drops the empty seats it cannot fill", U,
     '''    lines[#lines + 1] = string.format("Empty seats: %d of %d.", s.empty, #R.OFFICES)''',
     '''    if s.fillable > 0 then
        lines[#lines + 1] = string.format("Empty seats: %d of %d.", s.empty, #R.OFFICES)
    end'''),

    # Why the button pulses.
    ("the court button's tooltip with no heading saying why it pulses", U,
     '''        lines[1] = "[[col:yellow]]Waiting for you:[[/col]]"''',
     '''        lines[1] = ""'''),
    ("the waiting heading shown on a still button", U,
     '''    if #waiting > 0 then
        lines[1] = "[[col:yellow]]Waiting for you:[[/col]]"''',
     '''    if true then
        lines[1] = "[[col:yellow]]Waiting for you:[[/col]]"'''),
    ("a party leaving listed without the tab to open", U,
     '"%s leaves in %d turn%s. See Court."',
     '''"%s leaves the court in %d turn%s."'''),
    ("the reasons listed after the summary", U,
     """    if #waiting > 0 then
        lines[1] = "[[col:yellow]]Waiting for you:[[/col]]"
        for i = 1, #waiting do lines[#lines + 1] = waiting[i] end
        lines[#lines + 1] = ""
    end
    if court.houses[IC.CROWN] then
        lines[#lines + 1] = string.format("Your party holds %s%% of the court: %s.",
            ICUI.cost(IC.control(faction)), ICUI.band_name(IC.control_band(faction)))
    end""",
     """    if court.houses[IC.CROWN] then
        lines[#lines + 1] = string.format("Your party holds %s%% of the court: %s.",
            ICUI.cost(IC.control(faction)), ICUI.band_name(IC.control_band(faction)))
    end
    if #waiting > 0 then
        lines[#lines + 1] = "[[col:yellow]]Waiting for you:[[/col]]"
        for i = 1, #waiting do lines[#lines + 1] = waiting[i] end
    end"""),

    # The court button between turns.
    ("the court button lit whoever's turn it is", U,
     """    if live == nil then live = ICUI.player_turn() end""",
     """    if live == nil then live = true end"""),
    ("a failed turn query locks the player out of the court", U,
     """        return cm:model():world():is_factions_turn_by_key(ICUI.player())
    end)
    if not ok then return true end""",
     """        return cm:model():world():is_factions_turn_by_key(ICUI.player())
    end)
    if not ok then return false end"""),
    ("the court button's pulse stopped after the grey", U,
     """        ICUI.pulse_opener(false)
        pcall(function() button:SetDisabled(true) end)
        pcall(ICUI.grey_look, button, true)""",
     """        pcall(function() button:SetDisabled(true) end)
        pcall(ICUI.grey_look, button, true)
        ICUI.pulse_opener(false)"""),
    ("the court button left pulsing between turns", U,
     """        ICUI.pulse_opener(false)
        pcall(function() button:SetDisabled(true) end)""",
     """        pcall(function() button:SetDisabled(true) end)"""),
    ("the court opened by a click between turns", U,
     """            if comp(ICUI.PANEL) or ICUI.player_turn() then ICUI.toggle() end""",
     """            ICUI.toggle()"""),
    ("an open court not shut by its button between turns", U,
     """            if comp(ICUI.PANEL) or ICUI.player_turn() then ICUI.toggle() end""",
     """            if ICUI.player_turn() then ICUI.toggle() end"""),
    ("the court left open when the turn ends", U,
     """    if comp(ICUI.PANEL) then pcall(ICUI.close, true) end
    ICUI.gate_opener(false, false)""",
     """    ICUI.gate_opener(false, false)"""),
    ("the turn end greys by the model, which still calls it his turn", U,
     """    ICUI.gate_opener(false, false)
end, true)""",
     """    ICUI.gate_opener(false)
end, true)"""),
    ("any faction's turn end greys the court button", U,
     """    if faction:name() ~= ICUI.player() then return end
    if comp(ICUI.PANEL) then pcall(ICUI.close, true) end""",
     """    if comp(ICUI.PANEL) then pcall(ICUI.close, true) end"""),
    ("the turn-end listener registered once-only", U,
     """    ICUI.gate_opener(false, false)
end, true)""",
     """    ICUI.gate_opener(false, false)
end)"""),

    # The help page.
    # THE BUTTON LEFT AT THE END OF THE 600px BOX, when the plate is sized to
    # its words and ends hundreds of pixels short of it.
    ("the help button left where the title's box ends, not its plate", U,
     """        help:MoveTo(px + tx + tw + h[1] - (t[1] + t[3]), py + h[2])""",
     """        help:MoveTo(px + h[1], py + h[2])"""),
    # A SECOND PRESS THAT ALWAYS LANDS ON THE COURT, wherever it was opened.
    ("the help page closing onto the court and not the tab it came from", U,
     """        ICUI.view = ICUI.help_back or "court"
    else""",
     """        ICUI.view = "court"
    else"""),
    # A NAME THE MODEL LACKS FILLED WITH NOTHING, and the sentence reads on
    # with a hole where its number was.
    ("a help number the model lacks filled in blank", U,
     """        if type(v) ~= "number" then return nil end""",
     """        if type(v) ~= "number" then return "" end"""),
    # THE NUMBERS LEFT PLAIN.
    ("a help number drawn in the sentence's own colour", U,
     """        return string.format("[[col:%s]]%s[[/col]]", ICUI.SORT_LIT, tostring(v))""",
     """        return tostring(v)"""),
    # A TOPIC CLICK THAT CHANGES NOTHING.
    ("a help topic click that keeps the old page", U,
     """            ICUI.help_page = ICUI.HELP_TOPIC_INDEX[id]
            ICUI.refresh()""",
     """            ICUI.refresh()"""),
    # A SHORT TOPIC DRAWN OVER THE LAST ONE'S TAIL: the spare lines kept.
    ("a short help topic under the last topic's leftover lines", U,
     """            show(c, lines[i] ~= nil)""",
     """            show(c, true)"""),
    # THE SPARE TOPIC BUTTONS SHOWN, as blank tabs at the foot of the list.
    ("the spare help topic buttons drawn blank", U,
     """            show(c, topic ~= nil)""",
     """            show(c, true)"""),
    # THE WRONG TOPIC LIT, or all of them.
    ("every help topic lit at once", U,
     """            ICUI.light_plate(c, i == page, topic and""",
     """            ICUI.light_plate(c, true, topic and"""),
    # THE PAGE'S CARD LEFT OVER EVERY OTHER TAB.
    ("the help page left on screen over the other tabs", U,
     """        show(comp(name, panel), view == "help" and not ICUI.pick)""",
     """        show(comp(name, panel), true)"""),
    # THE LIST ROWS LEFT UNDER THE HELP PAGE.
    ("the last tab's list left under the help page", U,
     """    ICUI.fill_rows(panel, {}, "help")
    local page = ICUI.help_page""",
     """    local page = ICUI.help_page"""),

    # A RISING LEFT ON ITS SLEEPING PERSONALITY (a rebel faction must be
    # aggressive), and the same call aimed at the court it left.
    ("a rebellion left with the personality of a sleeping faction", M,
     """                cm:force_change_cai_faction_personality(rebels, IC.rebel_personality(faction_key))""",
     """                local _ = IC.rebel_personality(faction_key)"""),
    ("the court that was rebelled against made the aggressive one", M,
     """                cm:force_change_cai_faction_personality(rebels, IC.rebel_personality(faction_key))""",
     """                cm:force_change_cai_faction_personality(faction_key, IC.rebel_personality(faction_key))"""),

    # THE WRONG FACTION OF THE TWO IN SCOPE. faction_key is the court that was
    # rebelled against, is an upvalue here, and is the argument the war
    # declaration's first position takes - so the two calls read alike and one of
    # them makes the victim the villain.
    ("the court that was rebelled against marked as the threat", M,
     """                local f = cm:get_faction(rebels)
                if f and f ~= false then
                    cm:set_base_strategic_threat_score(f, IC.TUNE.rebel_threat)""",
     """                local f = cm:get_faction(faction_key)
                if f and f ~= false then
                    cm:set_base_strategic_threat_score(f, IC.TUNE.rebel_threat)"""),

    # Which heroes go.
    # THE LORDLY GUARD DROPPED. A lord whose subtype is on the hero whitelist -
    # the Castellan is on it, as an engineer - would be spawned as an AGENT,
    # his twenty-stack handed to nobody, and every check about the right men
    # leaving would still pass, because he does leave.
    ("a lord put on the rebels' side as an agent", M,
     """    if IC.is_lordly(character) then return false end
    if IC.is_legend(character) then return false end
    local key = nil
    pcall(function() key = character:character_subtype_key() end)
    return in_any_race("REBEL_HEROES", key) ~= nil""",
     """    if IC.is_legend(character) then return false end
    local key = nil
    pcall(function() key = character:character_subtype_key() end)
    return in_any_race("REBEL_HEROES", key) ~= nil"""),

    # THE WHITELIST DROPPED FOR ANY HERO AT ALL. It reads as generosity - why
    # should a Hobgoblin Khan not join a rebellion - and it deletes him from the
    # campaign: he is killed here and spawn_agent_at_position is handed a nil
    # agent type, so nothing is made there.
    ("any hero at all taken off the board to defect", M,
     """    return in_any_race("REBEL_HEROES", key) ~= nil
end""",
     """    return key ~= nil
end"""),

    # THE CEILING DROPPED. It is the one clamp the heroes have - a party of
    # wizards otherwise arrives whole - and it looks redundant beside the three
    # the lords carry.
    ("every hero in the party walking out at once", M,
     """    local taking = math.min(#leavers, IC.TUNE.rebel_heroes_max)""",
     """    local taking = #leavers"""),

    # THE HERO GIVEN AND NOT TAKEN. The rebellion gains a wizard and the player
    # loses nothing, which is the same mistake as a secession with no war: it
    # reads as working, because a hero does appear on the other side.
    ("a hero who changes sides and stays on yours as well", M,
     """                pcall(function() cm:kill_character(man.cqi, false) end)
""",
     """"""),

    # What a rebellion arrives with.
    # THE LORD COUNTED TWICE. Twenty is the army and nineteen is the roster,
    # because the general it is created with holds the twentieth slot - and
    # "full roster army (20)" is how the rule reads, so this is the number
    # somebody types.
    ("a rebel army one unit over what a stack holds", M,
     """    rebel_units         = 19,""",
     """    rebel_units         = 20,"""),

    # THE OLD RAIDING PARTY. Six units reads as a tuning choice rather than a
    # defect right up until the party that took eight provinces off you turns
    # up with six units of warriors.
    ("a rebellion that arrives as a raiding party again", M,
     """    rebel_units         = 19,""",
     """    rebel_units         = 6,"""),

    # What they are worth.
    # THE HEAL DROPPED. It looks redundant beside a force that was only just
    # created - and a force created on top of a siege, or joining a faction
    # already at war, is not at full health.
    ("a rebellion mustered at whatever health it happened to have", M,
     """                pcall(function() cm:heal_military_force(force) end)""",
     """                local _ = force"""),

    # THE THIRD ARGUMENT DROPPED. Without it the second argument is raw
    # EXPERIENCE POINTS rather than a level, so a lord meant to arrive at level
    # five arrives at level one with five points - and the call still returns.
    ("a lord given his level as raw experience points", M,
     """                    cm:add_agent_experience(
                        look, level or IC.TUNE.rebel_lord_level, true)""",
     """                    cm:add_agent_experience(
                        look, level or IC.TUNE.rebel_lord_level)"""),

    # THE CHARACTER PASSED WHERE THE FORCE BELONGS. They sit one line apart in
    # the same loop and three of the four calls beside it take the character.
    ("the character handed to a call that wants his force", M,
     """                pcall(function() cm:heal_military_force(force) end)""",
     """                pcall(function() cm:heal_military_force(man) end)"""),

    # Who gets it.
    # THE SNAPSHOT IGNORED. It reads as defensive clutter - the faction was
    # dormant a moment ago, who else could be in it - and a fifth party joining
    # a rebellion already running then re-levels every lord that rebellion
    # already had, because add_agent_experience ADDS.
    ("every lord of a running rebellion levelled again on each secession", M,
     """                and not before[man:command_queue_index()] then""",
     """                then"""),

    # The walls.
    # A REGION KEY WHERE A CQI BELONGS. Every other region call in this file
    # takes a key, CA's docs say "the region is specified by cqi" in one line of
    # prose, and passing the key is a silent no-op in game.
    ("a garrison healed by region key, which does nothing", M,
     """            if pcall(function() cm:heal_garrison(region:cqi()) end) then""",
     """            if pcall(function() cm:heal_garrison(region:name()) end) then"""),

    # What the men who left are carrying.
    # THE TYPED ROSTER PREFERRED OVER WHAT HE HAD. It reads as the safe default -
    # a list this file checked against main_units beats keys read off whatever
    # the player happens to be fielding - and it is the whole of the mod support
    # thrown away: a rebellion out of a court full of a unit mod's troops arrives
    # with vanilla Chaos Dwarf infantry.
    ("a rebellion that ignores the army it walked out of", M,
     """    if kit and #kit > 0 then""",
     """    if false then"""),

    # THE GENERAL'S OWN UNIT LEFT IN. has_unit_commander is one line and skipping
    # it looks like tidying: the unit IS one of his, it IS in his force's list,
    # and create_force_with_general makes the general separately - so the
    # rebellion marches with a second lord standing in the ranks.
    ("a lord's own unit handed back to him as a soldier", M,
     """                if not led and key and key ~= "" then""",
     """                if key and key ~= "" then"""),

    # THE GARRISON CHECK DROPPED. military_force_list counts garrisons and the
    # guard looks redundant beside a loop that is obviously about armies - and
    # the rebellion marches out of somebody's walls wearing wall troops.
    ("a rebellion mustered out of the nearest garrison", M,
     """        if citizenry then return end""",
     """        local _ = citizenry"""),

    # The Hashut draft: a rising is his own army, if he brought one, filled out
    # off IC.REBEL_DRAFT.
    ("every slot of a rebel army rolled for the first role", M,
     """        local role = R.REBEL_DRAFT[(i - 1) % #R.REBEL_DRAFT + 1]""",
     """        local role = R.REBEL_DRAFT[1]"""),
    ("the two-of-a-kind cap never applied", M,
     """            if (used[u[1]] or 0) < IC.REBEL_UNIT_CAP then""",
     """            if true then"""),
    ("the dice ignored and the first unit of each role taken", M,
     """                roll = roll - u[2]""",
     """                roll = roll - total"""),
    ("a lord's short army left short", M,
     """    local extra = IC.rebel_draw(want - #kit, faction_key)""",
     """    local extra = {}"""),

    # What he is worth.
    # THE FLAT NUMBER BACK. It reads as the tidier rule (every rebel lord the
    # same, one knob to tune) and throws away the rule that a rebel lord keeps
    # the rank he left the faction at.
    ("every rebel lord arriving at the same flat level", M,
     """    return rank""",
     """    return IC.TUNE.rebel_lord_level"""),

    # What the diplomacy screen says.
    # ONE PENALTY AND DONE, which is what the call looks like it is for and what
    # every CA use of it does. It is wrong here for a reason that is invisible
    # at the call site: the magnitude of a PENALTY_XXXLARGE lives in the DB, so
    # one application moves the number by an amount this file cannot know, and
    # the attitude it has to cross starts wherever the pair happens to be.
    ("a rebellion soured once and hoped for the best", M,
     """    local n = 0
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
    return n""",
     """    pcall(function()
        cm:apply_dilemma_diplomatic_bonus(rebels, other,
                                          IC.TUNE.rebel_relation_step)
    end)
    return 1"""),

    # ONE WAY ONLY: each half of the souring dropped. The rebels' own regard is
    # the number on the player's diplomacy screen; the others' regard for the
    # rebels is the other half of the rule.
    ("the rebels soured on nobody, only disliked", M,
     """        pcall(function()
            cm:apply_dilemma_diplomatic_bonus(other, rebels,
                                              IC.TUNE.rebel_relation_step)
        end)""",
     """"""),
    ("the rebels disliking everyone and disliked by nobody", M,
     """        pcall(function()
            cm:apply_dilemma_diplomatic_bonus(rebels, other,
                                              IC.TUNE.rebel_relation_step)
        end)
        n = n + 1""",
     """        n = n + 1"""),

    # THE EDICT RELIGHT BY ID: a relight that gives back every inactive button
    # frees the engine's own locks with the court's.
    ("the relight giving back every inactive edict", U,
     """                if not mine[c:Id()] then return end""",
     """"""),
    ("the grey pass counting the engine's lock as its own", U,
     """                if not to and not mine[id] then return end""",
     """"""),

    # THE COMPARISON THE WRONG WAY ROUND. Attitude runs from -230 to +230 and
    # "sour enough" is a number BELOW the target, which reads backwards to
    # anyone used to a loyalty or a score - so this is the sign error somebody
    # makes once. It breaks on the first read and applies nothing at all.
    ("the souring loop stopping as soon as they are still friends", M,
     """        if now and now <= IC.TUNE.rebel_relation then break end""",
     """        if now and now >= IC.TUNE.rebel_relation then break end"""),

    # THE COURT AND NOBODY ELSE. The war goes to the court the party left, and
    # in an AI secession that is not the player - who is the one reading the
    # number. This is the same hole the threat score fills, one layer up, and
    # it looks complete without the second half.
    ("a rebellion soured only against the court it left", M,
     """    local ok, human = pcall(function() return cm:get_human_factions() end)
    if ok and human then
        for i = 1, #human do targets[#targets + 1] = human[i] end
    end""",
     """"""),

    # THE SELF-CHECK DROPPED. It reads redundant - why would anybody sour a
    # faction against itself - until IC.rebel_faction_for hands back the human's
    # own key, which is exactly what it does for a house rising again into its
    # own faction.
    ("a faction soured against itself", M,
     """    if not rebels or not other or rebels == other then return 0 end""",
     """    if not rebels or not other then return 0 end"""),

    # The card a rotting party raises.
    # KEYED ON THE STATE INSTEAD OF THE CROSSING. This is the simpler condition
    # and it is right on the turn the party crosses; it is wrong on every turn
    # after, and drift_loyalty moves every house every turn, so it is a card a
    # turn for the rest of the campaign.
    ("a disloyalty card raised every turn a party stays unhappy", M,
     """    if slug ~= IC.CROWN
       and was > IC.TUNE.loyalty_warn
       and house.loyalty <= IC.TUNE.loyalty_warn then""",
     """    if slug ~= IC.CROWN
       and house.loyalty <= IC.TUNE.loyalty_warn then"""),

    # THE CROWN GUARD DROPPED. The player's own house sits in the same table as
    # the rivals, so without this he is warned that he is turning against
    # himself - the same fault tick_secession already carries a guard for.
    ("the player warned that his own house has turned on him", M,
     """    if slug ~= IC.CROWN
       and was > IC.TUNE.loyalty_warn""",
     """    if was > IC.TUNE.loyalty_warn"""),

    # THE WARNING MOVED ONTO THE SECESSION LINE. It looks like tidying - one
    # threshold instead of two - and it costs the warning its whole purpose:
    # it would arrive with the countdown rather than in front of it, and for a
    # party too small to ever count down it would arrive at the floor.
    ("the disloyalty warning set at the secession line", M,
     """    loyalty_warn        = 35,""",
     """    loyalty_warn        = 20,"""),

    # THE READ-BACK KEPT AND THE STOPPING THROWN AWAY. This is what somebody
    # writes on deciding the loop may as well always run its full course - the
    # rebellion still ends up hostile, so the fault is invisible to every check
    # that only looks at the number. What it costs is every pair paying the cap
    # in calls whatever it needed, which is the thing the read-back is for.
    ("a rebellion soured to the cap whether it needed it or not", M,
     """        if now and now <= IC.TUNE.rebel_relation then break end""",
     """"""),

    # THE BOUNDARY, ONE OFF. A party crossing exactly ONTO the line is the
    # common case - drift moves loyalty one point a turn - so this misses the
    # turn it lands and then fires on every turn after, which is both halves of
    # the rule wrong from a single character.
    # THE CAP, ONE OVER. Removing the cap outright does not fail, it HANGS (a
    # stale read never reaches the target), and a hang takes this whole runner
    # down. So the cap is mutated by an off-by-one instead: it terminates, it
    # leaves the ordinary case untouched at exactly the count it needed, and it
    # is the only mutant the stale-read check sees on its own.
    ("the souring cap off by one", M,
     """    while n < (max_steps or IC.TUNE.rebel_relation_max) do""",
     """    while n <= (max_steps or IC.TUNE.rebel_relation_max) do"""),

    ("a disloyalty warning that misses the turn a party lands on the line", M,
     """       and house.loyalty <= IC.TUNE.loyalty_warn then""",
     """       and house.loyalty < IC.TUNE.loyalty_warn then"""),

    # The Crown coming apart.
    # A SHARE MINTED INSTEAD OF MOVED. add_house already hands out weight_start
    # and this reads like the tidy-up nobody needed - it is invisible on the new
    # party's own card, which shows the right number, and it silently demotes
    # every OTHER party in the court because share is weight over TOTAL weight.
    ("a breakaway minted out of thin air rather than carved off the Crown", M,
     """    crown.weight = math.max(1, (crown.weight or 0) - IC.TUNE.splinter_weight)""",
     """"""),

    # THE RECOVERY READ AS A GIFT AND DELETED. It is a termination proof: the
    # Crown sits below the line, splits again next turn, and again, until the
    # interest pool is empty - a court of nine parties in eight turns, each one
    # taking another piece of the player's share.
    ("the Crown left below its own line after the split", M,
     """    IC.move_loyalty(faction_key, IC.CROWN, IC.TUNE.loyalty_start - keep)""",
     """"""),

    # SEATED AT THE NEUTRAL NUMBER, which is what add_house does for a party
    # seated by the roll and is wrong for a piece of one: the player would have
    # split his own court and bought a contented ally out of the men who just
    # walked out on him.
    ("a breakaway with no opinion about the thing it just did", M,
     """    if not IC.add_house(faction_key, slug, nil, keep) then return nil end""",
     """    if not IC.add_house(faction_key, slug) then return nil end"""),

    # THE BOUNDARY, ONE OFF. A Crown exactly ON the line is the common case -
    # drift moves loyalty a point at a time - so this never fires on the turn it
    # lands and the card reads SPLITTING at a number that does nothing.
    ("a Crown that has to fall past its line before it comes apart", M,
     """                    <= IC.TUNE.splinter_loyalty""",
     """                    < IC.TUNE.splinter_loyalty"""),

    # THE WEIGHT GATE DROPPED. math.max(1, ...) below looks like it already
    # covers this, and it does not: the floor keeps the Crown's weight legal
    # while the breakaway still takes a full splinter_weight it was never paid,
    # which mints share exactly as the first mutant does.
    ("a Crown spent past the bottom and split anyway", M,
     """                and (crown.weight or 0) > IC.TUNE.splinter_weight""",
     """"""),

    # THE EMPTY-POOL GUARD DROPPED. A court where every interest is already
    # seated - which a confederation can reach - has nothing to splinter into.
    ("a breakaway seated into a court with no chair left", M,
     """                and #pool > 0""",
     """"""),

    # SEATED BUT NEVER NAMED. roll_court calls add_house, name_party and
    # roll_party_traits together; this is the second place a party can be seated
    # and dropping either of the last two is a card with a blank plate where
    # every other party has a name.
    ("a breakaway nobody has a name for", M,
     """    IC.name_party(faction_key, slug)
    IC.roll_party_traits(faction_key, slug)
    local house = court.houses[slug]""",
     """    local house = court.houses[slug]"""),

    # THE MOST EXPENSIVE THING THE CROWN CAN DO TO ITSELF, in silence. The
    # record keeps it either way; the card is the half that reaches a player who
    # did not open the panel.
    ("a court that comes apart and says nothing about it", M,
     """    IC.feed(faction_key, "splinter")""",
     """"""),

    # AND THE WHOLE THING UNREACHABLE. A correct function that nothing calls
    # passes every check written against the function itself.
    ("your own house coming apart on no turn at all", M,
     """    local warned = IC.tick_secession(faction_key)
    IC.splinter(faction_key)
""",
     """    local warned = IC.tick_secession(faction_key)
"""),

    # THE TWO PASSES SWAPPED. The order looks arbitrary and it is not: a
    # breakaway arrives carrying the Crown's grievance, so a countdown running
    # after it opens against a house the player has not had one turn to answer.
    # MOVED, NOT DUPLICATED, and that distinction is the whole mutant. With a
    # count in front of the split, a second IC.splinter inserted above the
    # countdown only advances the count and the ORIGINAL call below still lands
    # the split, so the ordering never changes and the mutant survives.
    ("a party judged on the turn it was born", M,
     """    local warned = IC.tick_secession(faction_key)
    IC.splinter(faction_key)""",
     """    IC.splinter(faction_key)
    local warned = IC.tick_secession(faction_key)"""),

    # THE LINE ONE POINT TOO HIGH. Dropping the gate entirely is also a fault,
    # but the recovery check catches that one first - so this is the mutation
    # aimed at the check about the line itself, and it is the likelier mistake
    # anyway: the mood ladder says SPLINTERING at <= splinter_loyalty and a gate
    # written to agree with it off by one splits a Crown that is still above it.
    ("a Crown that comes apart one point above its own line", M,
     """                    <= IC.TUNE.splinter_loyalty""",
     """                    <= IC.TUNE.splinter_loyalty + 1"""),

    # THE RECORD HALF DROPPED. The card reaches a player who did not open the
    # panel; the record is what he reads when he does, and the Record tab is
    # where every other thing the court did to itself is written down.
    ("your own house coming apart, remembered by nobody", M,
     """    IC.log(faction_key, "splinter", slug, nil, house.weight)""",
     """"""),

    # What the player's own card says: never PLOTTING, a threat from the one
    # house no plot can be aimed at.
    # Who may be the face of a house.
    # THE FILTER NEVER APPLIED: the highest-standing man speaks for the house
    # whatever he is.
    ("a greenskin fronting a Chaos Dwarf house", M,
     """        if IC.may_speak(faction_key, lords[i]) then return lords[i] end""",
     """        if lords[i] then return lords[i] end"""),

    # THE RULE REACHING THE THRONE, which is the plausible over-application: a
    # reader who sees "no greenskin fronts a house" and files the ruler under
    # the same sentence. He is not fronting the faction, he IS it.
    ("the rule taking the ruler's own face off his own card", M,
     """        local seated = IC.faction_leader_cqi(faction_key)
        if seated and IC.house_of_cqi(faction_key, seated) == IC.CROWN then
            return seated
        end""",
     """        local seated = IC.faction_leader_cqi(faction_key)
        if seated and IC.house_of_cqi(faction_key, seated) == IC.CROWN
           and IC.may_speak(faction_key, seated) then
            return seated
        end"""),

    # AND THE FALLBACK PUT BACK. "Nobody qualifies, so use the first one
    # anyway" is the instinct that makes the rule cosmetic - it would hold in
    # every case except the one where it matters.
    ("a house falling back to the thrall it just refused", M,
     """        if IC.may_speak(faction_key, lords[i]) then return lords[i] end
    end
    return IC.party_colonel(faction_key, slug)""",
     """        if IC.may_speak(faction_key, lords[i]) then return lords[i] end
    end
    return lords[1] or IC.party_colonel(faction_key, slug)"""),

    # THE UNREADABLE SUBTYPE TREATED AS GUILTY. Silences a house on the
    # strength of a call that did not answer.
    ("an unnamed subtype struck off as a thrall", M,
     """    if not key or key == "" then return true end""",
     """    if not key or key == "" then return false end"""),

    # THE FILTER ONE FUNCTION TOO LOW. The card looks right and the politics
    # are gone: he stops counting toward his house's size, its weight and the
    # men who walk out with it.
    ("a thrall filtered out of his house instead of off its card", M,
     """        if man and not man:is_null_interface()
                and IC.house_of_character(man, faction_key) == slug then""",
     """        if man and not man:is_null_interface()
                and IC.may_speak(faction_key, man:command_queue_index())
                and IC.house_of_character(man, faction_key) == slug then"""),

    # AND THE SAME MISTAKE ONE BRANCH LOWER, which the check above cannot see:
    # members is counted before this branch, so the house still reads the right
    # size and the right speaker while the man vanishes out of its ORDER - and
    # the order is what the secession reads to decide who walks.
    ("a thrall dropped out of his house's order", M,
     """            if IC.is_lordly(man) then
                local cqi = man:command_queue_index()""",
     """            if IC.is_lordly(man)
               and IC.may_speak(faction_key, man:command_queue_index()) then
                local cqi = man:command_queue_index()"""),

    # What a trait says it is worth.
    # THE SENTENCE RETUNED AND THE FUNCTION LEFT ALONE. This is the direction
    # somebody takes when a trait "feels weak" and the card is the thing in
    # front of them - the words move, the drift does not, and the player plans
    # around a number that is never paid.
    ("a trait promising more than its function pays", M,
     """     rule = "-1 a turn",""",
     """     rule = "-3 a turn","""),

    # AND THE OTHER DIRECTION: the function retuned and the sentence left
    # behind. Same fault, opposite half, and a check that only walked one way
    # would never see it.
    ("a trait paying something its sentence never mentions", M,
     """     n = function(ctx) return ctx.govs > 0 and 1 or -2 end},""",
     """     n = function(ctx) return ctx.govs > 0 and 1 or -3 end},"""),

    # Ambition.
    # THE AMBITIOUS BAND FLATTENED. The band is the model's one owner of this
    # multiplier; changing it to Steady's value leaves the marker and the roll
    # intact while removing the incentive a player is meant to see in influence.
    ("ambition's Ambitious band flattened to Steady's factor", M,
     """    ambitious = {factor = 125, roll = 25},""",
     """    ambitious = {factor = 100, roll = 25},"""),

    # THE SCALE READ AS A UNIT. A 400-standing Ambitious courtier contributes
    # five points, not 500; the harness checks both the live house arithmetic
    # and the number promised by the standing-plate tooltip.
    ("ambition standing scale changed from 100 to 1", M,
     """    ambition_standing_per_weight = 100,""",
     """    ambition_standing_per_weight = 1,"""),

    # THE SAVED BAND REROLLED. Existing courtiers must preserve their slug on
    # every reconciliation; only a missing saved value is allowed to consume a
    # random roll.
    ("ambition rerolled whenever stamp_ambition runs", M,
     """    if not slug then
        slug = IC.roll_ambition()
        court.ambition[cqi] = slug
        moved = true
    end""",
     """    if true then
        slug = IC.roll_ambition()
        court.ambition[cqi] = slug
        moved = true
    end"""),

    # FIELD EIGHT IS THE SAVE'S AMBITION MAP. Dropping it leaves an old-looking
    # seven-field court that restamps everyone after a load.
    ("ambition omitted from field 8 of IC.pack", M,
     """                 join(logged, ";"), join(prov, ";"), join(ambition, ";"),""",
     """                 join(logged, ";"), join(prov, ";"), "","""),

    # A CQI that has left the faction must lose its band with its standing; it
    # otherwise remains serialized forever and can contaminate a reused CQI.
    ("ambition left behind when IC.income prunes departed courtiers", M,
     """    for cqi in pairs(court.ambition or {}) do
        if not alive[cqi] then court.ambition[cqi] = nil end
    end""",
     """    local _ = court.ambition"""),

    # Reconciliation has to remove an old marker before putting the saved one
    # back. Adding the saved trait alone leaves one courtier visibly wearing
    # two incompatible bands.
    ("ambition reconciliation leaves a wrong marker trait in place", M,
     """        if key ~= want and character:has_trait(key) then
            cm:force_remove_trait(lookup, key)
            moved = true
        end""",
     """        if false then
            cm:force_remove_trait(lookup, key)
            moved = true
        end"""),

    # Office and governor weight is saved, but members are a live contribution.
    # Omitting it makes every ambition band cosmetic even though all UI calls
    # still have the correct faction-aware signature.
    ("ambition member weight omitted from IC.house_weight", M,
     """    return house.weight + (house.gov_weight or 0)
        + IC.member_weight(faction_key, slug)""",
     """    return house.weight + (house.gov_weight or 0)"""),

    # THE PRE-AMBITION UI SIGNATURE. Passing the court table to the new model
    # signature produces a zero-share mirror rather than an engine error, so
    # the dial's displayed value is what proves this contract.
    ("ambition UI call restored the old IC.share(court, slug) signature", U,
     """    set_text(cell, string.format("%d%%",
                                 math.floor(IC.share(faction, slug) + 0.5)))""",
     """    set_text(cell, string.format("%d%%",
                                 math.floor(IC.share(court, slug) + 0.5)))"""),

    # The tooltip must use the model factor, not recover a number by parsing
    # text. A stale display string is not state and can disagree with the saved
    # band as soon as localization or wording changes.
    ("ambition tooltip recomputes its factor from text instead of the model", U,
     """    local factor = IC.ambition_factor(faction_key, cqi) / 100""",
     """    local factor = tonumber(string.match(name, "%d+")) or 1"""),

    # What Military Doctrine contributes.
    ("edict accepts every active commandment", M,
     """            if IC.governor_edict(faction_key, province_key)
                    == R.MILITARY_DOCTRINE then""",
     """            if IC.governor_edict(faction_key, province_key)
                    ~= nil then"""),

    ("edict query bypasses the active-governor gate", M,
     """function IC.governor_edict(faction_key, province_key)
    if not IC.governor_active(faction_key, province_key) then return nil end""",
     """function IC.governor_edict(faction_key, province_key)
    if false then return nil end"""),

    ("edict bonus ignores the governor's party", M,
     """    for province_key, cqi in pairs(court.govs) do
        if IC.house_of_cqi(faction_key, cqi) == slug then
            govs = govs + 1
            if IC.governor_edict(faction_key, province_key)
                    == R.MILITARY_DOCTRINE then
                doctrine = doctrine + 1
            end
        end
    end""",
     """    for province_key, cqi in pairs(court.govs) do
        if IC.house_of_cqi(faction_key, cqi) == slug then
            govs = govs + 1
        end
        if IC.governor_edict(faction_key, province_key)
                == R.MILITARY_DOCTRINE then
            doctrine = doctrine + 1
        end
    end"""),

    ("edict stacking pays one fixed province", M,
     """            n = doctrine * IC.TUNE.loyalty_military_doctrine,""",
     """            n = IC.TUNE.loyalty_military_doctrine,"""),

    ("edict arithmetic duplicated inside drift loyalty", M,
     """        local terms, snub_key = IC.loyalty_terms(faction_key, slug)
        IC.move_loyalty(faction_key, slug, IC.loyalty_net(terms))""",
     """        local terms, snub_key = IC.loyalty_terms(faction_key, slug)
        local doctrine = 0
        for province_key, cqi in pairs(court.govs) do
            if IC.house_of_cqi(faction_key, cqi) == slug
                    and IC.governor_edict(faction_key, province_key)
                        == IC.MILITARY_DOCTRINE then
                doctrine = doctrine + 1
            end
        end
        IC.move_loyalty(faction_key, slug, IC.loyalty_net(terms)
            + doctrine * IC.TUNE.loyalty_military_doctrine)"""),

    # And whether the cell says any of it.
    # THE LIVE NUMBER DROPPED. The rule alone tells a player what the trait CAN
    # pay; this line is the only thing that tells him what it is paying him now,
    # which for five of the eight is a different number depending on his court.
    ("a trait cell that never says what it is worth today", U,
     """        lines[#lines + 1] = string.format("%s loyalty per turn", ICUI.signed(n))""",
     """"""),

    # AND THE RULE DROPPED, which puts the cell back to a name and a flavour
    # line with no number.
    ("a trait cell back to flavour text and no numbers", U,
     """    if rule and not (n and flat) then lines[#lines + 1] = rule end""",
     """"""),

    # THE FLAT RULE PRINTED UNDER ITS OWN LIVE NUMBER: "-1 loyalty per turn"
    # then "-1 a turn", the tooltip a player reported.
    ("a flat trait rule repeating the live number", U,
     """    if rule and not (n and flat) then lines[#lines + 1] = rule end""",
     """    if rule then lines[#lines + 1] = rule end"""),

    # The effect icon on a trait.
    # THE DECORATION QUIETLY DROPPED. A trait is a term in the loyalty drift and
    # the icon is the only thing on the card that says so; without it the line
    # is a bare word among bare words. gen_ic_ui.py would go on measuring the
    # WIDER string, so the build alone cannot see this; only reading the drawn
    # cell can.
    ("a trait drawn as a bare word again", U,
     """    return string.format("[[img:%s]][[/img]]%s", ICUI.TRAIT_ICON, name)""",
     """    return name"""),

    # AND THE EMPTY CELL DECORATED. Both trait cells are written on EVERY draw
    # because the card pool recycles, so this leaves a picture of nothing on a
    # party with one trait instead of two, and on every party whose leader has
    # just died - which is the case the harness reaches by killing him.
    ("an empty trait cell wearing an icon of nothing", U,
     """    if not name or name == "" then return "" end""",
     """    if not name then name = "" end"""),

    ("the player's own card calling his house a plotter again", U,
     """function ICUI.mood(house, slug)
    if slug == IC.CROWN then""",
     """function ICUI.mood(house, slug)
    if false then"""),

    # THE AI'S THREE LEVERS, one mutant each. All three are exemptions or
    # preferences that a later reader would reasonably think were redundant,
    # which is exactly the shape of edit that gets made and never noticed: the
    # AI's court would still fill, still tick, still look right in the save, and
    # its parties would go back to walking out inside thirty turns.

    # The affinity preference collapsed back to "best man available". This is
    # the one that looks most like a simplification - two passes for what reads
    # as one loop - and it costs the claimed party loyalty_snubbed every time a
    # term turns over.
    ("the AI back to filling seats on standing alone", M,
     """                    if not used[cqi] and ((pass == 1) == affine)
                            and IC.can_appoint(faction_key, office.slug, cqi) then""",
     """                    if not used[cqi]
                            and IC.can_appoint(faction_key, office.slug, cqi) then"""),

    # THE SECOND PASS RUN WHATEVER THE CLAIMANT IS: an outsider takes a seat
    # that is empty or under the rank bar, and that AI party falls.
    ("the AI handing a claimed seat to an outsider again", M,
     """            local passes = court.houses[office.affinity] and 1 or 2""",
     """            local passes = 2"""),

    # BACKGROUNDS BEFORE THE COURT IS ROLLED. roll_court looks redundant here -
    # reconcile_houses calls it on the next line - and without it an AI's first
    # turn puts every starting man in the Crown.
    ("an AI court rolled after its men were dealt", M,
     """    IC.roll_court(faction_key)
    IC.stamp_court(faction_key)
    IC.reconcile_houses(faction_key)
    -- BEFORE ANYTHING READS A SHARE THIS TURN""",
     """    IC.stamp_court(faction_key)
    IC.reconcile_houses(faction_key)
    -- BEFORE ANYTHING READS A SHARE THIS TURN"""),

    # LORDS DEALT EVENLY AGAIN, the rule that left most rivals leaderless.
    ("a lord dealt anywhere while a party has nobody to lead it", M,
     """    local bg = IC.leaderless_bg(character, faction_key, tally)
               or IC.roll_background(faction_key, tally)""",
     """    local bg = IC.roll_background(faction_key, tally)"""),

    # The deal: how men are shared out among the parties.
    # ONE INDEPENDENT ROLL PER MAN: a Conclave start can roll the Chain for all
    # six men who are not lords.
    ("deal: every man rolled at random again", M,
     """    local list = R.BACKGROUNDS[IC.fewest(pool, tally)]
    if not list or #list == 0 then return nil end""",
     """    local list = R.BACKGROUNDS[pool[cm:random_number(#pool, 1)]]
    if not list or #list == 0 then return nil end"""),

    # THE TALLY READ ONCE AND NEVER KEPT, so every man in a pass sees the counts
    # from before it and they all go to the same party.
    ("deal: the tally not kept as men are dealt", M,
     """        tally.count[party] = tally.count[party] + 1
        if IC.can_lead(character) then tally.led[party] = true end""",
     """        if IC.can_lead(character) then tally.led[party] = true end"""),

    # A LEAD FILLED THIS PASS LEFT OPEN, so the lords keep coming to the
    # parties that already have one.
    ("deal: a lead filled this pass left open", M,
     """        if IC.can_lead(character) then tally.led[party] = true end""",
     """"""),

    # GARRISON COMMANDERS LEFT OUT, which is how the party leader fallback
    # could name one and the deal never gave any party one to name.
    ("deal: a garrison commander never sent to an empty lead", M,
     """    if not (IC.is_lordly(character) or IC.is_colonel(character)) then return false end""",
     """    if not IC.is_lordly(character) then return false end"""),

    # CHARACTER_LIST ORDER, so a garrison commander listed first takes the one
    # empty lead from the lord behind him.
    ("deal: whoever comes first on the list dealt first", M,
     """        if a.first ~= b.first then return a.first < b.first end""",
     """"""),

    # A leader put in the field.
    # THE AI GIVEN ARMIES, which recruits from the pool itself.
    ("field: an AI party given an army", M,
     """            elseif not house.fielded and IC.is_human(faction_key) and now > 1
                    and IC.field_leader(faction_key, slug) then""",
     """            elseif not house.fielded and now > 1
                    and IC.field_leader(faction_key, slug) then"""),

    # A FREE ARMY EVERY TIME A PARTY LOSES ITS LEADER.
    ("field: a second army for a party that lost its first", M,
     """            elseif not house.fielded and IC.is_human(faction_key)""",
     """            elseif IC.is_human(faction_key)"""),

    # THE ARMY ON ITS WAY NOT WAITED FOR, so the same turn's next pass puts a
    # second lord in the pool for a party that is about to be led.
    ("field: a lord pooled while the army is on its way", M,
     """            elseif house.fielded == now then
                -- HIS ARMY IS ON ITS WAY: the spawn lands after this frame.
""",
     """"""),

    # -1, -1 TAKEN FOR A PLACE.
    ("field: nowhere to stand taken for somewhere", M,
     """    if not x or x < 0 then return false end""",
     """    if not x then return false end"""),

    # THE FEED OPENED IN THE SAME FRAME, before the spawn's messages arrive.
    ("field: the feed opened again at once", M,
     """    cm:callback(function()
        for i = 1, #IC.QUIET_FEED do
            cm:disable_event_feed_events(false, IC.QUIET_FEED[i], "", "")
        end
    end, 1)""",
     """    for i = 1, #IC.QUIET_FEED do
        cm:disable_event_feed_events(false, IC.QUIET_FEED[i], "", "")
    end"""),

    # AND NEVER OPENED AGAIN, which swallows every character message after.
    # field_leader's own re-open, closed by its 1s delay: the starting members'
    # copy (2s) is a mutant of its own.
    ("field: the feed left shut", M,
     """            cm:disable_event_feed_events(false, IC.QUIET_FEED[i], "", "")
        end
    end, 1)""",
     """        end
    end, 1)"""),

    ("field: the agent messages left on", M,
     """IC.QUIET_FEED = {"wh_event_category_character", "wh_event_category_agent",""",
     """IC.QUIET_FEED = {"wh_event_category_character","""),

    # THE DEAL TRUSTED: his own CharacterCreated deals him to whatever party
    # is empty first, which need not be the one he was made for.
    ("field: the lord left in whatever party his birth dealt him", M,
     """                    if old ~= bg then""",
     """                    if not old then"""),

    ("field: the lord left at rank 1", M,
     """                    if rank > 0 then cm:add_agent_experience(lookup, rank, true) end""",
     """"""),

    # TO, NOT BY: the wrapper calls level_up_agent_rank.
    ("field: the lord raised one rank too many", M,
     """                    if rank > 0 then cm:add_agent_experience(lookup, rank, true) end""",
     """                    if rank > 0 then cm:add_agent_experience(lookup, rank + 1, true) end"""),

    ("field: the save forgetting the army", M,
     """            h.fielded or 0,
            h.gifted or 0,""",
     """            0,
            h.gifted or 0,"""),

    # Lord recruit rank.
    ("rank: a province's own source counted everywhere", M,
     """        local local_ok = here ~= nil and region:province_name() == here""",
     """        local local_ok = true"""),

    ("rank: a factionwide building counted only at home", M,
     """            total = total + row.faction + (local_ok and row.province or 0)""",
     """            total = total + (local_ok and (row.faction + row.province) or 0)"""),

    ("rank: a bundle a region holds ignored", M,
     """            if region:has_effect_bundle(key) then count(row) end""",
     """"""),

    ("rank: skills ignored", M,
     """            if man:has_skill(key) then total = total + row.faction + row.province end""",
     """"""),

    ("rank: technology ignored", M,
     """        if faction:has_technology(key) then total = total + row.faction + row.province end""",
     """"""),

    ("rank: a faction's bundle ignored", M,
     """        if faction:has_effect_bundle(key) then total = total + row.faction + row.province end""",
     """"""),

    # A LORD IN STORE MADE EVERY TURN. A pooled lord is invisible to
    # character_list, so without the flag nothing says one is already waiting.
    ("a lord made in store every turn", M,
     """            elseif not house.stored and not IC.seeding(faction_key) then""",
     """            elseif not IC.seeding(faction_key) then"""),

    # THE FLAG NEVER CLEARED, so a party that loses its leader later never gets
    # another.
    ("a party that found its leader still waiting on one", M,
     """            if led then
                house.stored = nil""",
     """            if led then
                house.stored = house.stored"""),

    # EVERY GOVERNOR JUDGED BY WHERE HE STANDS, which puts six of seven "away"
    # live: garrison commanders and pool lords cannot be where the rule asks.
    ("a garrison commander called away from a province he cannot reach", M,
     """    if IC.kind_of_character(character) ~= "general" then return true end
    local province = province_of_character(character)""",
     """    local province = province_of_character(character)"""),

    # AND HIS DOCTRINE READ OFF HIS OWN REGION, which a pool lord does not have
    # and a colonel has in the wrong province.
    ("a governor with no army reading his edict off where he stands", M,
     """        if IC.kind_of_character(character) ~= "general" then
            return IC.province_edict(faction_key, province_key)
        end""",
     """"""),

    # THE FIRST REGION'S EDICT, whichever province it is in.
    ("a province's edict read off the faction's first region", M,
     """        if region:province():key() == province_key then
            return region:get_active_edict_key()""",
     """        if true then
            return region:get_active_edict_key()"""),

    # THE REPAIR TAKING A MAN WHO HOLDS A POST, which empties an office to fill a
    # party.
    ("an officeholder moved out of the Crown to lead a party", M,
     """            if not busy[cqi] and not taken[cqi] and cqi ~= ruler""",
     """            if not taken[cqi] and cqi ~= ruler"""),

    # A LEGEND MOVED: he is the Crown's whatever his trade, so the party stays
    # leaderless and no lord is made either.
    ("a legend picked to lead a leaderless party", M,
     """        if tier and not IC.is_legend(man) and not IC.fixed_history(man) then""",
     """        if tier and not IC.fixed_history(man) then"""),

    # THE CROWN GIVING UP ITS BEST MAN instead of its least.
    ("the Crown's best idle lord given away first", M,
     """                         or (tier == best_tier and standing < best_standing)) then""",
     """                         or (tier == best_tier and standing > best_standing)) then"""),

    # THE OLD TRADE LEFT ON HIM: two background traits, and whichever is read
    # first decides his party.
    ("a moved lord keeping his old trade too", M,
     """                if old then cm:force_remove_trait(lookup, IC.bg_trait(old)) end
                cm:force_add_trait(lookup, IC.bg_trait(list[cm:random_number(#list, 1)]), false)""",
     """                cm:force_add_trait(lookup, IC.bg_trait(list[cm:random_number(#list, 1)]), false)"""),

    # AND THE LORD PUT IN THE FIELD KEEPING THE TRADE HIS BIRTH DEALT HIM: the
    # Forge comes before the Chain in IC.PARTIES, so he reads as the Forge's.
    ("field: the lord keeping the trade his birth dealt him too", M,
     """                        if old then cm:force_remove_trait(lookup, IC.bg_trait(old)) end""",
     """"""),

    # NO LAST RESORT: a court of legends leaves its parties faceless.
    ("a party with an idle overseer and still no face", M,
     """    return IC.party_colonel(faction_key, slug)
end""",
     """    return nil
end"""),

    # THE OVERSEER BEFORE THE LORD.
    ("an overseer moved over ahead of a lord", M,
     """                    and (not best or tier < best_tier""",
     """                    and (not best or tier > best_tier"""),

    # "RETAINER" FOR "COLONEL": a hero with an army reads as a garrison commander.
    ("a hero with an army taken for a garrison commander", M,
     """                and IC.is_colonel(man)
                and IC.house_of_character(man, faction_key) == slug then""",
     """                and IC.kind_of_character(man) == "retainer"
                and IC.house_of_character(man, faction_key) == slug then"""),

    # EVERY BREAKING PARTY SECEDES AGAIN, nothing to take or not.
    ("a party of nobody seceding with nothing to take", M,
     """        if IC.nothing_to_take(faction_key, seceding[i]) then""",
     """        if false then"""),

    # THE PROVINCE HALF DROPPED: an empty party that would take land dissolves.
    ("an empty party with land to take dissolving", M,
     """    return #(IC.defecting_provinces(faction_key, slug) or {}) == 0""",
     """    return true"""),

    # THE MEMBER HALF DROPPED: a party of men with no land dissolves.
    ("a party of men dissolving because it holds no land", M,
     """    if (members or 0) > 0 then return false end""",
     """"""),

    # DISSOLVED WITHOUT A WORD: a dissolution belongs in the event log.
    ("a party dissolving with no card", M,
     """    IC.feed(faction_key, "dissolved")""",
     """"""),

    # THE FLAG NOT SAVED: a lord in store is made again on every load.
    ("the lord in store forgotten by the save", M,
     """            h.split or 0,
            h.stored and 1 or 0,""",
     """            h.split or 0,
            0,"""),

    # The governor spread sorted once instead of per province, so two idle men
    # of one party take two provinces and a party with one man takes none.
    ("governors picked off a count that never updates", M,
     """                if best.slug then
                    holds[best.slug] = (holds[best.slug] or 0) + 1
                end""",
     """                if best.slug then
                    holds[best.slug] = holds[best.slug] or 0
                end"""),

    # The pressure exemption removed. The court still fills and every party is
    # content; the strongest one is pressed anyway and leaves at full loyalty.
    ("an AI court pressed like a player's", M,
     """    if not IC.TUNE.pressure or IC.grace_left() > 0 or not IC.is_human(faction_key) then
        for _slug, house in pairs(court.houses) do house.pressed = nil end
        return 0
    end
    local chance = IC.control_pressure(faction_key)""",
     """    if not IC.TUNE.pressure or IC.grace_left() > 0 then
        for _slug, house in pairs(court.houses) do house.pressed = nil end
        return 0
    end
    local chance = IC.control_pressure(faction_key)"""),

    # The standing bar put back on the AI. Its court is empty for the first
    # twenty to thirty turns and half of it walks before a seat is ever filled.
    ("the office bar put back on the AI", M,
     """    if IC.is_human(faction_key) then
        local need = IC.tier_influence(office.tier)
        local has = IC.standing(faction_key, cqi)
        if has < need then return false, "standing", need - has end
    end""",
     """    local need = IC.tier_influence(office.tier)
    local has = IC.standing(faction_key, cqi)
    if has < need then return false, "standing", need - has end"""),

    # And the half of that exemption that is easy to miss: enforce_bars runs
    # before ai_fill_offices every turn, so without its early return the AI is
    # seated and then unseated, and a dismissal is a loyalty event.
    ("enforce_bars taking an AI officer's seat back", M,
     """    if not IC.is_human(faction_key) then return end
    local court = IC.court(faction_key)
    local fallen = {}""",
     """    local court = IC.court(faction_key)
    local fallen = {}"""),

    # Rival parties that act on their own.
    ("the parties given no turn", M,
     "        local ok, err = pcall(IC.party_turn, faction_key)\n",
     "        local ok, err = true, nil\n"),
    # AI COURTS ACT, so the human-only gate is not a mutant. What stays
    # human-only is the governors' wages.
    ("an AI court paying its governors' wages", P,
     "    if human then IC.governor_xp(faction_key) end",
     "    IC.governor_xp(faction_key)"),
    ("two events in one turn", P,
     "        chosen.act.act(faction_key, chosen.slug, chosen.target)",
     "        for i = 1, #picks do picks[i].act.act(faction_key, picks[i].slug, picks[i].target) end"),
    ("a motive under the floor still acting", P,
     "                    if m >= T.party_act_floor then",
     "                    if m >= 0 then"),
    ("a governor's experience given by level", P,
     "                cm:add_agent_experience(cm:char_lookup_str(man), T.governor_xp)",
     "                cm:add_agent_experience(cm:char_lookup_str(man), T.governor_xp, true)"),
    ("a loyal party plotting", P,
     "        if not house or (house.loyalty or 0) > T.party_intrigue_line then",
     "        if not house then"),
    ("a move taken above its loyalty line", P,
     "            if house.loyalty <= move.line and purse >= IC.plot_cost(move.key, faction_key) then",
     "            if purse >= IC.plot_cost(move.key, faction_key) then"),
    ("a move the plotter cannot afford", P,
     "            if house.loyalty <= move.line and purse >= IC.plot_cost(move.key, faction_key) then",
     "            if house.loyalty <= move.line then"),
    ("a party move that costs nothing", P,
     "    IC.add_standing(faction_key, actor, -cost)",
     ""),
    ("a failed party move landing anyway", P,
     "    if cm:random_number(100, 1) > chance then",
     "    if false then"),
    ("the Crown's poorest man discredited", P,
     "                and (not best or n > best_n or (n == best_n and cqi < best)) then",
     "                and (not best or n < best_n or (n == best_n and cqi < best)) then"),
    ("a legend murdered", P,
     "            return not IC.is_legend(man) and c ~= ruler",
     "            return c ~= ruler"),
    ("a serious move without warning", P,
     "        if t.move.warned then",
     "        if false then"),
    ("a warned move landing the same turn", P,
     "    if IC.agenda(faction_key).plot then\n        local done = IC.land_plot(faction_key)",
     "    if false then\n        local done = IC.land_plot(faction_key)"),
    ("a placated party striking anyway", P,
     "    if not move or p.placated or (house.loyalty or 0) > move.line then\n",
     "    if not move or p.placated then\n"),
    ("a warned move following a man out of his seat", P,
     "    if p.move == \"unseat\" and court.offices[p.key] ~= p.target then",
     "    if false then"),
    ("a stolen seat starting no feud", P,
     "            if holder and holder ~= slug and holder ~= IC.CROWN",
     "            if false and holder ~= slug and holder ~= IC.CROWN"),
    ("equals never feuding", P,
     "                    <= T.party_feud_equal then",
     "                    < 0 then"),
    ("a feuding party still plotting against the Crown", P,
     "        if IC.agenda(faction_key).feuds[slug] then return nil end",
     ""),
    ("a feud murder at full odds", P,
     "                        t.move == \"murder\" and T.party_murder_odds_div or nil)",
     "                        nil)"),
    ("a feud outliving its seat", P,
     "                over = not holder or IC.house_of_cqi(faction_key, holder) ~= rec.b",
     "                over = false"),
    ("a feud with no end turn", P,
     "            local over = now >= rec.ends",
     "            local over = false"),
    ("no rest after a feud", P,
     "        return not a.feuds[s] and (a.calm[s] or 0) <= now",
     "        return not a.feuds[s]"),
    ("the feud half of the agenda not saved", P,
     "        if slug == rec.a then\n            feuds[#feuds + 1]",
     "        if false then\n            feuds[#feuds + 1]"),
    ("a countdown hidden behind the agenda", U,
     """    if slug == IC.CROWN or not IC.agenda or string.match(word, "^SECEDES") then""",
     "    if slug == IC.CROWN or not IC.agenda then"),
    ("the faction leader picked for murder", P,
     "            return not IC.is_legend(man) and c ~= ruler",
     "            return not IC.is_legend(man)"),
    ("a warned murder landing on a new faction leader", P,
     "    if p.move == \"murder\" and p.target == IC.faction_leader_cqi(faction_key) then",
     "    if false then"),
    ("a warned move landing after its party left", P,
     "    if not house then return \"gone\" end",
     "    if not house then return nil end"),
    ("a dead plotter's warned move landing", P,
     "    if not IC.character_by_cqi(faction_key, p.actor) then return \"plotter dead\" end",
     "    if not IC.character_by_cqi(faction_key, p.actor) then return nil end"),
    ("a warned move landing for a plotter who cannot pay", P,
     "        return \"poor\"",
     "        return nil"),
    ("a warned move landing on a dead man", P,
     "    if not victim then return \"target dead\" end",
     "    if not victim then return nil end"),
    ("a warned move following its man into a rival party", P,
     "    if IC.house_of_character(victim, faction_key) ~= IC.CROWN then",
     "    if false then"),
    ("a warned recall following the province, not the man", P,
     "    if p.move == \"recall\" and court.govs[p.key] ~= p.target then",
     "    if false then"),
    ("a feud murder with no card", P,
     "        IC.feed(faction_key, \"party_feud_murder\")\n",
     ""),
    ("a feud murder quartering the base and not the chance", P,
     "    local base = T[\"plot_chance_\" .. move] or 0\n"
     "    local edge = math.floor((IC.standing(faction_key, actor)\n"
     "                             - IC.standing(faction_key, target)) / 10)\n"
     "                 * T.plot_chance_per_10\n"
     "    local chance = math.max(T.plot_chance_min,\n"
     "                            math.min(T.plot_chance_max, base + edge))\n"
     "    if odds_div then\n"
     "        chance = math.max(T.plot_chance_min, math.floor(chance / odds_div))\n"
     "    end\n",
     "    local base = T[\"plot_chance_\" .. move] or 0\n"
     "    if odds_div then base = math.floor(base / odds_div) end\n"
     "    local edge = math.floor((IC.standing(faction_key, actor)\n"
     "                             - IC.standing(faction_key, target)) / 10)\n"
     "                 * T.plot_chance_per_10\n"
     "    local chance = math.max(T.plot_chance_min,\n"
     "                            math.min(T.plot_chance_max, base + edge))\n"),
    ("a party murder that kills nobody", P,
     "            cm:kill_character(cm:char_lookup_str(victim), false)\n",
     ""),
    ("a party discredit that costs the Crown no weight", P,
     "            house.weight = math.max(1, (house.weight or 0)\n"
     "                                    - T.plot_discredit_weight)\n",
     ""),
    ("a party discredit with no floor under the Crown's weight", P,
     "            house.weight = math.max(1, (house.weight or 0)\n"
     "                                    - T.plot_discredit_weight)\n",
     "            house.weight = (house.weight or 0) - T.plot_discredit_weight\n"),
    ("a move refused at its own loyalty line", P,
     "            if house.loyalty <= move.line and purse >= IC.plot_cost(move.key, faction_key) then",
     "            if house.loyalty < move.line and purse >= IC.plot_cost(move.key, faction_key) then"),
    ("the intrigue line closed at its own number", P,
     "        if not house or (house.loyalty or 0) > T.party_intrigue_line then",
     "        if not house or (house.loyalty or 0) >= T.party_intrigue_line then"),
    ("a warning that does not name its plotter", U,
     "            plotter and ICUI.character_name(plotter) or \"their plotter\")",
     "            \"their plotter\")"),

    # Demands.
    ("the demand band's low edge allowing 25", P,
     """        if loyalty < T.party_demand_low or loyalty > T.party_demand_high then""",
     """        if loyalty < T.party_demand_low - 1 or loyalty > T.party_demand_high then"""),

    ("the demand band's high edge allowing 75", P,
     """        if loyalty < T.party_demand_low or loyalty > T.party_demand_high then""",
     """        if loyalty < T.party_demand_low or loyalty > T.party_demand_high + 1 then"""),

    ("the one-live-demand guard removed", P,
     """        if a.demand then return nil end""",
     """"""),

    ("a refused party demanding again the next turn", P,
     """        if (a.rest[slug] or 0) > cm:model():turn_number() then return nil end""",
     """"""),

    ("a refused party resting one turn too long", P,
     """        if (a.rest[slug] or 0) > cm:model():turn_number() then return nil end""",
     """        if (a.rest[slug] or 0) >= cm:model():turn_number() then return nil end"""),

    ("a refusal that rests nobody", P,
     """        a.rest[d.slug] = cm:model():turn_number() + T.party_demand_rest""",
     """"""),

    ("a met or void demand resting its party too", P,
     """    if outcome == "refused" then
        a.rest[d.slug]""",
     """    if true then
        a.rest[d.slug]"""),

    ("a refusal's rest forgotten by the save", P,
     """        .. table.concat(offers, ";") .. "|" .. table.concat(rest, ";"))""",
     """        .. table.concat(offers, ";"))"""),

    ("a refusal's rest not read back from the save", P,
     """            if #b >= 2 then a.rest[b[1]] = tonumber(b[2]) end""",
     """"""),

    ("claimed offices searched after other offices", P,
     """    for _, list in ipairs({claimed, other}) do""",
     """    for _, list in ipairs({other, claimed}) do"""),

    ("a demand naming a province a rival holds", P,
     """        if not holder or IC.house_of_cqi(faction_key, holder) == IC.CROWN then""",
     """        if true then"""),

    ("a demand naming a man who fails can_appoint", P,
     """                if IC.can_appoint(faction_key, office_slug, cqi) then""",
     """                if true then"""),

    ("a demand motive with the posts held not subtracted", P,
     """        return math.max(0, IC.share(faction_key, slug) / 10 - held) * 8""",
     """        return math.max(0, IC.share(faction_key, slug) / 10) * 8"""),

    ("a demand motive with no floor at zero", P,
     """        return math.max(0, IC.share(faction_key, slug) / 10 - held) * 8""",
     """        return (IC.share(faction_key, slug) / 10 - held) * 8"""),

    ("a refused mission call keeping the demand on the books", P,
     """    if not ok then
        a.demand = nil
        IC.save_agenda(faction_key)""",
     """    if not ok then
        IC.save_agenda(faction_key)"""),

    ("no card when a demand is issued", P,
     """    IC.feed(faction_key, "party_demand")""",
     """"""),

    ("demand_state never meeting a demand", P,
     """    if holder == d.cqi then return "met" end""",
     """    if false then return "met" end"""),

    ("demand_state never refusing a post given elsewhere", P,
     """    if holder and holder ~= d.was then return "refused" end""",
     """    if false then return "refused" end"""),

    ("demand_state refusing the Crown's own original holder", P,
     """    if holder and holder ~= d.was then return "refused" end""",
     """    if holder then return "refused" end"""),

    ("demand_state with no expiry", P,
     """    if cm:model():turn_number() >= d.ends then\n""",
     """    if false then\n"""),

    ("a dead man's demand not voided", P,
     """    if not IC.character_by_cqi(faction_key, d.cqi) then return "void", "gone" end""",
     """"""),

    ("a departed party's demand not voided", P,
     """    if not court.houses[d.slug] then return "void", "gone" end""",
     """"""),

    ("no loyalty when a demand is met", P,
     """        IC.move_loyalty(faction_key, d.slug, T.party_demand_met)""",
     """"""),

    ("no loyalty lost when a demand is refused", P,
     """        IC.move_loyalty(faction_key, d.slug, -T.party_demand_refused)""",
     """"""),

    ("no card on a demand refusal", P,
     """        IC.feed(faction_key, "party_demand_refused")""",
     """"""),

    ("an ended demand mission closed again", P,
     """    if not ended and IC.is_human(faction_key) then""",
     """    if IC.is_human(faction_key) then"""),

    ("the demand listener settling any mission key", P,
     """        if key ~= IC.DEMAND_KEYS.office and key ~= IC.DEMAND_KEYS.gov then
            return
        end""",
     """"""),

    # WITH ITS NEIGHBOUR, because IC.grant_demand calls it too and the bare
    # line matches twice.
    ("IC.check_demand not called in the party's turn", P,
     """    IC.check_demand(faction_key)
    IC.expire_offers(faction_key)""",
     """    IC.expire_offers(faction_key)"""),

    ("ACCEPT on a demand that seats him but never settles it", P,
     """    IC.check_demand(faction_key)
    return true""",
     """    return true"""),

    # Offers.
    ("an offer made below the offer line", P,
     """        if not house or (house.loyalty or 0) < T.party_offer_line then""",
     """        if not house or (house.loyalty or 0) < T.party_offer_line - 1 then"""),

    ("a second offer from one party", P,
     """        if IC.agenda(faction_key).offers[slug] then return nil end""",
     """"""),

    ("offer gold not scaled by share", P,
     """    local out = {{kind = "gold", n = math.floor(IC.share(faction_key, slug)
                                                * T.party_offer_gold_per_share)}}""",
     """    local out = {{kind = "gold", n = T.party_offer_gold_per_share}}"""),

    ("backing offered to a man already past the bar", P,
     """                        and gap > 0 and gap <= T.party_offer_backing""",
     """                        and gap <= T.party_offer_backing"""),

    ("backing offered further than the backing can reach", P,
     """                        and gap > 0 and gap <= T.party_offer_backing""",
     """                        and gap > 0"""),

    ("backing offered to a man below the office's rank bar", P,
     """                        and cand.rank >= IC.office_rank(office.slug, faction_key)""",
     """"""),

    ("calm offered with no countdown running", P,
     """                and (house.clock or 0) > 0 then""",
     """                then"""),

    ("troops offered to an army with no room", P,
     """            if n and n <= ARMY_UNITS - T.party_offer_units""",
     """            if n"""),

    ("a lapsed offer accepted", P,
     """    if cm:model():turn_number() >= o.ends then return false, "lapsed" end""",
     """"""),

    ("troops accepted into a full army", P,
     """        if n > ARMY_UNITS - o.n then return false, "room" end""",
     """"""),

    ("gold not paid on accept", P,
     """        cm:treasury_mod(faction_key, o.n)""",
     """"""),

    ("backing not paid on accept", P,
     """        IC.add_standing(faction_key, tonumber(o.target), o.n)""",
     """"""),

    ("calm leaving the countdown running", P,
     """        court.houses[o.target].clock = 0""",
     """"""),

    ("envy charged to the giver", P,
     """        if other ~= slug and other ~= IC.CROWN then""",
     """        if other ~= IC.CROWN then"""),

    ("envy charged to the Crown", P,
     """        if other ~= slug and other ~= IC.CROWN then""",
     """        if other ~= slug then"""),

    ("no envy paid at all", P,
     """    for _, other in ipairs(IC.present_houses(faction_key)) do
        if other ~= slug and other ~= IC.CROWN then
            IC.move_loyalty(faction_key, other, -T.party_offer_envy)
        end
    end""",
     """"""),

    ("an accepted offer left open", P,
     """    local o = a.offers[slug]
    a.offers[slug] = nil
    local court = IC.court(faction_key)""",
     """    local o = a.offers[slug]
    local court = IC.court(faction_key)"""),

    ("offers never lapsing", P,
     """        if now >= o.ends or why == "gone" then""",
     """        if false or why == "gone" then"""),

    ("a departed party's offer kept open", P,
     """        if now >= o.ends or why == "gone" then""",
     """        if now >= o.ends then"""),

    ("IC.expire_offers not called in the party's turn", P,
     """    IC.check_demand(faction_key)
    IC.expire_offers(faction_key)""",
     """    IC.check_demand(faction_key)"""),

    # Demands and offers on the panel.
    ("DEMANDING never shown on the party card", U,
     """    if a.demand and a.demand.slug == slug then return "DEMANDING" end""",
     """"""),

    ("OFFERING never shown on the party card", U,
     """    if a.offers[slug] then return "OFFERING" end""",
     """"""),

    ("a demand shown over a warned move", U,
     """    if a.plot and a.plot.slug == slug then return "SCHEMING" end
    if a.demand and a.demand.slug == slug then return "DEMANDING" end""",
     """    if a.demand and a.demand.slug == slug then return "DEMANDING" end
    if a.plot and a.plot.slug == slug then return "SCHEMING" end"""),

    ("the demand tooltip not naming the office", U,
     """            what = string.format("seat %s as %s", who, ICUI.office_name(d.key))""",
     """            what = string.format("seat %s", who)"""),

    ("an acceptable offer row drawn as refused", U,
     """            local may = IC.can_accept_offer(faction, slug)""",
     """            local may = false"""),

    ("ACCEPT on an offer routed to decline_offer", U,
     '        op, arg = (yes and "accept" or "decline"), p.slug',
     '        op, arg = (yes and "decline" or "decline"), p.slug'),

    ("the warned move not leading the Intrigue alert", U,
     """    local plot_line = ICUI.plot_alert(faction)
    if plot_line then
        urgent = plot_line""",
     """    local plot_line = ICUI.plot_alert(faction)
    if plot_line and not urgent then
        urgent = plot_line"""),

    # The controller's three extra rules.
    ("a demand card raised whatever the outcome", P,
     """    if outcome == "met" then
        IC.move_loyalty(faction_key, d.slug, T.party_demand_met)
        IC.log(faction_key, "demand_met", d.slug, d.key, 0)
        IC.news(faction_key, "demand_met", d.slug)
    elseif outcome == "refused" then
        IC.move_loyalty(faction_key, d.slug, -T.party_demand_refused)
        IC.grudge_write(faction_key, d.slug, "demand")
        IC.log(faction_key, "demand_refused", d.slug, d.key, 0)
        IC.news(faction_key, "demand_refused", d.slug)
        IC.feed(faction_key, "party_demand_refused")
    else
        local _, why = IC.demand_state(faction_key, d)
        IC.log(faction_key, "demand_void", d.slug, d.key, IC.VOID_REASONS[why] or 0)
    end""",
     """    if outcome == "met" then
        IC.move_loyalty(faction_key, d.slug, T.party_demand_met)
        IC.log(faction_key, "demand_met", d.slug, d.key, 0)
        IC.news(faction_key, "demand_met", d.slug)
    elseif outcome == "refused" then
        IC.move_loyalty(faction_key, d.slug, -T.party_demand_refused)
        IC.grudge_write(faction_key, d.slug, "demand")
        IC.log(faction_key, "demand_refused", d.slug, d.key, 0)
        IC.news(faction_key, "demand_refused", d.slug)
        IC.feed(faction_key, "party_demand_refused")
    else
        local _, why = IC.demand_state(faction_key, d)
        IC.log(faction_key, "demand_void", d.slug, d.key, IC.VOID_REASONS[why] or 0)
    end
    IC.feed(faction_key, "party_demand_refused")"""),

    ("REFUSE on an offer routed to accept_offer", U,
     '        op, arg = (yes and "accept" or "decline"), p.slug',
     '        op, arg = (yes and "accept" or "accept"), p.slug'),

    ("the lapsed reason dropped from reason_text", U,
     """    elseif why == "lapsed" then
        return "That offer has lapsed."
    elseif why == "room" then""",
     """    elseif why == "room" then"""),

    # Demand expiry, the Intrigue alert and the second wage.
    ("the engine's expiry refusing a demand the player met", P,
     """                if now == "met" or now == "void" then result = now end""",
     """                if now == "void" then result = now end"""),

    ("a late event settling a demand issued this turn", P,
     """            if d.ends - T.party_demand_turns >= cm:model():turn_number() then return end""",
     """"""),

    ("the same-turn guard off by one", P,
     """            if d.ends - T.party_demand_turns >= cm:model():turn_number() then return end""",
     """            if d.ends - T.party_demand_turns > cm:model():turn_number() then return end"""),

    ("a demand for a lost province not voided", P,
     """        if not held then return "void", "lost" end""",
     """"""),

    ("the plotter's own clock counted in the Intrigue alert", U,
     """        speaker = IC.agenda(faction).plot.slug""",
     """        speaker = nil"""),

    ("a governor stuck at rank 0 never paid the second wage", P,
     """            if rank == "0" then""",
     """            if false then"""),

    ("every governor paid the second wage", P,
     """            if rank == "0" then""",
     """            if true then"""),

    # The screen's share of the layout.
    # THE BOX OFF THE WIDTH ALONE. A 2560x1080 ultrawide is 1080 tall, so a
    # 2560 box would run 360px off the bottom of it.
    ("the box read off the screen's width alone", U,
     """    local bw = math.floor(math.min(sw or 0, (sh or 0) * 16 / 9))""",
     """    local bw = math.floor(sw or 0)"""),

    # NO FLOOR. CA's screen is never under 1600x900, but a box under it would
    # scale below the compact files' own 1600 build.
    ("no clamp at the 1600 floor", U,
     """    if bw < 1600 then bw = 1600 elseif bw > 2560 then bw = 2560 end""",
     """    if bw > 2560 then bw = 2560 end"""),

    # ROUNDING DOWN, where the generator rounds half up. Every edge of every
    # cell then lands up to a pixel from where the generator measured it.
    ("sc rounding down instead of at the half", U,
     """    return math.floor((v * ICUI.BW + 960) / 1920)""",
     """    return math.floor((v * ICUI.BW) / 1920)"""),

    # AN OVERRIDE AT FULL STRENGTH EVERYWHERE. A cell widened for 1600's
    # smaller font keeps the widening at 1080p and runs into its neighbour.
    ("an override that does not fade", U,
     """    if ICUI.BW >= 1920 then return 0 end
    return math.floor((d * (1920 - ICUI.BW) + 160) / 320)""",
     """    return d"""),

    ("the compact files opened at 1920", U,
     """    ICUI.COMPACT = bw < 1920""",
     """    ICUI.COMPACT = bw <= 1920"""),

    # THE DEFAULT THIRD ARGUMENT scales every child by the parent's factor,
    # and then layout() sizes each of them again on top of it.
    ("Resize left to resize children too", U,
     """        c:Resize(w, h, false)""",
     """        c:Resize(w, h)"""),

    # SCALED FROM THE LAST ANSWER, not from BASE: a second open at another size
    # scales an already scaled layout.
    ("a scaled number compounded from its last scale", U,
     """        ICUI[n] = ICUI.sc(ICUI.BASE[n]) + (type(d) == "number" and ICUI.fade(d) or 0)""",
     """        ICUI[n] = ICUI.sc(ICUI[n]) + (type(d) == "number" and ICUI.fade(d) or 0)"""),

    ("a scaled cell compounded from its last scale", U,
     """            local t = ICUI[n]
            for k, b in pairs(base) do""",
     """            local t = ICUI[n]
            for k, b in pairs(t) do"""),

    # THE REDRAW WITHOUT THE BOX'S OFFSET: the pie, the header strip and the
    # arrows at the screen's corner on any screen the box does not fill.
    # Invisible at 1080p.
    ("a redraw that forgets the box offset", U,
     """    local px, py = panel:Position()
    px = px + ICUI.OX
    py = py + ICUI.OY
    -- The picker is modal""",
     """    local px, py = panel:Position()
    -- The picker is modal"""),

    # A FAILED SCALE THAT TAKES THE COURT WITH IT: the error reaches open()'s
    # outer pcall and the panel never opens, on a screen it opened on before.
    ("a failed scale that keeps the court shut", U,
     """        local scaled, why = pcall(ICUI.apply_scale, bw)""",
     """        ICUI.apply_scale(bw)
        local scaled, why = true, nil"""),

    # CENTRED SIDEWAYS ONLY. A 16:10 screen is 120px taller than its box, and
    # the box would sit on the top edge with the ground all below it.
    ("the box centred sideways and not down", U,
     """        ICUI.OY = math.floor((ph - bh) / 2)""",
     """        ICUI.OY = 0"""),

    # PLACED AND NEVER SIZED: a cell keeps its twui size, which below 1920 is
    # the 1600 file's, in a box that is not 1600.
    ("a panel cell placed and never sized", U,
     """            c:MoveTo(px + xy[1], py + xy[2])
            ICUI.resize(c, xy[3], xy[4])
        end
    end

    -- A POOL""",
     """            c:MoveTo(px + xy[1], py + xy[2])
        end
    end

    -- A POOL"""),

    # The Crown's box in two halves.
    ("the hint moved beside the pager and left at the grid's width", U,
     """            c:MoveTo(px + home[1], py + home[2])
            ICUI.resize(c, home[3], home[4])""",
     """            c:MoveTo(px + home[1], py + home[2])"""),

    ("an effect line kept from the band drawn before", U,
     """        set_text(comp(key, panel), ICUI.fx_line(fx[i]))""",
     """        if fx[i] then set_text(comp(key, panel), ICUI.fx_line(fx[i])) end"""),

    ("the band's effects split on a bare comma", U,
     """"(.-), ") do""",
     """"(.-),") do"""),

    ("the Crown's box writes his trait and not the party's two", U,
     """    for _, row in ipairs({{"ic_leader_trait", lead}, {"ic_leader_t1", traits[1]},
                          {"ic_leader_t2", traits[2]}}) do""",
     """    for _, row in ipairs({{"ic_leader_trait", lead}}) do"""),

    ("the Crown's traits drawn bare, without the card's icon", U,
     """        local c, trait = comp(row[1], panel), row[2]
        set_text(c, ICUI.trait_line(trait and trait.name))""",
     """        local c, trait = comp(row[1], panel), row[2]
        set_text(c, trait and trait.name or "")"""),

    ("the band line left on screen over another tab", U,
     """ICUI.CONTROL_KEYS = {"ic_control", "ic_control_band", "ic_control_fx",""",
     """ICUI.CONTROL_KEYS = {"ic_control", "ic_control_fx","""),

    # SEND A GIFT back on the bar.
    ("SEND A GIFT routed to the oath", U,
     """    ic_act_gift = {favour = "gift"},""",
     """    ic_act_gift = {favour = "secure"},"""),

    ("the gift's tooltip reading the oath's lines", U,
     """        if move.favour == "gift" then""",
     """        if false then"""),

    # THE NIL THAT BREAKS THE GAME: an and-chain starting with a nil
    # slug hands SetVisible nil, and the engine's string library dies with it.
    ("the bar's visibility built from an and-chain that can be nil", U,
     """    local rival = slug ~= nil and slug ~= IC.CROWN and court.houses[slug] ~= nil""",
     """    local rival = slug and slug ~= IC.CROWN and court.houses[slug] ~= nil"""),

    # Five fixes undone, and one fix made too wide.
    ("a full pool's fallback allowed to be the seceding court itself", M,
     """        if key ~= exclude then fallback = fallback or key end""",
     """        fallback = fallback or key"""),
    ("a party joining a running rising renames it again", M,
     """    if rebels and flying and (waking or not risen or risen == "") then""",
     """    if rebels and flying then"""),
    ("the parties' turn called bare again", M,
     """        local ok, err = pcall(IC.party_turn, faction_key)""",
     """        local ok, err = true, IC.party_turn(faction_key)"""),
    ("placated read after the drift again", M,
     """    if IC.party_placate then IC.party_placate(faction_key) end""",
     """    -- placated read late"""),
    ("the placated mark ignored at the landing", P,
     """    if not move or p.placated or (house.loyalty or 0) > move.line then""",
     """    if not move or (house.loyalty or 0) > move.line then"""),
    ("a demand nobody could grant refused at the turn's end", P,
     """        if d.kind == "office" and not IC.can_appoint(faction_key, d.key, d.cqi) then
            return "void", "short"
        end""",
     """        if d.kind == "office" and not IC.can_appoint(faction_key, d.key, d.cqi) then
            return "refused"
        end"""),
    ("every office demand lapses at the turn's end", P,
     """        if d.kind == "office" and not IC.can_appoint(faction_key, d.key, d.cqi) then""",
     """        if d.kind == "office" then"""),
    ("the engine's expiry charging a demand nobody could grant", P,
     """                if now == "met" or now == "void" then result = now end""",
     """                if now == "met" then result = now end"""),
    ("a dead officer's term left in the save", M,
     "                court.terms[office_slug] = nil\n",
     ""),

    # MCT: the settings, frozen into the save.
    ("mct: multiplayer reading MCT after all", M,
     "    if IC.is_mp() then return t end",
     "    if false then return t end"),
    ("mct: an erroring multiplayer check read as multiplayer", M,
     "    return ok and v == true",
     "    return (not ok) or v == true"),
    ("mct: an older save's missing key left nil", M,
     """    for k, v in pairs(IC.TUNE_DEFAULTS) do t[k] = v end
    -- EVERY FIELD, EMPTY ONES INCLUDED""",
     """    -- EVERY FIELD, EMPTY ONES INCLUDED"""),
    ("mct: an empty saved field sliding the rest onto the wrong keys", M,
     """    for chunk in string.gmatch((packed or "") .. "|", "([^|]*)|") do""",
     """    for chunk in string.gmatch(packed or "", "[^|]+") do"""),
    ("mct: a partial table packed as zeros", M,
     "        if v == nil then v = IC.TUNE_DEFAULTS[key] end",
     "        if v == nil then v = 0 end"),
    ("mct: an unreadable saved field read as zero", M,
     "        local n = tonumber(chunk)",
     "        local n = tonumber(chunk) or 0"),
    ("mct: the sliders read under every difficulty", M,
     "                and (preset == IC.PRESET_CUSTOM or IC.TUNE_START[key])",
     "                and true"),
    ("mct: the switches read under Custom only", M,
     '            if type(IC.TUNE_DEFAULTS[key]) == "boolean" or custom_number then',
     "            if custom_number then"),
    ("mct: a setting's type never checked", M,
     "            if type(v) == type(IC.TUNE_DEFAULTS[key]) then return v end",
     "            if v ~= nil then return v end"),
    ("mct: fewest rivals left above most", M,
     "    if t.rivals_min > t.rivals_max then t.rivals_min = t.rivals_max end",
     "    local _ = t.rivals_min"),
    ("mct: the intrigue line left where it loaded", M,
     "            move.line = IC.TUNE.party_intrigue_line",
     "            move.line = move.line"),
    ("mct: a reload re-reading MCT", M,
     '    if type(packed) == "string" and packed ~= "" then',
     "    if false then"),
    ("mct: the court rolled before the freeze", M,
     """    IC.freeze_tune()
    IC.register()""",
     """    IC.register()"""),
    ("mct: parties acting with parties_act off", P,
     "    if not T.parties_act then",
     "    if false then"),
    ("mct: AI courts run with ai_courts off", M,
     "    if IC.TUNE.ai_courts then return true end",
     # NOT a bare `return true`: Lua 5.1 refuses a statement after a return, so
     # that mutant was a parse error the runner rightly reported as no catch.
     "    if true then return true end"),
    ("mct: the settlement listener deaf to ai_courts", M,
     """        if not IC.runs_court(faction) then return end
        IC.loaded(faction:name())
        IC.add_standing(faction:name(), character:command_queue_index(),
                        IC.TUNE.settlement_influence)""",
     """        if not IC.is_chd(faction) then return end
        IC.loaded(faction:name())
        IC.add_standing(faction:name(), character:command_queue_index(),
                        IC.TUNE.settlement_influence)"""),
    ("mct: secession with secession off", M,
     """    if not IC.secession_on() then
        for _slug, house in pairs(court.houses) do house.clock = 0 end""",
     """    if false then
        for _slug, house in pairs(court.houses) do house.clock = 0 end"""),
    ("mct: pressure with pressure off", M,
     "    if not IC.TUNE.pressure or IC.grace_left() > 0 or not IC.is_human(faction_key) then",
     "    if IC.grace_left() > 0 or not IC.is_human(faction_key) then"),
    ("mct: the Crown splitting with crown_split off", M,
     """    if not IC.TUNE.crown_split or IC.grace_left() > 0 then
""",
     """    if IC.grace_left() > 0 then
"""),
    ("live: a split countdown left running with crown_split off", M,
     """        if crown then crown.split = 0 end
""",
     ""),
    ("mct: routine lines written with the detailed log off", M,
     "    if IC.TUNE and IC.TUNE.detailed_log == false then return end",
     "    if false then return end"),
    ("mct: the parties' turn failure silenced with the routine log", M,
     """            IC.warn("IRON COURT: the parties' turn failed in " .. faction_key""",
     """            IC.say("IRON COURT: the parties' turn failed in " .. faction_key"""),
    ("mct: a switch left off the settings page", S,
     '    {"parties_act", "Rival parties act on their own", "systems",',
     '    {"parties_act_gone", "Rival parties act on their own", "systems",'),
    ("mct: the frozen switches editable mid-campaign", S,
     """            else
                lock(o, true, LOCK_REASON)
            end""",
     """            else
                lock(o, false)
            end"""),
    ("live: ai_courts marked live on the page", S,
     '     .. "can split. Off, only your court runs.", false},',
     '     .. "can split. Off, only your court runs.", true},'),
    ("live: the live switches locked in a campaign", S,
     """            elseif SWITCHES[i][5] then
                lock(o, false)""",
     """            elseif SWITCHES[i][5] then
                lock(o, true, LOCK_REASON)"""),
    ("live: the switches open in multiplayer", S,
     """            if in_mp then
                lock(o, true, MP_REASON)""",
     """            if false then
                lock(o, true, MP_REASON)"""),
    ("live: an old save's locks never lifted", S,
     """core:add_listener("derpy_ic_mct_loaded", "MctInitialized", true, function(context)""",
     """core:add_listener("derpy_ic_mct_loaded_gone", "MctInitialized", true, function(context)"""),
    # THE 226121E7 CRASH: the model read from inside CA's LoadingGame callbacks.
    ("crash: the MCT page asking the game about multiplayer while it loads", S,
     """    in_mp = type(context.is_multiplayer) == "function" and context:is_multiplayer() == true""",
     """    in_mp = cm:is_multiplayer() == true"""),
    ("live: MCT's multiplayer answer ignored", S,
     """    in_mp = type(context.is_multiplayer) == "function" and context:is_multiplayer() == true""",
     """    in_mp = false"""),

    # Live switches: read again at load and on Finalize.
    ("live: the switches never read again at load", M,
     """    IC.apply_tune(t)
    IC.refresh_live_tune()
    return t""",
     """    IC.apply_tune(t)
    return t"""),
    ("live: ai_courts following MCT mid-campaign", M,
     """IC.LIVE_TUNE = {"parties_act", "secession", "pressure", "crown_split",""",
     """IC.LIVE_TUNE = {"parties_act", "secession", "pressure", "crown_split", "ai_courts","""),
    ("live: the log switch dropped from the live set", M,
     """                "all_cards", "detailed_log", "governments", "gov_drift", "deeds", "laws",""",
     """                "all_cards", "governments", "gov_drift", "deeds", "laws","""),
    ("live: multiplayer following each machine's MCT", M,
     """function IC.refresh_live_tune()
    if IC.is_mp() then return false end""",
     """function IC.refresh_live_tune()"""),
    ("live: a live change never written into the save", M,
     """    cm:set_saved_value("derpy_ic_tuned", IC.pack_tune(IC.TUNE))
    -- A COUNTDOWN""",
     """    -- A COUNTDOWN"""),
    ("live: countdowns settled when a switch goes ON", M,
     """                off[key] = not v
""",
     """                off[key] = v
"""),
    ("live: a switched-off secession left counting until the turn", M,
     """    if not IC.TUNE.secession then IC.tick_secession(faction_key) end
""",
     ""),
    ("live: the pressure mark left on", M,
     """    if not IC.TUNE.pressure then IC.tick_pressure(faction_key) end
""",
     ""),
    ("live: the Crown's count left on", M,
     """    if not IC.TUNE.crown_split then IC.splinter(faction_key) end
""",
     ""),
    ("live: the cleared countdowns never saved", M,
     """            IC.settle_switches(faction_key)
            IC.save(faction_key)""",
     """            IC.settle_switches(faction_key)"""),
    ("live: a court loaded with a switched-off count still running", M,
     """        IC.settle_switches(faction_key)
    end
    return IC.court(faction_key)""",
     """    end
    return IC.court(faction_key)"""),
    ("live: nothing listening for Finalize", M,
     """    core:add_listener("ic_live_tune", "MctFinalized", true, function()""",
     """    core:add_listener("ic_live_tune_gone", "MctFinalized", true, function()"""),

    # MP: every panel action through one transport.
    ("mp: an unsendable action applied on this machine", M,
     """    if not cqi then
        IC.warn("IRON COURT: no command queue index for " .. tostring(faction_key)
                .. " - " .. op .. " not sent")
        return false
    end""",
     """    if not cqi then
        IC.MP_OPS[op](faction_key, arg)
        return false
    end"""),
    ("mp: the length ceiling dropped", M,
     "    if #id > IC.MP_MAX then",
     "    if false then"),
    ("mp: another mod's trigger read as ours", M,
     """    local op, arg = string.match(id, "^" .. IC.MP_TAG .. "|([^|]*)|(.*)$")""",
     """    local op, arg = string.match(id, "^%w+|([^|]*)|(.*)$")"""),
    ("mp: a trigger from nobody acted on for the first human", M,
     "    local faction_key = IC.faction_by_cqi(cqi)",
     "    local faction_key = IC.faction_by_cqi(cqi) or (cm:get_human_factions() or {})[1]"),
    ("mp: a cqi left a string on the wire", M,
     """    return answer(fk, "appoint", arg, IC.appoint(fk, f[1], tonumber(f[2])))""",
     """    return answer(fk, "appoint", arg, IC.appoint(fk, f[1], f[2]))"""),
    ("mp: an empty plot target sent as an empty string", M,
     """    if target == "" then target = nil end""",
     "    local _ = target"),
    ("mp: the answer never reaching the panel", M,
     "    if IC.after_op then IC.after_op(faction_key, op, arg, done, why, spare) end",
     "    local _ = IC.after_op"),
    ("mp: the feed held in multiplayer", M,
     "    if IC.is_mp() then return 0 end",
     "    if false then return 0 end"),
    ("mp: the panel reading the first human again", U,
     "    local ok, me = pcall(function() return cm:get_local_faction_name(true) end)",
     "    local ok, me = false, nil"),
    ("mp: the unforced local-faction read", U,
     "    local ok, me = pcall(function() return cm:get_local_faction_name(true) end)",
     "    local ok, me = pcall(function() return cm:get_local_faction_name() end)"),
    ("mp: every machine answering every click", U,
     "    if mp and faction_key ~= ICUI.player() then return end",
     "    local _ = mp"),
    ("mp: an answer that never redraws in multiplayer", U,
     "    if mp then ICUI.refresh() end",
     "    local _ = mp"),
    ("mp: a dismissal called straight at the model", U,
     """        ICUI.send(faction, "dismiss", office.slug)""",
     """        IC.dismiss(faction, office.slug)"""),
    ("mp: the favour paid straight off the click", U,
     """        ICUI.send(faction, "favour", move.favour .. "|" .. slug)""",
     """        IC.favour(faction, move.favour, slug)"""),
    ("mp: a refused pick closing the picker", U,
     """        if not done then
            ICUI.notice = ICUI.reason_text(why, spare)
            ICUI.play(ICUI.SOUNDS.refused)
            return
        end""",
     """        if not done then
            ICUI.notice = ICUI.reason_text(why, spare)
            ICUI.play(ICUI.SOUNDS.refused)
        end"""),

    # MP: click waits, and a court only for a Chaos Dwarf player.
    ("mp: a second click sent before the answer", U,
     "    if ICUI.waiting then return false end",
     "    if false then return false end"),
    ("mp: the wait never ended by the answer", U,
     """    if mp and faction_key ~= ICUI.player() then return end
    ICUI.waiting = nil""",
     """    if mp and faction_key ~= ICUI.player() then return end"""),
    ("mp: the wait kept past closing the panel", U,
     """    -- AND AN ACTION STILL IN FLIGHT: see ICUI.send.
    ICUI.waiting = nil""",
     """    -- AND AN ACTION STILL IN FLIGHT: see ICUI.send."""),
    ("mp: a court button for a player who is not a Chaos Dwarf", U,
     """    attempt = attempt or 1
    if not ICUI.court_player() then return false end""",
     """    attempt = attempt or 1"""),
    ("mp: a court opened for a player who is not a Chaos Dwarf", U,
     """    if not ICUI.court_player() then return end
    if not ICUI.prefs_loaded then ICUI.load_prefs() end
    if comp(ICUI.PANEL) then ICUI.refresh() return end""",
     """    if not ICUI.prefs_loaded then ICUI.load_prefs() end
    if comp(ICUI.PANEL) then ICUI.refresh() return end"""),
    # The court's size is the difficulty.
    ("mct: Ruthless seating one party short of a full court", M,
     "        party_intrigue_line = 65, rivals_min = 5, rivals_max = 5, term_turns = 10,",
     "        party_intrigue_line = 65, rivals_min = 4, rivals_max = 4, term_turns = 10,"),
    ("mct: Default rolling a range again", M,
     "    rivals_min          = 2,",
     "    rivals_min          = 1,"),
    ("mct: Ruthless pressing a fresh full court from turn 1", M,
     "secede_share = 15, secede_turns = 3, pressure_below = 15,",
     "secede_share = 15, secede_turns = 3, pressure_below = 20,"),
    ("plot: the odds read after the price is taken", M,
     "    local chance = IC.plot_chance(faction_key, plot_key, actor_cqi, target)\n"
     "    if plot.gold then\n",
     "    IC.add_standing(faction_key, actor_cqi, -cost)\n"
     "    local chance = IC.plot_chance(faction_key, plot_key, actor_cqi, target)\n"
     "    if plot.gold then\n"),
    ("court: a roll that never marks the court rolled", M,
     "    IC.court(faction_key).rolled = true\n",
     "\n"),
    ("court: an old save never marked while it still has rivals", M,
     "    if n > 1 then court.rolled = true end\n",
     "\n"),
    ("court: the rolled marker never saved", M,
     "                 court.rolled and \"1\" or \"\", join(last",
     "                 \"\", join(last"),
    ("office: a dismissal takes back the single weight again", M,
     "            court.houses[slug].weight - IC.office_weight(office_slug, slug, faction_key))",
     "            court.houses[slug].weight - IC.TUNE.weight_per_office)"),
    ("office: a death in the seat takes back the single weight again", M,
     "                        - IC.office_weight(office_slug, slug, faction_key))",
     "                        - IC.TUNE.weight_per_office)"),
    ("office: a man whose term ended never kept waiting", M,
     "    if wait > 0 then return false, \"renew\", wait end\n",
     "    if false then return false, \"renew\", wait end\n"),
    ("office: a renewal welcomed like a new man", M,
     "    if not renewal then\n"
     "        IC.move_loyalty(faction_key, slug, IC.TUNE.loyalty_appointed)\n",
     "    if true then\n"
     "        IC.move_loyalty(faction_key, slug, IC.TUNE.loyalty_appointed)\n"),
    ("office: an ended term never remembers its man", M,
     "        court.last[done[i].slug] = {cqi = done[i].cqi, turn = turn}\n",
     "\n"),
    ("office: a new man leaves the old one's renewal standing", M,
     "    court.last[office_slug] = nil\n"
     "    court.offices[office_slug] = cqi\n",
     "    court.offices[office_slug] = cqi\n"),
    ("office: the renewal wait never saved", M,
     "                 court.rolled and \"1\" or \"\", join(last, \";\"),",
     "                 court.rolled and \"1\" or \"\", \"\","),
    ("office: the renewal wait never read back", M,
     "            court.last[bits[1]] = {cqi = cqi, turn = ended}\n",
     "\n"),
    ("mct: Harsh holding a seat for five turns again", M,
     "party_intrigue_line = 60, rivals_min = 3, rivals_max = 3, term_turns = 10,",
     "party_intrigue_line = 60, rivals_min = 3, rivals_max = 3, term_turns = 5,"),
    ("ui: the waiting man's row says nothing of the wait", U,
     "        elseif wait > 0 then\n"
     "            action = string.format(\"Wait %d\", wait)\n",
     ""),
    ("ui: the waiting man offered on the picker", U,
     "                (cand.rank >= rank_bar and wait == 0 and not cand.busy\n",
     "                (cand.rank >= rank_bar and not cand.busy\n"),
    ("ui: the renewal refusal not put into words", U,
     "    elseif why == \"renew\" then\n",
     "    elseif why == \"renew_\" then\n"),
    # Quality of life.
    ("qol: no warning the turn before a term ends", M,
     "    IC.expire_terms(faction_key)\n    IC.warn_terms(faction_key)\n",
     "    IC.expire_terms(faction_key)\n"),
    ("qol: the term warning two turns early", M,
     "        if ends and ends - turn == 1 then out[#out + 1] = slug end\n",
     "        if ends and ends - turn == 2 then out[#out + 1] = slug end\n"),
    ("qol: the term warning never names the seat", M,
     "            #ending == 1 and IC.office_title_key(ending[1], faction_key) or nil)",
     "            nil)"),
    ("qol: all_cards off silences nothing", M,
     "    if IC.TUNE.all_cards == false and IC.ROUTINE_EVENTS[slug] then return false end\n",
     "\n"),
    ("qol: all_cards off silences a warning too", M,
     "    office_lost = true, party_joined = true, snub = true, party_feud = true,",
     "    office_lost = true, secede_warn = true, party_joined = true, snub = true, party_feud = true,"),
    ("qol: all_cards left out of the save order", M,
     "    \"detailed_log\", \"all_cards\",\n",
     "    \"detailed_log\",\n"),
    ("qol: an empty seat's card never mentions the wait", U,
     '            if wait > 0 then\n                term_text = string.format("Last holder waits %d turn%s",',
     '            if false then\n                term_text = string.format("Last holder waits %d turn%s",'),
    ("qol: an empty seat's button never names its old holder", U,
     "                local tip = \"\"\n                if was then\n",
     "                local tip = \"\"\n                if false then\n"),
    ("qol: the button's summary leaves out the terms ending", U,
     "    if #s.ending > 0 then\n        local ending = {}",
     "    if false then\n        local ending = {}"),
    ("qol: the button's summary leaves out a party leaving", U,
     "        elseif seated[i] ~= IC.CROWN and house and (house.clock or 0) > 0 then",
     "        elseif seated[i] ~= IC.CROWN and house and (house.clock or 0) > 99 then"),
    ("qol: the button's summary leaves out who may return", U,
     "    if #back > 0 then\n        lines[#lines + 1] = \"Ready to return",
     "    if false then\n        lines[#lines + 1] = \"Ready to return"),
    ("qol: closing the court leaves the button's summary stale", U,
     "    ICUI.save_prefs()\n"
     "    -- WHAT THE PLAYER JUST CHANGED, on the button he closes the panel onto -\n"
     "    -- except from a turn handler (see place_opener).\n"
     "    if not quiet then ICUI.update_opener_tip() end\n",
     "    ICUI.save_prefs()\n"),
    ("qol: the player's turn start leaves the button's summary stale", U,
     "    cm:callback(function() ICUI.update_opener_tip() end, 0)\n",
     "\n"),
    ("qol: closing the court never saves the tab", U,
     "    ICUI.save_prefs()\n"
     "    -- WHAT THE PLAYER JUST CHANGED",
     "    -- WHAT THE PLAYER JUST CHANGED"),
    ("qol: opening the court never reads the tab back", U,
     "    if not ICUI.prefs_loaded then ICUI.load_prefs() end\n",
     "\n"),
    ("qol: multiplayer saves the tab", U,
     "function ICUI.save_prefs()\n    if IC.is_mp() then return false end\n",
     "function ICUI.save_prefs()\n"),
    ("qol: a tab that no longer exists is read back", U,
     "        if view == f[1] then ICUI.view = view end\n",
     "        ICUI.view = f[1]\n"),
    ("qol: a sort past its list's end is read back", U,
     "        if n and ICUI.SORTS[view] and ICUI.SORTS[view][n] then\n",
     "        if n then\n"),
    ("qol: a wounded man offered Find", U,
     "    if hurt_ok and hurt then return nil end\n",
     "\n"),
    ("qol: a man at nowhere offered Find", U,
     "    if not ok or not x or not y or (x == 0 and y == 0) then return nil end\n",
     "    if not ok or not x or not y then return nil end\n"),
    ("qol: Find leaves the court open over the map", U,
     "    if not x then return false end\n    ICUI.close()\n",
     "    if not x then return false end\n"),
    ("qol: Find keeps the camera from the player", U,
     "    cm:scroll_camera_from_current(true, 1, {x, y, 14.7, 0, 12})",
     "    cm:scroll_camera_from_current(false, 1, {x, y, 14.7, 0, 12})"),
    ("qol: a roster click sent as a governor", U,
     "    elseif ICUI.pick.kind == \"house\" then\n"
     "        -- NOT SENT: a camera is one player's own, and nothing in the model moves.\n"
     "        return ICUI.find(faction, chosen)\n",
     ""),
    ("qol: the fill plan seats as it plans", M,
     "                            and IC.can_appoint(faction_key, office.slug, cqi) then\n"
     "                        used[cqi] = true\n"
     "                        plan[#plan + 1]",
     "                            and IC.appoint(faction_key, office.slug, cqi) then\n"
     "                        used[cqi] = true\n"
     "                        plan[#plan + 1]"),
    ("qol: the fill button not red with nothing to do", U,
     "    set_text(button, #plan > 0 and ICUI.FILL_LABEL or ICUI.red(ICUI.FILL_LABEL))",
     "    set_text(button, ICUI.FILL_LABEL)"),
    ("qol: an empty fill sent anyway", U,
     "    if #IC.fill_plan(faction) == 0 then\n"
     "        ICUI.notice = ICUI.reason_text(\"no fill\")\n",
     "    if false then\n"
     "        ICUI.notice = ICUI.reason_text(\"no fill\")\n"),
    ("qol: the fill button on every tab", U,
     "    show(comp(\"ic_fill\", panel), ICUI.pick == nil and ICUI.view == \"offices\")",
     "    show(comp(\"ic_fill\", panel), ICUI.pick == nil)"),
    # THE OFFICES TAB'S ZIGGURAT.
    ("the ziggurat drawn on every tab", U,
     "    show(comp(\"ic_zig_bg\", panel), view == \"offices\")",
     "    show(comp(\"ic_zig_bg\", panel), true)"),
    ("the ziggurat never drawn", U,
     "    show(comp(\"ic_zig_bg\", panel), view == \"offices\")",
     "    show(comp(\"ic_zig_bg\", panel), false)"),
    ("qol: the fill tooltip without its plan", U,
     "    for i = 1, #plan do\n        local man = IC.character_by_cqi(faction, plan[i].cqi)",
     "    for i = 1, 0 do\n        local man = IC.character_by_cqi(faction, plan[i].cqi)"),
    ("qol: the fill's answer never says how many", U,
     "        ICUI.notice = string.format(\"%d seat%s filled.\", spare or 0,",
     "        ICUI.notice = string.format(\"%d seat%s done.\", spare or 0,"),
    ("court: the rolled marker never read back", M,
     "    court.rolled = (fields[9] == \"1\") or nil\n",
     "    court.rolled = nil\n"),
    # NOT `if empty` -> `if true`: IC.roll_court refuses a court already
    # rolled, so seeding a loaded court changes no loyalty and that mutant is
    # equivalent code. The load itself is what the old-save check guards.
    ("mct: an old save's court not read back on its first load", M,
     """            local court = IC.load(human[i])
            local empty = true""",
     """            local court = IC.court(human[i])
            local empty = true"""),
    # Living courts.
    ("a stalled office still paying", M,
     """        if court.offices[slug] and not court.stalled[slug] then""",
     """        if court.offices[slug] then"""),
    ("a stall outliving the man it was aimed at", M,
     """        local same = cqi and IC.house_of_cqi(faction_key, cqi) == s.of""",
     """        local same = cqi ~= nil"""),
    ("withholding above the line", P,
     """    if (house.loyalty or 0) > T.withhold_line then return nil end""",
     """    if (house.loyalty or 0) > 100 then return nil end"""),
    ("a settled feud that never ends", P,
     """    a.feuds[rec.a], a.feuds[rec.b] = nil, nil
    a.calm[rec.a] = now + T.party_feud_rest""",
     """    a.calm[rec.a] = now + T.party_feud_rest"""),
    ("every AI court acting every turn", P,
     """    return (cm:model():turn_number() + at) % period == 0""",
     """    return true"""),
    ("news for humans who never met them", M,
     """        if IC.hears(human[i], source_key) then
            local court = IC.court(human[i])""",
     """        if true then
            local court = IC.court(human[i])"""),
    ("a governor's rank giving nothing", M,
     """    return math.floor(rank / IC.TUNE.gov_rank_order_per),""",
     """    return 0 * math.floor(rank / IC.TUNE.gov_rank_order_per),"""),
    ("bystanders not minding rebels", M,
     """        if not seen[key] and key ~= rebels then""",
     """        if false then"""),
    ("a confederated court arriving at the default loyalty", M,
     """    if stamped > 0 and IC.add_house(faction_key, slug, true, loyalty) then""",
     """    if stamped > 0 and IC.add_house(faction_key, slug, true) then"""),
    # AI court loading and rotation, the warning clock and switched-off settings.
    ("an AI court touched before its own turn never loaded from the save", M,
     "    if faction_key and not IC.state[faction_key] then IC.load(faction_key) end",
     "    if false then IC.load(faction_key) end"),
    ("the last warning pinned to warn_turns, which Ruthless never reaches", M,
     """elseif house.clock == math.min(IC.TUNE.warn_turns,
                                               IC.tune(faction_key, "secede_turns") - 1) then""",
     """elseif house.clock == IC.TUNE.warn_turns then"""),
    ("dead courts counted in the AI rotation", P,
     "alive = f and not f:is_null_interface() and not f:is_dead()",
     "alive = f and not f:is_null_interface()"),
    ("a sabotage never raises its card", P,
     """        IC.feed(faction_key, "party_sabotage")
        return true""",
     """        return true"""),
    ("court news to every human who has met the court", M,
     """    if not IC.has_met(human_key, source_key) then return false end
    local ok, runs""",
     """    do return IC.has_met(human_key, source_key) end
    local ok, runs"""),
    ("Provoke starts a countdown with secession off", M,
     """if IC.TUNE.secession ~= false
               and (now <= 0 or now > count) then""",
     """if (now <= 0 or now > count) then"""),
    ("the Crown's card threatens a split the settings switched off", U,
     """if IC.TUNE.crown_split ~= false and IC.grace_left() == 0 then
            if (house.split""",
     """if true then
            if (house.split"""),
    ("an AI court switched off left standing in the save", M,
     'if packed and packed ~= "" then IC.dismantle(faction:name()) end',
     'if packed and packed ~= "" then end'),
    ("an AI ruler never placates", P,
     "        IC.ai_placate(faction_key)\n        IC.ai_weregild(faction_key)",
     "        IC.ai_weregild(faction_key)"),
    ("an away governor's tooltip claims his bonus", U,
     """    if not IC.governor_active(faction, province_key) then
        return string.format("He is away""",
     """    if false then
        return string.format("He is away"""),
    # UI feedback: the effects layer. Each is a plausible slip: the rim written
    # only when there is one (so a recycled card keeps it), the flash painted
    # but not remembered, the marker condition narrowed, the pulse never stopped.
    ("a held seat's rim never lit", U,
     """ICUI.set_rim(card, "card", cqi and look or nil)""",
     """ICUI.set_rim(card, "card", nil)"""),
    ("a stalled seat lit like a working one", U,
     """local stalled = stall ~= nil and stall_left > 0""",
     """local stalled = false"""),
    ("the burst never taken away", U,
     """            if b then b:Destroy() end""",
     """            if false then b:Destroy() end"""),
    ("a second claim finds the old burst and draws nothing", U,
     """        if old then old:Destroy() end""",
     """        if old then return end"""),
    ("a burst created and left hidden", U,
     '''        b:SetVisible(true)
    end)
    if not ok then IC.warn("IRON COURT: the claim burst failed: "''',
     '''        b:SetVisible(false)
    end)
    if not ok then IC.warn("IRON COURT: the claim burst failed: "'''),
    ("a filled seat back to the generic chime", U,
     """            if card then
                ICUI.play(ICUI.SOUNDS[op])""",
     """            if card then
                ICUI.play(ICUI.SOUND_OK)"""),
    ("releasing a governor answered with silence again", U,
     """ICUI.ANSWERS.ungov = confirmed(false, false, "ungov")""",
     """ICUI.ANSWERS.ungov_unused = confirmed(false, false, "ungov")"""),
    ("a yes answered with a chime and no words", U,
     """ICUI.notice = yes and ICUI.answer_text(op, arg, ICUI.player(), spare) or nil""",
     """ICUI.notice = nil"""),
    ("a flash wiped by the click's own redraw", U,
     """    ICUI.set_rim(card, "party", ICUI.flashes[slug])""",
     """    ICUI.set_rim(card, "party", nil)"""),
    ("a flash remembered forever", U,
     """        ICUI.flashes[slug] = nil""",
     """        ICUI.flashes[slug] = ICUI.flashes[slug]"""),
    ("a failed plot flashes nothing", U,
     """if slug then ICUI.flash(slug, "fail") end""",
     """if false then ICUI.flash(slug, "fail") end"""),
    # Plot flashes, tab markers and the button's pulse.
    ("a failed plot flashes the man's number, not his party", U,
     """local slug = target and IC.house_of_cqi(ICUI.player(), target)""",
     """local slug = target and tostring(target)"""),
    ("a demand's row forgets its party", U,
     """{kind = "demand", slug = d.slug}""",
     """{kind = "demand"}"""),
    ("an ungoverned province pulses the button", U,
     """    out.any = out.offices or out.court or out.petitions or out.laws
""",
     """    out.any = out.offices or out.court or out.petitions or out.laws or out.govs
"""),
    ("the summary silent on waiting petitions", U,
     """    if s.petitions > 0 then""",
     """    if false then"""),
    ("the summary silent on ungoverned provinces", U,
     """    if s.unruled > 0 then""",
     """    if false then"""),
    ("a baseline creates a court for a faction with none", U,
     """    local court = IC.state[faction]
    if not court then return end""",
     """    local court = IC.court(faction)
    if not court then return end"""),
    ("the pulse stopped only in the button's current state", U,
     """pulse_uicomponent(button, on, ICUI.PULSE_STRENGTH, false, state)""",
     """pulse_uicomponent(button, on, ICUI.PULSE_STRENGTH, false)"""),
    ("the Offices tab not marked for a seat somebody can take", U,
     """        offices = s.fillable > 0 or #s.ending > 0,""",
     """        offices = #s.ending > 0,"""),
    ("the Petitions tab blind to a demand", U,
     """    s.petitions = a.demand ~= nil and 1 or 0""",
     """    s.petitions = 0"""),
    ("the Court tab blind to a party leaving", U,
     """        court = #s.leaving > 0,""",
     """        court = false,"""),
    ("a governor away marks the Governors tab", U,
     """        if not court.govs[province] then s.unruled = s.unruled + 1 end""",
     """        s.unruled = s.unruled + 1"""),
    ("the markers never drawn", U,
     """    ICUI.draw_marks(panel, faction)
""",
     """    local _ = faction
"""),
    ("the button's pulse never stops", U,
     """        ICUI.pulse_opener(waiting == true)""",
     """        ICUI.pulse_opener(true)"""),
    ("a change coloured before any baseline", U,
     """    local d_loyalty = base and loyalty - base.loyalty or 0""",
     """    local d_loyalty = loyalty - (base and base.loyalty or 0)"""),
    ("a moved number left plain", U,
     """    return string.format("[[col:%s]]%s[[/col]]", n > 0 and "green" or "red", text)""",
     """    return text"""),
    ("the baseline taken at every faction's turn", U,
     """    if faction:name() ~= ICUI.player() then return end
    pcall(ICUI.take_baseline, faction:name())""",
     """    pcall(ICUI.take_baseline, faction:name())"""),

    # Three things the court must not do in silence.
    ("an officer's death that tells nobody", M,
     """            IC.feed(faction_key, "officer_died",""",
     """            IC.feed(faction_key, "officer_gone","""),
    ("a death card that never names the seat", M,
     """                    #seats == 1 and IC.office_title_key(seats[1], faction_key) or nil)""",
     """                    nil)"""),
    ("a death card for a man who held nothing", M,
     """        if not arranged and (#seats > 0 or #provinces > 0) then""",
     """        if not arranged then"""),
    ("a governor's death left off the card", M,
     """        if not arranged and (#seats > 0 or #provinces > 0) then""",
     """        if not arranged and #seats > 0 then"""),
    ("a dead man's province missing from the record", M,
     """            for i = 1, #provinces do
                IC.log(faction_key, "died", slug, provinces[i], 1)""",
     """            for i = 1, 0 do
                IC.log(faction_key, "died", slug, provinces[i], 1)"""),
    ("a dead governor's line reading as a seat's", U,
     """        if e.n == 1 then""",
     """        if e.n == 5 then"""),
    ("the player's own murder announced twice", M,
     """        IC.arranged_deaths[victim:command_queue_index()] = true
        cm:kill_character(cm:char_lookup_str(victim), false)""",
     """        cm:kill_character(cm:char_lookup_str(victim), false)"""),
    ("a feud's murder announced twice", P,
     """            IC.arranged_deaths[victim:command_queue_index()] = true""",
     """"""),
    ("a mark that outlives the death it was for", M,
     """        IC.arranged_deaths[cqi] = nil""",
     """"""),
    ("a party standing down in silence", M,
     """                IC.feed(faction_key, "threat_over")
            end
            house.clock = 0""",
     """            end
            house.clock = 0"""),
    ("your own house standing down in silence", M,
     """            IC.log(faction_key, "snub_off", IC.CROWN, nil, 0)
            IC.feed(faction_key, "threat_over")""",
     """            IC.log(faction_key, "snub_off", IC.CROWN, nil, 0)"""),
    ("your own house standing down with no line in the record", M,
     """            IC.log(faction_key, "snub_off", IC.CROWN, nil, 0)""",
     """"""),
    ("a stall that ended with its man announced as work", M,
     """            if same then back[#back + 1] = {slug = office_slug, of = s.of} end""",
     """            back[#back + 1] = {slug = office_slug, of = s.of}"""),
    ("an office back at work in silence", M,
     """        IC.feed(faction_key, "stall_end",""",
     """        IC.feed(faction_key, "stall_gone","""),
    ("an office back at work with no line in the record", M,
     """        IC.log(faction_key, "stall_end", back[i].of, back[i].slug, 0)""",
     """        IC.log(faction_key, "stall_ended", back[i].of, back[i].slug, 0)"""),
    ("a back-at-work card that never names the seat", M,
     """                #back == 1 and IC.office_title_key(back[1].slug, faction_key) or nil)""",
     """                nil)"""),

    # The party a man sits with, shown on the man.
    ("a party trait that ignores the roll's wrap", M,
     """    return IC.key("member", slug .. "_" .. ((house.tail - 1) % #tails + 1), faction_key)""",
     """    return IC.key("member", slug .. "_" .. house.tail, faction_key)"""),
    ("a confederate party's man wearing no party", M,
     """    if house.confed then return IC.key("member", slug, faction_key) end""",
     """"""),
    ("the sweep blind to the confederate parties", M,
     """        keys[#keys + 1] = IC.rkey("member", R.ORIGINS[i].slug, R)""",
     """"""),
    ("the sweep blind to the rolled parties", M,
     """                keys[#keys + 1] = IC.rkey("member", slug .. "_" .. j, R)""",
     """"""),
    ("a man wearing two parties at once", M,
     """            cm:force_remove_trait(lookup, keys[i])
            moved = true""",
     """            moved = true"""),
    ("a turn that never stamps the parties", M,
     """    IC.stamp_members(faction_key)
""",
     """"""),

    # A sound of its own for each answer.
    ("every petition answer back on one chime", U,
     """            ICUI.confirm(nil, yes, ICUI.SOUNDS[op])""",
     """            ICUI.confirm(nil, yes)"""),
    ("a refused answer in silence", U,
     """            ICUI.notice = ICUI.reason_text(why, spare)
            ICUI.play(ICUI.SOUNDS.refused)
        end""",
     """            ICUI.notice = ICUI.reason_text(why, spare)
        end"""),
    ("a refused pick in silence", U,
     """            ICUI.play(ICUI.SOUNDS.refused)
            return""",
     """            return"""),
    ("a refused fill answer in silence", U,
     """        ICUI.notice = ICUI.reason_text(why, spare)
        ICUI.play(ICUI.SOUNDS.refused)
    end""",
     """        ICUI.notice = ICUI.reason_text(why, spare)
    end"""),
    ("the Fill button's own refusal in silence", U,
     """        ICUI.notice = ICUI.reason_text("no fill")
        ICUI.play(ICUI.SOUNDS.refused)""",
     """        ICUI.notice = ICUI.reason_text("no fill")"""),
    ("a failed plot back on the generic no", U,
     """            ICUI.confirm(nil, false, ICUI.SOUNDS.plot_failed)""",
     """            ICUI.confirm(nil, false)"""),
    ("a landed plot back on the generic yes", U,
     """            else
                ICUI.confirm(nil, true, ICUI.SOUNDS[op])""",
     """            else
                ICUI.confirm(nil, true)"""),
    ("a province given to the ritual sound", U,
     """    gov         = "UI_CAM_Click_Kislev_Select_Available_Atamans",""",
     """    gov         = ICUI.SOUND_SEAT,"""),
    ("two answers sharing one sound", U,
     """    decline     = "UI_CAM_HUD_Diplomacy_Response_Deal_Declined",""",
     """    decline     = "UI_CAM_HUD_Diplomacy_Response_Deal_Accepted","""),
    ("a sacking on the generic no", U,
     """            ICUI.confirm(comp(ICUI.CARD .. "_" .. slot, comp(ICUI.PANEL)), false,
                         ICUI.SOUNDS.dismiss)""",
     """            ICUI.confirm(comp(ICUI.CARD .. "_" .. slot, comp(ICUI.PANEL)), false)"""),
    ("a fill on the generic yes", U,
     """        ICUI.confirm(nil, true, ICUI.SOUNDS.fill)""",
     """        ICUI.confirm(nil, true)"""),

    # A leaving party's posts, and where a governor's bonus lands.
    ("a leaving party's posts looked up after it is gone", M,
     """    local seats, provinces = {}, {}
    for office_slug, cqi in pairs(court.offices) do""",
     """    court.houses[slug] = nil
    local seats, provinces = {}, {}
    for office_slug, cqi in pairs(court.offices) do"""),
    ("a leaving party's term left behind", M,
     """        court.terms[seats[i]] = nil""",
     """"""),
    ("a leaving party's seat that keeps paying", M,
     """    if #seats > 0 then IC.apply_office_bundles(faction_key) end""",
     """"""),
    ("a leaving party's province that keeps its bonus", M,
     """    if #seats > 0 then IC.apply_office_bundles(faction_key) end
    if #provinces > 0 then IC.apply_governor_bundles(faction_key) end""",
     """    if #seats > 0 then IC.apply_office_bundles(faction_key) end"""),
    ("a defecting lord mourned by the Crown", M,
     """                    IC.arranged_deaths[rise.cqi] = "left\"""",
     """"""),
    ("a departing hero mourned by the Crown", M,
     """                IC.arranged_deaths[man.cqi] = "left\"""",
     """"""),
    ("a man who left charged to the Crown anyway", M,
     """        if arranged ~= "left" then""",
     """        if true then"""),
    ("a governor's bonus only where he stands", M,
     """        local region = character and IC.governor_active(faction_key, province_key)
                       and IC.held_region(faction_key, province_key)""",
     """        local province, region = province_of_character(character)
        if not (province and province:key() == province_key) then region = nil end"""),
    ("an away general's province given his bonus", M,
     """        local region = character and IC.governor_active(faction_key, province_key)
                       and IC.held_region(faction_key, province_key)""",
     """        local region = character and IC.held_region(faction_key, province_key)"""),
    ("a governor's bonus on the first province held", M,
     """                    and region:province():key() == province_key then""",
     """                    then"""),
    ("the governors' weight lost on every reload", M,
     """        pcall(IC.refresh_gov_weight, faction_key)""",
     """"""),

    # Provocations, a gone party's business, and the Record's names.
    ("a provocation the next turn forgets", M,
     """                house.provoked = true""",
     """"""),
    ("a provocation that outlives a bribe or an oath", M,
     """        if (house.clock or 0) <= 0 then house.provoked = nil end""",
     """"""),
    ("a provocation that a reload forgets", M,
     """            h.provoked and 1 or 0,""",
     """            0,"""),
    ("a woken rising that runs the dead one's court", M,
     """    if rebels and waking then IC.forget_court(rebels) end""",
     """"""),
    ("a living rising's court wiped by a party joining it", M,
     """    if rebels and waking then IC.forget_court(rebels) end""",
     """    if rebels then IC.forget_court(rebels) end"""),
    ("a gone party's business left before the court", M,
     """    if IC.drop_party_business then IC.drop_party_business(faction_key, slug) end""",
     """"""),
    ("a gone party's demand left open", P,
     """    if a.demand and a.demand.slug == slug then IC.settle_demand(faction_key, "void") end""",
     """"""),
    ("a gone party's plot still being prepared", P,
     """        a.plot = nil
    end
    IC.expire_offers(faction_key)""",
     """    end
    IC.expire_offers(faction_key)"""),
    ("a gone party's plot dropped in silence", P,
     """        IC.feed(faction_key, "party_plot_dropped")
        a.plot = nil""",
     """        a.plot = nil"""),
    ("a gone party's offer left open", P,
     """    IC.expire_offers(faction_key)
    IC.end_feuds(faction_key)""",
     """    IC.end_feuds(faction_key)"""),
    ("a gone party's feud left running", P,
     """    IC.end_feuds(faction_key)
    IC.save_agenda(faction_key)
end""",
     """    IC.save_agenda(faction_key)
end"""),
    ("a plotter never told his seat is at stake", M,
     """        if cqi == actor_cqi and office and after < IC.tier_influence(office.tier) then""",
     """        if false then"""),
    ("a plotter left exactly at his bar told he loses it", M,
     """        if cqi == actor_cqi and office and after < IC.tier_influence(office.tier) then""",
     """        if cqi == actor_cqi and office and after <= IC.tier_influence(office.tier) then"""),
    ("a plotter warned about somebody else's seat", M,
     """        if cqi == actor_cqi and office and after < IC.tier_influence(office.tier) then""",
     """        if office and after < IC.tier_influence(office.tier) then"""),
    ("a seat at stake with no word on the button", U,
     """        if loses then
            tip = string.format(""",
     """        if false then
            tip = string.format("""),
    ("a seat at stake drawn like any other row", U,
     '            loses and ICUI.red(string.format("%d influence: %s", has, holds))',
     '            false and ICUI.red(string.format("%d influence: %s", has, holds))'),
    ("a mood word on a fixed line", U,
     """    if house.loyalty <= IC.TUNE.party_intrigue_line then return "RESTLESS" end""",
     """    if house.loyalty <= 55 then return "RESTLESS" end"""),
    ("a Record line that keeps no name for its party", M,
     """        sw = IC.who_was(faction_key, slug),""",
     """        sw = nil,"""),
    ("a Record line that keeps no name for its target", M,
     """        kw = IC.who_was(faction_key, key),""",
     """        kw = nil,"""),
    ("a Record's names lost in the save", M,
     """            tostring(e.n or 0), e.sw or "-", e.kw or "-")""",
     """            tostring(e.n or 0), "-", "-")"""),
    ("a Record's names never read back", M,
     """                sw   = bits[6] ~= "-" and bits[6] or nil,""",
     """                sw   = nil,"""),
    ("a party's name forgotten the moment it leaves", M,
     """    IC.departed[faction_key .. "|" .. slug] = IC.who_was(faction_key, slug)
""",
     """"""),
    ("a confederate party kept in the Record as nobody", M,
     """    if house.confed then return "c" end""",
     """"""),
    ("a Record line named as the court stands now", U,
     """    local house = ICUI.logged_name(e.slug, e.sw)""",
     """    local house = ICUI.house_name(e.slug)"""),
    ("a confederate party that left read as its slug", U,
     """    if who == "c" then
        local came_from""",
     """    if false then
        local came_from"""),
    ("an influence plate for another race's lord", U,
     """    if not faction or not ICUI.court_player() then return hide() end""",
     """    if not faction then return hide() end"""),
    # Insults, lost demands, and the Dwarf court's own words and paint.
    ("a dismissed man seated again at once", M,
     """        court.last[office_slug] = {cqi = cqi, turn = cm:model():turn_number()}
    end""",
     """    end"""),
    ("a bribe that wipes the insult", M,
     """        if house then house.clock = 0 end
    elseif plot_key == "discredit" then""",
     """        if house then house.clock = 0; house.snubbed = nil end
    elseif plot_key == "discredit" then"""),
    ("a pledge that wipes the insult", M,
     """        if house then house.clock = 0 end
        local crown = IC.court(faction_key).houses[IC.CROWN]""",
     """        if house then house.clock = 0; house.snubbed = nil end
        local crown = IC.court(faction_key).houses[IC.CROWN]"""),
    ("an insult's seat lost in the save", M,
     """            h.snub_key or "-")""",
     """            "-")"""),
    ("an insult's seat never read back", M,
     """                snub_key = bits[20] ~= "-" and bits[20] or nil,""",
     """                snub_key = nil,"""),
    ("a dead governor's bonus left on his province", M,
        """        if #provinces > 0 then IC.apply_governor_bundles(faction_key) end
        IC.save(faction_key)
    end, true)""",
        """        IC.save(faction_key)
    end, true)"""),
    ("the Court tab naming the last countdown", U,
     """        if (house.clock or 0) > 0 and (not soonest or house.clock < soonest) then""",
     """        if (house.clock or 0) > 0 then"""),
    ("the Court tab saying turns of one", U,
     """                                 house.clock == 1 and "" or "s")
        end
    end""",
     """                                 "s")
        end
    end"""),
    ("Accept on a lost demand that refuses it", P,
     """    if state == "refused" then return false, "taken" end""",
     """"""),
    ("a lost demand's Accept with no reason", U,
     """            tip = not may and ICUI.reason_text(why, spare) or nil,""",
     """"""),
    ("the calm offer promising the gross figure", U,
     """        local net = o.n - IC.TUNE.party_offer_envy""",
     """        local net = o.n"""),
    ("a greyed slider that names no number", S,
     '                lock(o, true, string.format("Your difficulty sets this to "\n                    .. "%s. Choose Custom to edit it.", tostring(v)))',
     """                lock(o, true, "Set by the difficulty above. Choose Custom to edit it.")"""),
    ("a greyed slider naming the default under every difficulty", S,
     """                local set = PRESET_VALUES[preset] or {}""",
     """                local set = {}"""),
    ("a failed errand logged against a party", M,
     """               or plot_key, cost)""",
     """               or against, cost)"""),
    ("a button tip that names the move in the Chaos Dwarfs' words", U,
     """        local plot = ICUI.plot_of(move.plot, faction)
        local leader = IC.party_leader(faction, slug)""",
     """        local plot = IC.plot_by_key(move.plot)
        local leader = IC.party_leader(faction, slug)"""),
    ("a favour's tip that names it in the Chaos Dwarfs' words", U,
     """        local favour = ICUI.favour_of(move.favour, faction)""",
     """        local favour = IC.favour_by_key(move.favour)"""),
    ("a move label in the Chaos Dwarfs' words", U,
     """    local plot = ICUI.plot_of(plot_key)
    if not plot then return tostring(plot_key) end""",
     """    local plot = IC.plot_by_key(plot_key)
    if not plot then return tostring(plot_key) end"""),
    ("a mission picker title in the Chaos Dwarfs' words", U,
     """    local plot = ICUI.pick.plot and ICUI.plot_of(ICUI.pick.plot)""",
     """    local plot = ICUI.pick.plot and IC.plot_by_key(ICUI.pick.plot)"""),
    ("a move card in the Chaos Dwarfs' words", U,
     """        local plot = ICUI.plot_at[i] and ICUI.plot_of(ICUI.plot_at[i].key, faction)""",
     """        local plot = ICUI.plot_at[i]"""),
    ("a failed mission's record line in the Chaos Dwarfs' words", U,
     """        local sent = mission and ICUI.plot_of(mission)""",
     """        local sent = mission and IC.plot_by_key(mission)"""),
    ("a government card short of influence that hides by how much", U,
     """    if why == "gov_purse" then return "Short " .. ICUI.cost(turns or 0) end""",
     """    if why == "gov_purse" then return "Short" end"""),
    ("a Dwarf government card in Chaos Dwarf paint", U,
     """    local own = (ICUI.ART or {}).gov_art""",
     """    local own = nil"""),
    ("a Dwarf law card in Chaos Dwarf paint", U,
     """    local own = (ICUI.ART or {}).law_art""",
     """    local own = nil"""),
    ("a Dwarf move card wearing the Chaos Dwarf icon", U,
     """                         effect_no_secession = effect_ns, icon = icon}, {__index = plot})""",
     """                         effect_no_secession = effect_ns}, {__index = plot})"""),
    ("a Dwarf Help page wearing the Chaos Dwarf move icons", U,
     """    local move = ICUI.plot_of(name)""",
     """    local move = IC.plot_by_key(name)"""),
    ("a Dwarf shared button left in CA's red", U,
     """    local names = {"ic_card_button", "ic_plot_go", "ic_row_e", "ic_row_f"}""",
     """    local names = {}"""),
    ("a Dwarf chosen law glowing Hell-Forge red", U,
     """                card:SetImagePath(chosen and ICUI.law_glow() or ICUI.MASK_NONE, ICUI.LAW_GLOW_INDEX)""",
     """                card:SetImagePath(chosen and ICUI.LAW_GLOW or ICUI.MASK_NONE, ICUI.LAW_GLOW_INDEX)"""),
    ("a Dwarf party block's Win left red", U,
     """        ICUI.skin_buttons(comp(ICUI.LAWBLOCK .. "_" .. i, panel))""",
     """        local _ = i"""),
    ("a refused Chaos Dwarf button left red on CA's red plate", U,
     """    local theme = (ICUI.ART or {}).theme or ICUI.DEFAULT_SKIN""",
     """    local theme = (ICUI.ART or {}).theme if not theme then return end"""),
    ("a refused Dwarf button left on the blue plate", U,
     """    if ICUI.grey_refused then ICUI.grey_refused(c, text) end""",
     """    local _ = text"""),
    ("a refused Dwarf button's words left red on grey", U,
     """        if inner then pcall(function() c:SetText(inner, \"\") end) end""",
     """        local _ = inner"""),
    ("a refused Dwarf button's words in black on the dark grey", U,
     """        if inner then pcall(function() c:SetText(inner, \"\") end) end""",
     """        if inner then pcall(function() c:SetText(ICUI.lit_word(inner, true), \"\") end) end"""),
    ("a Dwarf themed path left in CA's red", U,
     """    return theme .. string.sub(path, #base + 1)""",
     """    return path"""),
    ("a Dwarf Governors row left in CA's red", UM,
     """        row:SetImagePath(ICUI.themed(art[1]), 0)""",
     """        row:SetImagePath(art[1], 0)"""),
    ("a Dwarf Governors toggle left in CA's red", UM,
     """                tog:SetImagePath(ICUI.themed(art[1]), ICUI.GM_TOG_ART[1])""",
     """                tog:SetImagePath(art[1], ICUI.GM_TOG_ART[1])"""),
    ("a Dwarf map pin in Chaos Dwarf paint", UM,
     """                if art.gm_pin then pcall(function() pin:SetImagePath(art.gm_pin, 0) end) end""",
     """                local _ = art.gm_pin"""),
    ("a Dwarf pin's name plate in Chaos Dwarf paint", UM,
     """                if art.gm_name then pcall(function() plate:SetImagePath(art.gm_name, 0) end) end""",
     """                local _ = art.gm_name"""),
    ("a Dwarf pin's loyalty plate in Chaos Dwarf paint", UM,
     """                if art.gm_loyal then pcall(function() loyal:SetImagePath(art.gm_loyal, 0) end) end""",
     """                local _ = art.gm_loyal"""),
    ("a Dwarf trait icon left Chaos Dwarf", U,
     """    ICUI.TRAIT_ICON = ICUI.ART.trait_icon or ICUI.CHD_TRAIT_ICON""",
     """    local _ = ICUI.ART.trait_icon"""),
    ("a Dwarf sort arrow left in CA's red", U,
     """    if not index or ICUI.sort[view] ~= index then return ICUI.themed(ICUI.SORT_ARROW.down) end""",
     """    if not index or ICUI.sort[view] ~= index then return ICUI.SORT_ARROW.down end"""),
    ("a Dwarf law card's vote mark in Hell-Forge heat", U,
     """                pcall(function() comp("ic_law_mark", card):SetImagePath(ICUI.ART.mark, 0) end)""",
     """                local _ = card"""),
    ("a Dwarf list's scrollbar handle left red", U,
     """            ICUI.skin_handle(handle)
        end
        show(slider, lines > s.lines)""",
     """        end
        show(slider, lines > s.lines)"""),
    ("a Dwarf Governors scrollbar handle left red", UM,
     """            ICUI.skin_handle(handle)
        end
        show(slider, n > ICUI.GM_ROWS)""",
     """        end
        show(slider, n > ICUI.GM_ROWS)"""),
    ("a Chaos Dwarf handle repainted with no theme", U,
     """    if not (handle and (ICUI.ART or {}).theme) then return end""",
     """    if not handle then return end"""),
    ("a Dwarf envoy province list reading the Chaos Dwarf bundles", U,
     """            for _, task in ipairs(IC.envoy_tasks(faction)) do
                local left""",
     """            for _, task in ipairs(IC.ENVOY_TASKS) do
                local left"""),
    ("a Dwarf envoy offered the Chaos Dwarf tasks", U,
     """        for _, task in ipairs(IC.envoy_tasks(faction)) do
            add({task.name""",
     """        for _, task in ipairs(IC.ENVOY_TASKS) do
            add({task.name"""),
    ("a Dwarf envoy's record line losing its task", U,
     """        local province, task = IC.envoy_split(e.key, ICUI.player())""",
     """        local province, task = IC.envoy_split(e.key)"""),
    ("a Dwarf envoy mission's place losing its task", U,
     """        local province, task = IC.envoy_split(target, ICUI.player())""",
     """        local province, task = IC.envoy_split(target)"""),
    ("a Dwarf influence readout on the Hell-Forge plate", U,
     """        if not plate then return hide() end
        ICUI.race_plate(plate)""",
     """        if not plate then return hide() end"""),
    ("a Dwarf governor note on the Hell-Forge plate", U,
     """        if not note then return nil end
        ICUI.race_plate(note)""",
     """        if not note then return nil end"""),
    ("a race plate read off nothing", U,
     """    local note = ((ICUI.race() or {}).art or {}).note""",
     """    local note = nil"""),
    ("a Chaos Dwarf readout repainted", U,
     """    if c and note then pcall(function() c:SetImagePath(note, 0) end) end""",
     """    if c then pcall(function() c:SetImagePath(note or "x.png", 0) end) end"""),
    ("a Dwarf list row's button left red", U,
     """ICUI.PLATE_BUTTONS = {ic_card_button = true, ic_plot_go = true, ic_row_e = true,""",
     """ICUI.PLATE_BUTTONS = {ic_card_button = true, ic_plot_go = true,"""),
    ("every red caption greyed as if a button", U,
     """    return ICUI.PLATE_BUTTONS[id] or string.match(id, "^ic_lb_win_%d+$") ~= nil""",
     """    return true or string.match(id, "^ic_lb_win_%d+$") ~= nil"""),
    ("a failed errand's line naming no errand", U,
     """        local errand = not e.key or ICUI.plot_of(e.key)""",
     """        local errand = not e.key"""),
    ("a failed errand's notice that somebody knows", U,
     '                ICUI.notice = "The move failed. The influence is spent."\n            end',
     """            end"""),
    ("a poor plotter told about a seat", U,
     """            "He is %d influence short.",""",
     """            "He has not the influence for that seat - %d short.","""),
    ("Provoke promising a count with secession off", U,
     """        lines[2] = IC.TUNE.secession == false and plot.effect_no_secession
                   or ICUI.plot_effect(plot, faction)""",
     """        lines[2] = ICUI.plot_effect(plot, faction)"""),
    ("a lapsed demand's reason never written", P,
     """        IC.log(faction_key, "demand_void", d.slug, d.key, IC.VOID_REASONS[why] or 0)""",
     """        IC.log(faction_key, "demand_void", d.slug, d.key, 0)"""),
    ("a lost province read as a man gone", P,
     """        if not held then return "void", "lost" end""",
     """        if not held then return "void", "gone" end"""),
    ("a short man read as a man gone", P,
     """            return "void", "short\"""",
     """            return "void", "gone\""""),
    ("a lost province's line read as a man gone", U,
     """        if e.n == IC.VOID_REASONS.lost then""",
     """        if false then"""),
    ("the control band a move reaches left for next turn", M,
     """    if done then IC.apply_control_bundle(faction_key) end""",
     """"""),
    ("a party at the breaking point on no list", U,
     """        if IC.at_breaking_point(faction, seated[i]) then""",
     """        if false then"""),
    ("a breaking party counted with secession off", M,
     """    if not IC.secession_on() or not slug or slug == IC.CROWN then return false end""",
     """    if not slug or slug == IC.CROWN then return false end"""),
    ("a breaking party's card reading PLOTTING", U,
     """    elseif IC.secession_on() and house.loyalty <= IC.TUNE.secede_break then""",
     """    elseif false then"""),
    ("a busy man free to take his old seat", U,
     """            local man = last and not posted[last.cqi]""",
     """            local man = last"""),
    ("the split tooltip printing a weight as a share", U,
     """            .. "share of the court.\"""",
     """            .. "share of the court, 5% of it.\""""),
    ("risings left out of the rotation", P,
     """    for i = 1, #R.REBEL_POOL do candidates[#candidates + 1] = R.REBEL_POOL[i] end""",
     """"""),
    ("a placated mark kept from an earlier turn", P,
     """    p.placated = (house and move and (house.loyalty or 0) > move.line) or nil""",
     """    if house and move and (house.loyalty or 0) > move.line then p.placated = true end"""),
    # Burst and flash timers.
    ("an old burst's timer taking the new one away", U,
     """        if ICUI.burst_n[host_name] ~= n then return end""",
     """"""),
    ("an old flash's timer putting out the new one", U,
     """        if ICUI.flash_n[slug] ~= n then return end""",
     """"""),
    ("a flash held for a card the tab does not draw", U,
     """    local card = ICUI.party_card(slug)
    if not card then return end
    local n = (ICUI.flash_n[slug] or 0) + 1""",
     """    local card = ICUI.party_card(slug)
    local n = (ICUI.flash_n[slug] or 0) + 1"""),
    ("a failed plot drawn in the lit rim's red", U,
     """(name == "fail" and ICUI.RIM_ART_FAIL or ICUI.RIM_ART)""",
     """ICUI.RIM_ART"""),
    ("a failed plot flashing as if it had worked", U,
     """if slug then ICUI.flash(slug, "fail") end""",
     """if slug then ICUI.flash(slug, "lit") end"""),
    # The plate that sticks after a close.
    ("the plate redrawn from a panel on its way out", U,
     """    ICUI.standing_shut = true
    ICUI.show_standing()""",
     """    ICUI.show_standing()"""),
    ("a queued redraw bringing a shut plate back", U,
     """    if ICUI.standing_shut then return hide() end""",
     """"""),
    ("the plate never coming back after one close", U,
     """    ICUI.standing_shut = nil
    cm:callback(function() ICUI.show_standing() end, 0)""",
     """    cm:callback(function() ICUI.show_standing() end, 0)"""),
    # Splits, figures left bare, and the help page's pictures.
    ("a split leaving its men's seats' weight on the Crown", M,
     """            crown.weight = math.max(1, crown.weight - IC.office_weight(office_slug, IC.CROWN, faction_key))
""",
     """"""),
    ("a split giving the new party none of its men's seats' weight", M,
     """            house.weight = house.weight + IC.office_weight(office_slug, slug, faction_key)
""",
     """"""),
    ("a party's end leaving its man his title", M,
     """            cm:force_remove_trait(cm:char_lookup_str(man), IC.office_trait(seats[i], faction_key))
""",
     """"""),
    ("a release of nobody written to the record", M,
     """    if not court.govs[province_key] then return false end
    IC.log(faction_key, "gov_off",
           IC.house_of_cqi(faction_key, court.govs[province_key]),
           province_key, 0)
""",
     """    IC.log(faction_key, "gov_off",
           IC.house_of_cqi(faction_key, court.govs[province_key] or -1),
           province_key, 0)
    if not court.govs[province_key] then return false end
"""),
    ("an AI court's rolled birthplace left on its men", M,
     """            cm:force_remove_trait(cm:char_lookup_str(man), IC.origin_trait(had))
""",
     """"""),
    ("a party paying for its move before its odds are read", P,
     """    local cost = IC.plot_cost(move, faction_key)
    local base = T["plot_chance_" .. move] or 0
    local edge = math.floor((IC.standing(faction_key, actor)
                             - IC.standing(faction_key, target)) / 10)
                 * T.plot_chance_per_10
    local chance = math.max(T.plot_chance_min,
                            math.min(T.plot_chance_max, base + edge))
    if odds_div then
        chance = math.max(T.plot_chance_min, math.floor(chance / odds_div))
    end
    -- THE ODDS BEFORE THE PRICE, as IC.plot reads them.
    IC.add_standing(faction_key, actor, -cost)
""",
     """    local cost = IC.plot_cost(move, faction_key)
    IC.add_standing(faction_key, actor, -cost)
    local base = T["plot_chance_" .. move] or 0
    local edge = math.floor((IC.standing(faction_key, actor)
                             - IC.standing(faction_key, target)) / 10)
                 * T.plot_chance_per_10
    local chance = math.max(T.plot_chance_min,
                            math.min(T.plot_chance_max, base + edge))
    if odds_div then
        chance = math.max(T.plot_chance_min, math.floor(chance / odds_div))
    end
"""),
    ("Refuse on a taken post answering that it failed", P,
     """    if state and state ~= "refused" then""",
     """    if state then"""),
    ("the button's tooltip written from every faction's turn start", U,
     """    ICUI.place_opener(1, true)""",
     """    ICUI.place_opener(1)"""),
    ("the button's tooltip written from the player's turn end", U,
     """    if comp(ICUI.PANEL) then pcall(ICUI.close, true) end""",
     """    if comp(ICUI.PANEL) then pcall(ICUI.close) end"""),
    ("the murder card printing only the plot's own penalty", M,
     """         IC.TUNE.plot_murder_loyalty - IC.TUNE.loyalty_member_died),""",
     """         IC.TUNE.plot_murder_loyalty),"""),
    ("a purge that landed bursting the player's own card", U,
     """    if slug == IC.CROWN then return nil end
    return slug""",
     """    return slug"""),
    ("news printing a confederate party's key", U,
     """    if hall then return loc("factions_screen_name_" .. hall, v) end""",
     """"""),
    ("a late multiplayer answer writing to a shut court", U,
     """    if mp and not comp(ICUI.PANEL) then return end
""",
     """"""),
    ("a turn ending on a band it does not wear", M,
     """    IC.apply_control_bundle(faction_key)
    -- THE BOOK, caught""",
     """    -- THE BOOK, caught"""),
    ("a rising soured by asking with an interface", M,
     """now = a:diplomatic_standing_with(other)""",
     """now = a:diplomatic_standing_with(b)"""),
    ("a counting party at the breaking point drawn with its count", U,
     """    elseif IC.secession_on() and house.loyalty <= IC.TUNE.secede_break then
        return "SECEDES 1"
    elseif (house.clock or 0) > 0 then
        return string.format("SECEDES %d", house.clock)
""",
     """    elseif (house.clock or 0) > 0 then
        return string.format("SECEDES %d", house.clock)
    elseif IC.secession_on() and house.loyalty <= IC.TUNE.secede_break then
        return "SECEDES 1"
"""),
    ("the summary giving a breaking party its count", U,
     """        if IC.at_breaking_point(faction, seated[i]) then
            s.leaving[#s.leaving + 1] = {slug = seated[i], clock = 1}
        elseif seated[i] ~= IC.CROWN and house and (house.clock or 0) > 0 then""",
     """        if seated[i] ~= IC.CROWN and house and (house.clock or 0) > 0 then
            s.leaving[#s.leaving + 1] = {slug = seated[i], clock = house.clock}
        elseif IC.at_breaking_point(faction, seated[i]) then"""),
    ("a breaking party's card drawn with its business", U,
     """string.match(word, "^SECEDES")""",
     """(house.clock or 0) > 0"""),
    ("PLOTTING drawn with the parties switched off", U,
     """    elseif IC.TUNE.parties_act ~= false
            and house.loyalty""",
     """    elseif house.loyalty"""),
    ("PLOTTING drawn above a low intrigue line", U,
     """math.min(25, IC.TUNE.party_intrigue_line) then""",
     """25 then"""),
    ("a click on the loading screen asking for a UI not built yet", U,
     """    if not parent and not core:is_ui_created() then return nil end
""",
     """"""),
    ("a marked figure marked a second time", U,
     """"([^%]%d%%%.%+%-])([%+%-]?%d+) (%a+)\"""",
     """"([^%d%%%.%+%-])([%+%-]?%d+) (%a+)\""""),
    ("a figure a turn away wearing no hourglass", U,
     """    turn = ICUI.TURNS_ICON,
""",
     """"""),
    ("the Record's figures left bare", U,
     """ICUI.units(a.text)""",
     """a.text"""),
    ("the notice's figures left bare", U,
     """set_text(alert, ICUI.units(text))""",
     """set_text(alert, text)"""),
    ("a row button's tooltip figures left bare", U,
     """c:SetTooltipText(ICUI.units(tip), "", true)""",
     """c:SetTooltipText(tip or "", "", true)"""),
    ("a petition's figures left bare", U,
     """    for i = 1, #lines do lines[i][2] = ICUI.units(lines[i][2]) end
""",
     """"""),
    ("the opener tooltip's figures left bare", U,
     """return "The Iron Court||" .. ICUI.units(table.concat(lines, "\\n"))""",
     """return "The Iron Court||" .. table.concat(lines, "\\n")"""),
    ("the court share in the opener left bare", U,
     """            ICUI.cost(IC.control(faction)), ICUI.band_name(IC.control_band(faction)))""",
     """            IC.control(faction), ICUI.band_name(IC.control_band(faction)))"""),
    ("an agenda's figures left bare", U,
     """    return ICUI.units(table.concat(parts, "\\n\\n"))""",
     """    return table.concat(parts, "\\n\\n")"""),
    ("a move tooltip's figures left bare", U,
     """    return ICUI.units(table.concat(lines, "\\n"))""",
     """    return table.concat(lines, "\\n")"""),
    ("a loyalty breakdown's figures left bare", U,
     """    return ICUI.units(table.concat(out, "\\n"))""",
     """    return table.concat(out, "\\n")"""),
    ("a trait in the breakdown named without its picture", U,
     """        if terms[i].trait then label = ICUI.trait_line(label) end
""",
     """"""),
    ("the character plate's figure left bare", U,
     """    return ICUI.cost(IC.standing(faction_key, cqi)) .. " influence\"""",
     """    return IC.standing(faction_key, cqi) .. " influence\""""),
    ("the help page's pictures never drawn", U,
     """        return ICUI.help_icon(name) and string.format("[[img:%s]][[/img]]", ICUI.help_icon(name)) or nil""",
     """        return nil"""),
    ("a move named on the help page without its card's picture", U,
     """    return ICUI.HELP_ICONS[name] or (move and move.icon) or nil""",
     """    return ICUI.HELP_ICONS[name] or nil"""),
    ("a help topic button with no picture", U,
     """topic and (ICUI.help_fill("{@" .. tostring(topic.icon)
                .. "}", {}) .. topic.title) or "")""",
     """topic and topic.title or "")"""),
    ("a help heading with no picture", U,
     """    set_text(head, ICUI.help_fill("{@" .. tostring(ICUI.HELP[page].icon) .. "}", {})
                   .. ICUI.HELP[page].title)""",
     """    set_text(head, ICUI.HELP[page].title)"""),
    ("the heading's picture left out of its plate", U,
     """ICUI.HEADING_CAP, true, 1)""",
     """ICUI.HEADING_CAP, true)"""),
    ("a plate's picture charged nothing", U,
     """    got = got + (pics or 0) * (line_h or ICUI.PLATE_EST * 2)
""",
     """"""),
    # Card prompts at roll time, gifts, and a governor's public order.
    ("the court's roll asking a card for every origin", M,
     """            if IC.stamp_origin(character, IC.origin_for(character, faction_key), true) then""",
     """            if IC.stamp_origin(character, IC.origin_for(character, faction_key)) then"""),
    ("the court's roll asking a card for every background", M,
     """                       IC.background_for(character, faction_key, tally), true) then""",
     """                       IC.background_for(character, faction_key, tally)) then"""),
    ("a confederation asking a card for every origin", M,
     """        if IC.stamp_origin(man, want, true) or had == want then""",
     """        if IC.stamp_origin(man, want) or had == want then"""),
    ("a confederation asking a card for every background", M,
     """        IC.stamp_bg(man, IC.background_for(man, faction_key, tally), true)""",
     """        IC.stamp_bg(man, IC.background_for(man, faction_key, tally))"""),
    ("an origin stamped loud whoever asked for quiet", M,
     """                       IC.origin_trait(slug), not quiet)""",
     """                       IC.origin_trait(slug), true)"""),
    ("a background stamped loud whoever asked for quiet", M,
     """                       IC.bg_trait(slug), not quiet)""",
     """                       IC.bg_trait(slug), true)"""),
    ("a new recruit's origin given in silence", M,
     """                       IC.origin_trait(slug), not quiet)""",
     """                       IC.origin_trait(slug), false)"""),
    ("a gift handing back no count of what it gave", M,
     """    return true, nil, gained
end""",
     """    return true
end"""),
    ("a gift counting its worth, not its gain", M,
     """        gained = (house.loyalty or was) - was""",
     """        gained = IC.TUNE.favour_gift_loyalty"""),
    ("a gift's tooltip promising more than fits", U,
     """math.max(0, math.min(IC.TUNE.favour_gift_loyalty, 100 - now)), now)""",
     """IC.TUNE.favour_gift_loyalty, now)"""),
    ("a gift's answer quoting its worth, not its gain", U,
     """            name, spare or T.favour_gift_loyalty or 0)""",
     """            name, T.favour_gift_loyalty or 0)"""),
    ("the answer sentence never told what the model counted", U,
     """ICUI.answer_text(op, arg, ICUI.player(), spare)""",
     """ICUI.answer_text(op, arg, ICUI.player())"""),
    ("a landed plot's burst on the card before the redraw", U,
     """                if slug then
                    ICUI.refresh()
                    target = ICUI.party_card(slug)""",
     """                if slug then
                    target = ICUI.party_card(slug)"""),
    ("a landed plot drawing no burst", U,
     """            elseif target then
                ICUI.play(ICUI.SOUNDS[op])
                ICUI.burst(target:Id())""",
     """            elseif target then
                ICUI.play(ICUI.SOUNDS[op])"""),
    ("a governor in place said to add public order", U,
     """    return string.format("At rank %d he adds +%d control and +%d%% \"""",
     """    return string.format("At rank %d he adds +%d public order and +%d%% \""""),
    ("a governor away said to add public order", U,
     """            .. "he returns. At rank %d he would add +%d control and +%d%% \"""",
     """            .. "he returns. At rank %d he would add +%d public order and +%d%% \""""),
    ("a gone party's business cleared and never saved", P,
     """    IC.end_feuds(faction_key)
    IC.save_agenda(faction_key)
end""",
     """    IC.end_feuds(faction_key)
end"""),
    # THE GRACE PERIOD.
    ("the grace period one turn short", M,
     """    return math.max(0, IC.TUNE.grace_turns + 1 - cm:model():turn_number())""",
     """    return math.max(0, IC.TUNE.grace_turns - cm:model():turn_number())"""),
    ("secession on in the grace period", M,
     """    return IC.TUNE.secession ~= false and IC.grace_left() == 0""",
     """    return IC.TUNE.secession ~= false"""),
    ("a countdown started in the grace period", M,
     """    if not IC.secession_on() then
        for _slug, house in pairs(court.houses) do house.clock = 0 end""",
     """    if not IC.TUNE.secession then
        for _slug, house in pairs(court.houses) do house.clock = 0 end"""),
    ("a party pressed in the grace period", M,
     """    if not IC.TUNE.pressure or IC.grace_left() > 0 or not IC.is_human(faction_key) then""",
     """    if not IC.TUNE.pressure or not IC.is_human(faction_key) then"""),
    ("the Crown split in the grace period", M,
     """    if not IC.TUNE.crown_split or IC.grace_left() > 0 then""",
     """    if not IC.TUNE.crown_split then"""),
    ("the Crown's card threatening a split in the grace period", U,
     """if IC.TUNE.crown_split ~= false and IC.grace_left() == 0 then""",
     """if IC.TUNE.crown_split ~= false then"""),
    ("the protection never said", U,
     """    if IC.TUNE.secession ~= false and grace > 0 then""",
     """    if false then"""),
    ("the protection said with secession switched off", U,
     """    if IC.TUNE.secession ~= false and grace > 0 then""",
     """    if grace > 0 then"""),
    ("Provoke sent in the grace period", M,
     """    if plot_key == "provoke" and IC.TUNE.secession ~= false
            and IC.grace_left() > 0 then""",
     """    if false then"""),
    ("Provoke refused in the grace period with secession off", M,
     """    if plot_key == "provoke" and IC.TUNE.secession ~= false
            and IC.grace_left() > 0 then""",
     """    if plot_key == "provoke" and IC.grace_left() > 0 then"""),
    ("Provoke's refusal counting the wrong turns", U,
     '            .. "countdown cannot begin yet.", left, left == 1 and "" or "s")',
     '            .. "countdown cannot begin yet.", 10, left == 1 and "" or "s")'),
    ("the protection said to last one turn longer", U,
     """            .. "for %d more turn%s.", grace, grace == 1 and "" or "s")""",
     """            .. "for %d more turn%s.", grace + 1, grace == 1 and "" or "s")"""),
    # THE CIVIL MISSIONS.
    ("an envoy's work on the wrong province", M,
     """            IC.held_region(faction_key, province), IC.TUNE.mission_turns)""",
     """            IC.held_region(faction_key, IC.seats(faction_key)[1]), IC.TUNE.mission_turns)"""),
    ("an envoy's work forever", M,
     """            IC.held_region(faction_key, province), IC.TUNE.mission_turns)""",
     """            IC.held_region(faction_key, province), -1)"""),
    ("the same work sent twice", M,
     """    if left then return false, "running", left end""",
     """"""),
    ("a lost province still sent to", M,
     """    if not held then return false, "lost" end""",
     """"""),
    ("an unknown task sent", M,
     """    if not task then return false, "no such task" end
    local left""",
     """    local left"""),
    # NOT the return line: "if not ok then return false, why, short end" is
    # already in the model twice before can_plot gains a third.
    ("a refusal's turns dropped by can_plot", M,
     """    local ok, why, short = IC.may_target(faction_key, plot_key, target)""",
     """    local ok, why = IC.may_target(faction_key, plot_key, target)"""),
    ("a failed mission logged without its place", M,
     """               or (plot.target and (plot_key .. ":" .. tostring(target)))""",
     """               or (plot.target and plot_key)"""),
    ("a mission's success logged without its place", M,
     """           plot.target and target or against, cost)""",
     """           against, cost)"""),
    ("grudge: the weregild logged as the man sent's payment", M,
     """    IC.log(faction_key, plot_key, plot.gold and IC.CROWN or slug,""",
     """    IC.log(faction_key, plot_key, slug,"""),
    ("grudge: a last-turn dismissal writes a grudge", M,
     """        if not ending then IC.grudge_write(faction_key, slug, "dismiss") end""",
     """        IC.grudge_write(faction_key, slug, "dismiss")"""),
    ("the diplomatic bonus the wrong way round", M,
     """        cm:apply_dilemma_diplomatic_bonus(faction_key, target, IC.TUNE.diplomats_bonus)""",
     """        cm:apply_dilemma_diplomatic_bonus(target, faction_key, IC.TUNE.diplomats_bonus)"""),
    ("diplomats never resting", M,
     """        court.sent[target] = cm:model():turn_number()""",
     """"""),
    ("the rest one turn long", M,
     """        local left = sent + IC.TUNE.diplomats_rest - cm:model():turn_number()""",
     """        local left = sent + IC.TUNE.diplomats_rest + 1 - cm:model():turn_number()"""),
    ("diplomats to the unmet", M,
     """    if not met then return false, "unmet" end""",
     """"""),
    ("diplomats to rebels", M,
     """    if them:is_rebel() then return false, "rebel" end""",
     """"""),
    ("diplomats to another player", M,
     """    if them:is_human() then return false, "player" end""",
     """"""),
    ("diplomats to the dead", M,
     """    if not them or them:is_null_interface() or them:is_dead() then""",
     """    if not them or them:is_null_interface() then"""),
    ("the rest not saved", M,
     """                 join(stalled, ";"), join(news, ";"), join(sent, ";"), gov, join(renown""",
     """                 join(stalled, ";"), join(news, ";"), gov, join(renown"""),
    ("an ended rest saved", M,
     """        if t + IC.TUNE.diplomats_rest > now then""",
     """        if true then"""),
    ("the Envoy's card opening the man's picker", U,
     """    if plot and plot.target == "province" then""",
     """    if false then"""),
    ("a running task's row clickable", U,
     """        keys[#lines] = may and (cells.key or target) or nil""",
     """        keys[#lines] = cells.key or target"""),
    ("the dead listed for diplomats", U,
     """                if them and not them:is_null_interface() and not them:is_dead() then""",
     """                if them and not them:is_null_interface() then"""),
    ("sort arrows over a mission list", U,
     """    if ICUI.pick then headers = mission or ICUI.HEADERS[view] or ICUI.PICK_HEADERS end""",
     """    if ICUI.pick then headers = ICUI.HEADERS[view] or ICUI.PICK_HEADERS end"""),
    ("the task target written wrong", U,
     """                ICUI.pick.province .. ":" .. task.code)""",
     """                ICUI.pick.province .. "|" .. task.code)"""),
    ("a failed mission's Record line losing its place", U,
     """        local mission, where = string.match(e.key or "", "^(%a+):(.+)$")""",
     """        local mission, where = nil, nil"""),
    # THE PARTY MAP: what the Governors map kept of it.
    ("a marker on the first region rather than the capital", UM,
     """    return capital or first""",
     """    return first"""),
    ("the map listeners never registered", UM,
     """    court_register()
    ICUI.map_register()""",
     """    court_register()"""),
    ("the legend forgetting no governor", UM,
     """    rows[#rows + 1] = {slug = nil}""",
     """"""),
    ("the Crown's row ringing its provinces", UM,
     """    if slug == IC.CROWN then return {}, "Your own party cannot secede." end""",
     """"""),
    ("the grace period ringing a threat", UM,
     """    if not IC.secession_on() then
        local left = IC.grace_left()""",
     """    if IC.TUNE.secession == false then
        local left = IC.grace_left()"""),
    ("a replaced governor leaving no record", M,
     """    if was and was ~= cqi then""",
     """    if false then"""),
    ("the same governor recorded leaving", M,
     """    if was and was ~= cqi then""",
     """    if was then"""),
    ("a governed marker promising a new governor", UM,
     """    else lines[#lines + 1] = man and "Click to replace its governor." or "Click to choose its governor." end""",
     """    else lines[#lines + 1] = "Click to choose its governor." end"""),
    # The marker's tip reads what each party would take off the refresh's memo
    # (ICUI.map_memo).
    ("a marker never saying which party it would go with", UM,
     """    for _, slug in ipairs(memo.goes[province] or {}) do""",
     """    for _, slug in ipairs({}) do"""),
    # One memo per refresh: asked per pin and per row, what each party would
    # take freezes a mid-game realm for seconds a click.
    ("a tip asking every party what it would take again, not reading the refresh's memo", UM,
     """    memo = memo or ICUI.map_memo(faction_key)""",
     """    memo = ICUI.map_memo(faction_key)"""),
    # WEIGHT FROM A DEVELOPED PROVINCE.
    ("a governorship worth the old flat 3 again", M,
     """    local worth = IC.gov_weight_of(levels[province_key])""",
     """    local worth = 3"""),
    ("a province of ruins giving its party nothing", M,
     """    return math.max(1, math.ceil((levels or 0) / IC.TUNE.gov_levels_per_weight))""",
     """    return math.max(0, math.ceil((levels or 0) / IC.TUNE.gov_levels_per_weight))"""),
    ("settlement levels rounded down", M,
     """    return math.max(1, math.ceil((levels or 0) / IC.TUNE.gov_levels_per_weight))""",
     """    return math.max(1, math.floor((levels or 0) / IC.TUNE.gov_levels_per_weight))"""),
    ("the weight setting ignored", M,
     """    return math.max(1, math.ceil((levels or 0) / IC.TUNE.gov_levels_per_weight))""",
     """    return math.max(1, math.ceil((levels or 0) / 2))"""),
    ("settlement levels counted from 0", M,
     """            if b and not b:is_null_interface() then level = b:building_level() + 1 end""",
     """            if b and not b:is_null_interface() then level = b:building_level() end"""),
    ("a ruin counted as a village", M,
     """            if b and not b:is_null_interface() then level = b:building_level() + 1 end""",
     """            if b then level = b:building_level() + 1 end"""),
    ("only one settlement of a province counted", M,
     """            out[key] = (out[key] or 0) + level""",
     """            out[key] = out[key] or level"""),
    ("the Help page's weight rule gone", U,
     """    vars.levels_per_weight = IC.TUNE.gov_levels_per_weight""",
     """    vars.levels_per_weight = nil"""),
    # THE GOVERNORS VIEW.
    ("the Governors view leaves the throne room over the map", UM,
     """    pcall(function() panel:SetImagePath(on and ICUI.MASK_NONE or ground, 0) end)""",
     """    pcall(function() panel:SetImagePath(ground, 0) end)"""),
    ("another tab leaves the map showing through the court", UM,
     """    pcall(function() panel:SetImagePath(on and ICUI.MASK_NONE or ground, 0) end)""",
     """    pcall(function() panel:SetImagePath(ICUI.MASK_NONE, 0) end)"""),
    ("the Governors view eats every click on the map", UM,
     """    panel:SetInteractive(not on)""",
     """    panel:SetInteractive(true)"""),
    ("another tab lets clicks through the court", UM,
     """    panel:SetInteractive(not on)""",
     """    panel:SetInteractive(false)"""),
    ("another tab leaves the pins up", UM,
     """        ICUI.gm_clear_pins(panel)
        ICUI.gm_light(nil)""",
     """        ICUI.gm_light(nil)"""),
    ("the face and plates made before the pin", UM,
     """                for k, name in ipairs(names) do pins:CreateComponent(name, paths[k]) end""",
     """                for k = #names, 1, -1 do pins:CreateComponent(names[k], paths[k]) end"""),
    ("a redraw remakes every pin", UM,
     """                if not comp(name, pins) then whole = false end""",
     """                whole = false"""),
    ("a lost province's pin left standing", UM,
     """        if seats[i] ~= province then drop_pair(pins, i) end""",
     """        if false then drop_pair(pins, i) end"""),
    ("a face pinned nowhere", UM,
     """                for _, c in ipairs({pin, face, plate, loyal, badge}) do c:SetContextObject(at) end""",
     """                for _, c in ipairs({pin, plate, loyal, badge}) do c:SetContextObject(at) end"""),
    ("the plates pinned nowhere", UM,
     """                for _, c in ipairs({pin, face, plate, loyal, badge}) do c:SetContextObject(at) end""",
     """                for _, c in ipairs({pin, face, badge}) do c:SetContextObject(at) end"""),
    ("the badge pinned nowhere", UM,
     """                for _, c in ipairs({pin, face, plate, loyal, badge}) do c:SetContextObject(at) end""",
     """                for _, c in ipairs({pin, face, plate, loyal}) do c:SetContextObject(at) end"""),
    ("a badge that shows no party", UM,
     """                badge:SetImagePath((slug and ICUI.crest(slug)) or ICUI.MASK_NONE, ICUI.GB_CREST)""",
     """"""),
    ("the badge made before the face that hides it", UM,
     """    return {ICUI.GM_PIN .. "_" .. i, ICUI.GM_FACE .. "_" .. i,
            ICUI.GM_NAME .. "_" .. i, ICUI.GM_LOYAL .. "_" .. i,
            ICUI.GM_BADGE .. "_" .. i}""",
     """    return {ICUI.GM_PIN .. "_" .. i, ICUI.GM_BADGE .. "_" .. i,
            ICUI.GM_NAME .. "_" .. i, ICUI.GM_LOYAL .. "_" .. i,
            ICUI.GM_FACE .. "_" .. i}"""),
    ("the pins' holder left at the box", UM,
     """    pins:MoveTo(0, 0)""",
     """    pins:MoveTo(ICUI.OX, ICUI.OY)"""),
    ("an empty seat's ring left to crash the draw", UM,
     """    if not slug or slug == "" then return ICUI.MASK_NONE end
    return "ui/derpy_ic/gm_ring_" .. slug .. ".png\"""",
     """    if slug == "" then return ICUI.MASK_NONE end
    return "ui/derpy_ic/gm_ring_" .. slug .. ".png\""""),
    ("an empty seat's name plate left to crash the draw", UM,
     """    if not slug or slug == "" then return ICUI.MASK_NONE end
    return "ui/derpy_ic/gm_wash_" .. slug .. ".png\"""",
     """    if slug == "" then return ICUI.MASK_NONE end
    return "ui/derpy_ic/gm_wash_" .. slug .. ".png\""""),
    ("a name plate never washed in its party's colour", UM,
     """                plate:SetImagePath(ICUI.gm_wash_path(slug), ICUI.GN_WASH)""",
     """"""),
    ("a lost province's plates left standing", UM,
     """    for _, name in ipairs(gm_names(i)) do""",
     """    for _, name in ipairs({ICUI.GM_PIN .. "_" .. i, ICUI.GM_FACE .. "_" .. i}) do"""),
    ("the loyalty plate left blank", UM,
     """                set_text(loyal, string.format("Loyalty %d%%", IC.province_loyalty(faction, province)))""",
     """                set_text(loyal, "")"""),
    ("a crest drawn over a governor's face", UM,
     """                face:SetImagePath((not port and slug and ICUI.crest(slug)) or ICUI.MASK_NONE,""",
     """                face:SetImagePath((slug and ICUI.crest(slug)) or ICUI.MASK_NONE,"""),
    ("a plate's long name not cut", UM,
     """                set_text(plate, ICUI.cut_text(plate, loc("provinces_onscreen_" .. province, province),
                                              ICUI.GM_NAME_W))""",
     """                set_text(plate, (loc("provinces_onscreen_" .. province, province)))"""),
    ("the Governors view shows the last tab's rows", UM,
     """    for i = 1, ICUI.MAX_ROWS do show(comp(ICUI.ROW .. "_" .. i, panel), false) end""",
     """    for i = 1, 0 do show(comp(ICUI.ROW .. "_" .. i, panel), false) end"""),
    ("a pin opens a picker for a province already lost", UM,
     """    if not ICUI.gm_held(faction, province) then ICUI.refresh() return end""",
     """    if false then ICUI.refresh() return end"""),
    ("a selection through the see-through court leaves it up", UM,
     """    if ICUI.gm_on() then ICUI.close() end""",
     """    if false then ICUI.close() end"""),
    ("a selection closes the court from any tab", UM,
     """    if ICUI.gm_on() then ICUI.close() end""",
     """    if comp(ICUI.PANEL) then ICUI.close() end"""),
    # Escape, and a name cut to the plate.
    ("the court never holds the Escape key", U,
     """        ICUI.hold_esc()
        ICUI.refresh()""",
     """        ICUI.refresh()"""),
    ("Escape leaves the court up", U,
     """            ICUI.esc_held = false
            ICUI.close()""",
     """            ICUI.esc_held = false"""),
    ("closing the court keeps the Escape key", U,
     """    ICUI.drop_esc()
    -- Drop the modal state with the panel.""",
     """    -- Drop the modal state with the panel."""),
    ("a failed steal still marked as held", U,
     """    ICUI.esc_held = pcall(function()""",
     """    ICUI.esc_held = true pcall(function()"""),
    ("a plate's name cut to its whole box", UM,
     """                                              ICUI.GM_NAME_W))""",
     """                                              nil))"""),
    ("a cut that ignores the room it is given", U,
     """    local w = room or ICUI.cell_w(c)""",
     """    local w = ICUI.cell_w(c)"""),
    # A governorship's weight is earned.
    ("a new governor counts in full at once", M,
     """    if was ~= cqi then court.gov_grown[province_key] = 0 end""",
     """    if was ~= cqi then court.gov_grown[province_key] = nil end"""),
    ("a replacement keeps his predecessor's growth", M,
     """    if was ~= cqi then court.gov_grown[province_key] = 0 end""",
     """    if was == nil then court.gov_grown[province_key] = 0 end"""),
    ("the sitting governor reappointed starts again", M,
     """    if was ~= cqi then court.gov_grown[province_key] = 0 end""",
     """    court.gov_grown[province_key] = 0"""),
    ("a governorship never grows", M,
     """                grown + IC.TUNE.gov_weight_per_turn)""",
     """                grown)"""),
    ("a governorship grows past its province's worth", M,
     """            court.gov_grown[province_key] = math.min(IC.gov_weight_of(levels[province_key]),
                grown + IC.TUNE.gov_weight_per_turn)""",
     """            court.gov_grown[province_key] = grown + IC.TUNE.gov_weight_per_turn"""),
    ("a province that loses levels keeps the grown weight", M,
     """    return math.min(worth, grown)""",
     """    return grown"""),
    ("the turn never grows its governors", M,
     """    IC.grow_governors(faction_key)
    IC.income(faction_key)""",
     """    IC.income(faction_key)"""),
    ("a save forgets a governorship's growth", M,
     """                          .. (grown and ("," .. tostring(grown)) or "")""",
     """                          .. (false and ("," .. tostring(grown)) or "")"""),
    ("an older save's governors start from nothing", M,
     """            court.gov_grown[bits[1]] = tonumber(bits[3])""",
     """            court.gov_grown[bits[1]] = tonumber(bits[3]) or 0"""),
    # THE START IS THE POOL'S.
    ("turn 1 puts a lord in the field again", M,
     """            elseif not house.fielded and IC.is_human(faction_key) and now > 1""",
     """            elseif not house.fielded and IC.is_human(faction_key)"""),
    ("an army follows the lord waiting in the pool from turn 1", M,
     """                if now <= 1 and IC.is_human(faction_key) then house.fielded = now end""",
     """"""),
    ("a hired pool lord left at rank 1", M,
     """    if have < want then
        cm:add_agent_experience(""",
     """    if false then
        cm:add_agent_experience("""),
    ("a hired pool lord raised TO his rank, not BY the gap", M,
     """        cm:add_agent_experience(cm:char_lookup_str(character), want - have, true)""",
     """        cm:add_agent_experience(cm:char_lookup_str(character), want, true)"""),
    ("a hired lord already at his rank raised again", M,
     """    if have < want then
        cm:add_agent_experience(""",
     """    if have <= want then
        cm:add_agent_experience("""),
    ("a hero hired raised to a lord's rank", M,
     """    if kind ~= "general" and kind ~= "lord" then return end""",
     """"""),
    ("every hire raised, not just a stored party's", M,
     """    if not (house and (house.stored or was)) then return end""",
     """    if not house then return end"""),
    ("a hired pool lord's rank ignores the recruit effects", M,
     """    local want = 1 + IC.recruit_rank(faction_key, region_key)""",
     """    local want = 1"""),
    ("nothing raises a hired pool lord", M,
     """            if man then IC.raise_hired(faction_key, man) end""",
     """            if false then IC.raise_hired(faction_key, man) end"""),
    # THE PETITION BUTTONS.
    ("the second button's tooltip never set", U,
     """                        if j == 5 or j == 6 then
                            local tip""",
     """                        if j == 5 then
                            local tip"""),
    ("the second button wears the first's tooltip", U,
     """                            local tip = j == 5 and line.tip or line.tip2""",
     """                            local tip = line.tip"""),
    ("a feud's Make Peace says nothing of its price", U,
     """                tip2 = string.format("Make Peace: %d gold, +%d loyalty for both.",""",
     """                tip3 = string.format("Make Peace: %d gold, +%d loyalty for both.","""),
    # THE GOVERNORS VIEW'S COLUMN.
    ("the column left up on another tab", UM,
     """    for _, name in ipairs(ICUI.GM_KEYS) do show(comp(name, panel), on) end""",
     """    for _, name in ipairs(ICUI.GM_KEYS) do show(comp(name, panel), true) end"""),
    ("the column's rows left up on another tab", UM,
     """    for i = 1, ICUI.GM_ROWS do show(comp(ICUI.GM_ROW .. "_" .. i, panel), on) end""",
     """    for i = 1, ICUI.GM_ROWS do show(comp(ICUI.GM_ROW .. "_" .. i, panel), true) end"""),
    ("the footer line with no plate over the map", UM,
     """    show(comp("ic_gm_foot", panel), said == true)""",
     """    show(comp("ic_gm_foot", panel), false)"""),
    ("a view entered afresh keeps the last choice", UM,
     """    if on and not ICUI.gm_was_on then ICUI.gm_reset() end""",
     """    if false then ICUI.gm_reset() end"""),
    ("a closed court remembers the view", UM,
     """    ICUI.gm_was_on = false
    ICUI.gm_list_key = nil
    ICUI.gm_light(nil)
    return court_close(...)""",
     """    ICUI.gm_list_key = nil
    ICUI.gm_light(nil)
    return court_close(...)"""),
    ("a toggle lit off its page", UM,
     """        local art = ICUI.GM_ROUND_ART[p == page and "selected" or "live"]""",
     """        local art = ICUI.GM_ROUND_ART["live"]"""),
    ("a toggle lit in one state only", UM,
     """                tog:SetImagePath(ICUI.themed(art[2]), ICUI.GM_TOG_ART[2])""",
     """                tog:SetImagePath(ICUI.themed(ICUI.GM_ROUND_ART.live[2]), ICUI.GM_TOG_ART[2])"""),
    ("a chosen party's row not marked", UM,
     """                if (r.look or "live") == "live" and chosen(r, i) then r.look = "selected" end""",
     """                if false then r.look = "selected" end"""),
    ("a row's look set in one state only", UM,
     """        row:SetImagePath(ICUI.themed(art[2]), 1)""",
     """        row:SetImagePath(ICUI.themed(ICUI.GM_ROW_ART.live[2]), 1)"""),
    ("a spare row left showing", UM,
     """            show(row, r ~= nil)""",
     """            show(row, true)"""),
    ("a second click on a party does not clear it", UM,
     """        ICUI.gm_party = (ICUI.gm_party ~= n) and n or nil""",
     """        ICUI.gm_party = n"""),
    ("the chosen party rings nothing", UM,
     """            for _, p in ipairs((ICUI.map_outline(faction, r.slug))) do ringed[p] = true end""",
     """            for _, p in ipairs({}) do ringed[p] = true end"""),
    ("a party that takes nothing still counts", UM,
     """                      l3 = (not why) and string.format("Would take %d", #list) or nil,""",
     """                      l3 = string.format("Would take %d", #list),"""),
    ("the hint forgets why a party rings nothing", UM,
     """            set_text(hint, (chosen and chosen.why) or "Click a party to see what it would take.")""",
     """            set_text(hint, "Click a party to see what it would take.")"""),
    ("a slider shown for a list that fits", UM,
     """        show(slider, n > ICUI.GM_ROWS)""",
     """        show(slider, true)"""),
    ("the column's cards placed at the screen's corner, not the holder's", UM,
     """        host, count = holder, n
        x, y = holder:Position()""",
     """        host, count = holder, n
        x, y = 0, 0"""),
    # THE SCROLLING LIST: the governor picker scrolls.
    ("the list never made again", UM,
     """    if list and key == ICUI.gm_list_key then""",
     """    if list then"""),
    ("every redraw makes the list again", UM,
     """    if list and key == ICUI.gm_list_key then""",
     """    if false then"""),
    ("the old list left under the new", UM,
     """    if list then pcall(function() list:Destroy() end) end""",
     """    local _ = list"""),
    ("a list made again leaves its holder off the window's top", UM,
     """        if holder then
            holder:MoveTo(x, y)""",
     """        if holder then"""),
    ("the list placed at the screen's corner", UM,
     """    list:MoveTo(x, y)""",
     """    list:MoveTo(0, 0)"""),
    ("the clip window left the file's size", UM,
     """        ICUI.resize(clip, ICUI.GM_ROW_W, h)""",
     """        local _ = h"""),
    ("the slider on top of the cards", UM,
     """        slider:MoveTo(x + ICUI.GM_ROW_W + ICUI.GM_SLIDER_GAP, y)""",
     """        slider:MoveTo(x, y)"""),
    ("a list with no length", UM,
     """        for i = 1, n do
            local name = ICUI.GM_SP""",
     """        for i = 1, 0 do
            local name = ICUI.GM_SP"""),
    ("the empty rows never laid out", UM,
     """        pcall(function() box:Layout() end)""",
     """        local _ = box"""),
    ("the cards never follow the list", UM,
     """    if hy ~= by then holder:MoveTo(hx, by) end""",
     """"""),
    ("a scroll redraws the court", UM,
     """    if panel then ICUI.gm_follow(panel) end""",
     """    if panel then ICUI.gm_follow(panel) ICUI.refresh() end"""),
    ("the cards made on the panel, outside the list", UM,
     """    local holder = list and comp(ICUI.GM_HOLDER, list)""",
     """    local holder = nil"""),
    ("the list left up on another tab", UM,
     """    show(comp(ICUI.GM_LIST, panel), on)""",
     """    local _ = on"""),
    ("the scroll poll never started", UM,
     """        pcall(ICUI.gm_scroll_poll)
""", ""),
    ("the lists' scroll poll never started", UM,
     """        pcall(ICUI.list_scroll_poll)
""", ""),
    # THE PICKER'S SORTS.
    ("the picker has no sorts", UM,
     """    if page == "picker" then return ICUI.GM_PICK_SORTS, "pick" end""",
     """    if false then return ICUI.GM_PICK_SORTS, "pick" end"""),
    ("the picker's sorts sort the Provinces page", UM,
     """    if page == "picker" then return ICUI.GM_PICK_SORTS, "pick" end""",
     """    if page == "picker" then return ICUI.GM_PICK_SORTS, "govs" end"""),
    ("the picker's sort buttons drawn as the Provinces page's", UM,
     """        ICUI.gm_draw_sorts(panel, page)
    else""",
     """        ICUI.gm_draw_sorts(panel, "provinces")
    else"""),
    # THE PROVINCES PAGE.
    ("a province's weight on its tooltip from the flat rule", UM,
     """                ICUI.house_name(slug, faction_key), now, levels, levels == 1 and "" or "s",""",
     """                ICUI.house_name(slug, faction_key), 3, levels, levels == 1 and "" or "s","""),
    ("a Provinces row tells the player a click appoints", UM,
     """        local tip = ICUI.map_tip(faction, p, true, memo)""",
     """        local tip = ICUI.map_tip(faction, p, nil, memo)"""),
    ("a Provinces row with no strength figure", UM,
     """                 or string.format("%d%%, +%d strength", loyal, now),""",
     """                 or string.format("%d%%", loyal),"""),
    ("an empty seat drawn with no silhouette", UM,
     """            face = port or ((not cqi) and ICUI.SILHOUETTE or nil),""",
     """            face = port,"""),
    ("an unresolved face with no crest in its place", UM,
     """            crest = (cqi and not port and slug) and ICUI.crest(slug) or nil,""",
     """            crest = nil,"""),
    ("a governor's face with no party crest on it", UM,
     """            badge = (port and slug) and ICUI.crest(slug) or nil,""",
     """            badge = nil,"""),
    ("the Provinces page ignores the sort", UM,
     """    ICUI.sort_rows("govs", rows, keys, #rows)
    return rows, keys""",
     """    return rows, keys"""),
    ("a lost province stays chosen", UM,
     """        if not held then ICUI.gm_sel = nil end""",
     """        if false then ICUI.gm_sel = nil end"""),
    ("a chosen province's row not marked", UM,
     """        ICUI.gm_draw_page(panel, rows, function(r) return r.key == ICUI.gm_sel end)""",
     """        ICUI.gm_draw_page(panel, rows, function(r) return false end)"""),
    ("the chosen province's pin not ringed", UM,
     """    if page == "provinces" and ICUI.gm_sel then ringed[ICUI.gm_sel] = true end""",
     """    if false then ringed[ICUI.gm_sel] = true end"""),
    ("choosing a province leaves the camera where it was", UM,
     """                ICUI.gm_look_at(ICUI.player(), r.key)""",
     """                local _ = r.key"""),
    ("the camera's zoom thrown away", UM,
     """        cm:scroll_camera_from_current(true, 1, {x, y, d, b, h})""",
     """        cm:scroll_camera_from_current(true, 1, {x, y, 14.7, 0, 12})"""),
    ("a second click on a province does not clear it", UM,
     """            if ICUI.gm_sel == r.key then
                ICUI.gm_sel = nil""",
     """            if false then
                ICUI.gm_sel = nil"""),
    ("the check live with nothing chosen", UM,
     """    local ok_on, no_on = ICUI.gm_sel ~= nil, governed""",
     """    local ok_on, no_on = true, governed"""),
    ("the cross offered for an empty province", UM,
     """    local no_shown = ICUI.gm_sel == nil or governed""",
     """    local no_shown = true"""),
    ("the round buttons shown on the Parties page", UM,
     """    show(comp("ic_gm_ok", panel), btns)""",
     """    show(comp("ic_gm_ok", panel), true)"""),
    ("a dead button only looks dead", UM,
     """    pcall(function() c:SetDisabled(not on) end)""",
     """    local _ = on"""),
    ("the check sends a lost province to the picker", UM,
     """    if not ICUI.gm_held(faction, ICUI.gm_sel) then
        ICUI.gm_sel = nil""",
     """    if false then
        ICUI.gm_sel = nil"""),
    ("the sort lands mid-list after a re-sort", UM,
     """        ICUI.gm_rescroll()                -- a re-sort starts at the top""",
     """        local _ = 0"""),
    ("the loyalty icon high at the start", UM,
     """    if loyalty > IC.TUNE.prov_loyalty_start then return ICUI.GM_FEALTY.high end""",
     """    if loyalty >= IC.TUNE.prov_loyalty_start then return ICUI.GM_FEALTY.high end"""),
    ("the loyalty icon never low", UM,
     """    if loyalty <= IC.TUNE.prov_defect_floor then return ICUI.GM_FEALTY.low end""",
     """    if false then return ICUI.GM_FEALTY.low end"""),
    # THE WEIGHT AS GROWN: a governorship's gradual weight.
    ("the tooltip counts a new governorship in full", UM,
     """            local now, worth = IC.gov_grown_weight(court, province, all), IC.gov_weight_of(levels)""",
     """            local now, worth = IC.gov_weight_of(levels), IC.gov_weight_of(levels)"""),
    ("a Provinces row counts a new governorship in full", UM,
     """        local now, worth = IC.gov_grown_weight(court, p, levels), IC.gov_weight_of(levels[p])""",
     """        local now, worth = IC.gov_weight_of(levels[p]), IC.gov_weight_of(levels[p])"""),
    ("a growing tooltip says nothing of what it grows to", UM,
     """                now < worth and string.format(", growing to +%d", worth) or "",""",
     """                "","""),
    ("a growing row says nothing of what it grows to", UM,
     """                 or (now < worth) and string.format("%d%%, +%d of %d strength", loyal, now, worth)""",
     """                 or (now < worth) and string.format("%d%%, +%d strength", loyal, now)"""),
    # THE PICKER IN THE COLUMN.
    ("the governor picker drawn full-screen again", UM,
     """    if ICUI.pick and ICUI.pick.kind == "gov" then return "picker" end
    return ICUI.gm_page""",
     """    return ICUI.gm_page"""),
    ("a man the click refuses drawn live", UM,
     """            look = ICUI.pick_rows[i] and "live" or "inactive",""",
     """            look = "live","""),
    ("the refusal not first on the tooltip", UM,
     """        if line.why then tip[#tip + 1] = line.why .. "." end""",
     """        if false then tip[#tip + 1] = line.why .. "." end"""),
    ("what he holds left off the tooltip", UM,
     '        tip[#tip + 1] = string.format("%d influence. Holds: %s.", line.sort.standing, line.holds)',
     '        local _ = line.holds'),
    ("a refused man choosable", UM,
     """        if r and r.cqi then
            ICUI.gm_pick_sel = (ICUI.gm_pick_sel ~= r.cqi) and r.cqi or nil""",
     """        if r and r.key then
            ICUI.gm_pick_sel = (ICUI.gm_pick_sel ~= r.key) and r.key or nil"""),
    ("the check live with no man chosen", UM,
     """        btns, ok_on, no_on, no_shown = true, ICUI.gm_pick_sel ~= nil, true, true""",
     """        btns, ok_on, no_on, no_shown = true, true, true, true"""),
    ("the picker's cross dead", UM,
     """        btns, ok_on, no_on, no_shown = true, ICUI.gm_pick_sel ~= nil, true, true""",
     """        btns, ok_on, no_on, no_shown = true, ICUI.gm_pick_sel ~= nil, false, true"""),
    ("the check appoints a man no longer free", UM,
     """        if not pick_still_free(ICUI.gm_picker_rows(faction)) then""",
     """        if false then"""),
    ("the check gives a lost province a governor", UM,
     """        if not ICUI.gm_held(faction, province) then
            ICUI.pick = nil""",
     """        if false then
            ICUI.pick = nil"""),
    ("a stale choice drawn as chosen", UM,
     """        if not pick_still_free(rows) then ICUI.gm_pick_sel = nil end""",
     """        if false then ICUI.gm_pick_sel = nil end"""),
    ("the picker's cross leaves the picker up", UM,
     """        -- BACK TO THE PAGE IT CAME FROM, with nothing done.
        ICUI.pick = nil""",
     """        -- BACK TO THE PAGE IT CAME FROM, with nothing done.
        local _ = ICUI.pick"""),
    ("a new pin keeps the last man chosen", UM,
     """    ICUI.gm_rescroll()
    ICUI.gm_pick_sel = nil""",
     """    ICUI.gm_rescroll()"""),
    ("a new pin opens where the last picker was scrolled", UM,
     """    ICUI.gm_rescroll()
    ICUI.gm_pick_sel = nil""",
     """    ICUI.gm_pick_sel = nil"""),
    ("the province being chosen for not ringed", UM,
     """    if page == "picker" then ringed[ICUI.pick.key] = true end""",
     """    if false then ringed[ICUI.pick.key] = true end"""),
    ("the picker shares the Provinces page's list", UM,
     """    local page = ICUI.gm_live_page()
    local key = page .. "|" .. n .. "|" .. ICUI.gm_list_gen""",
     """    local page = ICUI.gm_page
    local key = page .. "|" .. n .. "|" .. ICUI.gm_list_gen"""),
    # THE PARTIES ROWS' LINES BESIDE THE CREST.
    ("a party row's lines left in the portrait's place", UM,
     """    local dx = r.face and 0 or (2 * xy.ic_gr_crest[1] + xy.ic_gr_crest[3] - xy.ic_gr_l1[1])""",
     """    local dx = 0"""),
    ("a row with no loyalty icon keeps its gap", UM,
     """                   ic_gr_l3 = dx + (r.fealty and 0 or xy.ic_gr_l1[1] - xy.ic_gr_l3[1])}""",
     """                   ic_gr_l3 = dx}"""),
    # CA'S REGION OVERLAY ON WHAT THE CHOSEN PARTY GOVERNS.
    ("the overlay lights what the party would take", UM,
     """            local list = r.slug and IC.provinces_of_house(faction, r.slug)""",
     """            local list = r.slug and (ICUI.map_outline(faction, r.slug))"""),
    ("the overlay never turned off", UM,
     """        else
            CampaignUI.SetOverlayVisible(false)
        end""",
     """        end"""),
    ("every redraw calls the overlay", UM,
     """    if key == ICUI.gm_lit then return end
""",
     ""),
    ("the overlay lit on every page", UM,
     """    if faction and ICUI.gm_on() and ICUI.gm_live_page() == "parties" and ICUI.gm_party then""",
     """    if faction and ICUI.gm_on() and ICUI.gm_party then"""),
    ("closing the court leaves the regions lit", UM,
     """    ICUI.gm_list_key = nil
    ICUI.gm_light(nil)""",
     """    ICUI.gm_list_key = nil"""),
    # The drawn-whole column.
    ("the holder sized to one screen of cards", UM,
     """math.max(ICUI.GM_ROWS, n) * ICUI.GM_ROW_PITCH)""",
     """ICUI.GM_ROWS * ICUI.GM_ROW_PITCH)"""),
    ("only one screen of cards drawn", UM,
     """        host, count = holder, n
        x, y = holder:Position()""",
     """        host, count = holder, math.min(n, ICUI.GM_ROWS)
        x, y = holder:Position()"""),
    ("every card line rewritten on every redraw", UM,
     """            if ICUI.gm_drawn[id .. "/" .. cname] ~= want then""",
     """            if true then"""),
    ("the line memo kept across a new list", UM,
     """    ICUI.gm_list_key, ICUI.gm_drawn = nil, {}""",
     """    ICUI.gm_list_key = nil"""),
    ("another tab leaves the regions lit", UM,
     """        ICUI.gm_clear_pins(panel)
        ICUI.gm_light(nil)""",
     """        ICUI.gm_clear_pins(panel)"""),
    # THE MAP TAB, REMOVED.
    ("the Map tab back in the strip", U,
     """    ic_tab_intrigue  = {750, 62, 240, 32},""",
     """    ic_tab_map       = {750, 62, 240, 32},
    ic_tab_intrigue  = {994, 62, 240, 32},"""),
    ("a tab left where the Map tab's gap was", U,
     """    ic_tab_log       = {1238, 62, 240, 32},""",
     """    ic_tab_log       = {1482, 62, 240, 32},"""),
    ("the Petitions marker left on the old tab", U,
     """    ic_mark_petitions = {1200, 64, 28, 28},""",
     """    ic_mark_petitions = {1444, 64, 28, 28},"""),
    # The HUD hub.
    ("the court button moved by its own placement while the hub manages it", U,
     """    if ICUI.hubbed() then
        if not quiet then ICUI.update_opener_tip() end""",
     """    if false then
        if not quiet then ICUI.update_opener_tip() end"""),
    ("the hub-managed court button left with no tooltip and no pulse", U,
     """        if not quiet then ICUI.update_opener_tip() end
        return true""",
     """        return true"""),
    ("the hub-managed court tooltip written from the turn-start handler", U,
     """        if not quiet then ICUI.update_opener_tip() end
        return true""",
     """        ICUI.update_opener_tip()
        return true"""),
    ("the hub told the court button is live while it is grey", U,
     """    ICUI.opener_live = live and true or false""",
     """    ICUI.opener_live = true"""),
    ("the hub never told the court is waiting on a decision", U,
     """    ICUI.pulsing = on == true""",
     """    ICUI.pulsing = false"""),
    ("the court button registered with the hub under another key", U,
     """    key = ICUI.HUB_KEY, button = ICUI.BTN, order = 1,""",
     """    key = "court", button = ICUI.BTN, order = 1,"""),
    # Governments.
    ("gov: the government line does not say it is the government", U,
     """[[img:%s]][[/img]]Government: %s\",""",
     """[[img:%s]][[/img]]%s\","""),
    ("gov: the government line wears the band's picture", U,
     """Government: %s\", ICUI.gov_icon(court.gov),""",
     """Government: %s\", ICUI.BAND_ICON,"""),
    ("gov: the cards wear no picture", U,
     """            law_pic(panel, \"ic_gc_icon_\" .. i, ICUI.gov_art(g.slug))\n""",
     ""),
    ("law: the pane bar is never drawn", U,
     """    ICUI.draw_law_pbar(panel, p, all)\n""",
     ""),
    ("law: the pane bar's nay grows from the left", U,
     """            seg:MoveTo(side == \"aye\" and bx or bx + bw - w, by)""",
     """            seg:MoveTo(bx, by)"""),
    ("law: an empty court's pane bar draws a side", U,
     """        local w = all > 0 and math.floor(bw * p[side] / all) or 0""",
     """        local w = all > 0 and math.floor(bw * p[side] / all) or 1"""),
    ("gov: a card wears CA's 72px picture, not the upscale", U,
     """        return string.format(ICUI.GOV_ART_FILE, tostring(slug) .. (own and ICUI.SUFFIX or \"\"))""",
     """        return ICUI.LAW_ART_DIR .. (own or ICUI.GOV_ART)[tostring(slug)] .. \".png\""""),
    ("gov: a card's loyalty line spills a long name", U,
     """                        .. ICUI.cut_text(c, name, room))""",
     """                        .. name)"""),
    ("gov: a card's loyalty line leads with the name", U,
     """                    local name, head = ICUI.house_name(h[1], faction), string.format(\"%+d  \", h[2])""",
     """                    local name, head = ICUI.house_name(h[1], faction), \"\""""),
    ("gov: a refused card's button still sends", U,
     """            if ICUI.gc_may[i] and ICUI.gc_slugs[i] then""",
     """            if ICUI.gc_slugs[i] then"""),
    ("gov: the cards show off the doctrine pick", U,
     """    for _, name in ipairs(ICUI.GC_KEYS) do show(comp(name, panel), gov_pick) end""",
     """    for _, name in ipairs(ICUI.GC_KEYS) do show(comp(name, panel), true) end"""),
    ("gov: the header strip draws over the cards", U,
     """    if ICUI.pick and ICUI.pick.kind == \"doctrine\" then headers = nil end\n""",
     ""),
    ("gov: a card's loyalty ignores who is seated", U,
     """                if court.houses[p] then hit[#hit + 1] = {p, IC.TUNE.gov_force_gain} end""",
     """                hit[#hit + 1] = {p, IC.TUNE.gov_force_gain}"""),
    ('gov: Help states the base numbers', U,
     """        if type(v) == \"number\" then vars[k] = IC.tune(faction, k) end""",
     """        if type(v) == \"number\" then vars[k] = v end"""),
    ('gov: a choice nobody backs can still be paid for', M,
     """    if IC.gov_pull(faction_key) ~= ask.gov then
        court.gov_ask = nil""",
     """    if false then
        court.gov_ask = nil"""),
    ('gov: drift off keeps a waiting choice', M,
     """    if not IC.governments_on() or IC.TUNE.gov_drift == false then""",
     """    if not IC.governments_on() then"""),
    ("gov: the government's own party leading keeps the count", M,
     """    if want == court.gov then
        court.gov_toward, court.gov_pressure = nil, 0
        return false
    end""",
     """    if want == court.gov then return false end"""),
    ('gov: the tooltip counts points as turns', U,
     """        local per = top and 1 or IC.TUNE.gov_balance_turns""",
     """        local per = 1"""),
    ('gov: the tooltip counts while nothing moves', U,
     """       and want == court.gov_toward and IC.gov_drift_on(faction)""",
     """       and true"""),
    ('gov: the picker hides what a government gives', U,
     """            local tip = g.may and g.fx or (ICUI.reason_text(g.why, g.n) .. \"\\n\" .. g.fx)""",
     """            local tip = (not g.may) and ICUI.reason_text(g.why, g.n) or \"\" """),
    ('gov: an override answering for every court', M,
     """    local court = faction_key and IC.state[faction_key]
    return court and R.GOVS[court.gov or \"\"] or nil""",
     """    for _, c in pairs(IC.state) do if IC.GOVS[c.gov or \"\"] then return IC.GOVS[c.gov] end end
    return nil"""),
    ('gov: a table knob scaled into IC.TUNE itself', M,
     """        local out = {}
        for k, v in pairs(base) do out[k] = math.floor(v * o.mul + 0.5) end
        return out""",
     """        for k, v in pairs(base) do base[k] = math.floor(v * o.mul + 0.5) end
        return base"""),
    ("gov: the Slave-Lords' price left on IC.TUNE", M,
     """    return IC.tune(faction_key, plot.cost) or 0""",
     """    return IC.TUNE[plot.cost] or 0"""),
    ("gov: a house's own start ignored", M,
     """    if R.START_GOV[faction_key] then return R.START_GOV[faction_key] end
    local best, best_share = nil, -1""",
     """    local best, best_share = nil, -1"""),
    ('gov: the start turn drifts too', M,
     """        court.gov = IC.start_gov(faction_key)
    elseif IC.gov_turn then""",
     """        court.gov = IC.start_gov(faction_key)
    end
    if IC.gov_turn then"""),
    ('gov: a leader with no government builds pressure', M,
     """    if not top or not IC.gov_for_party(top, faction_key) then return nil, top, 0 end""",
     """    if not top then return nil, top, 0 end"""),
    ('gov: a leader with no government resets the pull', M,
     """    local want, top, step = IC.gov_pull(faction_key)
    if not want then return false end""",
     """    local want, top, step = IC.gov_pull(faction_key)"""),
    ('gov: the Conclave pulls every turn', M,
     """(now % IC.TUNE.gov_balance_turns == 0) and 1 or 0""",
     """1"""),
    ('gov: a new leader keeps the old count', M,
     """    if court.gov_toward ~= want then court.gov_toward, court.gov_pressure = want, 0 end""",
     """    court.gov_toward = want"""),
    ('gov: drift in the grace period', M,
     """        and IC.is_human(faction_key) and IC.grace_left() == 0""",
     """        and IC.is_human(faction_key)"""),
    ('gov: an AI court drifts', M,
     """        and IC.is_human(faction_key) and IC.grace_left() == 0""",
     """        and IC.grace_left() == 0"""),
    ('gov: pressure builds over a waiting choice', M,
     """    if not IC.gov_drift_on(faction_key) or now < (court.gov_cool or 0)
       or court.gov_ask then""",
     """    if not IC.gov_drift_on(faction_key) or now < (court.gov_cool or 0) then"""),
    ("gov: the purse spends a seat's bar", M,
     """                local spare = IC.standing(faction_key, cqi) - (bar[cqi] or 0)""",
     """                local spare = IC.standing(faction_key, cqi)"""),
    ("gov: the old government's party loses nothing", M,
     """    for _, p in ipairs(from and R.GOVS[from] and R.GOVS[from].parties or {}) do
        IC.move_loyalty(faction_key, p, loss)
    end""",
     """"""),
    ('gov: Hold costs the same every time', M,
     """    return IC.TUNE.gov_hold_cost * (1 + (IC.court(faction_key).gov_holds or 0))""",
     """    return IC.TUNE.gov_hold_cost"""),
    ('gov: Hold with an empty purse', M,
     """    if not ok then return false, \"gov_purse\", short end
    court.gov_holds""",
     """    court.gov_holds"""),
    ('gov: an unanswered choice never settles', M,
     """    if cm:model():turn_number() >= ask.ends then
        IC.gov_accept(faction_key)""",
     """    if false then
        IC.gov_accept(faction_key)"""),
    ("gov: a choice outlives the court's pull", M,
     """    if ask.gov == court.gov or want ~= ask.gov then""",
     """    if ask.gov == court.gov then"""),
    ('gov: a forced doctrine with no cooldown', M,
     """    IC.court(faction_key).gov_cool = cm:model():turn_number() + IC.TUNE.gov_force_cooldown""",
     """"""),
    ('gov: the setting off leaves the bundle on', M,
     """    local want = IC.governments_on() and IC.court(faction_key).gov or nil""",
     """    local want = IC.court(faction_key).gov"""),
    ('gov: the setting off keeps a waiting choice', M,
     """        IC.court(faction_key).gov_ask = nil
    end
    if not IC.governments_on() then IC.apply_gov_bundle(faction_key) end""",
     """    end
    if not IC.governments_on() then IC.apply_gov_bundle(faction_key) end"""),
    ('gov: an older save reads a government out of nothing', M,
     """    court.gov = R.GOVS[g[1] or \"\"] and g[1] or nil""",
     """    court.gov = g[1] or \"conclave\""""),
    ('gov: the doctrine picker offers the current government', U,
     """        if g ~= court.gov then""",
     """            if true then"""),
    ('gov: Hold on a petition accepts instead', U,
     """        op, arg = (yes and \"gov_accept\" or \"gov_hold\"), \"\"""",
     """        op, arg = \"gov_accept\", \"\""""),
    ('gov: the government drawn with governments off', U,
     """    local on = IC.governments_on() and court.gov ~= nil""",
     """    local on = court.gov ~= nil"""),
    ("gov: another tab leaves the government's row on screen", U,
     """        show(comp(\"ic_gov\", panel), false)
        show(comp(\"ic_gov_btn\", panel), false)""",
     """"""),
    # The government's glow and burst.
    ("gov fx: a government chosen bursts nothing", U,
     """                show(glow, true)
                ICUI.burst(\"ic_gov_glow\")""",
     """                show(glow, true)"""),
    ("gov fx: CA's pulse on the glow, which can clear its breathing", U,
     """                ICUI.confirm(nil, true, ICUI.SOUNDS[op])
                -- The glow is shown only""",
     """                ICUI.confirm(glow, true, ICUI.SOUNDS[op])
                -- The glow is shown only"""),
    ("gov fx: another tab leaves the glow on screen", U,
     """        show(comp(\"ic_gov_glow\", panel), false)""",
     """"""),
    ("gov fx: the glow drawn with governments off", U,
     """    show(comp(\"ic_gov_glow\", panel), on and ICUI.gov_moving(faction, court) and true or false)""",
     """    show(comp(\"ic_gov_glow\", panel), ICUI.gov_moving(faction, court) and true or false)"""),
    ('gov: the embezzle card states the base price', U,
     """    if plot.key ~= \"embezzle\" then return plot.effect end""",
     """    do return plot.effect end"""),
    # Deeds.
    ("deed: renown is not weight", M,
     """        + IC.member_weight(faction_key, slug) + renown""",
     """        + IC.member_weight(faction_key, slug)"""),
    ("deed: renown never fades", M,
     """        local left = n - math.max(1, math.floor(n * IC.TUNE.renown_fade_pct / 100))""",
     """        local left = n"""),
    ("deed: no limit to a turn's renown", M,
     """    n = math.min(n or 0, math.max(0, IC.TUNE.renown_turn_cap - got))""",
     """    n = n or 0"""),
    ("deed: an absent party banks past the line", M,
     """    if not court.houses[party] then
        n = math.min(n, math.max(0, IC.TUNE.renown_join_line - have))""",
     """    if false then
        n = math.min(n, math.max(0, IC.TUNE.renown_join_line - have))"""),
    ("deed: the Ledger never takes a convoy", M,
     """    if d.alt and not court.houses[party] and court.houses[d.alt] then party = d.alt end""",
     """"""),
    ("deed: AI courts score", M,
     """    return IC.TUNE.deeds ~= false and IC.is_human(faction_key)""",
     """    return IC.TUNE.deeds ~= false"""),
    ("deed: a battle scores per general", M,
     """    if IC.battles_seen[key] then return false end""",
     """"""),
    ("deed: a confederation's rites score", M,
     """        if code == \"rite\" and IC.court(faction:name()).confed_turn""",
     """        if false and IC.court(faction:name()).confed_turn"""),
    ("deed: recruiting captives counts as slaves", M,
     """        local yes = context:get_outcome_key() == IC.ENSLAVE_OUTCOME""",
     """        local yes = true or context:get_outcome_key() == IC.ENSLAVE_OUTCOME"""),
    ("deed: a full court still draws a party", M,
     """    if not IC.deeds_on(faction_key) or not IC.deed_room(faction_key) then return nil end""",
     """    if not IC.deeds_on(faction_key) then return nil end"""),
    ("deed: the smaller waiting party comes first", M,
     """           and n >= IC.TUNE.renown_join_line and n > most then""",
     """           and n >= IC.TUNE.renown_join_line and most == 0 then"""),
    ("deed: a legend is drawn", M,
     """    if not IC.can_lead(character) or IC.fixed_history(character) then return nil end""",
     """    if IC.fixed_history(character) then return nil end"""),
    ("deed: the introduction every turn", M,
     """        court.gov_intro = true
        IC.feed(faction_key, \"gov_intro\")""",
     """        IC.feed(faction_key, \"gov_intro\")"""),
    ("deed: the Record gets an entry per deed", M,
     """        if e.kind == \"deed\" and e.slug == party and e.key == code then""",
     """        if false then"""),
    ("deed: a party that leaves keeps its renown", M,
     """    if court.renown then court.renown[slug] = nil end""",
     """"""),
    ("deed: the Record sums only the last entry", M,
     """        if e.turn ~= now then break end""",
     """        if i < #log or e.turn ~= now then break end"""),
    ("deed: a ritual builds a court for any faction", M,
     """        if not IC.runs_court(faction) then return nil end
        IC.loaded(faction:name())""",
     """        IC.loaded(faction:name())"""),
    ("deed: a waiting party reads as still to come", U,
     """            elseif n >= IC.TUNE.renown_join_line then""",
     """            elseif false then"""),
    ("deed: a settled court shows a drift", U,
     """    if ICUI.gov_moving(faction, court) then
        text = text""",
     """    if true then
        text = text"""),
    # The laws and votes.
    ("law: a tie passes", M,
     """function IC.law_passes(t) return t.aye > t.nay end""",
     """function IC.law_passes(t) return t.aye >= t.nay end"""),
    ("law: a man with no influence votes", M,
     """                if n > 0 and party then out[#out + 1] = {cqi = cqi, party = party, n = n} end""",
     """                if n >= 0 and party then out[#out + 1] = {cqi = cqi, party = party, n = n} end"""),
    ("law: a won man is multiplied too", M,
     """        if won then
            side, why = won, "won"
        elseif side then""",
     """        if won then
            side, why = won, "won"
        end
        if side then"""),
    ("law: a disloyal party votes with the Crown", M,
     """        return vote.stance == "aye" and "nay" or "aye", "disloyal\"""",
     """        return vote.stance, "disloyal\""""),
    ("law: the loyal line is above, not at", M,
     """    if loyalty >= IC.TUNE.law_loyal_line then return vote.stance, "loyal" end""",
     """    if loyalty > IC.TUNE.law_loyal_line then return vote.stance, "loyal" end"""),
    ("law: a raise pays the full price", M,
     """    return cost[level] - (had and cost[had] or 0)""",
     """    return cost[level]"""),
    ("law: a level can be lowered", M,
     """    if level <= (vote.push[IC.CROWN] or 0) then return false, "law_pushed" end""",
     """    if level == (vote.push[IC.CROWN] or 0) then return false, "law_pushed" end"""),
    ("law: an abstaining Crown pushes", M,
     """    if vote.stance == "abstain" then return false, "law_abstain" end
    if level""",
     """    if level"""),
    ("law: a man against you is not doubled", M,
     """    if s and s ~= vote.stance then price = price * 2 end""",
     """"""),
    ("law: a Crown man can be won", M,
     """    if man.party == IC.CROWN then return nil, "law_crown_man" end""",
     """"""),
    ("law: the overrule angers the winners", M,
     """    local losing = pass and "nay" or "aye\"""",
     """    local losing = pass and "aye" or "nay\""""),
    ("law: a won man follows the Crown's new side", M,
     """    vote.stance = stance
    vote.answered = true""",
     """    for cqi in pairs(vote.won) do if stance ~= "abstain" then vote.won[cqi] = stance end end
    vote.stance = stance
    vote.answered = true"""),
    # The settle loop walks the law's own lists.
    ("law: a passed law pays the party against it", M,
     """            if court.houses[slug] then IC.move_loyalty(faction_key, slug, IC.TUNE.law_pass_loss) end""",
     """            if court.houses[slug] then IC.move_loyalty(faction_key, slug, IC.TUNE.law_pass_gain) end"""),
    ("law: a passed law angers before it pays", M,
     """        for _, slug in ipairs(o.pro or {}) do
            if court.houses[slug] then IC.move_loyalty(faction_key, slug, IC.TUNE.law_pass_gain) end
        end
        for _, slug in ipairs(o.con or {}) do
            if court.houses[slug] then IC.move_loyalty(faction_key, slug, IC.TUNE.law_pass_loss) end
        end""",
     """        for _, slug in ipairs(o.con or {}) do
            if court.houses[slug] then IC.move_loyalty(faction_key, slug, IC.TUNE.law_pass_loss) end
        end
        for _, slug in ipairs(o.pro or {}) do
            if court.houses[slug] then IC.move_loyalty(faction_key, slug, IC.TUNE.law_pass_gain) end
        end"""),
    ("law: a failed party proposal costs nothing", M,
     """        if vote.proposer ~= IC.CROWN then
            IC.move_loyalty(faction_key, vote.proposer, IC.TUNE.law_fail_loss)
        end""",
     """"""),
    ("law: a party proposes during its rest", M,
     """    if now - (court.law_rest or 0) < IC.TUNE.law_party_rest then return nil end""",
     """"""),
    ("law: a party proposes what it is against", M,
     """                   and IC.law_stance(cat, opt, slug, faction_key) == "aye" then""",
     """                   and IC.law_stance(cat, opt, slug, faction_key) ~= nil then"""),
    ("law: a party pushes while well ahead", M,
     """            if t[side] - t[other] <= margin and IC.spend_party(faction_key, slug, price) then""",
     """            if IC.spend_party(faction_key, slug, price) then"""),
    ("law: the purse spends a seat's bar", M,
     """                local spare = IC.standing(faction_key, cqi) - (bar[cqi] or 0)
                if spare > 0 then
                    men[#men + 1] = {cqi = cqi, spare = spare}""",
     """                local spare = IC.standing(faction_key, cqi)
                if spare > 0 then
                    men[#men + 1] = {cqi = cqi, spare = spare}"""),
    ("law: switched off, the votes stay", M,
     """    if IC.TUNE.laws == false then IC.court(faction_key).votes = {} end""",
     """"""),
    ("law: an AI court wears a law", M,
     """function IC.laws_on(faction_key)
    return IC.TUNE.laws ~= false and IC.is_human(faction_key)""",
     """function IC.laws_on(faction_key)
    return IC.TUNE.laws ~= false"""),
    ("law: the answer is not remembered", M,
     """    vote.stance = stance
    vote.answered = true""",
     """    vote.stance = stance"""),
    ("law: the marker ignores the answer", U,
     """        if v and v.proposer ~= IC.CROWN and not v.answered then s.laws = s.laws + 1 end""",
     """        if v and v.proposer ~= IC.CROWN then s.laws = s.laws + 1 end"""),
    ("law: the board frames the chosen card, not the law in force", U,
     """                card:SetImagePath(force and ICUI.PARTY_SELECTED or ICUI.MASK_NONE, ICUI.LAW_SEL_INDEX)""",
     """                card:SetImagePath(chosen and ICUI.PARTY_SELECTED or ICUI.MASK_NONE, ICUI.LAW_SEL_INDEX)"""),
    ("law: a block shows a Win button on every man", U,
     """            show(win, price ~= nil)""",
     """            show(win, true)"""),
    # The influence line, the abstain count and the button pulse for a waiting
    # law.
    ("law: a winnable man shows his influence over his Win button", U,
     """            show(inf, price == nil)""",
     """            show(inf, true)"""),
    ("law: the abstain line names every party", U,
     """    local who = #abst > 2 and string.format("%d parties, %d influence", #abst, held)""",
     """    local who = false and string.format("%d parties, %d influence", #abst, held)"""),
    ("law: the push margin counts the abstainers", M,
     """            local margin = math.floor((t.aye + t.nay) * IC.TUNE.law_push_margin / 100)""",
     """            local margin = math.floor((t.aye + t.nay + t.abstain) * IC.TUNE.law_push_margin / 100)"""),
    ("law: the Laws tab ignores a waiting vote", U,
     """                    if v and v.proposer ~= IC.CROWN and not v.answered then
                        ICUI.law_cat = cat""",
     """                    if false then
                        ICUI.law_cat = cat"""),
    ("law: the Laws tab opens an answered vote", U,
     """                    if v and v.proposer ~= IC.CROWN and not v.answered then
                        ICUI.law_cat = cat""",
     """                    if v and v.proposer ~= IC.CROWN then
                        ICUI.law_cat = cat"""),
    ("law: the button ignores a waiting law", U,
     """    out.any = out.offices or out.court or out.petitions or out.laws
""",
     """    out.any = out.offices or out.court or out.petitions
"""),

    # Race plumbing.
    # Each makes a Dwarf court run on Chaos Dwarf data, which no Chaos Dwarf
    # check can tell from the truth.
    ("race: IC.R never asking the faction its race", M,
     '    local k = IC._race_cache[faction_key] or IC.race_key(faction_key)',
     '    local k = IC._race_cache[faction_key]'),
    ("race: a failed race lookup kept for the session", M,
     '    if k then IC._race_cache[faction_key] = k end',
     '    IC._race_cache[faction_key] = k or "chd"'),
    ("race: the race's tune layer skipped", M,
     '    local base = IC.tune_layer(IC.TUNE[key], race and race.tune and race.tune[key])',
     '    local base = IC.TUNE[key]'),
    ("race: a key written without its race's infix", M,
     '    return "derpy_ic_" .. kind .. "_" .. (R or IC.RACES.chd).infix .. slug',
     '    return "derpy_ic_" .. kind .. "_" .. slug'),
    ("race: a race switched off still holding a court", M,
     '    return r.switch == nil or IC.TUNE[r.switch] ~= false',
     '    return true'),
    ("race: a larger race not raising the seat count", M,
     '    IC.MAX_SEATS = math.max(IC.MAX_SEATS or 0, r.MAX_SEATS)',
     '    IC.MAX_SEATS = IC.MAX_SEATS or r.MAX_SEATS'),
    ("race: the offices label counting the Chaos Dwarf tiers", U,
     '        widths[#widths + 1] = tostring(R.TIER_SEATS[R.TIERS[i]])',
     '        widths[#widths + 1] = tostring(IC.TIER_SEATS[IC.TIERS[i]])'),
    ("race: a lookup by slug answering the Chaos Dwarfs for every court", M,
     '    local R = IC.R(faction_key)\n    for i = 1, #R.OFFICES do\n        if R.OFFICES[i].slug == slug then return R.OFFICES[i] end',
     '    local R = IC.RACES.chd\n    for i = 1, #R.OFFICES do\n        if R.OFFICES[i].slug == slug then return R.OFFICES[i] end'),
    ("race: the panel drawing the Chaos Dwarf law board for any player", U,
     '    local R = ICUI.race()\n    local cat = R.LAW_ORDER[math.floor((i - 1) / 5) + 1]',
     '    local R = IC.RACES.chd\n    local cat = R.LAW_ORDER[math.floor((i - 1) / 5) + 1]'),
    # Grudges inside the court.
    ("grudge: the race guard dropped", M,
     """    if IC.race_key(faction_key) ~= "dwf" or not IC.GRUDGE_WORDS[code or ""] then return false end""",
     """    if not IC.GRUDGE_WORDS[code or ""] then return false end"""),
    ("grudge: the cap removed", M,
     """    if #book >= IC.TUNE.grudge_max then return false end""",
     """"""),
    ("grudge: the fade added", M,
     """        for i, g in ipairs(IC.grudges(faction_key, slug)) do""",
     """        for i, g in ipairs(IC.grudges(faction_key, slug)) do if cm:model():turn_number() - g.turn > 20 then break end"""),
    ("grudge: the newest settled, not the oldest", M,
     """    local g = table.remove(book, 1)""",
     """    local g = table.remove(book)"""),
    ("grudge: kinship on every race", M,
     """    local dwarf = IC.race_key(faction_key) == "dwf\"""",
     """    local dwarf = true"""),
    ("grudge: the countdown read off IC.TUNE", M,
     """                house.clock = IC.tune(faction_key, "secede_turns")""",
     """                house.clock = IC.TUNE.secede_turns"""),
    # The Book of Grudges.
    ("book: a band fired every turn", M,
     """        for i = had + 1, n do""",
     """        for i = 1, n do"""),
    ("book: a band reversed on a fall", M,
     """        local n = had
        while n < #bands and e.weight >= bands[n + 1] do n = n + 1 end
        for i = had + 1, n do
            cm:apply_dilemma_diplomatic_bonus(faction_key, e.key, penalty[i])
            fired = fired + 1
        end
        if n > had then court.book[e.key] = n end""",
     """        local n = 0
        while n < #bands and e.weight >= bands[n + 1] do n = n + 1 end
        for i = had + 1, n do
            cm:apply_dilemma_diplomatic_bonus(faction_key, e.key, penalty[i])
            fired = fired + 1
        end
        for i = n + 1, had do
            cm:apply_dilemma_diplomatic_bonus(faction_key, e.key, -penalty[i])
        end
        court.book[e.key] = n"""),
    ("book: band threshold off by one", M,
     """        while n < #bands and e.weight >= bands[n + 1] do n = n + 1 end""",
     """        while n < #bands and e.weight > bands[n + 1] do n = n + 1 end"""),
    ("book: named threshold off by one", M,
     """    return n > 0 and IC.TUNE.book_bands[n] >= IC.TUNE.book_named""",
     """    return n > 0 and IC.TUNE.book_bands[n] > IC.TUNE.book_named"""),
    ("book: deed on a fall", M,
     """        if context:resource():key() ~= IC.GRUDGE_POINTS or context:amount() <= 0 then""",
     """        if context:resource():key() ~= IC.GRUDGE_POINTS then"""),
    ("book: a deed for one party", M,
     """    if d.also then n = n + IC.add_renown(faction_key, d.also, IC.TUNE[d.tune], code) end""",
     """"""),
    ("book: the panel fills the turn's cache", M,
     """    if fill and not (IC._book and IC._book.turn == now) then""",
     """    if not (IC._book and IC._book.turn == now) then"""),
    ("book: a Chaos Dwarf court reads the Book", M,
     """    if not own or IC.race_key(faction_key) ~= "dwf" then return out end""",
     """    if not own then return out end"""),
    ("book: garrisons weighed", M,
     """    local forces = other:military_force_list(true)""",
     """    local forces = other:military_force_list()"""),
    ("book: a treaty read off the live weight", M,
     """    if not IC.in_book(faction_key, other_key) then return false end""",
     """    if IC.book_weight(faction_key, other_key) < IC.TUNE.book_named then return false end"""),
    ("book: another tab keeps the Book line", U,
     """        show(comp("ic_book", panel), false)""",
     """"""),
    ("book: the tooltip remembers a faction never named", U,
     """        if IC.in_book(faction, key) then""",
     """        if true then"""),
    ("book: the tooltip forgets who a treaty wrongs", U,
     """    if #known == 0 then return tip end""",
     """    do return tip end"""),
    # Both races in one campaign.
    ("both races: the race cache keyed by nothing", _holder(_SIG_R), _SIG_R,
     _SIG_R + "    IC._one_race = IC._one_race or IC._R_body(faction_key)\n"
     "    return IC._one_race\nend\nfunction IC._R_body(faction_key)\n"),
    ("both races: the race read off the player, not the faction in hand",
     _holder(_SIG_R), _SIG_R,
     _SIG_R + "    local human = cm:get_human_factions()\n"
     "    return IC._R_body(human and human[1] or faction_key)\nend\n"
     "function IC._R_body(faction_key)\n"),
    ("both races: one grudge book for every court", _holder(_SIG_GRUDGES), _SIG_GRUDGES,
     _SIG_GRUDGES + "    IC._first_book = IC._first_book or faction_key\n"
     "    return IC._grudges_body(IC._first_book, slug)\nend\n"
     "function IC._grudges_body(faction_key, slug)\n"),
    ("both races: a grudge written into a Chaos Dwarf court", _holder(_SIG_WRITE), _SIG_WRITE,
     _SIG_WRITE + _as_dwarf("IC._write_body, faction_key, slug, code")
     + "    return out\nend\nfunction IC._write_body(faction_key, slug, code)\n"),
    ("both races: the Book kept for every court", _holder(_SIG_TURN), _SIG_TURN,
     _SIG_TURN + _as_dwarf("IC.book_tick, faction_key")
     + "    return IC._turn_body(faction_key)\nend\nfunction IC._turn_body(faction_key)\n"),
    ("both races: the Dwarf courts switch ignored", _holder(_SIG_HAS), _SIG_HAS,
     _SIG_HAS + "    local was = IC.TUNE.dwarf_courts\n    IC.TUNE.dwarf_courts = true\n"
     "    local ok, out = pcall(IC._has_court_body, faction)\n"
     "    IC.TUNE.dwarf_courts = was\n    if not ok then error(out, 0) end\n"
     "    return out\nend\nfunction IC._has_court_body(faction)\n"),
    ("both races: a key built without its race", _holder(_SIG_KEY), _SIG_KEY,
     _SIG_KEY + "    return IC._key_body(kind, slug, nil)\nend\n"
     "function IC._key_body(kind, slug, faction_key)\n"),
    # Starting members.
    # THE POOL ROUTE. The wound gives the lord a new cqi, so every mistake that
    # keeps using the one he was made with returns nobody to the pool.
    ("starting members: the lord returned under the cqi he was made with", M,
     """        if wounded then cqi_back, hurt = IC.seed_wounded(faction_key, cqi, bg) end""",
     """        if wounded then cqi_back, hurt = cqi, true end"""),
    ("starting members: the wounded lord never returned to the pool", M,
     """            if hurt then cm:stop_character_convalescing(cqi_back) end
""",
     ""),
    # THE UNHURT LORD: the first lord of a party can come back from the wound
    # unhurt, and a lookup that wants is_wounded never finds him.
    ("starting members: the lookup wants the lord wounded", M,
     """        if man and not man:is_null_interface() and not man:has_military_force() then
            local cqi = man:command_queue_index()
            if cqi > after""",
     """        if man and not man:is_null_interface() and man:is_wounded() then
            local cqi = man:command_queue_index()
            if cqi > after"""),
    ("starting members: an unhurt lord sent home from convalescing", M,
     """            if hurt then cm:stop_character_convalescing(cqi_back) end""",
     """            cm:stop_character_convalescing(cqi_back)"""),
    # THE DWARF RUN OF EVENT RECORDS. Without the offset a Dwarf card names the
    # Chaos Dwarf record and wears its picture.
    ("dwarfs: a card raised at the Chaos Dwarf record", M,
     """    return ev[1] + (IC.R(faction_key).EVENT_OFFSET or 0)""",
     """    return ev[1]"""),
    ("dwarfs: located news numbered by the recipient, not the court it is about", M,
     """            x, y, ev[2], IC.event_index(slug, about or faction_key))""",
     """            x, y, ev[2], IC.event_index(slug, faction_key))"""),
    ("dwarfs: the plain card raised at the base record", M,
     """            ev[2], IC.event_index(slug, faction_key))""",
     """            ev[2], ev[1])"""),
    ("starting members: the lord keeps the background his birth dealt him", M,
     """        if old ~= bg then
            if old then cm:force_remove_trait(lookup, IC.bg_trait(old)) end
            cm:force_add_trait(lookup, IC.bg_trait(bg), false)
        end
        cm:wound_character(lookup, 1)""",
     """        cm:wound_character(lookup, 1)"""),
    ("starting members: the men a party already has not counted", M,
     """            local want = lo + cm:random_number(hi - lo + 1, 1) - 1 - (members or 0)""",
     """            local want = lo + cm:random_number(hi - lo + 1, 1) - 1"""),
    ("starting members: the roll ignored, every party at the fewest", M,
     """            local want = lo + cm:random_number(hi - lo + 1, 1) - 1 - (members or 0)""",
     """            local want = lo - (members or 0)"""),
    ("starting members: the Crown left out", M,
     """        if R.BACKGROUNDS[slug] then
            local _lords, members = IC.party_lords(faction_key, slug)""",
     """        if slug ~= IC.CROWN and R.BACKGROUNDS[slug] then
            local _lords, members = IC.party_lords(faction_key, slug)"""),
    ("starting members: a full party with nobody to lead it gets no lord", M,
     """            if want < 1 and slug ~= IC.CROWN and not IC.party_leader(faction_key, slug) then""",
     """            if false then"""),
    ("starting members: an AI court seeded too", M,
     """    if (IC.TUNE.seed_max or 0) <= 0 or not IC.is_human(faction_key) then return false end""",
     """    if (IC.TUNE.seed_max or 0) <= 0 then return false end"""),
    ("starting members: seeded after turn 1", M,
     """    if cm:model():turn_number() > 1 then return false end
    return not cm:get_saved_value(IC.SEED_DONE .. faction_key)""",
     """    return not cm:get_saved_value(IC.SEED_DONE .. faction_key)"""),
    ("starting members: never marked done, so seeded again", M,
     """    IC._seed_bg[faction_key] = nil
    cm:set_saved_value(IC.SEED_DONE .. faction_key, true)""",
     """    IC._seed_bg[faction_key] = nil"""),
    ("starting members: a spawn that never lands stalls the seeding", M,
     """        IC.warn("IRON COURT: a starting lord for " .. slug .. " never arrived")
        IC.seed_step(faction_key, plan, i + 1, made)""",
     """        IC.warn("IRON COURT: a starting lord for " .. slug .. " never arrived")"""),
    ("starting members: a lord landing after the watchdog gave up is wounded anyway", M,
     """                if IC._seed_wait[faction_key] ~= token then return end
""",
     ""),
    ("starting members: the turn-1 pool gift made beside the seeding", M,
     """            elseif not house.stored and not IC.seeding(faction_key) then""",
     """            elseif not house.stored then"""),
    ("starting members: MCT's numbers read under Custom only", M,
     """                and (preset == IC.PRESET_CUSTOM or IC.TUNE_START[key])""",
     """                and preset == IC.PRESET_CUSTOM"""),
    ("starting members: reversed numbers not swapped", M,
     """    if t.seed_min > t.seed_max then t.seed_min, t.seed_max = t.seed_max, t.seed_min end
""",
     ""),
    ("starting members: a hired starting lord not raised", M,
     """    if not (house and (house.stored or was)) then return end""",
     """    if not (house and house.stored) then return end"""),
    ("starting members: a hired starting lord never struck off", M,
     """        seeded[cqi] = nil
        IC.save_seeded_lords(faction_key, seeded)""",
     """        IC.save_seeded_lords(faction_key, seeded)"""),
    # THE CARDS AND THE MID-SEEDING PASS.
    ("starting members: a starting lord dealt and swapped like any recruit", M,
     """            local seeded = IC._seed_bg[faction_key]
            if seeded then""",
     """            local seeded = nil
            if seeded then"""),
    ("starting members: the leader pass runs mid-seeding", M,
     """    if IC._seeding[faction_key] then return 0 end
    local R = IC.R(faction_key)""",
     """    local R = IC.R(faction_key)"""),
    ("starting members: the feed shut by category only", M,
     """    for i = 1, #IC.SEED_QUIET_EVENTS do
        cm:disable_event_feed_events(off, "", "", IC.SEED_QUIET_EVENTS[i])
    end""",
     ""),
    ("starting members: the feed never shut before a lord", M,
     """    if i > #plan then return IC.seed_finish(faction_key, made, #plan) end
    IC.seed_quiet(true)""",
     """    if i > #plan then return IC.seed_finish(faction_key, made, #plan) end"""),
    ("starting members: the feed never opened again", M,
     """    cm:callback(function() IC.seed_quiet(false) end, 2)""",
     ""),
    # THE PRICE: the normal recruit price, charged once and written in the
    # panel.
    ("starting members: a starting lord hired free", M,
     """        if price then cm:treasury_mod(faction_key, -price) end""",
     ""),
    ("starting members: a starting lord paid for his hire", M,
     """        if price then cm:treasury_mod(faction_key, -price) end""",
     """        if price then cm:treasury_mod(faction_key, price) end"""),
    ("starting members: the price written on every real man's card", U,
     """        local price = cqi and seeded[cqi] and IC.seed_price(fk, cqi)""",
     """        local price = cqi and IC.seed_price(fk, cqi)"""),
    ("starting members: the price written with the cost left hidden", U,
     """                holder:SetVisible(true)
""",
     ""),
    ("starting members: the cards priced on every panel's opening", U,
     """    if context.string ~= ICUI.POOL_PANEL then return end
    ICUI.price_pool_later()""",
     """    ICUI.price_pool_later()"""),
    ("starting members: the cards never priced after a click", U,
     """    if not comp(ICUI.POOL_PANEL) then return end
    ICUI.price_pool_later()""",
     """    if not comp(ICUI.POOL_PANEL) then return end"""),
    # THE RECORD, READ AT A GLANCE.
    ("record: the Crown named by the faction again", U,
     """    if slug == IC.CROWN then
        return loc(IC.key("party_name", IC.CROWN, ICUI.player()), "The Crown")
    end
    if who == "c" then""",
     """    if who == "c" then"""),
    ("record: an unseated party's deed reads like a seated one's", U,
     """        local out = e.slug ~= IC.CROWN and not e.sw""",
     """        local out = false"""),
    ("record: a line drawn with no crest", U,
     """                    icon = a.icon, icon_kind = a.icon and "crest" or nil, plate = a.slug}""",
     """                    plate = a.slug}"""),
    ("record: a line drawn on no plate", U,
     """                    icon = a.icon, icon_kind = a.icon and "crest" or nil, plate = a.slug}""",
     """                    icon = a.icon, icon_kind = a.icon and "crest" or nil}"""),
    ("record: news drawn with no flag", U,
     """                             icon = news[i].faction
                                    and IC.house_icon(IC.CROWN, news[i].faction) or nil}""",
     """                             icon = nil}"""),
    ("record: a crest left at the porthole's height", U,
     """        local dy = kind == "porthole" and b[2] or ICUI.ROW_CHILD_XY.ic_row_crest[2]""",
     """        local dy = b[2]"""),
    ("a garrison captain stamped with his cards showing", M,
     """            local quiet = IC.is_colonel(character)""",
     """            local quiet = false"""),
]


def run():
    p = subprocess.run([LUA, HARNESS], capture_output=True, text=True)
    return p.returncode, (p.stdout + p.stderr).strip().splitlines()


def apply(path, old, new):
    """Write the mutation, returning the original source for the restore."""
    src = io.open(path, encoding="utf-8").read()
    if src.count(old) != 1:
        return None, src.count(old)
    io.open(path, "w", encoding="utf-8", newline="\n").write(src.replace(old, new))
    return src, 1


def restore(path, src):
    io.open(path, "w", encoding="utf-8", newline="\n").write(src)


def check(mutants, quiet=False):
    """Every mutant, one at a time. Returns the list of (what, why) failures."""
    code, lines = run()
    if code != 0:
        return [("the harness itself", "not green before anything was broken: %s"
                 % ("; ".join(l for l in lines if l.startswith("FAIL"))[:200]))]

    bad = []
    for what, path, old, new in mutants:
        src, hits = apply(path, old, new)
        if src is None:
            # THE CODE MOVED. Reported, never skipped: a mutant that cannot be
            # applied is a rule nobody is checking has stayed checked.
            bad.append((what, "STALE ANCHOR - matched %d times, not 1" % hits))
            continue
        try:
            code, lines = run()
        finally:
            restore(path, src)
        if code == 0:
            bad.append((what, "SURVIVED - the harness is green with this broken"))
            continue
        caught = [l for l in lines if l.startswith("FAIL")]
        if not caught:
            detail = "; ".join(lines)[:200]
            bad.append((what, "ERROR - harness exited without a FAIL assertion: %s"
                        % detail))
        elif not quiet:
            print("caught: %-58s %s" % (what, (caught[0][5:] if caught else "")[:70]))

    code, _lines = run()
    if code != 0:
        bad.append(("the tree", "left BROKEN - a restore did not take"))
    return bad


def selftest():
    """The runner's own: it has to be able to report a survivor.

    A mutation runner that could only ever print "caught" is the same failure it
    exists to find. So one is injected that this project's harness cannot
    possibly notice - a comment - and the run must report it as a survivor.

    And the file must come back byte for byte, because everything here writes
    into the SHIPPED script rather than a copy.
    """
    before = io.open(M, encoding="utf-8", newline="").read()
    harmless = [("a comment nobody can test", M,
                 "function IC.move_loyalty(faction_key, slug, delta)",
                 "-- mutate_iron_court selftest\n"
                 "function IC.move_loyalty(faction_key, slug, delta)")]
    bad = check(harmless, quiet=True)
    assert len(bad) == 1 and "SURVIVED" in bad[0][1], (
        "the runner did not report a mutation the harness cannot see: %r" % (bad,))

    # A STALE ANCHOR MUST BE REPORTED, not skipped. This is the failure mode a
    # frozen mutant list actually has: the code moves, the anchor stops matching,
    # and a runner that skipped it would print a clean report for rules nobody
    # had tested in months.
    stale = [("an anchor that has moved", M,
              "this string is in no version of the model", "x")]
    bad = check(stale, quiet=True)
    assert len(bad) == 1 and "STALE" in bad[0][1], (
        "a mutant whose anchor no longer matches was not reported: %r" % (bad,))

    # A Lua/parser crash is not evidence that an assertion protects a contract.
    # Keep the stderr/return-code distinction explicit: only a harness FAIL
    # counts as caught, otherwise a broken mutant could mask a broken harness.
    broken = [("a parser failure", M,
               "function IC.move_loyalty(faction_key, slug, delta)",
               "function IC.move_loyalty(")]
    bad = check(broken, quiet=True)
    assert len(bad) == 1 and "ERROR" in bad[0][1], (
        "the runner accepted a non-assertion harness failure: %r" % (bad,))

    after = io.open(M, encoding="utf-8", newline="").read()
    assert after == before, "the selftest did not restore the model byte for byte"

    # Every shipped mutant must at least be APPLICABLE right now, which is a
    # different question from whether it is caught - the run answers that - and
    # is the one worth failing fast on.
    for what, path, old, _new in MUTANTS:
        n = io.open(path, encoding="utf-8").read().count(old)
        assert n == 1, "%s: anchor matches %d times, not 1" % (what, n)

    print("selftest ok: %d mutants all anchored, a survivor and a stale anchor "
          "are both reported, the tree is restored" % len(MUTANTS))


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
        sys.exit(0)
    # An unknown flag would otherwise fall through to the FULL suite (flags are
    # dropped from the name filter), and a run killed midway leaves a mutant in
    # the shipped Lua.
    flags = [a for a in sys.argv[1:] if a.startswith("-")]
    if flags:
        sys.exit("unknown flag %r; usage: mutate_iron_court.py [--selftest] "
                 "[name substring ...]" % flags[0])
    want = sys.argv[1:]
    mutants = [m for m in MUTANTS
               if not want or any(w.lower() in m[0].lower() for w in want)]
    if not mutants:
        sys.exit("no mutant matches %r" % (want,))
    bad = check(mutants)
    for what, why in bad:
        print("SURVIVOR: %s - %s" % (what, why))
    print("%d mutants, %d unexplained" % (len(mutants), len(bad)))
    sys.exit(1 if bad else 0)
