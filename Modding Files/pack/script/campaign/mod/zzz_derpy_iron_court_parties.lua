-- Rival parties that act on their own: at most one court event a turn, in the
-- player's court only. Design:
-- docs/superpowers/specs/2026-09-23-iron-court-rival-party-ai-design.md
-- Loads after zzz_derpy_iron_court.lua ("." sorts before "_") and before the
-- panel. Defines functions and three mission listeners; nothing here may touch the campaign at load.

local T = IC.TUNE
T.party_act_floor       = 10   -- a motive below this is no event at all
T.party_feud_turns      = 10
T.party_feud_murder_age = 5
T.party_feud_seat       = 20   -- motive to feud over a stolen seat
T.party_feud_equal_motive = 12 -- motive to feud with an equal
T.party_feud_equal      = 5    -- share points apart that count as equal
T.party_feud_apart      = 10   -- an equals feud ends past this gap
T.party_feud_rest       = 5    -- turns before a party feuds again
T.party_feud_motive     = 15   -- motive for a feuding party's move
T.party_murder_odds_div = 4
T.governor_xp           = 750
T.party_demand_low      = 26   -- demands from this loyalty...
T.party_demand_high     = 74   -- ...to this one
T.party_demand_met      = 12   -- on top of loyalty_appointed
T.party_demand_refused  = 10
T.party_demand_turns    = 5
T.party_offer_line      = 75   -- offers at or above this loyalty
T.party_offer_turns     = 3
T.party_offer_envy      = 3    -- every OTHER rival party, when one is accepted
T.party_offer_gold_per_share = 60
T.party_offer_backing   = 100
T.party_offer_calm      = 10
T.party_offer_units     = 2

IC.agenda_state = {}

