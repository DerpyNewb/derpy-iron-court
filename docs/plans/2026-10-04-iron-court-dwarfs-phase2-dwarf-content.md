# Iron Court for Dwarfs - Phase 2: Dwarf content Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make a Dwarf faction (subculture `wh_main_sc_dwf_dwarfs`) run a whole Iron Court with no UI change: Dwarf parties, offices (tiers 2/4/4/4), governments (the Iron Law's changed rule included), start governments, laws, deeds, origins, backgrounds, party names and traits, rebels, envoy tasks, move and favour names, event wording, every bundle, trait and loc row with its verified effects, and the "Dwarf courts" MCT switch, live. A Chaos Dwarf court is unchanged in every key, row and number.

**Architecture:** The Dwarf race is one new Lua file, `zzz_derpy_iron_court_dwarf.lua`, that fills a `DWF` table in the contract's race shape and registers it with `IC.register_race`; its slugs are the Chaos Dwarf slots, so only words and effects change, and every key carries the `dwf_` infix through `IC.key`. The model gains small race-aware accessors where a Chaos Dwarf constant is read directly today (store lords, rebel lord, personality, doctrine name, envoy tasks, event wording, move and favour text). The generator gains the Dwarf effect constants (each pair read from db.pack), `RACES["dwf"]`, `emit_dwf` and `check_dwf`; the importer and deploy script learn the new file.

**Tech Stack:** Lua 5.1, Python 3 (py), RPFM MCP

**Spec:** docs/superpowers/specs/2026-10-04-iron-court-dwarfs-design.md (and the CONTRACT file docs/superpowers/plans/2026-10-04-iron-court-dwarfs-CONTRACT.md)

## Global Constraints

- Carried from phase 1's final review (2026-10-04), see the CONTRACT's "Phase 1 final review"
  amendment: `LUA_OF_PREFIX["DWF"] = "zzz_derpy_iron_court_dwarf.lua"` must be set beside
  `RACES["dwf"]` (phase 1's
  `race_lua(prefix)` reads it); `check_governments("dwf")` / `check_laws("dwf")` then work as
  written. `R.PARTY_TROOPS` / `R.TROOPS_DEFAULT` are race fields now: the Dwarf race supplies its
  own unit keys, verified against db.pack. Standing, ambition and the government base bundle
  already take the infix in phase 1. THE PANEL'S PLAYER TEXT is still the Chaos Dwarfs':
  `ICUI.DEED_TEXT` (Hashut / Hell-Forge / slaves) and `ICUI.HELP` (two lines say "Chaos
  Dwarf") - this phase gives the Dwarf race its own deed and help text, read through the
  player's race, and the race scan covers the new names.
- Phase 1 is done exactly as the CONTRACT describes: `IC.RACES`, `IC.RACE_ORDER = {"chd"}`, `IC.register_race`, `IC.build_race`, `IC.race_of`, `IC.race_key`, `IC.R` (cached in `IC._race_cache`), `IC.has_court`, `IC.is_chd`, `IC.runs_court`, `IC.tune`, `IC.key(kind, slug, faction_key)`, and in Python `RACES`, `tier_seats(race)`, `bundle_key(kind, slug, race="chd")`. Line numbers below are today's (before phase 1); find each site by the quoted text.
- Not a git repo. Every "Checkpoint" runs THE GATES, from the workspace root `G:\Modding for resources`:
  ```powershell
  & "C:\Program Files (x86)\Lua\5.1\luac.exe" -p "Modding Files\pack\script\campaign\mod\zzz_derpy_iron_court.lua" "Modding Files\pack\script\campaign\mod\zzz_derpy_iron_court_dwarf.lua" "Modding Files\pack\script\campaign\mod\zzz_derpy_iron_court_parties.lua" "Modding Files\pack\script\campaign\mod\zzz_derpy_iron_court_ui.lua" "Modding Files\pack\script\campaign\mod\zzz_derpy_iron_court_ui_map.lua"
  $env:IC_TEST_ALL = 1; & "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua; Remove-Item Env:IC_TEST_ALL
  py tools\check_lua_api.py
  py tools\check_lua_literal_left.py
  py tools\check_lua_undeclared.py
  py tools\gen_ic_ui.py --check
  py tools\gen_ic_ui.py --selftest
  py tools\gen_iron_court.py --check
  ```
  Expected: luac silent; the harness prints `iron court harness: ok (N checks)` with no `FAIL` line; every tool exits 0. `check_lua_undeclared.py` with no argument scans every `script/campaign/mod/*.lua` together, the Dwarf file included.
- Running only this phase's checks: `$env:IC_ONLY = "dwarfs:"; & "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua; Remove-Item Env:IC_ONLY`. Every check this plan adds is named `dwarfs: ...`.
- The harness block this plan adds is ONE `do ... end` (the main chunk is near Lua's 200-local limit), inserted immediately above `-- THE PREVIEW'S DEMO (plan 2026-10-02 laws, Task 10)`. Task 1 creates it; later tasks insert their checks directly above its closing line `end -- DWARF CONTENT (plan 2026-10-04 phase 2)`.
- Every new check is watched failing for its own reason before the code that passes it is written.
- Lua 5.1 with the game's miscompile: no number literal on the LEFT of an arithmetic operator in shipped Lua. No `string.find` plain flag in shipped Lua. A model function never calls loc (turn-1 CTD); the Dwarf file holds plain English only.
- Every `DWF.X = {` table in `zzz_derpy_iron_court_dwarf.lua` closes with a column-0 `}` (the scrapers read `DWF\.X = \{(.*?)\n\}`).
- Every key (faction, unit, subtype, effect, scope, icon, building, edict, personality) was read out of `db.pack` / the vanilla cache on 2026-10-04 with `tools/read_vanilla_db.py`, `tools/read_vanilla_loc.py` and `gen_iron_court._cache_table`; `check()` and `check_dwf()` re-read every one at build time. A key that did not verify was dropped (Ruling 5), never guessed.
- Player text: no emojis, never "rung", "standing", "cap", "AI" or "HUD"; no Chaos Dwarf word (Hashut, Zharr, Hell-Forge, slave, Labourer, Hobgoblin, convoy, ziggurat, daemon) and no "Guild" in any Dwarf string.
- Edit `.lua`/`.py` with the Edit or Write tool only (Git Bash `sed -i` strips CRLF; heredocs eat backslashes). Never edit a `.pack`, `.loc` or DB binary as text.
- Build and deploy only with `py tools\deploy_iron_court.py` (needs RPFM open; backs up to `Modding Files/Backup/`, never into data/ or Workshop folders; deploys to data/ only when Warhammer3.exe is not running; `--wait` otherwise).

## Rulings against the spec

1. **Governments and laws keep the Chaos Dwarf slot slugs** (`conclave priest forge legion chain convoy`; `labour tribute worship war` with their option slugs). Only names, rules, effects and icons change; keys differ by the infix (`derpy_ic_doctrine_dwf_chain`, `derpy_ic_law_dwf_labour_lash`). Phases 4 and 6 already address `DWF.GOVS.chain` and Karak Kadrin's `"legion"`, and the model's `"conclave"` default needs no change. The Dwarf laws keep each slot's pro and con parties exactly (spec section 7's table is the slot table).
2. **The Iron Law here is the discount only**: Swear on the Ancestors, Stand His Patron and Oath on the Anvil cost a third less (`{mul = 0.67}`). The broken-oath loyalty (`oath_broken_loyalty`, its two sites and the rule text's second sentence) is phase 4's Task 3, which replaces this `over` and this rule string.
3. **No temple deed.** `db.pack` has no Dwarf temple chain: the Dwarf chains are `wh_main_DWARFS_*`, and the nearest rows (`wh_main_dwf_slayer_1/2` Slayer Shrine / Monument of Grimnir, `wh_main_dwf_barracks_4` Hall of Oaths, `wh_dlc06_dwf_eight_peaks_3` Ancestor Tombs, `wh3_main_underdeep_dwf_grudges_1/2/3` Hall of Remembering) are not temples. `DWF.TEMPLE_BUILDINGS = {}`; `DWF.DEEDS` holds battle and research. The grudge deed is phase 5's.
4. **The rebel pool is `wh_main_dwf_dwarfs_qb2`-`qb4` only.** The four `wh_main_dwf_dwarfs_seperatists_qb1`-`qb4` permit one general subtype, `wh3_dlc25_dwf_daemon_slayer_spawned_army` (a Slayer and CA's scripted spawn), so a rising there has no lord the court may field. `qb1`, `wh3_dlc26_dwf_dwarfs_invasion` and `wh_main_dwf_dwarf_rebels` are excluded per the spec.
5. **Dropped, failed verification** (no vanilla bundle, building or technology ships the pair a faction bundle needs): `wh3_dlc25_effect_recruitment_cost_dwf_war_machines_all`, `wh3_dlc25_effect_force_stat_missile_strength_dwf_artillery_flying_war_machines` (character scope only), `wh3_dlc25_effect_force_stat_range_dwf_thunderers_irondrakes`, `wh3_dlc25_effect_force_stat_range_dwf_arty_warmachines`, `wh3_dlc25_effect_force_recruit_rank_dwf_dwarf_melee_infantry`, `wh3_dlc25_effect_force_stat_leadership_dwf_melee_infantry`, `wh3_dlc24_effect_tech_xp_gain_increase_chaos_dwarfs`, `wh3_dlc25_effect_upkeep_dwf_melee_infantry` / `_ranged_infantry`, `wh3_dlc25_effect_building_construction_cost_mod_dwf_industry`, and any Dwarf faction-scope corruption effect. The Chaos Dwarf `E_RAID` (raiding) is not used for Dwarfs (unverified for their stances). `wh_main_faction_political_diplomacy_mod_dwarfs` verified but is unused.
6. **Office effects where the spec leaves a choice:** the Overseer of the Mines carries mining income alone and the Master of the Stonecutters carries construction cost; the Brewmaster carries culture income (CA's own brewmaster ancillary is a culture-income one); the Keeper of the Lore carries research; the Keeper of the Clan Banners carries Grudge Settler recruitment cost; growth is set in growth points (5 / 3 / 8), not copied from a percentage.
7. **Rebel generals are `wh_main_dwf_lord` and `wh_dlc06_dwf_runelord`; heroes are the Thane, Master Engineer and Runesmith.** Excluded with named reasons in `DWF_REBEL_GEN_EXCLUDED` / `DWF_REBEL_HERO_EXCLUDED`: Thorgrim and Belegar (legends), the two Daemon Slayers and the Dragon Slayer (a Slayer has forsworn his hold), and the Lord on the colonel and minister agent types (a lord's subtype).
8. **No `LORD_HISTORY` for Dwarf legends**: a Dwarf legendary lord takes his faction's origin through the existing fallback.
9. **Pictures stay Chaos Dwarf in this phase**: event images (`chd/...`) and party sigils are phase 3's art pass. Dwarf trait categories reuse this pack's own categories.
10. **`IC.dismantle` also takes the government and law bundles off** (both races): a player court switched off by "Dwarf courts" wore both and nothing else removes them.
11. **Party drawn, move results and the two reworded events are loc-only**: the event records and indices are shared; a Dwarf court passes Dwarf loc keys (`IC.event_stem`, `IC.party_drawn_key`, `IC.move_result_key(..., faction_key)`).

## Contract additions (consumed by the phase named)

- Race table fields: `switch` (this phase), `ENVOY_TASKS` (phase 3), `STORE_LORDS`, `REBEL_LORD`, `REBEL_PERSONALITY`, `MILITARY_DOCTRINE_NAME`, `PLOT_TEXT` (phases 3, 4), `FAVOUR_TEXT` (phase 3), `EVENT_LOC` (phase 5 adds its grudge text).
- Lua: `IC.store_lords(fk)`, `IC.rebel_lord(fk)`, `IC.rebel_personality(fk)`, `IC.doctrine_name(fk)`, `IC.rebel_draw(count, faction_key)`, `IC.rebel_force(..., kit, court_key)`, `IC.envoy_tasks(fk)`, `IC.envoy_task(code, faction_key)`, `IC.envoy_split(target, faction_key)` (phase 3 passes the player at its four UI sites), `IC.plot_text(plot_key, fk) -> name, blurb, effect, effect_no_secession` and `IC.favour_text(key, fk) -> name, blurb` (phase 3 draws them), `IC.event_stem(slug, fk)`, `IC.raise_feed_located(fk, slug, x, y, about)`, `IC.party_drawn_key(fk, party)`, `IC.move_result_key(plot_key, ok, faction_key)`.
- TUNE: `dwarf_courts` (contract), `envoy_oath = 20`, `envoy_grow = 5`, `envoy_rec = 15` (not MCT settings, not in `IC.TUNE_ORDER`).
- Python: `RACES["dwf"]` extra keys `NOT_AN_ORIGIN, ORIGIN_COLOUR, PARTY_GOV_BLURB, BG_COLOUR, CONTROL_BANDS, GOVERNOR_BASE, ENVOY_EFFECT, ENVOY_BLURB, TIER_NAME, STANDING_BAND, PARTY_DRAWN, EVENT_TEXT, BUNDLE_ICON`; `DWF_LUA`, `_dwf_block`, `_dwf_list`, the `dwf_*` scrapers, `emit_dwf`, `DWF_ROWS`, `check_race_effects`, `check_dwf`; `import_iron_court.DWARF_LUA`.

## Review Focus

1. **A Chaos Dwarf court is untouched**: every Chaos Dwarf row `build()` makes is identical to the snapshot taken before this phase (Task 5 Step 1, compared in Task 6 Step 5); every Chaos Dwarf key builder answers what it did; the harness's existing checks stay green.
2. **A Dwarf court never wears a Chaos Dwarf key, and every key it wears ships**: two turns of a Dwarf player court, every `derpy_ic_` bundle and trait read back against the generated TSVs. Pinned in Task 7.
3. **The Iron Law bends only Dwarf courts**: the Slave-Lords' discount stays Chaos Dwarf, the oath discount stays Dwarf, the other five keep their slot's rule. Pinned in Task 1.
4. **"Dwarf courts" off takes a Dwarf court off the map whole** (offices, vacancies, control, government, laws, the save) and leaves a Chaos Dwarf court running. Pinned in Task 4.
5. **A Dwarf rising is all Dwarf**: lord, units, heroes and personality, and a Chaos Dwarf rising never draws a Dwarf unit. Pinned in Task 2.

---

### Task 1: The Dwarf race table

**Files:**
- Create: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_dwarf.lua`
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court.lua` - `IC.gov_row` (today 911-915) and `IC.start_gov` (today 6033-6034), only where phase 1 left them reading `IC.GOVS` / `IC.START_GOV`
- Test: `tools/_iron_court_harness.lua` - the Dwarf file load (after the model chunk), and the new block

**Interfaces:**
- Consumes: CONTRACT `IC.register_race`, `IC.RACE_ORDER`, `IC.R`, `IC.race_key`, `IC.key`, `IC.law_opt(cat, opt, faction_key)`, `IC.law_in_force`, `IC.tune`, `IC.start_gov`, `IC.party_name`, `IC.roll_court`, `IC.court_rolled`.
- Produces: race `IC.RACES.dwf` (`DWF`), `IC.RACE_ORDER = {"chd", "dwf"}`; the race fields `key subculture infix switch layout ORIGINS PARTIES OFFICES BACKGROUNDS NAME_HEADS NAME_TAILS PARTY_TRAITS LEADER_TRAITS GOV_ORDER GOVS START_GOV LAW_ORDER LAWS DEEDS REBEL_POOL REBEL_GENERALS REBEL_POOLS REBEL_DRAFT REBEL_HEROES REBEL_LORD REBEL_PERSONALITY STORE_LORDS LEGEND_SUBTYPES TEMPLE_BUILDINGS MILITARY_DOCTRINE MILITARY_DOCTRINE_NAME PLOT_KEYS tune grid art`; `IC.gov_row(faction_key)` reading the court's race's `GOVS`.

- [ ] **Step 1: Load the Dwarf file in the harness.** In `tools/_iron_court_harness.lua`, directly after the line `IC.governments_on = function() return IC_GOVS_ON == true end` (and before `local PARTIES_FILE =`), add:

```lua

-- THE DWARF RACE (plan 2026-10-04 phase 2): after the model and before the
-- parties, the order the game loads them in ("." < "_" and "d" < "p").
do
    local path = os.getenv("IC_DWARF_FILE")
        or "Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_dwarf.lua"
    local dwarf_chunk, dwarf_err = loadfile(path)
    assert(dwarf_chunk, "could not load " .. path .. ": " .. tostring(dwarf_err))
    dwarf_chunk()
    assert(IC.RACES and IC.RACES.dwf, "the Dwarf file must register race dwf")
end
```

- [ ] **Step 2: Write the failing checks.** Immediately above the line `-- THE PREVIEW'S DEMO (plan 2026-10-02 laws, Task 10): with IC_DUMP set, draw`, add the block:

```lua
-- THE DWARF CONTENT (plan 2026-10-04 phase 2). ONE block, so the main chunk's
-- local count does not move. D is Karak Kadrin (Ungrim), the spec's demo court.
do
    local D = "wh_main_dwf_karak_kadrin"
    local DWF_SUB = "wh_main_sc_dwf_dwarfs"
    local RF = {chd = F, dwf = D}
    local SUB = {chd = IC.CHD_SUBCULTURE, dwf = DWF_SUB}
    local function fresh()
        IC._race_cache = {}
        IC.state = {}
        factions = {}
        applied = {}
    end
    -- PLAYER TEXT ONLY: a string with a capital or a space. A slot slug the two
    -- races share ("convoy", "hellforge") is a key and is never drawn.
    local BANNED = {"hashut", "zharr", "hell%-?forge", "slave", "labourer", "hobgoblin",
                    "convoy", "ziggurat", "daemon", "chaos dwarf", "guild"}
    local function player_strings(t, path, out, seen)
        if seen[t] then return out end
        seen[t] = true
        for k, v in pairs(t) do
            local here = path .. "." .. tostring(k)
            if type(v) == "table" then
                player_strings(v, here, out, seen)
            elseif type(v) == "string" and (string.find(v, "%u") or string.find(v, " ")) then
                out[#out + 1] = {here, v}
            end
        end
        return out
    end

    check("dwarfs: the race is registered second and answers for a Dwarf faction", function()
        fresh()
        assert(#IC.RACE_ORDER == 2 and IC.RACE_ORDER[1] == "chd" and IC.RACE_ORDER[2] == "dwf",
            "the race order is " .. table.concat(IC.RACE_ORDER, ","))
        local R = IC.RACES.dwf
        assert(R.key == "dwf" and R.subculture == DWF_SUB and R.infix == "dwf_",
            "the Dwarf race's identity is wrong")
        make_faction(D, DWF_SUB, {}, {})
        make_faction(F, IC.CHD_SUBCULTURE, {}, {})
        assert(IC.race_key(D) == "dwf", "Karak Kadrin is race " .. tostring(IC.race_key(D)))
        assert(IC.R(D) == R, "IC.R does not answer the Dwarf race for Karak Kadrin")
        assert(IC.key("office", "priest", D) == "derpy_ic_office_dwf_priest",
            "a Dwarf key is " .. IC.key("office", "priest", D))
        assert(IC.key("office", "priest", F) == "derpy_ic_office_priest",
            "a Chaos Dwarf key moved: " .. IC.key("office", "priest", F))
    end)

    check("dwarfs: tiers are 2/4/4/4 and each office sits in its Great Hall cell", function()
        local R = IC.RACES.dwf
        local want = {
            {"priest", "temple", 1, {1, 0}}, {"forge", "forge", 1, {3, 0}},
            {"ledger", "ledger", 2, {0, 0}}, {"warden", "legion", 2, {4, 0}},
            {"hand", "tower", 2, {1, 1}}, {"roads", "road", 2, {3, 1}},
            {"chains", "chain", 3, {0, 1}}, {"pits", "chain", 3, {4, 1}},
            {"quarry", "forge", 3, {1, 2}}, {"muster", "legion", 3, {3, 2}},
            {"kilns", "hearth", 4, {0, 2}}, {"fields", "hearth", 4, {4, 2}},
            {"scribes", "tower", 4, {1, 3}}, {"banners", "legion", 4, {3, 3}},
        }
        assert(#R.OFFICES == #want, #R.OFFICES .. " Dwarf offices")
        for i, w in ipairs(want) do
            local o = R.OFFICES[i]
            assert(o.slug == w[1] and o.affinity == w[2] and o.tier == w[3],
                "office " .. i .. " is " .. o.slug .. "/" .. o.affinity .. "/" .. o.tier)
            local c = R.grid.cells[i]
            assert(c[1] == w[4][1] and c[2] == w[4][2], o.slug .. " sits at " .. c[1] .. "," .. c[2])
        end
        assert(R.grid.cols == 5 and R.grid.rows == 4 and R.grid.throne[1] == 2
               and R.grid.throne[2] == 0, "the Great Hall is not 5x4 with the throne at 2,0")
        local seats = {2, 4, 4, 4}
        for t = 1, 4 do
            assert(R.TIER_SEATS[t] == seats[t], "tier " .. t .. " has " .. tostring(R.TIER_SEATS[t]))
        end
        local factions_n = 0
        for _, o in ipairs(R.ORIGINS) do if o.faction then factions_n = factions_n + 1 end end
        assert(factions_n == 14 and #R.ORIGINS == 18, factions_n .. " faction origins of " .. #R.ORIGINS)
        assert(R.MAX_SEATS == #R.PARTIES + factions_n, "MAX_SEATS is " .. tostring(R.MAX_SEATS))
        for _, p in ipairs(R.PARTIES) do
            for _, bg in ipairs(R.BACKGROUNDS[p]) do
                assert(R.PARTY_OF_BG[bg] == p, bg .. " does not seat its man in " .. p)
            end
        end
    end)

    check("dwarfs: a Dwarf party's name rolls from the Dwarf words and fits", function()
        local R = IC.RACES.dwf
        local heads = {}
        for _, h in ipairs(R.NAME_HEADS) do
            heads[h] = true
            for w in string.gmatch(string.lower(h), "%a+") do
                for party, tails in pairs(R.NAME_TAILS) do
                    for _, tail in ipairs(tails) do
                        for tw in string.gmatch(string.lower(tail), "%a+") do
                            assert(tw ~= w, "the head " .. h .. " repeats a word of " .. party .. "'s " .. tail)
                        end
                    end
                end
            end
        end
        for party, tails in pairs(R.NAME_TAILS) do
            for _, tail in ipairs(tails) do
                assert(#tail <= 18, party .. "'s tail " .. tail .. " is " .. #tail .. " characters")
                for _, h in ipairs(R.NAME_HEADS) do
                    assert(#h + 4 + #tail <= 30, h .. " of " .. tail .. " is over 30 characters")
                end
            end
        end
        for _ = 1, 8 do
            fresh()
            make_faction(D, DWF_SUB, {}, {})
            IC.roll_court(D)
            assert(IC.court_rolled(D), "the Dwarf court did not roll")
            for slug, house in pairs(IC.court(D).houses) do
                if slug ~= "crown" and not house.confed then
                    local name = IC.party_name(D, slug)
                    local head, tail = string.match(tostring(name), "^(.-) of (.+)$")
                    assert(head and heads[head], slug .. " is named " .. tostring(name))
                    local known = false
                    for _, t in ipairs(R.NAME_TAILS[slug]) do if t == tail then known = true end end
                    assert(known, slug .. "'s tail " .. tostring(tail) .. " is not a Dwarf tail")
                end
            end
        end
    end)

    check("dwarfs: governments keep their slot's rule but the Iron Law's, per court", function()
        fresh()
        IC_GOVS_ON = true
        make_faction(D, DWF_SUB, {}, {})
        make_faction(F, IC.CHD_SUBCULTURE, {}, {})
        local R = IC.RACES.dwf
        local function same(a, b)
            if type(a) ~= "table" or type(b) ~= "table" then return a == b end
            for k, v in pairs(a) do if not same(v, b[k]) then return false end end
            for k in pairs(b) do if a[k] == nil then return false end end
            return true
        end
        assert(same(R.GOV_ORDER, IC.GOV_ORDER), "the Dwarf governments are not the six slots")
        for _, g in ipairs(IC.GOV_ORDER) do
            assert(same(R.GOVS[g].parties, IC.GOVS[g].parties), g .. " is backed by other parties")
            if g ~= "chain" then
                assert(same(R.GOVS[g].over, IC.GOVS[g].over), g .. " does not keep its slot's rule")
            end
        end
        IC.court(D).gov = "chain"
        IC.court(F).gov = "chain"
        for _, key in ipairs({"plot_oath_cost", "plot_pledge_cost", "plot_patron_cost"}) do
            local third = math.floor(IC.TUNE[key] * 0.67 + 0.5)
            assert(IC.tune(D, key) == third, key .. " costs " .. tostring(IC.tune(D, key))
                .. " under the Iron Law, not " .. third)
            assert(IC.tune(F, key) == IC.TUNE[key], key .. " moved under the Slave-Lords")
        end
        assert(IC.tune(D, "plot_murder_cost") == IC.TUNE.plot_murder_cost,
            "the Iron Law kept the Slave-Lords' murder discount")
        assert(IC.tune(F, "plot_murder_cost") == math.floor(IC.TUNE.plot_murder_cost * 0.65 + 0.5),
            "the Slave-Lords lost their murder discount")
        IC_GOVS_ON = nil
    end)

    check("dwarfs: each Dwarf faction starts on its own government", function()
        local want = {
            wh_main_dwf_dwarfs = "priest", wh_main_dwf_karak_kadrin = "legion",
            wh_main_dwf_karak_izor = "chain", wh3_main_dwf_the_ancestral_throng = "priest",
            wh2_dlc17_dwf_thorek_ironbrow = "conclave", wh3_dlc25_dwf_malakai = "forge",
            wh_main_dwf_barak_varr = "convoy", wh_main_dwf_zhufbar = "forge",
            wh_main_dwf_kraka_drak = "conclave", wh3_main_dwf_karak_azorn = "conclave",
            wh_main_dwf_karak_norn = "conclave", wh_main_dwf_karak_hirn = "conclave",
            wh_main_dwf_karak_azul = "conclave", wh_main_dwf_karak_ziflin = "conclave",
        }
        for fk, g in pairs(want) do
            fresh()
            make_faction(fk, DWF_SUB, {}, {})
            assert(IC.start_gov(fk) == g, fk .. " starts on " .. tostring(IC.start_gov(fk)))
        end
        fresh()
        make_faction(F, IC.CHD_SUBCULTURE, {}, {})
        assert(IC.start_gov(F) == "convoy", "Uzkulak no longer starts on the Convoy Concern")
    end)

    check("dwarfs: Dwarf laws keep each slot's votes and start on their first option", function()
        fresh()
        make_faction(D, DWF_SUB, {}, {})
        local R = IC.RACES.dwf
        for _, cat in ipairs(IC.LAW_ORDER) do
            assert(R.LAWS[cat], "the Dwarfs have no " .. cat .. " category")
            assert(IC.law_in_force(D, cat) == R.LAWS[cat].order[1],
                cat .. " starts on " .. tostring(IC.law_in_force(D, cat)))
            for _, opt in ipairs(IC.LAWS[cat].order) do
                local mine, slot = IC.law_opt(cat, opt, D), IC.LAWS[cat].opts[opt]
                assert(mine == R.LAWS[cat].opts[opt], cat .. "." .. opt .. " is not the Dwarf option")
                assert(table.concat(mine.pro or {}, ",") == table.concat(slot.pro or {}, ",")
                       and table.concat(mine.con or {}, ",") == table.concat(slot.con or {}, ","),
                    cat .. "." .. opt .. " changed its parties")
            end
        end
    end)

    check("dwarfs: no Chaos Dwarf word and no Guild in any Dwarf string", function()
        for _, pair in ipairs(player_strings(IC.RACES.dwf, "dwf", {}, {})) do
            local low = string.lower(pair[2])
            for _, word in ipairs(BANNED) do
                assert(not string.find(low, word), pair[1] .. " says " .. pair[2])
            end
        end
    end)

    check("dwarfs: deeds are battle and research, and a Chaos Dwarf deed moves nothing", function()
        fresh()
        make_faction(D, DWF_SUB, {}, {})
        cm.get_human_factions = function() return {D} end
        IC.add_house(D, "crown")
        assert(IC.deed(D, "hellforge") == 0 and IC.deed(D, "convoy") == 0
               and IC.deed(D, "temple") == 0, "a Chaos Dwarf deed moved a Dwarf court")
        assert(IC.deed(D, "battle") > 0 and IC.renown(D, "legion") > 0,
            "a victory gave the Clan Warriors no renown")
        assert(IC.deed(D, "research") > 0 and IC.renown(D, "tower") > 0,
            "research gave the Runesmiths no renown")
        cm.get_human_factions = function() return {} end
    end)

    -- THE FIXTURE SET, ONCE PER RACE (spec section 10): a player court of each
    -- race rolls and wears its own race's keys.
    for _, rk in ipairs(IC.RACE_ORDER) do
        check("dwarfs: race " .. rk .. ": a player's court rolls whole and wears its race's keys", function()
            local fk = RF[rk]
            fresh()
            saved["derpy_ic_" .. fk] = nil
            cm.get_human_factions = function() return {fk} end
            IC_GOVS_ON = true
            local men = {}
            for i = 1, 4 do men[i] = make_character(9700 + i, ANY_SEAT, nil, nil) end
            local f = make_faction(fk, SUB[rk], men, {"prov_a"})
            IC.register()
            core.listeners["ic_turn"]({faction = function() return f end})
            IC_GOVS_ON = nil
            cm.get_human_factions = function() return {} end
            local R = IC.R(fk)
            assert(R == IC.RACES[rk], fk .. " resolved to race " .. tostring(R and R.key))
            assert(IC.court_rolled(fk), "the " .. rk .. " court did not roll")
            local allowed = {}
            for _, p in ipairs(R.PARTIES) do allowed[p] = true end
            for slug, house in pairs(IC.court(fk).houses) do
                assert(allowed[slug] or house.confed, slug .. " is not a " .. rk .. " party")
            end
            for _, o in ipairs(R.OFFICES) do
                assert(applied[IC.key("office", o.slug, fk)] or applied[IC.key("vacant", o.slug, fk)],
                    "the " .. rk .. " court wears nothing for " .. o.slug)
            end
            assert(applied[IC.key("doctrine", R.START_GOV[fk], fk)],
                "the " .. rk .. " court does not wear its start government " .. R.START_GOV[fk])
            for _, cat in ipairs(R.LAW_ORDER) do
                local key = IC.key("law", cat .. "_" .. R.LAWS[cat].order[1], fk)
                assert(applied[key], "the " .. rk .. " court does not wear " .. key)
            end
            local bands = 0
            for _, b in ipairs(IC.CONTROL) do
                if applied[IC.key("control", b.slug, fk)] then bands = bands + 1 end
            end
            assert(bands == 1, "the " .. rk .. " court wears " .. bands .. " control bands")
        end)
    end
end -- DWARF CONTENT (plan 2026-10-04 phase 2)

```

- [ ] **Step 3: Run to verify they fail**

Run: `& "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua`
Expected: exit 1 at load, `could not load Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_dwarf.lua: cannot open Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_dwarf.lua`.

- [ ] **Step 4: Create the Dwarf file.** Write `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_dwarf.lua` with exactly:

```lua
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
DWF.tune = {}
DWF.art = {}

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
    crown  = {"household", "lineblood", "oathsworn"},
    temple = {"shrinekeeper", "valayan", "tombwarden"},
    forge  = {"smith", "engineer", "foundry"},
    chain  = {"miner", "prospector", "tunneller"},
    legion = {"longbeard", "ironbreaker", "thane"},
    ledger = {"reckoner", "trader", "goldsmith"},
    tower  = {"runesmith", "loremaster", "scribe"},
    road   = {"ranger", "wayfinder", "underwarden"},
    hearth = {"farmer", "brewer", "elder"},
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
                        plot_pledge_cost = {mul = 0.67}}},
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
}

-- REGISTERED LAST, once: IC.build_race derives TIERS, TIER_SEATS, PARTY_OF_BG
-- and MAX_SEATS from the tables above, and register_race appends "dwf" to
-- IC.RACE_ORDER itself (phase 1) - never append it by hand.
IC.register_race(DWF)
```

- [ ] **Step 5: Make the government read the court's race.** Run `Select-String -Path "Modding Files\pack\script\campaign\mod\zzz_derpy_iron_court.lua" -Pattern "IC.GOVS\[court.gov","IC.START_GOV\[faction_key\]"`. For each hit (phase 1 may already have replaced both; then there is nothing to do):
  - in `IC.gov_row`, replace `return court and IC.GOVS[court.gov or ""] or nil` with `return court and IC.R(faction_key).GOVS[court.gov or ""] or nil`;
  - in `IC.start_gov`, replace `if IC.START_GOV[faction_key] then return IC.START_GOV[faction_key] end` with:

```lua
    local own = IC.R(faction_key).START_GOV[faction_key]
    if own then return own end
```

- [ ] **Step 6: Run to verify they pass**

Run: `$env:IC_ONLY = "dwarfs:"; & "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua; Remove-Item Env:IC_ONLY`
Expected: `iron court harness: ok (10 checks)`. A `FAIL dwarfs: race dwf: ...` naming a Chaos Dwarf key means a phase 1 key builder ignores the race: STOP and report it (phase 1 is not done). A phase 1 check that pins `IC.RACE_ORDER` to `{"chd"}` alone fails in the full run by design: change its expected list to `{"chd", "dwf"}`.

- [ ] **Step 7: Checkpoint.** Run THE GATES. Expected: all green; the harness count is phase 1's plus 10.

---

### Task 2: Rebels, store lords and the doctrine name read the race

**Files:**
- Modify: `zzz_derpy_iron_court.lua` - after `IC.STORE_LORDS = {...}` (today 2624-2630); `IC.ensure_leaders` (today 2713) and `IC.field_leader` (today 2760); `IC.loyalty_terms` doctrine (today 4146-4163); `IC.rebel_general` (today 4401-4415); `IC.rebel_kit` (today 4454); `IC.rebel_draw` (today 4462-4492); `IC.rebel_force` (today 4647-4656) and its caller (today 4763-4764); the personality call (today 4854)
- Test: harness block

**Interfaces:**
- Consumes: `DWF.REBEL_LORD`, `REBEL_PERSONALITY`, `REBEL_POOLS`, `REBEL_DRAFT`, `REBEL_GENERALS`, `STORE_LORDS`, `MILITARY_DOCTRINE`, `MILITARY_DOCTRINE_NAME` (Task 1).
- Produces: `IC.store_lords(fk) -> list`, `IC.rebel_lord(fk) -> subtype`, `IC.rebel_personality(fk) -> key`, `IC.doctrine_name(fk) -> string`, `IC.rebel_draw(count, faction_key) -> {unit keys}`, `IC.rebel_force(rebels, region_key, x, y, general, crown, kit, court_key)`.

- [ ] **Step 1: Write the failing checks** (above `end -- DWARF CONTENT (plan 2026-10-04 phase 2)`):

```lua
    check("dwarfs: a Dwarf rising is a Dwarf army under a Dwarf lord with a Dwarf mind", function()
        fresh()
        make_faction(D, DWF_SUB, {}, {})
        make_faction(F, IC.CHD_SUBCULTURE, {}, {})
        local R = IC.RACES.dwf
        assert(IC.rebel_general(D, nil).subtype == "wh_main_dwf_lord",
            "a Dwarf rising is led by " .. IC.rebel_general(D, nil).subtype)
        assert(IC.rebel_general(F, nil).subtype == IC.REBEL_LORD, "the Chaos Dwarf rebel lord moved")
        assert(IC.rebel_lord(D) == R.REBEL_LORD and IC.rebel_lord(F) == IC.REBEL_LORD,
            "IC.rebel_lord does not answer per race")
        assert(IC.rebel_personality(D) == "wh3_combi_dwarf_endgame"
               and IC.rebel_personality(F) == IC.REBEL_PERSONALITY,
            "the rising's personality does not follow the race")
        local ours = {}
        for _, pool in pairs(R.REBEL_POOLS) do
            for _, u in ipairs(pool) do ours[u[1]] = true end
        end
        local drawn = IC.rebel_draw(IC.TUNE.rebel_units, D)
        assert(#drawn == IC.TUNE.rebel_units, "a Dwarf draft drew " .. #drawn .. " units")
        for _, u in ipairs(drawn) do assert(ours[u], "a Dwarf rising drew " .. u) end
        for _, u in ipairs(IC.rebel_draw(IC.TUNE.rebel_units)) do
            assert(not ours[u], "a Chaos Dwarf rising drew the Dwarf unit " .. u)
        end
        for _, u in ipairs(IC.rebel_kit(D, nil)) do
            assert(ours[u], "a Dwarf rising's kit was topped up with " .. u)
        end
    end)

    check("dwarfs: a Dwarf party's new lord is a Dwarf lord, and its doctrine says its own name", function()
        fresh()
        make_faction(D, DWF_SUB, {}, {})
        make_faction(F, IC.CHD_SUBCULTURE, {}, {})
        local lords = IC.store_lords(D)
        assert(#lords == 2 and lords[1] == "wh_main_dwf_lord" and lords[2] == "wh_dlc06_dwf_runelord",
            "a leaderless Dwarf party is given " .. table.concat(lords, ","))
        assert(IC.store_lords(F) == IC.STORE_LORDS, "the Chaos Dwarf store lords moved")
        assert(IC.doctrine_name(D) == "Masters of Steel and Stone",
            "the Dwarf doctrine line reads " .. IC.doctrine_name(D))
        assert(IC.doctrine_name(F) == "Military Doctrine", "the Chaos Dwarf doctrine line moved")
    end)
```

- [ ] **Step 2: Run to verify they fail**

Run: `$env:IC_ONLY = "dwarfs:"; & "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua; Remove-Item Env:IC_ONLY`
Expected: exit 1, `FAIL dwarfs: a Dwarf rising is a Dwarf army under a Dwarf lord with a Dwarf mind: ... a Dwarf rising is led by wh3_dlc23_chd_overseer`.

- [ ] **Step 3: Implement the accessors.** In `zzz_derpy_iron_court.lua`, directly after the `IC.STORE_LORDS = {...}` block's closing `}`, add:

```lua

-- THE RACE'S OWN WHERE IT HAS ONE (plan 2026-10-04 phase 2). The Chaos Dwarf
-- constants stay where they are and answer for a race that names none, and for
-- a caller with no faction in hand.
local function race_or_chd(faction_key)
    return faction_key and IC.R(faction_key) or IC.RACES.chd
end

function IC.store_lords(faction_key)
    return race_or_chd(faction_key).STORE_LORDS or IC.STORE_LORDS
end

function IC.rebel_lord(faction_key)
    return race_or_chd(faction_key).REBEL_LORD or IC.REBEL_LORD
end

function IC.rebel_personality(faction_key)
    return race_or_chd(faction_key).REBEL_PERSONALITY or IC.REBEL_PERSONALITY
end

function IC.doctrine_name(faction_key)
    return race_or_chd(faction_key).MILITARY_DOCTRINE_NAME or "Military Doctrine"
end
```

(If the main chunk of the model is at Lua's 200-local limit, `luac -p` says `too many local variables`; then write `IC.race_or_chd = function(faction_key) ... end` instead of the local and call `IC.race_or_chd` in the four bodies and in Step 5.)

- [ ] **Step 4: Switch the sites.**
  - In `IC.ensure_leaders` and in `IC.field_leader`, replace each `local subtype = IC.STORE_LORDS[cm:random_number(#IC.STORE_LORDS, 1)]` with:

```lua
    local lords = IC.store_lords(faction_key)
    local subtype = lords[cm:random_number(#lords, 1)]
```
  (keep each site's own indentation).
  - In `IC.loyalty_terms`, replace `== IC.MILITARY_DOCTRINE then` with `== IC.R(faction_key).MILITARY_DOCTRINE then` unless phase 1 already reads the race there, and replace

```lua
            label = doctrine == 1 and "Military Doctrine"
                    or string.format("Military Doctrine in %d provinces", doctrine),
```
  with
```lua
            label = doctrine == 1 and IC.doctrine_name(faction_key)
                    or string.format("%s in %d provinces", IC.doctrine_name(faction_key), doctrine),
```
  - In `IC.rebel_general`, replace `local out = {subtype = IC.REBEL_LORD, forename = "", surname = ""}` with `local out = {subtype = IC.rebel_lord(faction_key), forename = "", surname = ""}`, and, if the line reads `if key and key ~= "" and IC.REBEL_GENERALS[key] then`, replace it with `if key and key ~= "" and IC.R(faction_key).REBEL_GENERALS[key] then`.
  - In `IC.rebel_kit`, replace `local extra = IC.rebel_draw(want - #kit)` with `local extra = IC.rebel_draw(want - #kit, faction_key)`.

- [ ] **Step 5: The draft and the force.** Replace the head of `IC.rebel_draw` from `function IC.rebel_draw(count)` through `local pool = IC.REBEL_POOLS[role] or {}` with:

```lua
function IC.rebel_draw(count, faction_key)
    local R = race_or_chd(faction_key)
    local out, used = {}, {}
    for i = 1, math.max(0, count or 0) do
        local role = R.REBEL_DRAFT[(i - 1) % #R.REBEL_DRAFT + 1]
        local pool = R.REBEL_POOLS[role] or {}
```

(the rest of the function is unchanged). In `IC.rebel_force`, replace the signature and its first lines

```lua
function IC.rebel_force(rebels, region_key, x, y, general, crown, kit)
    if not rebels or not region_key then return false end
    general = general or {subtype = IC.REBEL_LORD, forename = "", surname = ""}
```
with
```lua
function IC.rebel_force(rebels, region_key, x, y, general, crown, kit, court_key)
    if not rebels or not region_key then return false end
    -- THE COURT IT LEFT DECIDES THE RACE (plan 2026-10-04 phase 2); a dormant
    -- faction's own interface is not asked.
    general = general or {subtype = IC.rebel_lord(court_key or rebels), forename = "", surname = ""}
```
and in its body replace `units = IC.rebel_draw(IC.TUNE.rebel_units)` with `units = IC.rebel_draw(IC.TUNE.rebel_units, court_key or rebels)`. At its caller in the secession steps, replace

```lua
                IC.rebel_force(rebels, rise.region, rise.x, rise.y,
                               rise.general, crown, rise.kit)
```
with
```lua
                IC.rebel_force(rebels, rise.region, rise.x, rise.y,
                               rise.general, crown, rise.kit, faction_key)
```
and replace `cm:force_change_cai_faction_personality(rebels, IC.REBEL_PERSONALITY)` with `cm:force_change_cai_faction_personality(rebels, IC.rebel_personality(faction_key))`.

- [ ] **Step 6: Run to verify they pass**

Run: `$env:IC_ONLY = "dwarfs:"; & "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua; Remove-Item Env:IC_ONLY`
Expected: `iron court harness: ok (12 checks)`.

- [ ] **Step 7: Checkpoint.** Run THE GATES. Expected: all green.

---

### Task 3: Moves, favours, envoys and the feed in Dwarf words

**Files:**
- Modify: `zzz_derpy_iron_court_dwarf.lua` - four tables before `-- REGISTERED LAST`
- Modify: `zzz_derpy_iron_court.lua` - `IC.TUNE` (after `envoy_lab`, today 561); `IC.raise_feed` (today 1353-1368); `IC.move_result_key` (today 1371-1375) and its two callers (today 5849, 5977); `IC.deed_join` (today 2585-2586); after `IC.favour_by_key` (today 5415-5420); `IC.envoy_task` / `IC.envoy_split` (today 5531-5547) and their callers `IC.may_send_envoy` (today 5567) and the envoy branch of `IC.plot` (today 5958); `IC.raise_feed_located` (today 6639-6650) and its caller (today 4739-4740)
- Test: harness block

**Interfaces:**
- Consumes: Task 1's race, `IC.plot_by_key`, `IC.favour_by_key`, `IC.EVENTS`.
- Produces: `DWF.ENVOY_TASKS`, `DWF.PLOT_TEXT`, `DWF.FAVOUR_TEXT`, `DWF.EVENT_LOC`; TUNE `envoy_oath = 20`, `envoy_grow = 5`, `envoy_rec = 15`; `IC.plot_text(plot_key, fk) -> name, blurb, effect, effect_no_secession`, `IC.favour_text(key, fk) -> name, blurb`, `IC.envoy_tasks(fk)`, `IC.envoy_task(code, faction_key)`, `IC.envoy_split(target, faction_key)`, `IC.event_stem(slug, fk)`, `IC.raise_feed_located(fk, slug, x, y, about)`, `IC.party_drawn_key(fk, party)`, `IC.move_result_key(plot_key, ok, faction_key)`. Phase 3 consumes `plot_text`, `favour_text`, `envoy_tasks` and the two-argument `envoy_split`.

- [ ] **Step 1: Write the failing checks** (above `end -- DWARF CONTENT (plan 2026-10-04 phase 2)`):

```lua
    check("dwarfs: every move and favour has its Dwarf name, and a Chaos Dwarf court keeps its own", function()
        fresh()
        make_faction(D, DWF_SUB, {}, {})
        make_faction(F, IC.CHD_SUBCULTURE, {}, {})
        local R = IC.RACES.dwf
        local listed = {}
        for _, key in ipairs(R.PLOT_KEYS) do
            listed[key] = true
            assert(IC.plot_by_key(key), "PLOT_KEYS names " .. key .. ", which IC.PLOTS has not")
            local name, blurb, effect = IC.plot_text(key, D)
            assert(R.PLOT_TEXT[key] and name == R.PLOT_TEXT[key].name, key .. " has no Dwarf name")
            assert(blurb and blurb ~= "" and effect and effect ~= "", key .. " has no Dwarf blurb or effect")
            assert(IC.plot_text(key, F) == IC.plot_by_key(key).name, key .. "'s Chaos Dwarf name moved")
        end
        for key in pairs(R.PLOT_TEXT) do
            assert(listed[key], "PLOT_TEXT words " .. key .. ", which PLOT_KEYS does not list")
        end
        local _n, _b, slayer = IC.plot_text("murder", D)
        assert(string.find(slayer, "Slayer Oath", 1, true), "the murder slot says " .. slayer)
        for _, fav in ipairs(IC.FAVOURS) do
            local name, blurb = IC.favour_text(fav.key, D)
            assert(name == R.FAVOUR_TEXT[fav.key].name and blurb == R.FAVOUR_TEXT[fav.key].blurb,
                fav.key .. " has no Dwarf words")
            assert(IC.favour_text(fav.key, F) == fav.name, fav.key .. "'s Chaos Dwarf name moved")
        end
    end)

    check("dwarfs: the envoy's four Dwarf tasks are control, Oathgold, growth and recruitment", function()
        fresh()
        make_faction(D, DWF_SUB, {}, {})
        make_faction(F, IC.CHD_SUBCULTURE, {}, {})
        local codes = {}
        for _, t in ipairs(IC.envoy_tasks(D)) do
            codes[#codes + 1] = t.code
            assert(t.bundle == IC.key("envoy", t.code, D), t.code .. " applies " .. t.bundle)
            assert(type(IC.TUNE[t.knob]) == "number", t.code .. "'s knob " .. t.knob .. " is not a setting")
        end
        assert(table.concat(codes, ",") == "ctl,oath,grow,rec", "the Dwarf tasks are " .. table.concat(codes, ","))
        local p, task = IC.envoy_split("prov_a:oath", D)
        assert(p == "prov_a" and task and task.bundle == "derpy_ic_envoy_dwf_oath", "prov_a:oath split wrong")
        local _p, none = IC.envoy_split("prov_a:arm", D)
        assert(none == nil, "a Dwarf envoy can still drive the armaments")
        local _q, arm = IC.envoy_split("prov_a:arm")
        assert(arm and arm.bundle == "derpy_ic_envoy_arm", "the Chaos Dwarf envoy lost its armaments task")
        assert(IC.envoy_tasks(F) == IC.ENVOY_TASKS, "the Chaos Dwarf tasks moved")
    end)

    check("dwarfs: the feed reads Dwarf words where the Dwarfs have them", function()
        fresh()
        make_faction(D, DWF_SUB, {}, {})
        make_faction(F, IC.CHD_SUBCULTURE, {}, {})
        shown = {}
        IC.raise_feed(D, "gov_intro")
        assert(shown[#shown].title == "event_feed_strings_text_derpy_ic_event_dwf_gov_intro_title",
            "a Dwarf court's introduction reads " .. tostring(shown[#shown].title))
        IC.raise_feed(D, "plot_ok")
        assert(shown[#shown].title == "event_feed_strings_text_derpy_ic_event_plot_ok_title",
            "a shared event took a Dwarf key: " .. tostring(shown[#shown].title))
        IC.raise_feed(F, "gov_intro")
        assert(shown[#shown].title == "event_feed_strings_text_derpy_ic_event_gov_intro_title",
            "the Chaos Dwarf introduction moved")
        IC.raise_feed_located(F, "realm_secede", 10, 20, D)
        assert(shown[#shown].primary == "event_feed_strings_text_derpy_ic_event_dwf_realm_secede_primary",
            "news of a Dwarf split reads " .. tostring(shown[#shown].primary))
        assert(IC.party_drawn_key(D, "legion")
               == "event_feed_strings_text_derpy_ic_event_party_drawn_dwf_legion", "party_drawn key")
        assert(IC.party_drawn_key(F, "legion")
               == "event_feed_strings_text_derpy_ic_event_party_drawn_legion", "the Chaos Dwarf party_drawn key moved")
        assert(IC.move_result_key("bribe", true, D)
               == "event_feed_strings_text_derpy_ic_move_dwf_bribe_ok", "the Dwarf move result key")
        assert(IC.move_result_key("bribe", false, F)
               == "event_feed_strings_text_derpy_ic_move_bribe_fail", "the Chaos Dwarf move result key moved")
        assert(IC.move_result_key("bribe", true)
               == "event_feed_strings_text_derpy_ic_move_bribe_ok", "the two-argument move result key moved")
    end)
```

- [ ] **Step 2: Run to verify they fail**

Run: `$env:IC_ONLY = "dwarfs:"; & "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua; Remove-Item Env:IC_ONLY`
Expected: exit 1, `FAIL dwarfs: every move and favour has its Dwarf name, ...: ... attempt to call field 'plot_text' (a nil value)`.

- [ ] **Step 3: The Dwarf words.** In `zzz_derpy_iron_court_dwarf.lua`, directly above `-- REGISTERED LAST, once:`, add:

```lua
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
    rumour = {name = "Whispers in the Halls",
     blurb = "Talk in the halls ruins one name.",
     effect = string.format(
         "-%d influence for him. His party is unaffected.",
         IC.TUNE.plot_rumour_damage)},
    murder = {name = "Drive Him to the Slayer Oath",
     blurb = "His party will know who drove him to it.",
     effect = string.format(
         "He takes the Slayer Oath and leaves the court for good. -%d loyalty from his party.",
         IC.TUNE.plot_murder_loyalty - IC.TUNE.loyalty_member_died)},
    provoke = {name = "An Insult to the Clan",
     blurb = "An insult they cannot ignore.",
     effect = string.format(
         "-%d loyalty. Sets their secession countdown to %d turns.",
         IC.TUNE.plot_provoke_loyalty,
         IC.TUNE.plot_provoke_clock),
     effect_no_secession = string.format(
         "-%d loyalty. With secession switched off, no countdown starts.",
         IC.TUNE.plot_provoke_loyalty)},
    purge = {name = "Cast Out the Clan",
     blurb = "The court watches.",
     effect = string.format(
         "Removes the party. -%d loyalty to all others. Failure: another -%d to the target.",
         IC.TUNE.plot_purge_witness,
         IC.TUNE.plot_purge_backfire)},
    unseat = {name = "Bar Them from the Hall",
     blurb = "They keep only their name.",
     effect = string.format(
         "Empties every office they hold. -%d loyalty.",
         IC.TUNE.plot_unseat_loyalty)},
    recall = {name = "Recall Governors",
     blurb = "The throne takes back its provinces.",
     effect = string.format(
         "Recalls every governor from their party. -%d loyalty.",
         IC.TUNE.plot_recall_loyalty)},
    oath = {name = "Swear on the Ancestors",
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
    audience = {name = "Hold Court in the Great Hall",
     blurb = "A day of ale and grievances.",
     effect = string.format(
         "+%d loyalty to every party in the court.",
         IC.TUNE.plot_audience_loyalty)},
    circuit = {name = "Walk the Holds",
     blurb = "A ledger and an armed escort.",
     effect = string.format(
         "+%d control in every province you hold.",
         IC.TUNE.plot_circuit_prov)},
    envoy = {name = "Send an Envoy",
     blurb = "He sees it done.",
     effect = string.format(
         "One of your provinces, for %d turns: control, Oathgold, growth or "
         .. "recruitment cost.", IC.TUNE.mission_turns)},
    diplomats = {name = "Send Diplomats",
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
```

- [ ] **Step 4: The model.**
  - In `IC.TUNE`, directly after the line `envoy_lab             = 15,   -- % fewer labourers lost`, add:

```lua
    -- THE DWARF ENVOY'S OTHER THREE (plan 2026-10-04 phase 2). Not settings;
    -- gen_iron_court reads them for the bundles' values.
    envoy_oath            = 20,   -- % Oathgold from buildings
    envoy_grow            = 5,    -- growth
    envoy_rec             = 15,   -- % off recruitment cost
```
  - Replace `IC.move_result_key` whole with:

```lua
-- THE RACE'S OWN LINE when a faction is in hand (plan 2026-10-04 phase 2):
-- a Chaos Dwarf key is unchanged, a Dwarf one carries the infix.
function IC.move_result_key(plot_key, ok, faction_key)
    if not plot_key then return nil end
    local stem = faction_key and IC.key("move", plot_key, faction_key)
                 or ("derpy_ic_move_" .. plot_key)
    return "event_feed_strings_text_" .. stem .. (ok and "_ok" or "_fail")
end

-- WHICH LOC AN EVENT READS: a race that words an event its own way lists the
-- slug in R.EVENT_LOC, and its keys carry the infix.
function IC.event_stem(slug, faction_key)
    local R = faction_key and IC.R(faction_key) or IC.RACES.chd
    if R.EVENT_LOC and R.EVENT_LOC[slug] then return IC.key("event", slug, faction_key) end
    return "derpy_ic_event_" .. slug
end

function IC.party_drawn_key(faction_key, party)
    return "event_feed_strings_text_" .. IC.key("event_party_drawn", party, faction_key)
end
```
  - At its two callers, replace `IC.move_result_key(plot_key, false))` with `IC.move_result_key(plot_key, false, faction_key))` and `IC.feed(faction_key, "plot_ok", IC.move_result_key(plot_key, true))` with `IC.feed(faction_key, "plot_ok", IC.move_result_key(plot_key, true, faction_key))`.
  - In `IC.raise_feed`, replace `local key = "derpy_ic_event_" .. slug` with `local key = IC.event_stem(slug, faction_key)`.
  - Replace the head of `IC.raise_feed_located`

```lua
function IC.raise_feed_located(faction_key, slug, x, y)
    local ev = IC.EVENTS[slug]
    if not ev or not x or not y then return false end
    local key = "derpy_ic_event_" .. slug
```
  with
```lua
-- `about` is the court the news is about, whose race words it; the card goes
-- to faction_key.
function IC.raise_feed_located(faction_key, slug, x, y, about)
    local ev = IC.EVENTS[slug]
    if not ev or not x or not y then return false end
    local key = IC.event_stem(slug, about or faction_key)
```
  and at its caller replace

```lua
                IC.raise_feed_located(human[i], "realm_secede",
                                      risings[1].x, risings[1].y)
```
  with
```lua
                IC.raise_feed_located(human[i], "realm_secede",
                                      risings[1].x, risings[1].y, faction_key)
```
  - In `IC.deed_join`, replace

```lua
    IC.feed(faction_key, "party_drawn",
            "event_feed_strings_text_derpy_ic_event_party_drawn_" .. party)
```
  with
```lua
    IC.feed(faction_key, "party_drawn", IC.party_drawn_key(faction_key, party))
```
  - Directly after `IC.favour_by_key`'s closing `end`, add:

```lua

-- A MOVE'S AND A FAVOUR'S WORDS FOR THIS COURT (plan 2026-10-04 phase 2): the
-- race's own where it has them, IC.PLOTS / IC.FAVOURS otherwise. The panel
-- draws these; the numbers stay IC.PLOTS'.
function IC.plot_text(plot_key, faction_key)
    local plot = IC.plot_by_key(plot_key)
    if not plot then return nil end
    local R = faction_key and IC.R(faction_key) or IC.RACES.chd
    local t = (R.PLOT_TEXT or {})[plot_key] or {}
    return t.name or plot.name, t.blurb or plot.blurb, t.effect or plot.effect,
           t.effect_no_secession or plot.effect_no_secession
end

function IC.favour_text(key, faction_key)
    local favour = IC.favour_by_key(key)
    if not favour then return nil end
    local R = faction_key and IC.R(faction_key) or IC.RACES.chd
    local t = (R.FAVOUR_TEXT or {})[key] or {}
    return t.name or favour.name, t.blurb or favour.blurb
end
```
  - Replace `IC.envoy_task` and `IC.envoy_split` whole with:

```lua
-- THE COURT'S OWN FOUR (plan 2026-10-04 phase 2). No faction is the Chaos
-- Dwarf list, which every caller written before the Dwarfs passes.
function IC.envoy_tasks(faction_key)
    local R = faction_key and IC.R(faction_key) or IC.RACES.chd
    return R.ENVOY_TASKS or IC.ENVOY_TASKS
end

function IC.envoy_task(code, faction_key)
    local tasks = IC.envoy_tasks(faction_key)
    for i = 1, #tasks do
        if tasks[i].code == code then return tasks[i] end
    end
    return nil
end
```
  and, keeping `IC.envoy_effect` between them as it is,
```lua
-- "province:code" -> the province key and the task; either is nil when the
-- target is malformed. Province keys never hold a ":".
function IC.envoy_split(target, faction_key)
    local province, code = string.match(tostring(target or ""), "^(.+):(%a+)$")
    return province, IC.envoy_task(code, faction_key)
end
```
  - In `IC.may_send_envoy` replace `local province, task = IC.envoy_split(target)` with `local province, task = IC.envoy_split(target, faction_key)`; in `IC.plot`'s `elseif plot_key == "envoy" then` branch make the same replacement.

- [ ] **Step 5: Run to verify they pass**

Run: `$env:IC_ONLY = "dwarfs:"; & "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua; Remove-Item Env:IC_ONLY`
Expected: `iron court harness: ok (15 checks)`. "no Chaos Dwarf word and no Guild in any Dwarf string" now also walks the moves, favours and envoy tasks.

- [ ] **Step 6: Checkpoint.** Run THE GATES. Expected: all green. (The panel still draws `IC.PLOTS`' names and the Chaos Dwarf envoy picker for a Dwarf court until phase 3.)

---

### Task 4: The "Dwarf courts" switch

**Files:**
- Modify: `zzz_derpy_iron_court.lua` - `IC.TUNE` switches (after `all_cards = true,`, today 681), `IC.TUNE_ORDER` (today 696-705), `IC.LIVE_TUNE` (today 1060-1061), `IC.has_court` (phase 1), `IC.dismantle` (today 3945-3966), the `ic_turn` listener (today 7041)
- Modify: `Modding Files/pack/script/mct/settings/derpy_iron_court.lua` - `SWITCHES` (today 81-121)
- Test: harness block

**Interfaces:**
- Consumes: `DWF.switch` (Task 1).
- Produces: TUNE `dwarf_courts = true` (last in `IC.TUNE_ORDER`, in `IC.LIVE_TUNE`), the MCT switch "Dwarf courts" (systems, live); `IC.has_court(faction)` false for a race whose switch is off; `IC.dismantle` removing the government and law bundles.

- [ ] **Step 1: Write the failing checks** (above `end -- DWARF CONTENT (plan 2026-10-04 phase 2)`):

```lua
    check("dwarfs: the Dwarf courts setting is registered, live and on by default", function()
        assert(IC.TUNE.dwarf_courts == true, "dwarf_courts is " .. tostring(IC.TUNE.dwarf_courts))
        assert(IC.TUNE_ORDER[#IC.TUNE_ORDER] == "dwarf_courts",
            "dwarf_courts is not appended last to the save order")
        local live = false
        for _, k in ipairs(IC.LIVE_TUNE) do if k == "dwarf_courts" then live = true end end
        assert(live, "dwarf_courts cannot be flipped in a running campaign")
        assert(IC.RACES.dwf.switch == "dwarf_courts", "the Dwarf race names no switch")
    end)

    check("dwarfs: with Dwarf courts off a Dwarf court comes off the map whole and a Chaos Dwarf one runs", function()
        fresh()
        saved["derpy_ic_" .. D] = nil
        cm.get_human_factions = function() return {D} end
        IC_GOVS_ON = true
        local f = make_faction(D, DWF_SUB, {make_character(9801, ANY_SEAT, nil, nil),
                                            make_character(9802, ANY_SEAT, nil, nil)}, {"prov_a"})
        local g = make_faction(F, IC.CHD_SUBCULTURE, {}, {"prov_b"})
        IC.register()
        core.listeners["ic_turn"]({faction = function() return f end})
        local worn = 0
        for key in pairs(applied) do
            if string.find(key, "_dwf_", 1, true) then worn = worn + 1 end
        end
        assert(worn > 0, "the Dwarf court wore nothing with the setting on, so off proves nothing")
        with_frozen({dwarf_courts = false}, function()
            assert(not IC.has_court(f), "a Dwarf faction has a court with Dwarf courts off")
            assert(IC.has_court(g), "a Chaos Dwarf faction lost its court to the Dwarf setting")
            core.listeners["ic_turn"]({faction = function() return f end})
            for key in pairs(applied) do
                assert(not string.find(key, "_dwf_", 1, true), "still worn with Dwarf courts off: " .. key)
            end
            assert(saved["derpy_ic_" .. D] == "", "the switched-off Dwarf court is still in the save")
        end)
        IC_GOVS_ON = nil
        cm.get_human_factions = function() return {} end
    end)
```

- [ ] **Step 2: Run to verify they fail**

Run: `$env:IC_ONLY = "dwarfs:"; & "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua; Remove-Item Env:IC_ONLY`
Expected: exit 1, `FAIL dwarfs: the Dwarf courts setting is registered, live and on by default: ... dwarf_courts is nil`.

- [ ] **Step 3: The setting.**
  - In `IC.TUNE`, directly after `all_cards           = true,`, add:

```lua
    -- DWARF COURTS (plan 2026-10-04 phase 2): off, no Dwarf faction has a
    -- court, and one already running comes off the map at its next turn.
    dwarf_courts        = true,
```
  - In `IC.TUNE_ORDER`, replace the closing `    "laws",` + `}` (the list's last entry and its closer) with:

```lua
    "laws",
    "dwarf_courts",
}
```
  - Replace `"all_cards", "detailed_log", "governments", "gov_drift", "deeds", "laws"}` in `IC.LIVE_TUNE` with `"all_cards", "detailed_log", "governments", "gov_drift", "deeds", "laws",` + newline + `                "dwarf_courts"}`.
  - In the MCT file, directly after the `{"laws", "Laws", "systems", ... true},` entry, add:

```lua
    {"dwarf_courts", "Dwarf courts", "systems",
     "Dwarf factions run courts of their own: Dwarf parties, offices, governments "
     .. "and laws. Off, no Dwarf faction has a court, and one already running is "
     .. "taken off the map at its next turn.", true},
```
  and replace the `ai_courts` label and tooltip

```lua
    {"ai_courts", "Other Chaos Dwarf factions have courts", "systems",
     "Chaos Dwarf factions you do not play run courts of their own, and theirs "
     .. "can split. Off, only your court runs.", false},
```
  with
```lua
    {"ai_courts", "Other Chaos Dwarf and Dwarf factions have courts", "systems",
     "Chaos Dwarf and Dwarf factions you do not play run courts of their own, and "
     .. "theirs can split. Off, only your court runs.", false},
```

- [ ] **Step 4: The switch takes effect.**
  - Read `IC.has_court` (`Select-String -Path "Modding Files\pack\script\campaign\mod\zzz_derpy_iron_court.lua" -Pattern "^function IC.has_court" -Context 0,6`). Unless it already reads `r.switch`, replace the whole function with:

```lua
-- A FACTION OF A RACE WITH A COURT, and that race switched on (its MCT key).
function IC.has_court(faction)
    local r = IC.race_of(faction)
    if not r then return false end
    return not r.switch or IC.TUNE[r.switch] ~= false
end
```
  - In the `ic_turn` listener, if the line reads `if IC.is_chd(faction) then` (above `local packed = cm:get_saved_value("derpy_ic_" .. faction:name())`), replace it with `if IC.race_of(faction) then`, and replace the comment above it `-- A CHAOS DWARF COURT THE SETTINGS SWITCHED OFF, still in the save.` with `-- A COURT THE SETTINGS SWITCHED OFF, still in the save, of either race.`
  - In `IC.dismantle`, directly before `IC.clear_gov_bundles(faction_key)`, add:

```lua
    -- THE GOVERNMENT AND THE LAWS TOO (plan 2026-10-04 phase 2): a player's
    -- court switched off wore both, and nothing else takes them off.
    local race = IC.R(faction_key)
    for _, g in ipairs(race.GOV_ORDER) do
        cm:remove_effect_bundle(IC.key("doctrine", g, faction_key), faction_key)
    end
    for _, cat in ipairs(race.LAW_ORDER) do
        for _, opt in ipairs(race.LAWS[cat].order) do
            cm:remove_effect_bundle(IC.key("law", cat .. "_" .. opt, faction_key), faction_key)
        end
    end
```

- [ ] **Step 5: Run to verify they pass**

Run: `$env:IC_ONLY = "dwarfs:"; & "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua; Remove-Item Env:IC_ONLY`
Expected: `iron court harness: ok (17 checks)`. Then the full harness (`$env:IC_TEST_ALL = 1; ...`): the existing check "every setting is registered in MCT, in the save order and with its default" passes with the new switch; a `FAIL` there names the missing half (TUNE, TUNE_ORDER or SWITCHES).

- [ ] **Step 6: Checkpoint.** Run THE GATES. Expected: all green.

---

### Task 5: The Dwarf effects and `RACES["dwf"]` in the generator

**Files:**
- Modify: `tools/gen_iron_court.py` - effect constants (before `ENVOY_EFFECT = {`, today 153), `ALL_EFFECTS` (today 171-174), `EFFECT_TEXT` / `EFFECT_SHORT` / `EFFECT_PERCENT` / `EFFECT_TEXT_TR` (today 417-588), the Dwarf data after phase 1's `RACES` definition, `check_race_effects()` (new, before `def check():`), `check()` (today 2598-2621)

**Interfaces:**
- Consumes: CONTRACT `RACES`, `tier_seats(race)`, `bundle_key(kind, slug, race)`; the existing `E_*` constants, `BOON`, `MALUS`, `AMBITION_BANDS`.
- Produces: `E_DWF_*`, `E_ENVOY_OATH`, `E_ENVOY_GROW`, `E_ENVOY_REC`, `DWF_EFFECTS`; `RACES["dwf"]` with keys `infix ORIGINS NOT_AN_ORIGIN ORIGIN_COLOUR PARTIES PARTY_GOV_BLURB BACKGROUNDS BG_COLOUR OFFICES GOVERNMENTS LAWS CONTROL_BANDS GOVERNOR_BASE ENVOY_EFFECT ENVOY_BLURB TIER_NAME STANDING_BAND PARTY_DRAWN EVENT_TEXT BUNDLE_ICON`; `check_race_effects() -> [problem]`.

- [ ] **Step 1: Snapshot the Chaos Dwarf build** (compared in Task 6 Step 5):

Run: `py -c "import sys, json, os; sys.path.insert(0, 'tools'); import gen_iron_court as G; json.dump(G.build(), open(os.path.join(os.environ['TEMP'], 'ic_build_before_phase2.json'), 'w'))"`
Expected: no output, exit 0.

- [ ] **Step 2: Write the failing check.** In `tools/gen_iron_court.py`, directly above `def check():`, add:

```python
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
```

and in `check()`, directly after `out.extend(check_party_drawn())`, add `out.extend(check_race_effects())`.

- [ ] **Step 3: Run to verify it fails**

Run: `py tools\gen_iron_court.py --check`
Expected: exit 1, `FAIL RACES has no dwf entry`.

- [ ] **Step 4: The effect constants.** Directly above the line `ENVOY_EFFECT = {"ctl": E_ENVOY_CTL, "arm": E_ENVOY_ARM,`, add:

```python
# THE DWARF EFFECTS (plan 2026-10-04 phase 2, spec section 4). Every (effect,
# scope) pair is one a vanilla Dwarf bundle, building or technology ships and
# every flag is CA's, read out of db.pack 2026-10-04; the source is named on
# each line. check() items 1, 2 and 15 re-read all of them. Dropped for want of
# a shipped pair: plan ruling 5.
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
```

  Append them to `ALL_EFFECTS`: replace `               E_ENVOY_CTL, E_ENVOY_ARM, E_ENVOY_RAW, E_ENVOY_LAB] + LAW_EFFECTS` with `               E_ENVOY_CTL, E_ENVOY_ARM, E_ENVOY_RAW, E_ENVOY_LAB] + LAW_EFFECTS + DWF_EFFECTS`.

- [ ] **Step 5: Their words.** In `EFFECT_TEXT`, directly before its closing `}` (after the `E_LAW_RANGED_COST[0]: ...` line), add (CA's own text, read with `read_vanilla_loc.load("effects")` 2026-10-04; check 15 re-reads it):

```python
    # THE DWARFS (plan 2026-10-04 phase 2). E_ENVOY_OATH and E_ENVOY_REC share
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
```

  In `EFFECT_SHORT`, before its closing `}`:

```python
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
```

  In `EFFECT_PERCENT`, before its closing `}`:

```python
    E_DWF_GRUDGE_ORDER[0]: False, E_DWF_GROWTH[0]: False, E_DWF_GROWTH_GOV[0]: False,
    E_ENVOY_GROW[0]: False, E_DWF_SETTLER_SRC[0]: False, E_DWF_ART_RANK[0]: False,
```

  In `EFFECT_TEXT_TR`, before its closing `}`:

```python
    E_DWF_GRUDGE_ORDER[0]: ("public_order_effect", "Control"),
```

- [ ] **Step 6: The Dwarf data.** Directly after phase 1's `RACES = {...}` definition (`Select-String -Path tools\gen_iron_court.py -Pattern "^RACES = "`), add:

```python
# ---------------------------------------------------------------------------
# THE DWARFS (plan 2026-10-04 phase 2; spec sections 2-4, 7, 8). The model's
# tables are in zzz_derpy_iron_court_dwarf.lua as DWF.X; check_dwf() holds the
# two together. Slugs are the Chaos Dwarf slots; every key carries "dwf_".
# ---------------------------------------------------------------------------
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

# Dwarf factions deliberately NOT origins, each named (spec section 3).
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
    "karaz":     "Raised under the High King's own roof, and impossible to impress.",
    "kadrin":    "Kadrin-born, where every second dwarf has sworn an oath he means to die by.",
    "angrund":   "Clan Angrund raised him on the tale of Eight Peaks, and he means to see it retaken.",
    "throng":    "He marched with the Throng, and saw things the Ancestors only spoke of.",
    "ironbrow":  "Ironbrow's people go further from home than any dwarf should.",
    "malakai":   "Malakai's people build things that should not fly, and fly them.",
    "barakvarr": "Raised by the sea-gate, counting other folk's cargo.",
    "zhufbar":   "Zhufbar-born: he knows an engine by its sound.",
    "krakadrak": "From the far north, where the cold keeps a dwarf honest.",
    "azorn":     "Azorn raised him, and raised him hard.",
    "norn":      "Norn-born, from the Grey Mountains, and proud of the stone.",
    "hirn":      "Hirn's people hear the mountain, and listen to it.",
    "azul":      "Azul's forges never cool, and neither do its grudges.",
    "ziflin":    "Ziflin-born, from a small hold with a long memory.",
    "rangers":   "Raised among the rangers, and never easy under a roof.",
    "deeps":     "Born deep underground and never entirely comfortable above it.",
    "grey":      "Grey Mountains born: he measures everything against a peak.",
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
    "crown":  "Your own men hold it, and they are watched.",
    "temple": "The priests keep the province, and every grudge in it is remembered.",
    "forge":  "The Forgewrights run the province like a forge floor, and the Oathgold comes in.",
    "chain":  "The Deepdelvers work the seams, and what the battlefields yield is counted.",
    "legion": "A hold under a thane costs less to keep than it should.",
    "ledger": "The Reckoners keep the province's books, and the tithe arrives whole.",
    "tower":  "The Runesmiths read everything that passes through, and pass it on.",
    "road":   "The Underway Wardens keep the roads open whatever the season.",
    "hearth": "The Hearth Clans hold it, and men come back to the muster faster.",
}

DWF_BACKGROUNDS = {
    "crown":  [("household",    "Household Warrior"),
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
               ("elder",        "Clan Elder")],
}

DWF_BG_COLOUR = {
    "household":    "He stood at the king's door before he ever stood in a shield wall.",
    "lineblood":    "Close enough to the throne to be dangerous, and he knows it.",
    "oathsworn":    "He swore to the throne before the Ancestors, and means every word.",
    "shrinekeeper": "He keeps the ancestor shrines, and knows every name carved in them.",
    "valayan":      "Valaya's priest. The hearth is his altar and the hold his charge.",
    "tombwarden":   "He guards the dead of the hold, and the dead are many.",
    "smith":        "He can tell good gromril by its ring, and bad by its silence.",
    "engineer":     "He can tell you what a gun will do before it does it.",
    "foundry":      "Twenty years at a furnace mouth. His beard is shorter for it.",
    "miner":        "He has dug further down than most dwarfs have ever been.",
    "prospector":   "He goes looking for seams nobody else believes in, and finds them.",
    "tunneller":    "He can hear rock about to give before it gives.",
    "longbeard":    "Old enough to complain that nothing is as it was, and right to.",
    "ironbreaker":  "He has held the underways against things that never come up to the light.",
    "thane":        "A thane of a small clan, with a long memory for every slight to it.",
    "reckoner":     "He prices everything, including this conversation.",
    "trader":       "He has traded with men, elves and worse, and been cheated by none of them.",
    "goldsmith":    "He weighs gold by eye and is never more than a grain out.",
    "runesmith":    "He strikes the runes his master taught him, and tells no one how.",
    "loremaster":   "He has read more of the hold's old books than they were written for.",
    "scribe":       "He writes the grudges down, and forgets none of them.",
    "ranger":       "He has walked the high passes enough times to have stopped counting.",
    "wayfinder":    "He knows the old roads the maps have forgotten.",
    "underwarden":  "He keeps the underways open by making the alternative worse.",
    "farmer":       "He grows barley on a mountainside, which nobody believes until they drink it.",
    "brewer":       "He can judge a brew by its smell, and has never been wrong.",
    "elder":        "Old clan, small clan, and a memory for every slight in it.",
}

# THE FOURTEEN SEATS, tier-4 magnitudes raised by TIER_MULT (plan ruling 6).
DWF_OFFICES = [
    {"slug": "priest", "name": "High Priest of the Ancestors", "affinity": "temple", "tier": 1,
     "blurb": "The Ancestors are honoured in every hall, and the hold is quiet.",
     "vacant_blurb": "The shrines stand unattended and the old names go unspoken.",
     "effects": [(E_ORDER, 2, BOON), (E_GDP, 4, BOON)],
     "vacancy": [(E_ORDER, 2, MALUS)]},
    {"slug": "forge", "name": "Master Forgewright", "affinity": "forge", "tier": 1,
     "blurb": "Every forge in the hold answers to one hammer, and it is his.",
     "vacant_blurb": "No master stands at the great anvil. The work slips and no one is blamed.",
     "effects": [(E_DWF_OATHGOLD, 5, BOON), (E_DWF_CRAFT, 4, BOON)],
     "vacancy": [(E_DWF_OATHGOLD, 2, MALUS)]},
    {"slug": "ledger", "name": "Keeper of the Reckoning", "affinity": "ledger", "tier": 2,
     "blurb": "Every debt the hold is owed is written down, and he holds the book.",
     "vacant_blurb": "The books go unbalanced and the tithe arrives light.",
     "effects": [(E_GDP, 6, BOON)],
     "vacancy": [(E_GDP, 3, MALUS)]},
    {"slug": "warden", "name": "Warden of the Gate", "affinity": "legion", "tier": 2,
     "blurb": "The gate is watched, and the watchers are paid on time.",
     "vacant_blurb": "The gate keeps itself, badly and at the hold's expense.",
     "effects": [(E_UPKEEP, 5, BOON), (E_REPLEN, 5, BOON)],
     "vacancy": [(E_ORDER, 2, MALUS)]},
    {"slug": "hand", "name": "Keeper of the Grudge-Book", "affinity": "tower", "tier": 2,
     "blurb": "Every wrong is written in his hand. From the next Age of Reckoning, fewer grudges need settling.",
     "vacant_blurb": "The Book goes unkept. From the next Age of Reckoning, more grudges need settling.",
     "effects": [(E_DWF_GRUDGE_REQ, 5, BOON)],
     "vacancy": [(E_DWF_GRUDGE_REQ, 2, MALUS)]},
    {"slug": "roads", "name": "Warden of the Underway", "affinity": "road", "tier": 2,
     "blurb": "The underways are his, and they are quicker than they were.",
     "vacant_blurb": "The underways go unwatched, and the traders take the long way round.",
     "effects": [(E_MOVEMENT, 4, BOON)],
     "vacancy": [(E_MOVEMENT, 2, MALUS)]},
    {"slug": "chains", "name": "Overseer of the Mines", "affinity": "chain", "tier": 3,
     "blurb": "He counts every cart that comes up the shaft, and the miners know he counts.",
     "vacant_blurb": "Uncounted, the miners dig at their own pace.",
     "effects": [(E_LAW_MINES, 10, BOON)],
     "vacancy": [(E_LAW_MINES, 4, MALUS)]},
    {"slug": "pits", "name": "Master of the Delvings", "affinity": "chain", "tier": 3,
     "blurb": "What comes back from a battlefield is his to weigh and his to store.",
     "vacant_blurb": "The spoils are picked over by whoever reaches them first.",
     "effects": [(E_DWF_LOOT, 16, BOON)],
     "vacancy": [(E_DWF_LOOT, 7, MALUS)]},
    {"slug": "quarry", "name": "Master of the Stonecutters", "affinity": "forge", "tier": 3,
     "blurb": "Stone is cut to his measure, and the halls rise for less.",
     "vacant_blurb": "The stonecutters work at the pace of the slowest of them.",
     "effects": [(E_CONSTRUCT, 6, BOON)],
     "vacancy": [(E_CONSTRUCT, 3, MALUS)]},
    {"slug": "muster", "name": "Thane of the Muster", "affinity": "legion", "tier": 3,
     "blurb": "He knows what a warrior costs, and he pays no more than that.",
     "vacant_blurb": "Every clan is mustered at whatever it asks for.",
     "effects": [(E_RECRUIT, 8, BOON)],
     "vacancy": [(E_RECRUIT, 4, MALUS)]},
    {"slug": "kilns", "name": "Brewmaster of the Hold", "affinity": "hearth", "tier": 4,
     "blurb": "The hold's ale is the best in the mountains, and the trade in its fine work follows it.",
     "vacant_blurb": "The brewhouse goes unkept, and the hold's fine work sells for less.",
     "effects": [(E_DWF_CULTURE, 8, BOON)],
     "vacancy": [(E_DWF_CULTURE, 4, MALUS)]},
    {"slug": "fields", "name": "Steward of the Holdfarms", "affinity": "hearth", "tier": 4,
     "blurb": "The holdfarms are tended, and the hold grows.",
     "vacant_blurb": "The holdfarms go untended, and the hold grows slowly.",
     "effects": [(E_DWF_GROWTH, 5, BOON)],
     "vacancy": [(E_DWF_GROWTH, 2, MALUS)]},
    {"slug": "scribes", "name": "Keeper of the Lore", "affinity": "tower", "tier": 4,
     "blurb": "The old books are kept and read, and new work comes quicker for it.",
     "vacant_blurb": "The lore goes unread, and new work comes slowly.",
     "effects": [(E_RESEARCH, 5, BOON)],
     "vacancy": [(E_RESEARCH, 2, MALUS)]},
    {"slug": "banners", "name": "Keeper of the Clan Banners", "affinity": "legion", "tier": 4,
     "blurb": "Every clan banner is counted, and the Grudge Settlers march cheaper for it.",
     "vacant_blurb": "The banners go uncounted, and the Grudge Settlers ask more to march.",
     "effects": [(E_DWF_SETTLER_COST, 10, BOON)],
     "vacancy": [(E_DWF_SETTLER_COST, 5, MALUS)]},
]

# THE GOVERNMENTS, in DWF.GOV_ORDER's order: slug, name, rule, blurb, effects.
# The Iron Law's broken-oath sentence is phase 4's (plan ruling 2).
DWF_GOVERNMENTS = [
    ("conclave", "The Council of Elders",
     "Office terms are shorter. A man may take a seat again after 1 turn.",
     "The eldest of the clans sit in council, and the throne hears them out.",
     [(E_RESEARCH, 5, BOON)]),
    ("priest", "The Ancestors' Writ",
     "Each rank a man gains is worth double influence. Battles are worth less.",
     "The Ancestors set down how a hold is ruled, and the priests read it aloud.",
     [(E_DWF_GRUDGE_ORDER, 2, BOON)]),
    ("forge", "The Forge-Throne",
     "Governors earn more income. Men at court earn less influence each turn.",
     "The master smiths rule from the forge, and the anvil keeps the time.",
     [(E_DWF_OATHGOLD, 10, BOON)]),
    ("legion", "The War-King",
     "Battles are worth more influence and loyalty. Men at court earn no "
     "influence each turn.",
     "The king rules from the shield wall, and so does every dwarf who would follow him.",
     [(E_UPKEEP, 5, BOON)]),
    ("chain", "The Iron Law",
     "Swear on the Ancestors, Stand His Patron and Oath on the Anvil cost a third less.",
     "An oath sworn in the hold is kept, or it is written down.",
     [(E_DWF_SETTLER_SRC, 1, BOON)]),
    ("convoy", "The Reckoning-Throne",
     "Gifts and oaths cost less gold. Skimming the Tally angers the parties twice as much.",
     "Every debt is counted, and the throne keeps the count.",
     [(E_DWF_TARIFF, 10, BOON)]),
]

# THE LAWS (spec section 7), in DWF.LAW_ORDER and each category's order.
DWF_LAWS = [
    ("labour", "Craft", "edict_masters_of_steel_and_stone.png", [
        ("measure", "The Old Ways", "The clans work as their fathers worked.", []),
        ("lash", "Deep Seams", "The miners go deeper, and the holdfarms go short of hands.",
         [(E_LAW_MINES, 15, BOON), (E_DWF_GROWTH, 3, MALUS)]),
        ("kept", "Hearth and Holdfarm", "The holdfarms are tended first, and the mines wait.",
         [(E_DWF_GROWTH, 8, BOON), (E_LAW_MINES, 10, MALUS)]),
        ("quota", "The Master's Mark", "Only marked work leaves the forge, and the forge eats the hours.",
         [(E_DWF_CRAFT, 15, BOON), (E_REPLEN, 5, MALUS)]),
        ("ash", "Raise the Halls", "The halls are raised and widened, and the counting-houses pay.",
         [(E_CONSTRUCT, 15, BOON), (E_GDP, 5, MALUS)]),
    ]),
    ("tribute", "Tribute", "edict_collect_tribute.png", [
        ("tithe", "The King's Tithe", "The throne takes its tithe, as it always has.", []),
        ("roads", "Open Underways", "The underways are opened to trade, and the vassal holds pay less.",
         [(E_DWF_TARIFF, 15, BOON), (E_MOVEMENT, 5, BOON), (E_LAW_VASSAL, 20, MALUS)]),
        ("tariff", "The Reckoners' Tariff", "Every hall pays the Reckoners, and the traders pay more at the gate.",
         [(E_GDP, 5, BOON), (E_DWF_TARIFF, 10, MALUS)]),
        ("mines", "The Oathgold Hoard", "The Oathgold is hoarded, and the roads are left to keep themselves.",
         [(E_DWF_OATHGOLD, 15, BOON), (E_MOVEMENT, 5, MALUS)]),
        ("charter", "Hold Charters", "The holds are chartered to trade their craft, and the warriors pay for it.",
         [(E_DWF_CULTURE, 15, BOON), (E_LAW_GOODS, 10, BOON), (E_UPKEEP, 5, MALUS)]),
    ]),
    ("worship", "Ancestors", "edict_venerate_the_ancestors.png", [
        ("rites", "The Ancestors' Rites", "The rites are kept, as they always have been.", []),
        ("fires", "Valaya's Hearth", "Valaya's hearths are kept warm, and the loremasters go short.",
         [(E_DWF_GRUDGE_ORDER, 2, BOON), (E_DWF_GROWTH, 3, BOON), (E_RESEARCH, 5, MALUS)]),
        ("seats", "Rune-Lore", "The runesmiths are given their head, and the shrines are given less.",
         [(E_DWF_RUNECRAFT, 15, BOON), (E_DWF_GRUDGE_ORDER, 1, MALUS)]),
        ("lore", "The Lore of the Book", "The old books are opened, and the holdfarms lose their hands to them.",
         [(E_RESEARCH, 10, BOON), (E_DWF_GROWTH, 3, MALUS)]),
        ("licence", "The Anvil's Licence", "The forge is licensed to work without the priests' leave.",
         [(E_DWF_CRAFT, 10, BOON), (E_DWF_GRUDGE_ORDER, 1, MALUS)]),
    ]),
    ("war", "War", "edict_levy_conscripts.png", [
        ("levy", "The Muster", "The clans are mustered as they always have been.", []),
        ("grudge", "Grudge Settlers", "Grudge Settlers march at the throne's cost, and the counting-houses pay.",
         [(E_DWF_SETTLER_COST, 15, BOON), (E_DWF_SETTLER_SRC, 1, BOON), (E_GDP, 5, MALUS)]),
        ("hellforge", "Batteries of the Hold", "The guns come first, and every warrior costs more.",
         [(E_DWF_WM_UPKEEP, 10, BOON), (E_DWF_GT_DMG, 5, BOON), (E_DWF_INF_COST, 10, MALUS)]),
        ("legions", "Clan Hosts", "The clans march in strength, and the guns wait.",
         [(E_DWF_INF_COST, 10, BOON), (E_DWF_WM_UPKEEP, 10, MALUS)]),
        ("gunnery", "Thunder and Iron", "The engineers drill the guns and the thunderers, and every recruit costs more.",
         [(E_DWF_THUNDER, 10, BOON), (E_DWF_ART_RANK, 1, BOON), (E_RECRUIT, 5, MALUS)]),
    ]),
]

DWF_CONTROL_BANDS = [
    ("grip", 75, "An Iron Grip on the Court",
     "Nothing moves in the hold that the throne did not set moving.",
     [(E_ORDER, 6, BOON), (E_GDP, 12, BOON), (E_UPKEEP, 15, BOON),
      (E_DWF_OATHGOLD, 5, BOON)]),
    ("mastery", 60, "Master of the Court",
     "The clans argue, and then they do as they are told.",
     [(E_ORDER, 4, BOON), (E_GDP, 8, BOON), (E_UPKEEP, 10, BOON)]),
    ("command", 40, "In Command of the Court",
     "The throne is first among the clans, and no more than first.",
     [(E_ORDER, 2, BOON)]),
    ("contested", 10, "A Contested Court",
     "No decree passes without a bargain struck.",
     [(E_ORDER, 2, MALUS), (E_UPKEEP, 5, MALUS)]),
    ("lost", 0, "The Court Is Not Yours",
     "The clans rule and the throne is consulted, when there is time.",
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
        "A clan or two would take him, and one says so openly.",
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
        "ctl": "An envoy of the throne is keeping order here.",
        "oath": "An envoy of the throne is seeing that the forges here pay their Oathgold.",
        "grow": "An envoy of the throne is seeing to the holdfarms here.",
        "rec": "An envoy of the throne is mustering the clans here for less.",
    },
    "TIER_NAME": DWF_TIER_NAME,
    "STANDING_BAND": DWF_STANDING_BAND,
    # THE SECONDARY LINE party_drawn PASSES, one per party a Dwarf deed draws.
    "PARTY_DRAWN": {
        "legion": "Your victories drew the Clan Warriors to court.",
        "tower": "Your research drew the Runesmiths to court.",
    },
    # THE EVENTS IN DWF.EVENT_LOC: title, primary, secondary.
    "EVENT_TEXT": {
        "gov_intro": (
            "Your Deeds Move the Court",
            "Your court has a government, shown in the throne's box. What you do "
            "moves it. Victories raise the Clan Warriors, and research raises the "
            "Runesmiths. A party that grows strong enough asks for its own government.",
            "The Court Watches You"),
        "realm_secede": (
            "A Rival Court Splits",
            "A party in a Dwarf hold's court has broken away and risen in rebellion. "
            "The Record tab names them; the camera button shows where.",
            "Rebellion!"),
    },
    "BUNDLE_ICON": "trait_dwarf.png",
}
```

- [ ] **Step 7: Run to verify it passes**

Run: `py tools\gen_iron_court.py --check`
Expected: exit 0, `ok: <N> bundles, ...` with the same four numbers as before this task (Task 6 emits the rows). A `FAIL effect key not in vanilla`, `is_positive_value_good disagrees`, `(effect, scope) pair not shipped by CA` or `tooltip text drifted` naming a `dwf` effect means the cache moved since 2026-10-04: re-read the pair with `py tools\read_vanilla_db.py effect_bundles_to_effects_junctions_tables` and drop the effect (and record it in Ruling 5) rather than change its scope by guess.

- [ ] **Step 8: Checkpoint.** Run THE GATES. Expected: all green.

---

### Task 6: Emit every Dwarf row, and `check_dwf`

**Files:**
- Modify: `tools/gen_iron_court.py` - the Dwarf scrapers and `emit_dwf` (after `model_tails()`, today 1519-1534), `build()` (before `missions = []`, today 1869), `check_dwf()` (new, before `def check():`), `check()`

**Interfaces:**
- Consumes: Task 1-3 Lua (`DWF.ORIGINS OFFICES GOV_ORDER GOVS START_GOV LAW_ORDER LAWS DEEDS ENVOY_TASKS NAME_TAILS PLOT_KEYS PLOT_TEXT EVENT_LOC REBEL_*`), Task 5 `RACES["dwf"]`; `emit`, `emit_trait`, `emit_member`, `loc` inside `build()`; `tier_value`, `effect_line`, `party_cat`, `model_moves`, `model_tune`, `AMBITION_BANDS`, `EVENTS`, `JARGON`, `_cache_table`.
- Produces: `DWF_LUA`, `_dwf_block(name)`, `_dwf_list(name)`, `dwf_origins()`, `dwf_offices()`, `dwf_gov_icons()`, `dwf_law_icons()`, `dwf_law_orders()`, `dwf_envoy_tasks()`, `dwf_tails()`, `dwf_start_gov()`, `dwf_plot_names()`, `emit_dwf(emit, emit_trait, emit_member, loc)`, `DWF_ROWS = {"bundles": [...], "traits": [...], "loc": [...]}`, `check_dwf() -> [problem]`. Rows: 73 bundles, 104 junctions, 134 traits.

- [ ] **Step 1: Write the failing check.** Directly above `def check():`, add:

```python
# WHY EACH DWARF SUBTYPE ALL THREE POOL FACTIONS PERMIT IS LEFT OUT (plan ruling 7).
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
# THE CHAOS DWARFS' OWN WORDS, which no Dwarf string may carry (spec section 2).
CHD_WORDS = re.compile(r"hashut|zharr|hell-?forge|slave|labourer|hobgoblin|convoy|"
                       r"ziggurat|daemon|chaos dwarf", re.I)
DWF_SUBCULTURE = "wh_main_sc_dwf_dwarfs"


def great_guild_dwarf_names():
    """The six Great Guilds Dwarf names, off that mod's own leader bundles."""
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
    words its own (plan 2026-10-04 phase 2)."""
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
    if _dwf_list("GOV_ORDER") != [g[0] for g in R["GOVERNMENTS"]]:
        out.append("DWF.GOV_ORDER is %s" % _dwf_list("GOV_ORDER"))
    if _dwf_list("LAW_ORDER") != [c[0] for c in R["LAWS"]]:
        out.append("DWF.LAW_ORDER is %s" % _dwf_list("LAW_ORDER"))
    orders = dwf_law_orders()
    for cat, _n, _i, options in R["LAWS"]:
        if orders.get(cat) != [o[0] for o in options]:
            out.append("DWF.LAWS.%s order is %s" % (cat, orders.get(cat)))
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
    if len(guilds) != 6:
        out.append("read %d Great Guilds Dwarf names, not 6" % len(guilds))
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
```

and in `check()`, directly after `out.extend(check_race_effects())`, add `out.extend(check_dwf())`.

- [ ] **Step 2: The scrapers and the store.** Directly after `def model_tails():`'s function body (before `def member_trait_key`), add:

```python
# THE DWARF RACE'S TABLES, READ OUT OF ITS OWN FILE (plan 2026-10-04 phase 2)
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
    """The body of a column-0 DWF.<name> = { ... } - phase 1's lua_table, the one
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


def dwf_gov_icons():
    return dict(re.findall(r'(\w+)\s*=\s*\{icon = "([^"]+)"', _dwf_block("GOVS")))


def _dwf_law_cats():
    return re.finditer(r"\n    (\w+) = \{icon = \"[^\"]+\",\s*\n\s*order = \{([^}]*)\},"
                       r"\s*\n\s*opts = \{(.*?)\n    \}\}", _dwf_block("LAWS"), re.S)


def dwf_law_icons():
    out = {}
    for cm in _dwf_law_cats():
        for om in re.finditer(r"(\w+)\s*=\s*\{icon = \"([^\"]+)\"", cm.group(3)):
            out[(cm.group(1), om.group(1))] = om.group(2)
    return out


def dwf_law_orders():
    return dict((cm.group(1), re.findall(r'"(\w+)"', cm.group(2))) for cm in _dwf_law_cats())


def dwf_envoy_tasks():
    tasks = re.findall(
        r'\{code = "(\w+)", name = "([^"]+)", knob = "(\w+)", fmt = "[^"]*",\s*'
        r'bundle = "(\w+)", icon = "([^"]+)"\}', _dwf_block("ENVOY_TASKS"))
    if len(tasks) != 4:
        raise RuntimeError("DWF.ENVOY_TASKS parsed to %d tasks, not 4" % len(tasks))
    return tasks


def dwf_tails():
    return dict((slug, re.findall(r'"([^"]+)"', body)) for slug, body in
                re.findall(r"(\w+)\s*=\s*\{(.*?)\}", _dwf_block("NAME_TAILS"), re.S))


def dwf_start_gov():
    return dict(re.findall(r'(\w+) = "(\w+)"', _dwf_block("START_GOV")))


def dwf_plot_names():
    return dict(re.findall(r'\n    (\w+) = \{name = "([^"]+)"', _dwf_block("PLOT_TEXT")))


def emit_dwf(emit, emit_trait, emit_member, loc):
    """Every Dwarf bundle, trait and loc row. Each key is bundle_key(kind, slug,
    "dwf"), the Lua's IC.key with the dwf_ infix (plan 2026-10-04 phase 2)."""
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
    gov_icons = dwf_gov_icons()
    for slug, name, rule, blurb, effects in R["GOVERNMENTS"]:
        emit(K("doctrine", slug), name, blurb, "faction", effects, icon=gov_icons.get(slug))
        text(K("doctrine_name", slug), name)
        text(K("doctrine_rule", slug), rule)
    law_icons = dwf_law_icons()
    for cat, cat_name, _icon, options in R["LAWS"]:
        text(K("law_cat", cat), cat_name)
        for opt, name, blurb, effects in options:
            emit(K("law", cat + "_" + opt), name, blurb, "faction", effects,
                 icon=law_icons.get((cat, opt)))
            text(K("law_name", cat + "_" + opt), name)
            for n, (e, m, intent) in enumerate(effects, start=1):
                text(K("law_fx%d" % n, cat + "_" + opt), effect_line(e, m, intent))
    emit(K("gov", "base"), "Governor of the Province",
         "A governor of the throne sits here, and the province knows it.",
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
                       "He has left the trade behind, whatever he says.", party_cat(party))
    for tier in [0] + sorted(R["TIER_NAME"]):
        name, colour, explain = R["STANDING_BAND"][tier]
        emit_trait(K("standing", str(tier)), name, colour, explain,
                   "His influence at court has changed.", "derpy_ic_cat_standing")
    for slug in ("cautious", "steady", "ambitious"):
        name, colour, explain = AMBITION_BANDS[slug]
        emit_trait(K("ambition", slug), name, colour, explain,
                   "His ambition does not change.", "derpy_ic_cat_ambition")
    emit_member(K("member", CROWN), "the Throne-Sworn", party_cat(CROWN))
    for slug, _faction, display in R["ORIGINS"]:
        emit_member(K("member", slug), display, "derpy_ic_cat_confed")
    tails = dwf_tails()
    for party, _d, _e, _m in R["PARTIES"]:
        if party != CROWN:
            for n, tail in enumerate(tails[party], 1):
                emit_member("%s_%d" % (K("member", party), n), tail, party_cat(party))
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
            text("event_feed_strings_text_" + K("move", move_key) + "_ok", name + " - Success!")
            text("event_feed_strings_text_" + K("move", move_key) + "_fail", name + " - Failure")
```

- [ ] **Step 3: Run to verify the check fails**

Run: `py tools\gen_iron_court.py --check`
Expected: exit 1, `FAIL build() emitted no Dwarf bundle`.

- [ ] **Step 4: Call it from `build()`.** In `build()`, directly above the line `    missions = []`, add:

```python
    # THE DWARFS (plan 2026-10-04 phase 2), after every Chaos Dwarf row so none
    # of those moves; what they wrote is kept for check_dwf.
    _was = (len(bundles), len(traits), len(loc))
    emit_dwf(emit, emit_trait, emit_member, loc)
    DWF_ROWS["bundles"] = [r["key"] for r in bundles[_was[0]:]]
    DWF_ROWS["traits"] = [r["key"] for r in traits[_was[1]:]]
    DWF_ROWS["loc"] = [r["key"] for r in loc[_was[2]:]]
```

- [ ] **Step 5: Run to verify it passes, and the Chaos Dwarf rows did not move**

Run: `py tools\gen_iron_court.py --check`
Expected: exit 0, `ok: <B> bundles, <J> junctions, <T> traits, <L> loc rows`.

Run: `py -c "import sys, json, os; sys.path.insert(0, 'tools'); import gen_iron_court as G; old = json.load(open(os.path.join(os.environ['TEMP'], 'ic_build_before_phase2.json'))); new = G.build(); dwf = lambda r: 'dwf_' in str(list(r.values())[0]); bad = [t for t in old if [r for r in new[t] if not dwf(r)] != old[t]]; print('chd rows unchanged' if not bad else 'CHANGED: %s' % bad); print('added', dict((t, len(new[t]) - len(old[t])) for t in ('effect_bundles', 'effect_bundles_to_effects_junctions', 'character_traits')))"`
Expected: `chd rows unchanged` and `added {'effect_bundles': 73, 'effect_bundles_to_effects_junctions': 104, 'character_traits': 134}`.

- [ ] **Step 6: Write the TSVs.**

Run: `py tools\gen_iron_court.py`
Expected: the `ok:` line, then one `wrote ...` line per table under `Modding Files\source\iron_court`.

- [ ] **Step 7: Checkpoint.** Run THE GATES. Expected: all green.

---

### Task 7: The importer and deploy script learn the Dwarf file; every worn key ships

**Files:**
- Modify: `tools/import_iron_court.py` - `SCRIPTS` (today 26), check 0e's sources (today 911-914), check 2c (today 1067-1103)
- Modify: `tools/deploy_iron_court.py` - `SCRIPTS` (today 65-77)
- Test: harness block

**Interfaces:**
- Consumes: Task 6's TSVs in `Modding Files/source/iron_court/`; `G.bundle_key`, `G.tier_seats`.
- Produces: `import_iron_court.DWARF_LUA`; the Dwarf file in both `SCRIPTS` lists (so luac, `check_lua_api`, `check_lua_undeclared`, `check_lua_literal_left`, the tune-read check and the saved-pack presence check all reach it).

- [ ] **Step 1: Write the failing check** (above `end -- DWARF CONTENT (plan 2026-10-04 phase 2)`):

```lua
    check("dwarfs: every key a Dwarf court wears is a Dwarf row the generator ships", function()
        local function first_column(file)
            local out = {}
            local fh = assert(io.open("Modding Files/source/iron_court/" .. file, "r"),
                "no " .. file .. " - run py tools\\gen_iron_court.py")
            for line in fh:lines() do
                local k = string.match(line, "^([^\t]+)")
                if k then out[k] = true end
            end
            fh:close()
            return out
        end
        local bundles = first_column("effect_bundles.tsv")
        local traits = first_column("character_traits.tsv")
        fresh()
        traits_added = {}
        saved["derpy_ic_" .. D] = nil
        cm.get_human_factions = function() return {D} end
        IC_GOVS_ON = true
        local men = {}
        for i = 1, 6 do men[i] = make_character(9600 + i, ANY_SEAT, nil, nil) end
        local f = make_faction(D, DWF_SUB, men, {"prov_a"})
        IC.register()
        for _ = 1, 2 do core.listeners["ic_turn"]({faction = function() return f end}) end
        IC_GOVS_ON = nil
        cm.get_human_factions = function() return {} end
        local worn = 0
        for key in pairs(applied) do
            if string.sub(key, 1, 9) == "derpy_ic_" then
                worn = worn + 1
                assert(string.find(key, "_dwf_", 1, true), "a Dwarf court wears the Chaos Dwarf bundle " .. key)
                assert(bundles[key], "a Dwarf court wears " .. key .. ", which no effect_bundles row declares")
            end
        end
        assert(worn >= 20, "a Dwarf court wore only " .. worn .. " court bundles")
        local stamped = 0
        for _, entry in ipairs(traits_added) do
            local trait = string.match(entry, "=(.+)$")
            if trait and string.sub(trait, 1, 9) == "derpy_ic_" then
                stamped = stamped + 1
                assert(string.find(trait, "_dwf_", 1, true), "a Dwarf lord was given the Chaos Dwarf trait " .. trait)
                assert(traits[trait], "a Dwarf lord was given " .. trait .. ", which no character_traits row declares")
            end
        end
        assert(stamped > 0, "no court trait was stamped on a Dwarf lord, so the trait half proves nothing")
    end)
```

and in `tools/import_iron_court.py`'s 2c, inside the `else:` branch directly after the `for tier in [0] + sorted(set(t for _slug, t in seq)):` loop (before `# And the other way:`), add:

```python
            # THE DWARF BANDS (plan 2026-10-04 phase 2): the same stem with the
            # race's infix, one per Dwarf tier and the man who clears none.
            for tier in [0] + sorted(G.tier_seats("dwf")):
                key = G.bundle_key("standing", str(tier), "dwf")
                want.add(key)
                if key not in declared:
                    problems.append("the Lua stamps Dwarf standing band %s, which no "
                                    "character_traits row declares" % key)
```

- [ ] **Step 2: Run to verify it fails**

Run: `py tools\import_iron_court.py`
Expected: exit 1 with a `REFUSING` / problem line `the setting dwarf_courts is on the MCT page and read nowhere - its control would change nothing` (the model reads it only through `IC.TUNE[r.switch]`, and the Dwarf file that names it is not scanned yet).

Run: `$env:IC_ONLY = "dwarfs:"; & "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua; Remove-Item Env:IC_ONLY`
Expected: `iron court harness: ok (18 checks)` - the worn-key check already passes against Task 6's TSVs; watch it fail by renaming `Modding Files\source\iron_court\character_traits.tsv` to `character_traits.tsv.off`, running again (expected `FAIL dwarfs: every key a Dwarf court wears ...: ... no character_traits.tsv`), and renaming it back.

- [ ] **Step 3: Wire the file.**
  - In `tools/import_iron_court.py`, directly after `MODEL_LUA = ...`, add `DWARF_LUA = "Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_dwarf.lua"`, and replace `SCRIPTS = [MODEL_LUA, UI_LUA, PARTIES_LUA, MCT_LUA, MAP_LUA]` with `SCRIPTS = [MODEL_LUA, DWARF_LUA, UI_LUA, PARTIES_LUA, MCT_LUA, MAP_LUA]`.
  - In check 0e, replace `for p in (MODEL_LUA, PARTIES_LUA, UI_LUA) if os.path.isfile(p)]` with `for p in (MODEL_LUA, PARTIES_LUA, UI_LUA, DWARF_LUA) if os.path.isfile(p)]` (the model stays first: `srcs[0]` is where `IC.TUNE_ORDER` is read).
  - In `tools/deploy_iron_court.py`'s `SCRIPTS`, directly after the model's tuple, add:

```python
    # THE DWARF RACE (plan 2026-10-04 phase 2): loads after the model, before
    # the parties file.
    ("Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_dwarf.lua",
     "script/campaign/mod/zzz_derpy_iron_court_dwarf.lua"),
```

- [ ] **Step 4: Run to verify it passes**

Run: `py tools\import_iron_court.py`
Expected: exit 0, the verify-only report with no problem line.

Run: `py -c "import sys; sys.path.insert(0, 'tools'); import import_iron_court as V, deploy_iron_court as D; n = 'zzz_derpy_iron_court_dwarf.lua'; print('import', any(n in s for s in V.SCRIPTS)); print('deploy', any(n in d for _s, d in D.SCRIPTS))"`
Expected: `import True` and `deploy True`.

- [ ] **Step 5: Checkpoint.** Run THE GATES. Expected: all green; the harness count is phase 1's plus 18.

---

### Task 8: Build, deploy, and verify the saved pack

**Files:**
- Create (scratch, not shipped): `$env:TEMP\verify_ic_phase2.py`
- No source change.

**Interfaces:**
- Consumes: everything above; RPFM open.
- Produces: `Modding Files\Modpacks\derpy_iron_court.pack`, deployed to `data\` (backup in `Modding Files\Backup\deployed_auto\`).

- [ ] **Step 1: RPFM is open.**

Run: `Invoke-WebRequest http://127.0.0.1:45127/sessions -TimeoutSec 4 -UseBasicParsing`
Expected: status 200. Connection refused: RPFM is closed; say so and stop.

- [ ] **Step 2: Build and deploy.**

Run: `py tools\deploy_iron_court.py`
Expected: `gates green`, one line per table and file including `  script/campaign/mod/zzz_derpy_iron_court_dwarf.lua`, `saved ...derpy_iron_court.pack (N bytes)`, `verified N file(s) in the saved pack`, then the backup and the byte-compared copy into `data\`. If Warhammer3 is running it refuses: run `py tools\deploy_iron_court.py --deploy-only --wait` in the background instead.

- [ ] **Step 3: Export every table back out of the saved pack and count rows.** Write `$env:TEMP\verify_ic_phase2.py` with the Write tool:

```python
"""Re-open the SAVED derpy_iron_court.pack and round-trip every table and the
loc back out as TSV; each must hold exactly the rows build() makes."""
import json
import os
import sys
import tempfile

ROOT = r"G:\Modding for resources"
sys.path.insert(0, os.path.join(ROOT, "tools"))
os.chdir(ROOT)
import gen_iron_court as G                       # noqa: E402
from import_house_ancillaries import call       # noqa: E402

PACK = os.path.join(ROOT, "Modding Files", "Modpacks", "%s.pack" % G.PACK_NAME)


def rows_in(path):
    lines = [l for l in open(path, encoding="utf-8").read().split("\n") if l.strip()]
    return len(lines) - 2


call("set_game_selected", {"game_name": "warhammer_3", "rebuild_dependencies": False})
pack = call("open_packfiles", {"paths": [PACK]})["StringContainerInfo"][0]
built = G.build()
paths = dict(("db/%s/%s" % (G.TSV_META[t][0], G.PACK_NAME), t) for t in G.TSV_META if t != "loc")
paths["text/db/%s.loc" % G.PACK_NAME] = "loc"
bad = []
with tempfile.TemporaryDirectory() as td:
    call("extract_packed_files", {
        "pack_key": pack,
        "source_paths": json.dumps({"PackFile": [{"File": p} for p in paths]}),
        "destination_path": td,
        "export_as_tsv": True,
    })
    for path, table in sorted(paths.items()):
        got_path = os.path.join(td, *path.split("/")) + ".tsv"
        if not os.path.isfile(got_path):
            bad.append("%s did not come back out of the saved pack" % path)
            continue
        got, want = rows_in(got_path), len(built[table])
        print("  %-4s %-62s %5d rows (build %d)" % ("ok" if got == want else "BAD", path, got, want))
        if got != want:
            bad.append("%s: %d rows in the pack, build() makes %d" % (path, got, want))
for rel in ["script/campaign/mod/zzz_derpy_iron_court_dwarf.lua"]:
    if not call("packed_file_exists", {"pack_key": pack, "value": rel}).get("Bool"):
        bad.append("%s is not in the saved pack" % rel)
call("close_pack", {"pack_key": pack})
print("\n".join(bad) if bad else "saved pack verified: every table and the loc match build()")
sys.exit(1 if bad else 0)
```

Run: `py "$env:TEMP\verify_ic_phase2.py"`
Expected: an `ok` line per table and the loc, then `saved pack verified: every table and the loc match build()`, exit 0.

- [ ] **Step 4: The sign review and the bundle loc gate.**

Run: `py tools\check_effect_signs.py "G:\Modding for resources\Modding Files\Modpacks\derpy_iron_court.pack" derpy_ic_`
Expected: exit 0 (a review report). Every `_dwf_` row it lists as a penalty is a vacancy (`derpy_ic_vacant_dwf_*`), a law option's malus (`derpy_ic_law_dwf_*`) or the contested / lost band (`derpy_ic_control_dwf_contested`, `derpy_ic_control_dwf_lost`); any other `_dwf_` row is a sign fault in Task 5's data and goes back to Task 5.

Run: `py tools\check_effect_bundle_loc.py "G:\Modding for resources\Modding Files\Modpacks\derpy_iron_court.pack"`
Expected: `<N> bundles, <M> loc keys, 0 finding(s)`, exit 0.

- [ ] **Step 5: Final checkpoint.** Run THE GATES once more, and `py tools\import_iron_court.py`. Expected: all green. Report to the author: the pack deployed (or waiting on the game), the 73 Dwarf bundles / 104 junctions / 134 traits, the dropped keys (Rulings 3-5), and that the panel draws a Dwarf court with Chaos Dwarf layout, names of moves and envoy picker until phase 3.