local function split(text, sep)
    local out = {}
    if not text or text == "" then return out end
    for piece in string.gmatch(text, "([^" .. sep .. "]+)") do
        out[#out + 1] = piece
    end
    return out
end

-- plot = {slug, move, actor, target, key, turn}: one warned move, court-wide.
-- feuds[slug] = rec for BOTH parties of a pair, rec = {a, b, cause, key, since, ends}.
-- calm[slug] = the turn a party may feud again.
-- demand = {slug, kind, cqi, key, was, ends}: one live demand, court-wide. `was`
-- is who held the post when it was made (0 for nobody).
-- offers[slug] = {kind, n, target, ends}. A target is a cqi or a party slug and
-- reads back from a save as a string.
function IC.agenda(faction_key)
    local a = IC.agenda_state[faction_key]
    if a then return a end
    a = {plot = nil, feuds = {}, calm = {}, demand = nil, offers = {}}
    local packed = cm:get_saved_value("derpy_ic_agenda_" .. faction_key)
    if packed and packed ~= "" then
        local parts = {}
        for field in string.gmatch(packed .. "|", "([^|]*)|") do
            parts[#parts + 1] = field
        end
        local p = split(parts[1] or "", ",")
        if #p >= 6 then
            a.plot = {slug = p[1], move = p[2], actor = tonumber(p[3]),
                      target = tonumber(p[4]),
                      key = p[5] ~= "-" and p[5] or nil,
                      turn = tonumber(p[6]) or 0}
        end
        for _, entry in ipairs(split(parts[2] or "", ";")) do
            local b = split(entry, ",")
            if #b >= 6 then
                local rec = {a = b[1], b = b[2], cause = b[3],
                             key = b[4] ~= "-" and b[4] or nil,
                             since = tonumber(b[5]) or 0,
                             ends = tonumber(b[6]) or 0}
                a.feuds[rec.a], a.feuds[rec.b] = rec, rec
            end
        end
        for _, entry in ipairs(split(parts[3] or "", ";")) do
            local b = split(entry, ",")
            if #b >= 2 then a.calm[b[1]] = tonumber(b[2]) end
        end
        local d = split(parts[4] or "", ",")
        if #d >= 6 then
            a.demand = {slug = d[1], kind = d[2], cqi = tonumber(d[3]) or 0,
                        key = d[4], was = tonumber(d[5]) or 0,
                        ends = tonumber(d[6]) or 0}
        end
        for _, entry in ipairs(split(parts[5] or "", ";")) do
            local o = split(entry, ",")
            if #o >= 5 then
                a.offers[o[1]] = {kind = o[2], n = tonumber(o[3]) or 0,
                                  target = o[4] ~= "-" and o[4] or nil,
                                  ends = tonumber(o[5]) or 0}
            end
        end
    end
    IC.agenda_state[faction_key] = a
    return a
end

function IC.save_agenda(faction_key)
    local a = IC.agenda(faction_key)
    local plot = ""
    if a.plot then
        local p = a.plot
        plot = string.format("%s,%s,%d,%d,%s,%d", p.slug, p.move, p.actor,
                             p.target, p.key or "-", p.turn or 0)
    end
    local feuds, calm = {}, {}
    for slug, rec in pairs(a.feuds) do
        if slug == rec.a then
            feuds[#feuds + 1] = string.format("%s,%s,%s,%s,%d,%d", rec.a,
                rec.b, rec.cause, rec.key or "-", rec.since, rec.ends)
        end
    end
    for slug, n in pairs(a.calm) do
        calm[#calm + 1] = slug .. "," .. tostring(n)
    end
    local demand = ""
    if a.demand then
        local d = a.demand
        demand = string.format("%s,%s,%d,%s,%d,%d", d.slug, d.kind, d.cqi,
                               d.key, d.was or 0, d.ends)
    end
    local offers = {}
    for slug, o in pairs(a.offers) do
        offers[#offers + 1] = string.format("%s,%s,%d,%s,%d", slug, o.kind, o.n,
            o.target ~= nil and tostring(o.target) or "-", o.ends)
    end
    table.sort(feuds)
    table.sort(calm)
    table.sort(offers)
    cm:set_saved_value("derpy_ic_agenda_" .. faction_key,
        plot .. "|" .. table.concat(feuds, ";") .. "|"
        .. table.concat(calm, ";") .. "|" .. demand .. "|"
        .. table.concat(offers, ";"))
end

-- Each entry: {key, can(fk, slug) -> target|nil, motive(fk, slug, target) -> int,
-- act(fk, slug, target)}. Filled by the sections below.
IC.PARTY_ACTS = {}

-- Most severe first: a party takes the worst move its loyalty allows and its
-- plotter can pay for.
IC.PARTY_MOVES = {
    {key = "murder",    line = 10, warned = true},
    {key = "unseat",    line = 25, warned = true},
    {key = "recall",    line = 25, warned = true},
    {key = "discredit", line = T.party_intrigue_line},
    {key = "rumour",    line = T.party_intrigue_line},
}

function IC.party_move_by_key(key)
    for _, move in ipairs(IC.PARTY_MOVES) do
        if move.key == key then return move end
    end
    return nil
end

local function men_of(faction_key, slug)
    local out = {}
    local faction = cm:get_faction(faction_key)
    if not faction or faction:is_null_interface() then return out end
    local list = faction:character_list()
    for i = 0, list:num_items() - 1 do
        local man = list:item_at(i)
        if man and not man:is_null_interface()
                and IC.house_of_character(man, faction_key) == slug then
            out[#out + 1] = man
        end
    end
    return out
end

local function richest(faction_key, slug, keep)
    local best, best_n
    for _, man in ipairs(men_of(faction_key, slug)) do
        local cqi = man:command_queue_index()
        local n = IC.standing(faction_key, cqi)
        if (not keep or keep(man, cqi))
                and (not best or n > best_n or (n == best_n and cqi < best)) then
            best, best_n = cqi, n
        end
    end
    return best, best_n or 0
end

function IC.party_plotter(faction_key, slug)
    return richest(faction_key, slug, function(_man, cqi)
        return IC.may_speak(faction_key, cqi)
    end)
end

-- The Crown's office this party claims, else its highest-tier seat.
local function crown_seat(faction_key, slug)
    local court = IC.court(faction_key)
    local best, best_tier
    for i = 1, #IC.OFFICES do
        local office = IC.OFFICES[i]
        local cqi = court.offices[office.slug]
        if cqi and IC.house_of_cqi(faction_key, cqi) == IC.CROWN then
            if office.affinity == slug then return cqi, office.slug end
            if not best or office.tier < best_tier then
                best, best_tier = office.slug, office.tier
            end
        end
    end
    if best then return court.offices[best], best end
    return nil
end

local function crown_governor(faction_key)
    local court = IC.court(faction_key)
    local keys = {}
    for province in pairs(court.govs) do keys[#keys + 1] = province end
    table.sort(keys)
    for _, province in ipairs(keys) do
        local cqi = court.govs[province]
        if IC.house_of_cqi(faction_key, cqi) == IC.CROWN then
            return cqi, province
        end
    end
    return nil
end

function IC.party_target(faction_key, slug, move, enemy)
    if move == "unseat" then
        if enemy ~= IC.CROWN then return nil end
        return crown_seat(faction_key, slug)
    elseif move == "recall" then
        if enemy ~= IC.CROWN then return nil end
        return crown_governor(faction_key)
    elseif move == "murder" then
        local ruler = IC.faction_leader_cqi(faction_key)
        local cqi = richest(faction_key, enemy, function(man, c)
            return not IC.is_legend(man) and c ~= ruler
        end)
        return cqi
    end
    local cqi = richest(faction_key, enemy)
    return cqi
end

-- The player's own numbers: cost, base odds, 1 point per 10 influence of edge.
function IC.party_strike(faction_key, slug, move, actor, target, key, odds_div)
    local cost = IC.plot_cost(move)
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
    local victim_house = IC.house_of_cqi(faction_key, target)
    local at_crown = victim_house == IC.CROWN
    if cm:random_number(100, 1) > chance then
        IC.log(faction_key, "plot_failed", slug, victim_house, cost)
        if at_crown then IC.feed(faction_key, "party_plot_fail") end
        return false
    end
    if move == "rumour" then
        IC.add_standing(faction_key, target, -T.plot_rumour_damage)
    elseif move == "discredit" then
        IC.add_standing(faction_key, target, -T.plot_discredit_standing)
        local house = IC.court(faction_key).houses[victim_house or ""]
        if house then
            house.weight = math.max(1, (house.weight or 0)
                                    - T.plot_discredit_weight)
        end
    elseif move == "unseat" then
        IC.dismiss(faction_key, key, true)
        IC.court(faction_key).terms[key] = nil
        IC.apply_office_bundles(faction_key)
    elseif move == "recall" then
        IC.release_governor(faction_key, key)
    elseif move == "murder" then
        local victim = IC.character_by_cqi(faction_key, target)
        if victim then cm:kill_character(cm:char_lookup_str(victim), false) end
    end
    local kind = (move == "unseat" or move == "recall")
                 and ("party_" .. move) or move
    IC.log(faction_key, kind, slug, victim_house, cost)
    if at_crown then IC.feed(faction_key, "party_plot_ok") end
    if move == "murder" and not at_crown then
        IC.feed(faction_key, "party_feud_murder")
    end
    return true
end

function IC.party_warn(faction_key, slug, t)
    IC.agenda(faction_key).plot = {
        slug = slug, move = t.move.key, actor = t.actor, target = t.target,
        key = t.key, turn = cm:model():turn_number(),
    }
    IC.log(faction_key, "party_warn", slug, t.move.key, 0)
    IC.feed(faction_key, "party_plot_warn")
end

-- PLACATED IS READ AS THE PLAYER LEFT IT. IC.turn calls this before the turn
-- moves any loyalty: the landing below runs after the drift, so a party lifted
-- one above its line on the player's turn drifted back onto it and the warned
-- move landed anyway (found 2026-09-25). Not saved: set and read in one turn.
function IC.party_placate(faction_key)
    local p = IC.agenda(faction_key).plot
    if not p then return end
    local house = IC.court(faction_key).houses[p.slug]
    local move = IC.party_move_by_key(p.move)
    if house and move and (house.loyalty or 0) > move.line then p.placated = true end
end

-- Why a warned move no longer lands, or nil when it still does.
function IC.plot_void(faction_key, p)
    local court = IC.court(faction_key)
    local house = court.houses[p.slug]
    if not house then return "gone" end
    local move = IC.party_move_by_key(p.move)
    if not move or p.placated or (house.loyalty or 0) > move.line then
        return "placated"
    end
    if not IC.character_by_cqi(faction_key, p.actor) then return "plotter dead" end
    if IC.standing(faction_key, p.actor) < IC.plot_cost(p.move) then
        return "poor"
    end
    local victim = IC.character_by_cqi(faction_key, p.target)
    if not victim then return "target dead" end
    if p.move == "murder" and p.target == IC.faction_leader_cqi(faction_key) then
        return "ruler"
    end
    if IC.house_of_character(victim, faction_key) ~= IC.CROWN then
        return "moved"
    end
    if p.move == "unseat" and court.offices[p.key] ~= p.target then
        return "moved"
    end
    if p.move == "recall" and court.govs[p.key] ~= p.target then
        return "moved"
    end
    return nil
end

function IC.land_plot(faction_key)
    local a = IC.agenda(faction_key)
    local p = a.plot
    a.plot = nil
    if IC.plot_void(faction_key, p) then
        IC.log(faction_key, "party_dropped", p.slug, p.move, 0)
        IC.feed(faction_key, "party_plot_dropped")
        return "dropped"
    end
    IC.party_strike(faction_key, p.slug, p.move, p.actor, p.target, p.key)
    return "landed"
end

IC.PARTY_ACTS[#IC.PARTY_ACTS + 1] = {
    key = "intrigue",
    can = function(faction_key, slug)
        local house = IC.court(faction_key).houses[slug]
        if not house or (house.loyalty or 0) > T.party_intrigue_line then
            return nil
        end
        if IC.agenda(faction_key).feuds[slug] then return nil end
        local actor, purse = IC.party_plotter(faction_key, slug)
        if not actor then return nil end
        for _, move in ipairs(IC.PARTY_MOVES) do
            if house.loyalty <= move.line and purse >= IC.plot_cost(move.key) then
                local target, key = IC.party_target(faction_key, slug,
                                                    move.key, IC.CROWN)
                if target then
                    return {move = move, actor = actor, target = target,
                            key = key}
                end
            end
        end
        return nil
    end,
    motive = function(faction_key, slug, _t)
        local court = IC.court(faction_key)
        local claimed = 0
        for i = 1, #IC.OFFICES do
            local cqi = court.offices[IC.OFFICES[i].slug]
            if IC.OFFICES[i].affinity == slug and cqi
                    and IC.house_of_cqi(faction_key, cqi) == IC.CROWN then
                claimed = claimed + 1
            end
        end
        return (T.party_intrigue_line + 1 - court.houses[slug].loyalty)
               + 10 * claimed
    end,
    act = function(faction_key, slug, t)
        if t.move.warned then
            IC.party_warn(faction_key, slug, t)
        else
            IC.party_strike(faction_key, slug, t.move.key, t.actor, t.target, t.key)
        end
    end,
}

function IC.feud_target(faction_key, slug)
    local a = IC.agenda(faction_key)
    local now = cm:model():turn_number()
    local function free(s)
        return not a.feuds[s] and (a.calm[s] or 0) <= now
    end
    if not free(slug) then return nil end
    local court = IC.court(faction_key)
    for i = 1, #IC.OFFICES do
        local office = IC.OFFICES[i]
        local cqi = court.offices[office.slug]
        if office.affinity == slug and cqi then
            local holder = IC.house_of_cqi(faction_key, cqi)
            if holder and holder ~= slug and holder ~= IC.CROWN
                    and court.houses[holder] and free(holder) then
                return {with = holder, cause = "seat", key = office.slug}
            end
        end
    end
    local mine = IC.share(faction_key, slug)
    for _, other in ipairs(IC.present_houses(faction_key)) do
        if other ~= slug and other ~= IC.CROWN and free(other)
                and math.abs(IC.share(faction_key, other) - mine)
                    <= T.party_feud_equal then
            return {with = other, cause = "equal"}
        end
    end
    return nil
end

IC.PARTY_ACTS[#IC.PARTY_ACTS + 1] = {
    key = "feud",
    can = function(faction_key, slug) return IC.feud_target(faction_key, slug) end,
    motive = function(_fk, _slug, t)
        return t.cause == "seat" and T.party_feud_seat or T.party_feud_equal_motive
    end,
    act = function(faction_key, slug, t)
        local now = cm:model():turn_number()
        local rec = {a = slug, b = t.with, cause = t.cause, key = t.key,
                     since = now, ends = now + T.party_feud_turns}
        local a = IC.agenda(faction_key)
        a.feuds[slug], a.feuds[t.with] = rec, rec
        IC.log(faction_key, "feud", slug, t.with, 0)
        IC.feed(faction_key, "party_feud")
    end,
}

IC.PARTY_ACTS[#IC.PARTY_ACTS + 1] = {
    key = "feud_move",
    can = function(faction_key, slug)
        local rec = IC.agenda(faction_key).feuds[slug]
        if not rec then return nil end
        local enemy = rec.a == slug and rec.b or rec.a
        local actor, purse = IC.party_plotter(faction_key, slug)
        if not actor then return nil end
        local order = {"discredit", "rumour"}
        if cm:model():turn_number() - rec.since >= T.party_feud_murder_age then
            order = {"murder", "discredit", "rumour"}
        end
        for _, move in ipairs(order) do
            if purse >= IC.plot_cost(move) then
                local target = IC.party_target(faction_key, slug, move, enemy)
                if target then
                    return {move = move, actor = actor, target = target}
                end
            end
        end
        return nil
    end,
    motive = function() return T.party_feud_motive end,
    act = function(faction_key, slug, t)
        IC.party_strike(faction_key, slug, t.move, t.actor, t.target, nil,
                        t.move == "murder" and T.party_murder_odds_div or nil)
    end,
}

-- Upkeep, not an event: every feud whose cause is gone, whose time is up, or
-- whose party has left ends here.
function IC.end_feuds(faction_key)
    local a = IC.agenda(faction_key)
    local court = IC.court(faction_key)
    local now = cm:model():turn_number()
    local ended = {}
    for slug, rec in pairs(a.feuds) do
        if slug == rec.a then
            local over = now >= rec.ends
                or not court.houses[rec.a] or not court.houses[rec.b]
            if not over and rec.cause == "seat" then
                local holder = court.offices[rec.key or ""]
                over = not holder or IC.house_of_cqi(faction_key, holder) ~= rec.b
            elseif not over and rec.cause == "equal" then
                over = math.abs(IC.share(faction_key, rec.a)
                                - IC.share(faction_key, rec.b)) > T.party_feud_apart
            end
            if over then ended[#ended + 1] = rec end
        end
    end
    for _, rec in ipairs(ended) do
        a.feuds[rec.a], a.feuds[rec.b] = nil, nil
        a.calm[rec.a] = now + T.party_feud_rest
        a.calm[rec.b] = now + T.party_feud_rest
        IC.log(faction_key, "feud_end", rec.a, rec.b, 0)
        IC.feed(faction_key, "party_feud_end")
    end
    return #ended
end

-- Rank is half of every office's bar; a governor serves at home and would
-- otherwise never climb. One log line lists every governor's rank.
-- A rank of 0 is a man the engine will not level: measured live, seven of nine
-- governors stayed at 0 through three grants while the lords with armies
-- climbed (garrison commanders and pool lords, the spec's two unknowns). The
-- post pays such a man a second governor wage instead, marked "+inf" in the log.
function IC.governor_xp(faction_key)
    local given = {}
    for _province, cqi in pairs(IC.court(faction_key).govs) do
        local man = IC.character_by_cqi(faction_key, cqi)
        if man then
            pcall(function()
                cm:add_agent_experience(cm:char_lookup_str(man), T.governor_xp)
            end)
            local rank = "?"
            pcall(function() rank = tostring(man:rank()) end)
            local line = tostring(cqi) .. "@r" .. rank
            if rank == "0" then
                IC.add_standing(faction_key, cqi, IC.TUNE.governor_income)
                line = line .. "+inf"
            end
            given[#given + 1] = line
        end
    end
    table.sort(given)
    if #given > 0 then
        IC.say("IRON COURT: governors given " .. T.governor_xp .. " xp in "
               .. faction_key .. ": " .. table.concat(given, " "))
    end
    return #given
end

-- DEMANDS. One live demand court-wide, issued as a real mission so the player
-- sees it in the objectives panel. The mission's text is loc and cannot name
-- anyone; the party card's tooltip names the man and the post.
IC.DEMAND_KEYS = {office = "derpy_ic_demand_office",
                  gov = "derpy_ic_demand_province"}
IC.DEMAND_SCRIPT_KEY = "derpy_ic_demand"
IC.DEMAND_REWARD = "derpy_ic_demand_reward"

-- This party's men who hold no post, richest first.
local function free_men(faction_key, slug)
    local out = {}
    for _, cand in ipairs(IC.candidates(faction_key)) do
        if cand.slug == slug and not cand.busy then out[#out + 1] = cand.cqi end
    end
    table.sort(out, function(x, y)
        local sx, sy = IC.standing(faction_key, x), IC.standing(faction_key, y)
        if sx ~= sy then return sx > sy end
        return x < y
    end)
    return out
end

-- A vacant office one of its free men can take now, the offices it claims
-- first; else a province with no overseer or a Crown one.
function IC.demand_target(faction_key, slug)
    local men = free_men(faction_key, slug)
    if #men == 0 then return nil end
    local court = IC.court(faction_key)
    local claimed, other = {}, {}
    for i = 1, #IC.OFFICES do
        local office = IC.OFFICES[i]
        if not court.offices[office.slug] then
            local list = office.affinity == slug and claimed or other
            list[#list + 1] = office.slug
        end
    end
    for _, list in ipairs({claimed, other}) do
        for _, office_slug in ipairs(list) do
            for _, cqi in ipairs(men) do
                if IC.can_appoint(faction_key, office_slug, cqi) then
                    return {kind = "office", cqi = cqi, key = office_slug, was = 0}
                end
            end
        end
    end
    for _, province in ipairs(IC.seats(faction_key)) do
        local holder = court.govs[province]
        if not holder or IC.house_of_cqi(faction_key, holder) == IC.CROWN then
            return {kind = "gov", cqi = men[1], key = province, was = holder or 0}
        end
    end
    return nil
end

function IC.demand_string(kind)
    local key = IC.DEMAND_KEYS[kind]
    return "mission{key " .. key .. ";issuer CLAN_ELDERS;turn_limit "
        .. T.party_demand_turns .. ";primary_objectives_and_payload{"
        .. "objective{type SCRIPTED;script_key " .. IC.DEMAND_SCRIPT_KEY
        .. ";override_text mission_text_text_" .. key .. ";}"
        .. "payload{text_display " .. IC.DEMAND_REWARD .. ";}}}"
end

function IC.issue_demand(faction_key, slug, t)
    local a = IC.agenda(faction_key)
    a.demand = {slug = slug, kind = t.kind, cqi = t.cqi, key = t.key,
                was = t.was or 0,
                ends = cm:model():turn_number() + T.party_demand_turns}
    -- Saved before the engine call: a mission can raise its own events from
    -- inside the call that creates it.
    IC.save_agenda(faction_key)
    local ok, err = pcall(function()
        cm:trigger_custom_mission_from_string(faction_key,
                                              IC.demand_string(t.kind))
    end)
    if not ok then
        a.demand = nil
        IC.save_agenda(faction_key)
        IC.warn("IRON COURT: demand not issued in " .. faction_key .. ": "
               .. tostring(err))
        return false
    end
    IC.log(faction_key, "demand", slug, t.key, 0)
    IC.feed(faction_key, "party_demand")
    IC.say("IRON COURT: " .. slug .. " demands " .. t.kind .. " " .. t.key
           .. " for cqi " .. tostring(t.cqi) .. " in " .. faction_key)
    return true
end

IC.PARTY_ACTS[#IC.PARTY_ACTS + 1] = {
    key = "demand",
    can = function(faction_key, slug)
        local house = IC.court(faction_key).houses[slug]
        if not house then return nil end
        local loyalty = house.loyalty or 0
        if loyalty < T.party_demand_low or loyalty > T.party_demand_high then
            return nil
        end
        if IC.agenda(faction_key).demand then return nil end
        return IC.demand_target(faction_key, slug)
    end,
    motive = function(faction_key, slug, _t)
        local held = #IC.offices_of_house(faction_key, slug)
                     + #IC.provinces_of_house(faction_key, slug)
        return math.max(0, IC.share(faction_key, slug) / 10 - held) * 8
    end,
    act = function(faction_key, slug, t) IC.issue_demand(faction_key, slug, t) end,
}

-- Where a live demand stands: "met", "refused" or "void", or nil while it waits.
function IC.demand_state(faction_key, d)
    local court = IC.court(faction_key)
    if not court.houses[d.slug] then return "void" end
    if not IC.character_by_cqi(faction_key, d.cqi) then return "void" end
    local holder
    if d.kind == "office" then
        holder = court.offices[d.key]
    else
        -- A PROVINCE NO LONGER HELD can never be given. IC.seats is what
        -- IC.demand_target picked it from, so the two cannot disagree.
        local held = false
        for _, province in ipairs(IC.seats(faction_key)) do
            if province == d.key then held = true end
        end
        if not held then return "void" end
        holder = court.govs[d.key]
    end
    if holder == d.cqi then return "met" end
    if holder and holder ~= d.was then return "refused" end
    if cm:model():turn_number() >= d.ends then
        -- A DEMAND NOBODY COULD GRANT LAPSES. Its man short of the office's bar
        -- is exactly when ACCEPT is red (can_grant_demand), and running out
        -- charged the refusal for a seat the player could never give (found
        -- 2026-09-25). A man put in another post is still a refusal: that one
        -- the player chose.
        if d.kind == "office" and not IC.can_appoint(faction_key, d.key, d.cqi) then
            return "void"
        end
        return "refused"
    end
    return nil
end

-- Idempotent: the record is cleared before anything else, so the mission
-- event the engine raises from inside the calls below finds nothing left to
-- settle. `ended` means the engine has already closed the mission.
function IC.settle_demand(faction_key, outcome, ended)
    local a = IC.agenda(faction_key)
    local d = a.demand
    if not d then return false end
    a.demand = nil
    IC.save_agenda(faction_key)
    local mission = IC.DEMAND_KEYS[d.kind]
    if outcome == "met" then
        IC.move_loyalty(faction_key, d.slug, T.party_demand_met)
        IC.log(faction_key, "demand_met", d.slug, d.key, 0)
    elseif outcome == "refused" then
        IC.move_loyalty(faction_key, d.slug, -T.party_demand_refused)
        IC.log(faction_key, "demand_refused", d.slug, d.key, 0)
        IC.feed(faction_key, "party_demand_refused")
    else
        IC.log(faction_key, "demand_void", d.slug, d.key, 0)
    end
    if not ended then
        pcall(function()
            if outcome == "void" then
                cm:cancel_custom_mission(faction_key, mission)
            else
                cm:complete_scripted_mission_objective(faction_key, mission,
                    IC.DEMAND_SCRIPT_KEY, outcome == "met")
            end
        end)
    end
    IC.say("IRON COURT: " .. d.slug .. "'s demand for " .. d.key .. " "
           .. outcome .. " in " .. faction_key)
    IC.save(faction_key)
    return true
end

-- Upkeep, not an event.
function IC.check_demand(faction_key)
    local d = IC.agenda(faction_key).demand
    if not d then return nil end
    local outcome = IC.demand_state(faction_key, d)
    if outcome then IC.settle_demand(faction_key, outcome) end
    return outcome
end

-- ANSWERED FROM THE PETITIONS TAB (author, 2026-09-24). A demand is always a
-- seat, so granting it seats the man it names in the post it names - through
-- the same calls the Offices and Governors tabs make, so no rule of theirs is
-- skipped - and settles it now instead of at the next turn start.
-- Returns ok, why, spare; the codes are the panel's to turn into sentences.
-- THE QUESTION WITHOUT THE ACT, so the tab can draw ACCEPT red on exactly the
-- demands the click would refuse. An open demand only: one the turn has
-- already decided is grant_demand's to settle.
function IC.can_grant_demand(faction_key)
    local d = IC.agenda(faction_key).demand
    if not d then return false, "no demand" end
    if IC.demand_state(faction_key, d) then return true end
    -- ONE POST PER MAN, which the pickers enforce by drawing him BUSY. The
    -- demand picked a free man; he may have taken another post since.
    local court = IC.court(faction_key)
    for _, cqi in pairs(court.offices) do
        if cqi == d.cqi then return false, "busy" end
    end
    for _, cqi in pairs(court.govs) do
        if cqi == d.cqi then return false, "busy" end
    end
    if d.kind == "office" then
        -- The office's own rank and influence bars, shortfall and all.
        return IC.can_appoint(faction_key, d.key, d.cqi)
    end
    return true
end

function IC.grant_demand(faction_key)
    local may, why, spare = IC.can_grant_demand(faction_key)
    if not may then return false, why, spare end
    local d = IC.agenda(faction_key).demand
    local state = IC.demand_state(faction_key, d)
    if state then
        IC.settle_demand(faction_key, state)
        if state == "met" then return true end
        return false, "gone"
    end
    if d.kind == "office" then
        if not IC.appoint(faction_key, d.key, d.cqi) then return false, "no" end
    elseif not IC.assign_governor(faction_key, d.key, d.cqi) then
        return false, "no"
    end
    IC.check_demand(faction_key)
    return true
end

-- The turn limit's answer, given now. A demand that has already been met or
-- voided is settled as what it is, not as a refusal.
function IC.refuse_demand(faction_key)
    local d = IC.agenda(faction_key).demand
    if not d then return false, "no demand" end
    local state = IC.demand_state(faction_key, d)
    if state then
        IC.settle_demand(faction_key, state)
        return false, "gone"
    end
    return IC.settle_demand(faction_key, "refused")
end

-- The engine's own word on a demand: a turn limit running out fails the
-- mission. Only a demand still open is settled here.
local function demand_event(outcome)
    return function(context)
        local faction_key, key
        pcall(function() faction_key = context:faction():name() end)
        pcall(function() key = context:mission():mission_record_key() end)
        if not faction_key or not key then return end
        if key ~= IC.DEMAND_KEYS.office and key ~= IC.DEMAND_KEYS.gov then
            return
        end
        local d = IC.agenda(faction_key).demand
        if d and IC.DEMAND_KEYS[d.kind] == key then
            -- A LATE EVENT FROM THE DEMAND BEFORE, on the same key. Nothing can
            -- end a demand mission on the turn it is issued: no manual cancel, a
            -- SCRIPTED objective ends only through the Lua, and the turn limit
            -- cannot run out on turn 0.
            if d.ends - T.party_demand_turns >= cm:model():turn_number() then return end
            -- The engine's expiry and IC.check_demand fall on one turn boundary
            -- in no known order, so a man seated on the last turn is re-read.
            -- A local, not `outcome`: that upvalue is every later event's too.
            local result = outcome
            -- AND ONE NOBODY COULD GRANT LAPSES, as IC.demand_state rules.
            if result == "refused" then
                local now = IC.demand_state(faction_key, d)
                if now == "met" or now == "void" then result = now end
            end
            IC.settle_demand(faction_key, result, true)
        end
    end
end

core:add_listener("ic_demand_succeeded", "MissionSucceeded", true,
                  demand_event("met"), true)
core:add_listener("ic_demand_failed", "MissionFailed", true,
                  demand_event("refused"), true)
core:add_listener("ic_demand_cancelled", "MissionCancelled", true,
                  demand_event("void"), true)

-- OFFERS. A loyal party gives the Crown something; the player takes it on the
-- Petitions tab, and every other party resents it.
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
-- ponytail: the engine's army size, fixed at 20; read it if CA ever exposes it.
local ARMY_UNITS = 20

function IC.troop_key(slug)
    return IC.PARTY_TROOPS[slug] or IC.TROOPS_DEFAULT
end

-- The free Crown man nearest below a vacant office's influence bar, within
-- the backing of it and already past its rank bar.
function IC.backing_target(faction_key)
    local court = IC.court(faction_key)
    local best, best_gap
    for _, cand in ipairs(IC.candidates(faction_key)) do
        if cand.slug == IC.CROWN and not cand.busy then
            local has = IC.standing(faction_key, cand.cqi)
            for i = 1, #IC.OFFICES do
                local office = IC.OFFICES[i]
                local gap = IC.tier_influence(office.tier) - has
                if not court.offices[office.slug]
                        and cand.rank >= IC.office_rank(office.slug)
                        and gap > 0 and gap <= T.party_offer_backing
                        and (not best or gap < best_gap
                             or (gap == best_gap and cand.cqi < best)) then
                    best, best_gap = cand.cqi, gap
                end
            end
        end
    end
    return best
end

function IC.calm_target(faction_key, slug)
    local court = IC.court(faction_key)
    for _, other in ipairs(IC.present_houses(faction_key)) do
        local house = court.houses[other]
        if other ~= slug and other ~= IC.CROWN and house
                and (house.clock or 0) > 0 then
            return other
        end
    end
    return nil
end

local function army_units(man)
    local n
    pcall(function()
        local force = man:military_force()
        if not force:is_null_interface() and not force:is_armed_citizenry() then
            n = force:unit_list():num_items()
        end
    end)
    return n
end

function IC.troops_target(faction_key)
    local best
    for _, cand in ipairs(IC.candidates(faction_key)) do
        if cand.slug == IC.CROWN and cand.character then
            local n = army_units(cand.character)
            if n and n <= ARMY_UNITS - T.party_offer_units
                    and (not best or cand.cqi < best) then
                best = cand.cqi
            end
        end
    end
    return best
end

-- Everything this party could offer now, gold first because it is always there.
function IC.offer_options(faction_key, slug)
    local out = {{kind = "gold", n = math.floor(IC.share(faction_key, slug)
                                                * T.party_offer_gold_per_share)}}
    local man = IC.backing_target(faction_key)
    if man then
        out[#out + 1] = {kind = "backing", n = T.party_offer_backing, target = man}
    end
    local calm = IC.calm_target(faction_key, slug)
    if calm then
        out[#out + 1] = {kind = "calm", n = T.party_offer_calm, target = calm}
    end
    local lord = IC.troops_target(faction_key)
    if lord then
        out[#out + 1] = {kind = "troops", n = T.party_offer_units, target = lord}
    end
    return out
end

IC.PARTY_ACTS[#IC.PARTY_ACTS + 1] = {
    key = "offer",
    can = function(faction_key, slug)
        local house = IC.court(faction_key).houses[slug]
        if not house or (house.loyalty or 0) < T.party_offer_line then
            return nil
        end
        if IC.agenda(faction_key).offers[slug] then return nil end
        return IC.offer_options(faction_key, slug)
    end,
    motive = function(faction_key, slug, _t)
        return (IC.court(faction_key).houses[slug].loyalty
                - (T.party_offer_line - 1))
               + IC.share(faction_key, slug) / 5
    end,
    act = function(faction_key, slug, options)
        local pick = options[cm:random_number(#options, 1)] or options[1]
        IC.agenda(faction_key).offers[slug] = {
            kind = pick.kind, n = pick.n, target = pick.target,
            ends = cm:model():turn_number() + T.party_offer_turns}
        IC.log(faction_key, "offer", slug, pick.kind, pick.n)
        IC.feed(faction_key, "party_offer")
    end,
}

-- Returns ok, why. The codes are the panel's to turn into sentences.
function IC.can_accept_offer(faction_key, slug)
    local o = IC.agenda(faction_key).offers[slug or ""]
    if not o then return false, "no offer" end
    if cm:model():turn_number() >= o.ends then return false, "lapsed" end
    local court = IC.court(faction_key)
    if not court.houses[slug] then return false, "gone" end
    if o.kind == "backing" then
        if not IC.character_by_cqi(faction_key, tonumber(o.target)) then
            return false, "gone"
        end
    elseif o.kind == "calm" then
        if not court.houses[o.target or ""] then return false, "gone" end
    elseif o.kind == "troops" then
        local lord = IC.character_by_cqi(faction_key, tonumber(o.target))
        local n = lord and army_units(lord)
        if not n then return false, "gone" end
        if n > ARMY_UNITS - o.n then return false, "room" end
    end
    return true
end

function IC.accept_offer(faction_key, slug)
    local ok, why = IC.can_accept_offer(faction_key, slug)
    if not ok then return false, why end
    local a = IC.agenda(faction_key)
    local o = a.offers[slug]
    a.offers[slug] = nil
    local court = IC.court(faction_key)
    if o.kind == "gold" then
        cm:treasury_mod(faction_key, o.n)
    elseif o.kind == "backing" then
        IC.add_standing(faction_key, tonumber(o.target), o.n)
    elseif o.kind == "calm" then
        court.houses[o.target].clock = 0
        IC.move_loyalty(faction_key, o.target, o.n)
    elseif o.kind == "troops" then
        local lord = IC.character_by_cqi(faction_key, tonumber(o.target))
        local lookup = cm:char_lookup_str(lord)
        for _ = 1, o.n do
            cm:grant_unit_to_character(lookup, IC.troop_key(slug))
        end
    end
    for _, other in ipairs(IC.present_houses(faction_key)) do
        if other ~= slug and other ~= IC.CROWN then
            IC.move_loyalty(faction_key, other, -T.party_offer_envy)
        end
    end
    IC.log(faction_key, "offer_taken", slug, o.kind, o.n)
    IC.save_agenda(faction_key)
    IC.save(faction_key)
    return true
end

function IC.decline_offer(faction_key, slug)
    local a = IC.agenda(faction_key)
    if not a.offers[slug or ""] then return false, "no offer" end
    a.offers[slug] = nil
    IC.save_agenda(faction_key)
    return true
end

-- Upkeep, not an event: offers past their turns, or from a party that left.
function IC.expire_offers(faction_key)
    local a = IC.agenda(faction_key)
    local court = IC.court(faction_key)
    local now = cm:model():turn_number()
    local gone = 0
    for slug, o in pairs(a.offers) do
        if now >= o.ends or not court.houses[slug] then
            a.offers[slug] = nil
            gone = gone + 1
        end
    end
    return gone
end

function IC.party_turn(faction_key)
    if not IC.is_human(faction_key) then return nil end
    IC.governor_xp(faction_key)
    IC.end_feuds(faction_key)
    IC.check_demand(faction_key)
    IC.expire_offers(faction_key)
    if IC.agenda(faction_key).plot then
        local done = IC.land_plot(faction_key)
        IC.save_agenda(faction_key)
        IC.save(faction_key)
        return done
    end
    -- THE parties_act SETTING OFF: what is already open settles above, and
    -- nothing new - no scheme, feud, demand or offer - is started.
    if not T.parties_act then
        IC.save_agenda(faction_key)
        IC.save(faction_key)
        return nil
    end
    local picks = {}
    for _, slug in ipairs(IC.present_houses(faction_key)) do
        if slug ~= IC.CROWN then
            for _, act in ipairs(IC.PARTY_ACTS) do
                local target = act.can(faction_key, slug)
                if target then
                    local m = math.floor(act.motive(faction_key, slug, target))
                    if m >= T.party_act_floor then
                        picks[#picks + 1] = {act = act, slug = slug,
                                             target = target, motive = m}
                    end
                end
            end
        end
    end
    local done = nil
    if #picks > 0 then
        table.sort(picks, function(x, y)
            if x.motive ~= y.motive then return x.motive > y.motive end
            if x.slug ~= y.slug then return x.slug < y.slug end
            return x.act.key < y.act.key
        end)
        local top = math.min(3, #picks)
        local total = 0
        for i = 1, top do total = total + picks[i].motive end
        local roll = cm:random_number(total, 1)
        local chosen = picks[top]
        for i = 1, top do
            roll = roll - picks[i].motive
            if roll <= 0 then chosen = picks[i]; break end
        end
        chosen.act.act(faction_key, chosen.slug, chosen.target)
        done = chosen.act.key
    end
    IC.save_agenda(faction_key)
    IC.save(faction_key)
    return done
end
