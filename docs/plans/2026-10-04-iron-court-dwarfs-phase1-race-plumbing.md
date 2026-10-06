# Iron Court for Dwarfs - Phase 1: race plumbing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make every Iron Court table read, key and tuning knob go through the race of the faction in hand - `IC.R(faction_key)` - with the Chaos Dwarfs as the only registered race, so phase 2 can register the Dwarfs by adding data alone, and prove the Chaos Dwarf court is unchanged: harness green plus the new race checks, every generator count unchanged, and every generated DB, loc, `.twui.xml` and plate file byte-identical.

**Architecture:** A race block at the foot of `zzz_derpy_iron_court.lua` builds `IC.RACES.chd` out of the existing `IC.X` tables (the same tables, not copies, so the scrapers and the harness's 304 references keep matching), derives `TIERS`/`TIER_SEATS`/`PARTY_OF_BG`/`MAX_SEATS` per race, and answers a faction's race from its subculture (`IC.race_of`, `IC.race_key`, `IC.R`, `IC.has_court`). Keys gain `IC.key(kind, slug, faction_key)` with the race's infix (`""` for the Chaos Dwarfs, so byte-identical). Each of the ~200 reading sites reads `R.X` where `local R = IC.R(<the faction in hand>)`; lookups by a key that belongs to no faction (a subtype, an origin slug) ask every race. The harness pins all of it with a throwaway second race `tst` (offices 2/4/4/4, its own origins, backgrounds and law category), a source scan for any site left on `IC.X`, and an arity scan for any keyed call that leaves the faction off. Python gains `RACES`, `tier_seats(race)`, `bundle_key(kind, slug, race)`, prefix-parameterised scrapers and race-parameterised card grids.

**Tech Stack:** Lua 5.1 (game and C:\Program Files (x86)\Lua\5.1), Python 3 (py), RPFM MCP for packing

**Spec:** docs/superpowers/specs/2026-10-04-iron-court-dwarfs-design.md (and the CONTRACT file docs/superpowers/plans/2026-10-04-iron-court-dwarfs-CONTRACT.md)

## Global Constraints

- Not a git repo: every task ends in a **checkpoint** that runs the gates; nothing is committed.
- Run everything from the workspace root `G:\Modding for resources` in Git Bash (the mutation runner reports a false "harness not green" from `tools/`).
- Line numbers are the files as they stood on 2026-10-04 before Task 1; earlier tasks move them. Match on the quoted code, never on the number.
- The Chaos Dwarf tables stay where and as they are: same names, same column-0 `}` closers (the `IC\.X = \{(.*?)\n\}` scrapers and the harness depend on it).
- The race is never saved; it is the faction's subculture. No save field changes in this phase.
- Chaos Dwarf infix is `""`: every Chaos Dwarf bundle, trait and loc key stays byte-identical.
- Zero behaviour change for a Chaos Dwarf court. Baselines (measured 2026-10-04): harness `iron court harness: ok (974 checks)`; `py tools/gen_iron_court.py --check` -> `ok: 73 bundles, 112 junctions, 146 traits, 1116 loc rows`; `--selftest` -> `selftest: ok (73 bundles, 112 junctions, 146 traits, 1116 loc)`; `py tools/gen_ic_ui.py --check` -> `ok: 28 files, 1054 components`; `--selftest` -> `selftest: ok (28 files, 1054 components, 3981 guids)`; `py tools/import_iron_court.py` -> `verify ok - 73 bundles, 112 junctions, 146 traits, 1116 loc, 6 script(s), 28 ui file(s), 1740 generated png(s)`; `check_lua_api` -> `4 file(s), 0 suspect call(s)`; `check_lua_literal_left` -> `4 file(s), 0 literal-left site(s)`.
- Harness count after each task: Task 2 977, Task 3 978, Task 4 980, Task 5 981, Task 6 983, Task 7 983, Task 8 984.
- New harness checks go in one section inserted directly above the line `-- THE PREVIEW'S DEMO (plan 2026-10-02 laws, Task 10): with IC_DUMP set, draw` in `tools/_iron_court_harness.lua`; each later task appends its checks at the end of that section (still above that line).
- The harness main chunk holds 142 top-level locals of Lua 5.1's 200; this plan adds 7 (`TST_F`, `test_race`, `with_test_race`, `RACE_ARITY`, `top_level_args`, `RACE_SCAN_FILES`, `RACE_SCAN_ALLOW`). Add no others.
- Lua 5.1 with the game's miscompile: no number literal on the LEFT of an arithmetic operator (`py tools/check_lua_literal_left.py`).
- No loc call in the model; names resolve in the panel.
- Every new check is watched failing for its own reason before the code that passes it is written.
- After `tools/mutate_iron_court.py`, re-run both generators: the runner restores the source, not what that source wrote.
- Build and deploy only with `py tools/deploy_iron_court.py` (needs RPFM open; backs up to `Modding Files/Backup/`; deploys to data/ only while Warhammer3.exe is shut, `--wait` otherwise). There is no Workshop copy of `derpy_iron_court.pack` (checked 2026-10-04), so there is no Workshop step.
- No emojis; never the word "rung"; player text in plain words. This phase writes no player text.
- No new DB key in this phase; nothing to verify against `db.pack`.
- Every touched UI view is rendered with `tools/preview_iron_court.py` from the shipped Lua; this phase must render byte-identical pictures (Task 12), and any difference goes to the author before it ships.

## Review Focus

1. **A failed race lookup kept for the session.** `cm:get_faction` fails before the world exists; a cache that kept the Chaos Dwarf fallback then would run a Dwarf court on Chaos Dwarf tables until reload. Pinned in Task 2 (check "race plumbing: a faction's race comes from its subculture, and only a found one is kept").
2. **A reading site left on `IC.X`.** It is identical for every Chaos Dwarf court, so no behaviour check of this phase can see it. Pinned by the source scan in Tasks 6-8 (check "race plumbing: no site reads a race table off IC").
3. **A keyed helper called without the faction.** `IC.office_bundle(slug)` silently answers the Chaos Dwarf key for any court. Pinned by the arity scan in Tasks 4-5 (check "race plumbing: every call of a keyed helper names the faction").
4. **The race layer applied over the government, or written into `IC.TUNE`.** Kinship's x1.5 must sit under the government's override and leave `IC.TUNE` alone. Pinned in Task 3 (check "race plumbing: IC.tune layers the race under the government").
5. **The dial sized before a race registers, or not sized for the larger race.** The panel creates one seat component per `IC.MAX_SEATS` at load. Pinned in Task 2 (check "race plumbing: a second race derives its own tiers and the seat count sizes for the larger").

---

### Task 1: Baseline snapshot of every generated file and gate line

**Files:**
- Create: `Modding Files/Backup/ic_phase1_baseline/` (source/, twui/, plates/, preview/, lua/, gates_before.txt)
- Read-only: everything else

**Interfaces:**
- Consumes: nothing.
- Produces: the baseline Tasks 12 and 13 diff against.

- [ ] **Step 1: Write the generated files fresh, so the baseline is the generators' own output.**

```bash
cd "/g/Modding for resources"
py tools/gen_iron_court.py
py tools/gen_ic_ui.py
py tools/preview_iron_court.py
```
Expected: `gen_iron_court` ends with `wrote ...loc.tsv` lines, `gen_ic_ui` ends with `ok: 28 files, 1054 components` and `wrote ...` lines, the preview writes `ic_*.png` under `.skilltree_cache/ui_preview/`.

- [ ] **Step 2: Copy them out.**

```bash
B="Modding Files/Backup/ic_phase1_baseline"
mkdir -p "$B/twui" "$B/lua" "$B/preview"
cp -r "Modding Files/source/iron_court" "$B/source"
cp "Modding Files/pack/ui/campaign ui/"derpy_ic_*.twui.xml "$B/twui/"
cp -r "Modding Files/pack/ui/derpy_ic" "$B/plates"
cp .skilltree_cache/ui_preview/ic_*.png "$B/preview/"
cp "Modding Files/pack/script/campaign/mod/"zzz_derpy_iron_court*.lua "$B/lua/"
ls "$B/twui" | wc -l
```
Expected: `28`.

- [ ] **Step 3: Prove the generators are deterministic, or the Task 12 diff means nothing.**

```bash
py tools/gen_iron_court.py > /dev/null
py tools/gen_ic_ui.py > /dev/null
py tools/preview_iron_court.py > /dev/null
diff -r "Modding Files/source/iron_court" "$B/source" && echo SOURCE-SAME
for f in "$B/twui/"*.twui.xml; do cmp "$f" "Modding Files/pack/ui/campaign ui/$(basename "$f")" || echo "DIFF $f"; done; echo TWUI-CHECKED
diff -r "Modding Files/pack/ui/derpy_ic" "$B/plates" && echo PLATES-SAME
for f in "$B/preview/"*.png; do cmp "$f" ".skilltree_cache/ui_preview/$(basename "$f")" || echo "DIFF $f"; done; echo PREVIEW-CHECKED
```
Expected: `SOURCE-SAME`, `TWUI-CHECKED` with no `DIFF` line, `PLATES-SAME`, `PREVIEW-CHECKED` with no `DIFF` line. A `DIFF` here is a pre-existing non-determinism: stop and report it, do not start Task 2.

- [ ] **Step 4: Record every gate line.**

```bash
{
"/c/Program Files (x86)/Lua/5.1/lua.exe" tools/_iron_court_harness.lua 2>&1 | tail -1
py tools/gen_iron_court.py --check 2>&1 | tail -1
py tools/gen_iron_court.py --selftest 2>&1 | tail -1
py tools/gen_ic_ui.py --check 2>&1 | tail -1
py tools/gen_ic_ui.py --selftest 2>&1 | tail -1
py tools/import_iron_court.py 2>&1 | head -1
py tools/import_iron_court.py --selftest 2>&1 | tail -1
py tools/mutate_iron_court.py --selftest 2>&1 | tail -1
} > "$B/gates_before.txt"
cat "$B/gates_before.txt"
```
Expected: the baselines listed under Global Constraints, and `selftest ok: 1097 mutants all anchored, ...`.

---

### Task 2: The race registry and its accessors

**Files:**
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court.lua` - delete lines 49-52 (`IC.MAX_SEATS` loop), 381-387 (`IC.TIER_SEATS`/`IC.TIERS` loop), 2400-2404 (`IC.PARTY_OF_BG` loop); rewrite `IC.is_chd` (2271-2274) and the first line of `IC.runs_court` (2279); lines 7041, 7084, 7278; insert the race block above `-- THE MODEL'S FIRST TICK, named so the harness can drive it` (~7267).
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_ui.lua:1973` (`ICUI.court_player`).
- Test: `tools/_iron_court_harness.lua` - `make_faction` (257), new section above the PREVIEW'S DEMO line.

**Interfaces:**
- Consumes: the existing `IC.X` tables, `real_faction` (model local, line 1916), `IC.CHD_SUBCULTURE`.
- Produces: `IC.RACE_FIELDS` (array of the 22 field names, ADDED to the contract: the scan reads it and phase 2's Dwarf table must define every one), `IC.RACES`, `IC.RACE_ORDER`, `IC._race_cache`, `IC.build_race(r) -> r`, `IC.register_race(r) -> r` (builds, stores, APPENDS `r.key` to `IC.RACE_ORDER` on first registration, raises `IC.MAX_SEATS` to the largest race's), `IC.race_of(faction) -> race | nil`, `IC.race_key(faction_key) -> "chd" | nil`, `IC.R(faction_key) -> race` (chd for nil or no race; caches only a found race), `IC.has_court(faction) -> bool`, `IC.is_chd(faction)` (kept, chd race only). Race-table field ADDED to the contract: `switch` - an `IC.TUNE` switch name that turns the race's courts on (nil = always; phase 2 sets `switch = "dwarf_courts"`). `IC.TIERS`, `IC.TIER_SEATS`, `IC.PARTY_OF_BG` stay as aliases of the chd race's derived tables; `IC.MAX_SEATS` becomes the largest race's count.

- [ ] **Step 1: Clear a re-made faction's cached race in the harness.** In `make_faction` (line 257), directly after `    local f`, add:

```lua
    -- A FACTION RE-MADE IS ASKED ITS RACE AGAIN (plan 2026-10-04 phase 1): one
    -- check makes F Bretonnian, and a cached Chaos Dwarf race must not outlive it.
    if IC and IC._race_cache then IC._race_cache[name] = nil end
```

- [ ] **Step 2: Write the test race and the three failing checks.** Insert above the PREVIEW'S DEMO line:

```lua
-- ---------------------------------------------------------------------------
-- RACE PLUMBING (plan 2026-10-04 phase 1). TST_F's race is the one phase 2's
-- Dwarf file will register, in miniature: the Chaos Dwarf tables under another
-- subculture and infix, the offices re-tiered 2/4/4/4 (the Warden of the Roads
-- up to II and the Muster up to III, as the Dwarf hall seats them), its own
-- origins, backgrounds, legend and name words, and the Labour laws renamed
-- Craft. A site still reading IC.X answers this court with a Chaos Dwarf tier,
-- slug or key, and the checks below see it.
-- ---------------------------------------------------------------------------
local TST_F = "tst_karak"

local function test_race()
    local chd = IC.RACES.chd
    local t = {key = "tst", subculture = "tst_sc", infix = "tst_",
               tune = {secede_turns = {mul = 1.5}}, layout = "grid", art = {}}
    for _, k in ipairs(IC.RACE_FIELDS) do t[k] = chd[k] end
    local tier = {priest = 1, forge = 1, ledger = 2, warden = 2, hand = 2, roads = 2,
                  chains = 3, pits = 3, quarry = 3, muster = 3,
                  kilns = 4, fields = 4, scribes = 4, banners = 4}
    local order = {"priest", "forge", "ledger", "warden", "hand", "roads", "chains",
                   "pits", "quarry", "muster", "kilns", "fields", "scribes", "banners"}
    t.OFFICES = {}
    for _, slug in ipairs(order) do
        for _, o in ipairs(chd.OFFICES) do
            if o.slug == slug then
                t.OFFICES[#t.OFFICES + 1] = {slug = slug, affinity = o.affinity, tier = tier[slug]}
            end
        end
    end
    t.ORIGINS = {{slug = "tkarak", faction = TST_F}, {slug = "thold"}}
    t.BACKGROUNDS = {}
    for party, list in pairs(chd.BACKGROUNDS) do
        t.BACKGROUNDS[party] = {}
        for i, bg in ipairs(list) do t.BACKGROUNDS[party][i] = "t" .. bg end
    end
    t.NAME_HEADS = {"Kin"}
    t.NAME_TAILS = {}
    for party, tails in pairs(chd.NAME_TAILS) do t.NAME_TAILS[party] = tails end
    t.NAME_TAILS.temple = {"the Test Hall"}
    t.LEGEND_SUBTYPES = {tst_legend = true}
    t.LAW_ORDER = {"craft", "tribute", "worship", "war"}
    t.LAWS = {craft = chd.LAWS.labour, tribute = chd.LAWS.tribute,
              worship = chd.LAWS.worship, war = chd.LAWS.war}
    t.START_GOV = {[TST_F] = "forge"}
    return t
end

-- REGISTERED FOR ONE CHECK, and taken out again whatever the check did.
local function with_test_race(fn, race)
    local saved_max = IC.MAX_SEATS
    local t = race or test_race()
    IC.register_race(t)
    local ok, err = pcall(fn, t)
    IC.RACES[t.key] = nil
    for i = #IC.RACE_ORDER, 1, -1 do
        if IC.RACE_ORDER[i] == t.key then table.remove(IC.RACE_ORDER, i) end
    end
    IC.MAX_SEATS = saved_max
    IC._race_cache = {}
    if not ok then error(err, 0) end
end

check("race plumbing: the Chaos Dwarf race is registered over the existing tables", function()
    local chd = IC.RACES.chd
    assert(chd and IC.RACE_ORDER[1] == "chd", "the Chaos Dwarfs are not the first race")
    assert(chd.subculture == IC.CHD_SUBCULTURE and chd.infix == "" and chd.layout == "ziggurat",
        "the Chaos Dwarf race's own fields are wrong")
    -- THE SAME TABLES, not copies: a copy would let a harness edit of IC.X miss
    -- the race, and the references here would be testing a twin.
    for _, k in ipairs(IC.RACE_FIELDS) do
        assert(chd[k] == IC[k], k .. " on the race is not IC." .. k)
    end
    assert(IC.TIERS == chd.TIERS and IC.TIER_SEATS == chd.TIER_SEATS
           and IC.PARTY_OF_BG == chd.PARTY_OF_BG, "the old names are not the race's tables")
    local widths = {}
    for _, t in ipairs(chd.TIERS) do widths[#widths + 1] = chd.TIER_SEATS[t] end
    assert(table.concat(widths, "/") == "2/3/4/5", "the ziggurat is " .. table.concat(widths, "/"))
    assert(chd.PARTY_OF_BG.ashpriest == "temple", "a background maps to " .. tostring(chd.PARTY_OF_BG.ashpriest))
    assert(IC.MAX_SEATS == chd.MAX_SEATS, "the seat count is not the Chaos Dwarfs'")
end)

check("race plumbing: a faction's race comes from its subculture, and only a found one is kept", function()
    with_test_race(function(T)
        factions = {}
        make_faction(F, IC.CHD_SUBCULTURE, {}, {})
        make_faction(TST_F, T.subculture, {}, {})
        local brt = make_faction("wh_main_brt_bretonnia", "wh_main_sc_brt_bretonnia", {}, {})
        assert(IC.R(F) == IC.RACES.chd and IC.R(TST_F) == T, "IC.R answered the wrong race")
        assert(IC.race_key(F) == "chd" and IC.race_key(TST_F) == "tst"
               and IC.race_key("wh_main_brt_bretonnia") == nil, "race_key is wrong")
        assert(IC.R(nil) == IC.RACES.chd and IC.R("wh_main_brt_bretonnia") == IC.RACES.chd,
            "a faction with no race is not answered as the Chaos Dwarfs")
        local tst = cm:get_faction(TST_F)
        assert(IC.has_court(tst) and not IC.is_chd(tst), "the second race holds no court, or is Chaos Dwarf")
        assert(IC.is_chd(cm:get_faction(F)) and not IC.has_court(brt), "is_chd or has_court is wrong")
        -- A RACE SWITCHED OFF holds no court.
        T.switch, IC.TUNE.tst_courts = "tst_courts", false
        local on = IC.has_court(tst)
        T.switch, IC.TUNE.tst_courts = nil, nil
        assert(not on, "a race switched off still holds a court")
        -- A LOOKUP THAT FAILS IS NOT KEPT: before the world exists cm:get_faction
        -- errors, and a court that cached the fallback then would run on it.
        IC._race_cache = {}
        local real = cm.get_faction
        cm.get_faction = function() error("no world yet") end
        local early = IC.R(TST_F)
        cm.get_faction = real
        assert(early == IC.RACES.chd, "a failed lookup answered " .. tostring(early and early.key))
        assert(IC.R(TST_F) == T, "the failed lookup was kept")
        -- AND A FACTION RE-MADE AS ANOTHER RACE is asked again.
        make_faction(TST_F, IC.CHD_SUBCULTURE, {}, {})
        assert(IC.R(TST_F) == IC.RACES.chd, "a cached race outlived its faction")
    end)
end)

check("race plumbing: a second race derives its own tiers and the seat count sizes for the larger", function()
    with_test_race(function(T)
        local widths = {}
        for _, t in ipairs(T.TIERS) do widths[#widths + 1] = T.TIER_SEATS[t] end
        assert(table.concat(widths, "/") == "2/4/4/4", "the hall's tiers are " .. table.concat(widths, "/"))
        assert(T.PARTY_OF_BG.tashpriest == "temple" and T.PARTY_OF_BG.ashpriest == nil,
            "the second race maps the first race's backgrounds")
        assert(T.MAX_SEATS == #T.PARTIES + 1, "the second race seats " .. tostring(T.MAX_SEATS))
        assert(IC.MAX_SEATS == IC.RACES.chd.MAX_SEATS, "a smaller race moved the seat count")
    end)
    -- A LARGER RACE RAISES IT: the panel makes one dial seat per IC.MAX_SEATS at load.
    local big = test_race()
    big.key, big.subculture = "big", "big_sc"
    big.ORIGINS = {}
    for i = 1, IC.RACES.chd.MAX_SEATS do big.ORIGINS[i] = {slug = "b" .. i, faction = "big_" .. i} end
    with_test_race(function(B)
        assert(B.MAX_SEATS > IC.RACES.chd.MAX_SEATS and IC.MAX_SEATS == B.MAX_SEATS,
            "the seat count is " .. tostring(IC.MAX_SEATS) .. " beside a race of " .. tostring(B.MAX_SEATS))
    end, big)
    assert(IC.MAX_SEATS == IC.RACES.chd.MAX_SEATS, "the larger race's count outlived it")
    -- EVERY REGISTERED RACE FITS THE DIAL THE PANEL MADE AT LOAD.
    for _, k in ipairs(IC.RACE_ORDER) do
        assert(ICUI.MAX_HOUSES >= IC.RACES[k].MAX_SEATS, k .. " has more seats than the dial")
    end
end)
```

- [ ] **Step 3: Run and watch them fail.**

Run: `IC_ONLY="race plumbing" IC_TEST_ALL=1 "/c/Program Files (x86)/Lua/5.1/lua.exe" tools/_iron_court_harness.lua 2>&1 | grep "^FAIL"`
Expected: three lines, each `FAIL race plumbing: ...: ... attempt to index field 'RACES' (a nil value)` (or `'chd'`).

- [ ] **Step 4: Delete the three load-time derivations.** Remove these blocks from the model, exactly:

```lua
IC.MAX_SEATS = #IC.PARTIES
for i = 1, #IC.ORIGINS do
    if IC.ORIGINS[i].faction then IC.MAX_SEATS = IC.MAX_SEATS + 1 end
end
```
```lua
IC.TIER_SEATS = {}
IC.TIERS = {}
for i = 1, #IC.OFFICES do
    local t = IC.OFFICES[i].tier
    if not IC.TIER_SEATS[t] then IC.TIERS[#IC.TIERS + 1] = t end
    IC.TIER_SEATS[t] = (IC.TIER_SEATS[t] or 0) + 1
end
```
```lua
IC.PARTY_OF_BG = {}
for i = 1, #IC.PARTIES do
    local list = IC.BACKGROUNDS[IC.PARTIES[i]]
    for j = 1, #list do IC.PARTY_OF_BG[list[j]] = IC.PARTIES[i] end
end
```

- [ ] **Step 5: Insert the race block** directly above `-- THE MODEL'S FIRST TICK, named so the harness can drive it: the harness's cm`:

```lua
-- ---------------------------------------------------------------------------
-- THE RACES (plan 2026-10-04 phase 1; spec 2026-10-04 Dwarfs section 9). A
-- court reads its tables off its faction's race, R = IC.R(faction_key), never
-- off IC.X. The Chaos Dwarf race IS the IC.X tables above - the same tables,
-- not copies - so every scraper and harness reference to them still holds. The
-- race is never saved: it is the faction's subculture.
-- ---------------------------------------------------------------------------
IC.RACE_FIELDS = {
    "ORIGINS", "PARTIES", "OFFICES", "GOVS", "GOV_ORDER", "START_GOV", "LAWS",
    "LAW_ORDER", "DEEDS", "REBEL_POOL", "REBEL_POOLS", "REBEL_GENERALS",
    "REBEL_HEROES", "REBEL_DRAFT", "BACKGROUNDS", "NAME_HEADS", "NAME_TAILS",
    "PARTY_TRAITS", "LEADER_TRAITS", "LEGEND_SUBTYPES", "TEMPLE_BUILDINGS",
    "MILITARY_DOCTRINE",
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
function IC.has_court(faction)
    local r = IC.race_of(faction)
    return r ~= nil and (r.switch == nil or IC.TUNE[r.switch] ~= false)
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
```

- [ ] **Step 6: Route the Chaos Dwarf test through the race.** Replace `IC.is_chd` (2271-2274) with:

```lua
function IC.is_chd(faction)
    local r = IC.race_of(faction)
    return r ~= nil and r.key == "chd"
end
```
In `IC.runs_court` replace `    if not IC.is_chd(faction) then return false end` with `    if not IC.has_court(faction) then return false end`, and its comment's first line `-- A CHAOS DWARF FACTION WHOSE COURT THIS CAMPAIGN RUNS. With the ai_courts` with `-- A FACTION WHOSE RACE HOLDS A COURT THIS CAMPAIGN RUNS. With the ai_courts`. Then:

| line | before | after |
|---|---|---|
| 7041 (`ic_turn`) | `            if IC.is_chd(faction) then` | `            if IC.race_of(faction) then` |
| 7084 (`ic_born`) | `        if IC.is_chd(faction) and IC.court_rolled(faction_key) then` | `        if IC.has_court(faction) and IC.court_rolled(faction_key) then` |
| 7278 (`IC.first_tick`) | `        if IC.is_chd(faction) then` | `        if IC.has_court(faction) then` |
| ui 1973 (`ICUI.court_player`) | `    return IC.is_chd(f)` | `    return IC.has_court(f)` |

(7041 asks `race_of`, not `has_court`: a court whose race was switched off is still dismantled there.)

- [ ] **Step 7: Run and watch them pass.**

Run: `"/c/Program Files (x86)/Lua/5.1/lua.exe" tools/_iron_court_harness.lua 2>&1 | tail -1`
Expected: `iron court harness: ok (977 checks)`.

- [ ] **Step 8: Checkpoint.**

```bash
for f in "Modding Files/pack/script/campaign/mod/"zzz_derpy_iron_court*.lua; do "/c/Program Files (x86)/Lua/5.1/luac.exe" -p "$f" || echo "LUAC FAIL $f"; done
M="Modding Files/pack/script/campaign/mod"
py tools/check_lua_api.py "$M/zzz_derpy_iron_court.lua" "$M/zzz_derpy_iron_court_parties.lua" "$M/zzz_derpy_iron_court_ui.lua" "$M/zzz_derpy_iron_court_ui_map.lua" | tail -1
py tools/check_lua_literal_left.py "$M/zzz_derpy_iron_court.lua" "$M/zzz_derpy_iron_court_parties.lua" "$M/zzz_derpy_iron_court_ui.lua" "$M/zzz_derpy_iron_court_ui_map.lua" | tail -1
py tools/gen_iron_court.py --check | tail -1
py tools/gen_ic_ui.py --check | tail -1
py tools/gen_ic_ui.py --selftest | tail -1
py tools/import_iron_court.py | head -1
```
Expected: no `LUAC FAIL`; `4 file(s), 0 suspect call(s)`; `4 file(s), 0 literal-left site(s)`; `ok: 73 bundles, 112 junctions, 146 traits, 1116 loc rows`; `ok: 28 files, 1054 components`; `selftest: ok (28 files, 1054 components, 3981 guids)`; `verify ok - 73 bundles, ...` (`import_iron_court.py` runs `check_lua_undeclared` over the set). Every later checkpoint runs this same block with the harness line from its own task.

---

### Task 3: The race layer in `IC.tune`

**Files:**
- Modify: `zzz_derpy_iron_court.lua:917-929` (`IC.tune`)
- Test: `tools/_iron_court_harness.lua` (race plumbing section)

**Interfaces:**
- Consumes: `IC.R`, race field `tune` (Task 2).
- Produces: `IC.tune(faction_key, key)` = `IC.TUNE[key]`, then the race's `tune[key]`, then the government's `over[key]`; a number replaces, `{mul = x}` scales (a table knob entry by entry), rounded. Phase 4 puts the x1.5 secession knobs in the dwf race's `tune`.

- [ ] **Step 1: Write the failing check** (append to the section):

```lua
check("race plumbing: IC.tune layers the race under the government", function()
    with_test_race(function(T)
        IC.state = {}
        factions = {}
        make_faction(TST_F, T.subculture, {}, {})
        make_faction(F, IC.CHD_SUBCULTURE, {}, {})
        local base = IC.TUNE.secede_turns
        assert(IC.tune(TST_F, "secede_turns") == math.floor(base * 1.5 + 0.5),
            "the race's x1.5 gave " .. tostring(IC.tune(TST_F, "secede_turns")))
        assert(IC.tune(F, "secede_turns") == base, "the Chaos Dwarfs took the other race's layer")
        assert(IC.TUNE.secede_turns == base, "the layer wrote into IC.TUNE")
        -- UNDER THE GOVERNMENT: the Conclave's {mul = 0.6} scales the race's
        -- value, and its renew_wait = 1 replaces the race's.
        T.tune.term_turns = {mul = 2}
        T.tune.renew_wait = 9
        IC_GOVS_ON = true
        IC.add_house(TST_F, IC.CROWN)
        IC.court(TST_F).gov = "conclave"
        local term, wait = IC.tune(TST_F, "term_turns"), IC.tune(TST_F, "renew_wait")
        IC_GOVS_ON = nil
        local want = math.floor(math.floor(IC.TUNE.term_turns * 2 + 0.5) * 0.6 + 0.5)
        assert(term == want, "race then government gave " .. tostring(term) .. ", not " .. want)
        assert(wait == 1, "the government's number did not replace the race's: " .. tostring(wait))
    end)
end)
```

- [ ] **Step 2: Run and watch it fail.**

Run: `IC_ONLY="race plumbing" "/c/Program Files (x86)/Lua/5.1/lua.exe" tools/_iron_court_harness.lua 2>&1 | grep "^FAIL"`
Expected: `FAIL race plumbing: IC.tune layers the race under the government: ... the race's x1.5 gave 5`.

- [ ] **Step 3: Implement.** Replace `IC.tune` (917-929) with:

```lua
-- ONE OVERRIDE ON A VALUE: a number replaces it, {mul = x} scales it (a table
-- knob entry by entry), rounded.
local function tune_over(base, o)
    if type(o) == "number" then return o end
    if type(base) == "table" then
        local out = {}
        for k, v in pairs(base) do out[k] = math.floor(v * o.mul + 0.5) end
        return out
    end
    return math.floor(base * o.mul + 0.5)
end

-- IC.TUNE, then the race's own layer (kinship, phase 4), then the government's.
function IC.tune(faction_key, key)
    local base = IC.TUNE[key]
    local r = faction_key and IC.R(faction_key).tune[key]
    if r ~= nil then base = tune_over(base, r) end
    local row = IC.gov_row(faction_key)
    local o = row and row.over[key]
    if o == nil then return base end
    return tune_over(base, o)
end
```

- [ ] **Step 4: Run and watch it pass.**

Run: `"/c/Program Files (x86)/Lua/5.1/lua.exe" tools/_iron_court_harness.lua 2>&1 | tail -1`
Expected: `iron court harness: ok (978 checks)`.

- [ ] **Step 5: Checkpoint.** Run the Task 2 Step 8 block. Expected: its lines unchanged; harness 978.

---

### Task 4: Keys carry the race's infix

**Files:**
- Modify: `zzz_derpy_iron_court.lua` - race block (new `IC.rkey`, `IC.key`, `IC.origin_trait`, `IC.bg_trait`); builders 810, 862-864, 1377-1379, 3184-3186, 3589, 4251; `IC.origin_of_character` 2378-2385; `IC.bg_of_character` 2387-2398; `IC.house_of_character` 2416-2418; `IC.MEMBER_TRAIT` 3239 (delete); `IC.member_trait` 3241-3252; `IC.member_trait_keys` 3255-3269; trait-literal and builder call sites listed in Step 5.
- Modify: `zzz_derpy_iron_court_ui.lua` - loc and builder sites listed in Step 6.
- Modify: `tools/gen_iron_court.py:2478-2486` (`check_governments` reads the new `IC.gov_bundle`); `tools/import_iron_court.py:1118-1121` (check 3's builder probes).
- Test: `tools/_iron_court_harness.lua`.

**Interfaces:**
- Consumes: `IC.R`, `IC.RACE_ORDER`, race `infix`/`ORIGINS`/`PARTY_OF_BG`.
- Produces: `IC.key(kind, slug, faction_key)` (contract); ADDED: `IC.rkey(kind, slug, R)` (a key from a race table, for lookups that hold a race and no faction; phases 2-3), `IC.origin_trait(slug)` and `IC.bg_trait(slug)` (a trait key from a slug alone; phase 2 MUST keep origin and background slugs unique across races, and adds the check). Signatures gaining a trailing `faction_key`: `IC.gov_bundle(slug, fk)`, `IC.law_bundle(cat, opt, fk)`, `IC.office_title_key(office_slug, fk)`, `IC.office_bundle(slug, fk)`, `IC.vacancy_bundle(slug, fk)`, `IC.office_trait(slug, fk)`, `IC.gov_bundle_house(slug, fk)`, `IC.control_bundle(slug, fk)`, `IC.member_trait_keys(fk)`. `IC.origin_of_character` and `IC.bg_of_character` now return `slug, R` (the race the trait belongs to). Kinds used: `office`, `vacant`, `title`, `doctrine`, `law`, `gov_house`, `control`, `member`, `house`, `bg`, and loc kinds `control_name`, `doctrine_name`, `doctrine_rule`, `law_cat`, `law_name`, `law_fxN`, `origin_name`, `party_name`, `bg_name`.

- [ ] **Step 1: Write the failing checks** (append to the section):

```lua
check("race plumbing: every key the court writes carries its race's infix", function()
    with_test_race(function(T)
        IC.state = {}
        factions = {}
        make_faction(TST_F, T.subculture, {}, {})
        make_faction(F, IC.CHD_SUBCULTURE, {}, {})
        -- THE CHAOS DWARF KEYS ARE TODAY'S, byte for byte: saves and loc name them.
        assert(IC.office_bundle("priest", F) == "derpy_ic_office_priest"
               and IC.vacancy_bundle("priest", F) == "derpy_ic_vacant_priest"
               and IC.office_trait("priest", F) == "derpy_ic_title_priest"
               and IC.gov_bundle("forge", F) == "derpy_ic_doctrine_forge"
               and IC.law_bundle("labour", "lash", F) == "derpy_ic_law_labour_lash"
               and IC.gov_bundle_house("forge", F) == "derpy_ic_gov_house_forge"
               and IC.control_bundle("grip", F) == "derpy_ic_control_grip"
               and IC.bg_trait("ashpriest") == "derpy_ic_bg_ashpriest"
               and IC.origin_trait("khorakk") == "derpy_ic_house_khorakk",
            "a Chaos Dwarf key moved")
        assert(IC.office_bundle("priest", TST_F) == "derpy_ic_office_tst_priest"
               and IC.vacancy_bundle("priest", TST_F) == "derpy_ic_vacant_tst_priest"
               and IC.office_trait("priest", TST_F) == "derpy_ic_title_tst_priest"
               and IC.gov_bundle("forge", TST_F) == "derpy_ic_doctrine_tst_forge"
               and IC.law_bundle("craft", "lash", TST_F) == "derpy_ic_law_tst_craft_lash"
               and IC.gov_bundle_house("forge", TST_F) == "derpy_ic_gov_house_tst_forge"
               and IC.control_bundle("grip", TST_F) == "derpy_ic_control_tst_grip"
               and IC.bg_trait("tashpriest") == "derpy_ic_bg_tst_tashpriest"
               and IC.origin_trait("tkarak") == "derpy_ic_house_tst_tkarak",
            "a key of the second race has no infix")
        -- THE MEMBER TRAITS are the race's own, off its own tails.
        IC.add_house(TST_F, IC.CROWN)
        local keys = {}
        for _, k in ipairs(IC.member_trait_keys(TST_F)) do keys[k] = true end
        assert(keys[IC.member_trait(TST_F, IC.CROWN)] and keys["derpy_ic_member_tst_crown"],
            "the second race's member keys are not its own")
        assert(keys["derpy_ic_member_tst_temple_1"] and not keys["derpy_ic_member_tst_temple_2"]
               and not keys["derpy_ic_member_crown"], "the member keys came off the Chaos Dwarf tails")
        -- A MAN WEARING THE SECOND RACE'S TRAITS IS READ BACK AS ITS.
        local man = make_character(9201, ANY_SEAT, nil, nil)
        man._traits["derpy_ic_bg_tst_tashpriest"] = true
        man._traits["derpy_ic_house_tst_tkarak"] = true
        local bg, R = IC.bg_of_character(man)
        assert(bg == "tashpriest" and R == T, "the background read back as " .. tostring(bg))
        assert(IC.origin_of_character(man) == "tkarak", "the origin read back wrong")
        assert(IC.house_of_character(man) == "temple", "the man's party is " .. tostring(IC.house_of_character(man)))
    end)
end)

-- EVERY CALL OF A KEYED HELPER NAMES THE FACTION (plan 2026-10-04 phase 1).
-- Left off, the helper answers the Chaos Dwarfs for any court: the one failure
-- no Chaos Dwarf check can see. RACE_ARITY[name] is the argument count with the
-- faction. A call split over two lines is not matched; none is today.
local RACE_ARITY = {
    key = 3, rkey = 3, office_bundle = 2, vacancy_bundle = 2, office_trait = 2,
    gov_bundle = 2, law_bundle = 3, gov_bundle_house = 2, control_bundle = 2,
    office_title_key = 2, member_trait_keys = 1,
}

-- THE ARGUMENTS IN A "(...)" %b() HANDED BACK, counted at depth one.
local function top_level_args(inner)
    local depth, n, seen = 0, 0, false
    for i = 1, #inner do
        local c = string.sub(inner, i, i)
        if c == "(" or c == "{" then
            depth = depth + 1
        elseif c == ")" or c == "}" then
            depth = depth - 1
        elseif c == "," and depth == 1 then
            n = n + 1
        elseif depth >= 1 and not string.find(c, "%s") then
            seen = true
        end
    end
    return seen and n + 1 or 0
end

check("race plumbing: every call of a keyed helper names the faction", function()
    local dir = "Modding Files/pack/script/campaign/mod/"
    local bad = {}
    for _, file in ipairs({"zzz_derpy_iron_court.lua", "zzz_derpy_iron_court_parties.lua",
                           "zzz_derpy_iron_court_ui.lua", "zzz_derpy_iron_court_ui_map.lua"}) do
        local n = 0
        for line in io.lines(dir .. file) do
            n = n + 1
            local code = string.gsub(line, "%-%-.*$", "")
            if not string.find(code, "^%s*function ") then
                for name, want in pairs(RACE_ARITY) do
                    for inner in string.gmatch(code, "IC%." .. name .. "(%b())") do
                        if top_level_args(inner) ~= want then
                            bad[#bad + 1] = file .. ":" .. n .. ": " .. string.match(line, "^%s*(.-)%s*$")
                        end
                    end
                end
            end
        end
    end
    assert(#bad == 0, #bad .. " call(s) leave the faction off:\n  " .. table.concat(bad, "\n  "))
end)
```

- [ ] **Step 2: Run and watch them fail.**

Run: `IC_ONLY="race plumbing" IC_TEST_ALL=1 "/c/Program Files (x86)/Lua/5.1/lua.exe" tools/_iron_court_harness.lua 2>&1 | grep -A60 "^FAIL"`
Expected: `FAIL race plumbing: every key the court writes carries its race's infix: ... attempt to call field 'bg_trait' (a nil value)` and `FAIL race plumbing: every call of a keyed helper names the faction: N call(s) leave the faction off:` followed by the call sites of Steps 5 and 6.

- [ ] **Step 3: Add the key functions to the race block**, directly above its `do` registration:

```lua
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
```

- [ ] **Step 4: Rewrite the builders and the trait readers.**

```lua
function IC.gov_bundle(slug, faction_key) return IC.key("doctrine", slug, faction_key) end
```
```lua
function IC.law_bundle(category, option, faction_key)
    return IC.key("law", category .. "_" .. option, faction_key)
end
```
```lua
function IC.office_title_key(office_slug, faction_key)
    return "effect_bundles_localised_title_" .. IC.office_bundle(office_slug, faction_key)
end
```
```lua
function IC.office_bundle(slug, faction_key)  return IC.key("office", slug, faction_key) end
function IC.vacancy_bundle(slug, faction_key) return IC.key("vacant", slug, faction_key) end
function IC.office_trait(slug, faction_key)   return IC.key("title", slug, faction_key) end
```
```lua
function IC.gov_bundle_house(slug, faction_key) return IC.key("gov_house", slug, faction_key) end
```
```lua
function IC.control_bundle(slug, faction_key) return IC.key("control", slug, faction_key) end
```
```lua
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
```
In `IC.house_of_character` replace

```lua
    local bg = IC.bg_of_character(character)
    if not bg then return nil end
    local party = IC.PARTY_OF_BG[bg]
```
with
```lua
    local bg, R = IC.bg_of_character(character)
    if not bg then return nil end
    local party = R.PARTY_OF_BG[bg]
```
Delete `IC.MEMBER_TRAIT = "derpy_ic_member_"` (3239) and replace `IC.member_trait` / `IC.member_trait_keys` with:

```lua
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
```

- [ ] **Step 5: Name the faction at every model call site.** Each `before` is the code on the line; only the quoted fragment changes.

| line | function | before | after |
|---|---|---|---|
| 892 | `IC.apply_law_bundles` | `IC.law_bundle(cat, opt)` | `IC.law_bundle(cat, opt, faction_key)` |
| 895 | `IC.apply_law_bundles` | `IC.law_bundle(cat, IC.law_in_force(faction_key, cat))` | `IC.law_bundle(cat, IC.law_in_force(faction_key, cat), faction_key)` |
| 2364 | `IC.remove_house` | `IC.office_trait(seats[i])` | `IC.office_trait(seats[i], faction_key)` |
| 2700 | `IC.ensure_leaders` | `"derpy_ic_bg_" .. old` | `IC.bg_trait(old)` |
| 2701 | `IC.ensure_leaders` | `"derpy_ic_bg_" .. list[cm:random_number(#list, 1)]` | `IC.bg_trait(list[cm:random_number(#list, 1)])` |
| 2719 | `IC.ensure_leaders` | `"derpy_ic_bg_" .. bg` | `IC.bg_trait(bg)` |
| 2780 | `IC.field_leader` | `"derpy_ic_bg_" .. old` | `IC.bg_trait(old)` |
| 2781 | `IC.field_leader` | `"derpy_ic_bg_" .. bg` | `IC.bg_trait(bg)` |
| 3059 | `IC.correct_history` | `"derpy_ic_house_" .. has` | `IC.origin_trait(has)` |
| 3061 | `IC.correct_history` | `"derpy_ic_house_" .. want.origin` | `IC.origin_trait(want.origin)` |
| 3068 | `IC.correct_history` | `"derpy_ic_bg_" .. trade` | `IC.bg_trait(trade)` |
| 3070 | `IC.correct_history` | `"derpy_ic_bg_" .. want.bg` | `IC.bg_trait(want.bg)` |
| 3144 | `IC.stamp_origin` | `"derpy_ic_house_" .. slug, not quiet)` | `IC.origin_trait(slug), not quiet)` |
| 3153 | `IC.stamp_bg` | `"derpy_ic_bg_" .. slug, not quiet)` | `IC.bg_trait(slug), not quiet)` |
| 3297 | `IC.stamp_members` | `IC.member_trait_keys()` | `IC.member_trait_keys(faction_key)` |
| 3518 | `IC.appoint` | `IC.office_trait(office_slug)` | `IC.office_trait(office_slug, faction_key)` |
| 3544 | `IC.dismiss` | `IC.office_trait(office_slug)` | `IC.office_trait(office_slug, faction_key)` |
| 3574 | `IC.apply_office_bundles` | `IC.office_bundle(slug)` | `IC.office_bundle(slug, faction_key)` |
| 3575 | `IC.apply_office_bundles` | `IC.vacancy_bundle(slug)` | `IC.vacancy_bundle(slug, faction_key)` |
| 3577 | `IC.apply_office_bundles` | `IC.office_bundle(slug)` | `IC.office_bundle(slug, faction_key)` |
| 3934 | `IC.clear_gov_bundles` | `IC.gov_bundle_house(IC.PARTIES[j])` | `IC.gov_bundle_house(IC.PARTIES[j], faction_key)` |
| 3950 | `IC.dismantle` | `IC.office_bundle(slug)` | `IC.office_bundle(slug, faction_key)` |
| 3951 | `IC.dismantle` | `IC.vacancy_bundle(slug)` | `IC.vacancy_bundle(slug, faction_key)` |
| 3955 | `IC.dismantle` | `IC.office_trait(slug)` | `IC.office_trait(slug, faction_key)` |
| 3960 | `IC.dismantle` | `IC.control_bundle(IC.CONTROL[i].slug)` | `IC.control_bundle(IC.CONTROL[i].slug, faction_key)` |
| 3988 | `IC.apply_governor_bundles` | `IC.gov_bundle_house(slug)` | `IC.gov_bundle_house(slug, faction_key)` |
| 4069 | `IC.expire_terms` | `IC.office_title_key(done[1].slug)` | `IC.office_title_key(done[1].slug, faction_key)` |
| 4096 | `IC.warn_terms` | `IC.office_title_key(ending[1])` | `IC.office_title_key(ending[1], faction_key)` |
| 4229 | `IC.drift_loyalty` | `IC.office_title_key(snub_key)` | `IC.office_title_key(snub_key, faction_key)` |
| 4256 | `IC.apply_control_bundle` | `IC.control_bundle(IC.CONTROL[i].slug)` | `IC.control_bundle(IC.CONTROL[i].slug, faction_key)` |
| 4259 | `IC.apply_control_bundle` | `IC.control_bundle(want)` | `IC.control_bundle(want, faction_key)` |
| 6048 | `IC.apply_gov_bundle` | `IC.gov_bundle(g)` | `IC.gov_bundle(g, faction_key)` |
| 6050 | `IC.apply_gov_bundle` | `IC.gov_bundle(want)` | `IC.gov_bundle(want, faction_key)` |
| 6584 | `IC.end_stalls` | `IC.office_title_key(back[1].slug)` | `IC.office_title_key(back[1].slug, faction_key)` |
| 6772 | `IC.stamp_incoming` | `"derpy_ic_house_" .. had` | `IC.origin_trait(had)` |
| 7245 | listener `ic_dead` | `IC.office_title_key(seats[1])` | `IC.office_title_key(seats[1], faction_key)` |

- [ ] **Step 6: Name the faction at every panel site.** `faction` below is the function's own parameter or local; where the function has none, the player's court is the one drawn, so `ICUI.player()`.

| ui line | function | after (whole line) |
|---|---|---|
| 3523 | `ICUI.band_name(slug)` | `    return loc(IC.key("control_name", slug, ICUI.player()), slug)` |
| 3527 | `ICUI.band_effects(slug)` | `    return loc("derpy_ic_effects_" .. IC.control_bundle(slug, ICUI.player()), "")` |
| 4255 | `ICUI.gov_name(slug)` | `    return loc(IC.key("doctrine_name", tostring(slug), ICUI.player()), tostring(slug))` |
| 4258 | `ICUI.gov_rule(slug)` | `    return loc(IC.key("doctrine_rule", tostring(slug), ICUI.player()), "")` |
| 4268 | `ICUI.gov_fx(slug)` | `    return loc("derpy_ic_effects_" .. IC.gov_bundle(slug, ICUI.player()), "")` |
| 4310 | `ICUI.law_cat_name(category)` | `    return loc(IC.key("law_cat", tostring(category), ICUI.player()), tostring(category))` |
| 4358 | `ICUI.law_short(category, option)` | `    local text = loc("derpy_ic_effects_" .. IC.law_bundle(category, option, ICUI.player()), "")` |
| 4464 | `ICUI.draw_law_pane(panel, faction, cat, opt)` | `        local line = loc(IC.key("law_fx" .. k, cat .. "_" .. opt, faction), "")` |
| 4870 | `ICUI.law_name(category, option)` | `    return loc(IC.key("law_name", tostring(category) .. "_" .. tostring(option), ICUI.player()), tostring(option))` |
| 5260 | `ICUI.draw_offices` | `            local bundle = IC.office_bundle(office.slug, faction)` |
| 5264 | `ICUI.draw_offices` | `                         .. IC.office_bundle(office.slug, faction), office.slug))` |
| 5554 | `ICUI.house_name` | `            return loc(IC.key("origin_name", slug, faction_key), slug)` |
| 5559 | `ICUI.house_name` | `    return loc(IC.key("party_name", slug, faction_key), slug)` |
| 5612 | `ICUI.office_name(key)` | `    return loc("effect_bundles_localised_title_" .. IC.office_bundle(key, ICUI.player()), key)` |
| 5643 | `ICUI.logged_name` | `        return loc(IC.key("origin_name", tostring(slug), ICUI.player()), slug)` |
| 7017 | `ICUI.pick_title()` | `            loc("effect_bundles_localised_title_" .. IC.office_bundle(ICUI.pick.key, ICUI.player()),` |
| 7334 | `ICUI.picker_lines(faction, court)` | `                            .. IC.office_bundle(cand.busy.key, faction), cand.busy.key)` |
| 7435 | `ICUI.picker_lines(faction, court)` | `                loc("effect_bundles_localised_title_" .. IC.office_bundle(loses, faction), loses))` |

And `ICUI.bg_name` / `ICUI.origin_name` (5565-5577) become:

```lua
function ICUI.bg_name(character)
    local bg, R = IC.bg_of_character(character)
    if not bg then return nil end
    return loc(IC.rkey("bg_name", bg, R), bg)
end
```
```lua
function ICUI.origin_name(character)
    local origin, R = IC.origin_of_character(character)
    if not origin then return nil end
    return loc(IC.rkey("origin_name", origin, R), origin)
end
```

- [ ] **Step 7: Teach the two Python gates the new builder shape.** In `tools/gen_iron_court.py` `check_governments`, replace

```python
    m = re.search(r'function IC\.gov_bundle\(slug\) return "(\w+)" \.\. slug end', lua)
    stem = m.group(1) if m else None
    built = {r["key"]: r for r in build()["effect_bundles"]}
    icons = model_gov_icons()
    for slug in mine:
        row = built.get((stem or "?") + slug)
        if not row:
            out.append("the model applies %s%s and no such bundle is built" % (stem, slug))
```
with
```python
    m = re.search(r'function IC\.gov_bundle\(slug, faction_key\) return '
                  r'IC\.key\("(\w+)", slug, faction_key\) end', lua)
    kind = m.group(1) if m else "?"
    built = {r["key"]: r for r in build()["effect_bundles"]}
    icons = model_gov_icons()
    for slug in mine:
        key = bundle_key(kind, slug)
        row = built.get(key)
        if not row:
            out.append("the model applies %s and no such bundle is built" % key)
```
In `tools/import_iron_court.py` `verify()` check 3, replace

```python
        for prefix in ('"derpy_ic_office_"', '"derpy_ic_vacant_"',
                       '"derpy_ic_gov_house_"'):
```
with
```python
        for prefix in ('IC.key("office"', 'IC.key("vacant"', 'IC.key("gov_house"'):
```
(Check 4's literal trait scan now finds no literal at all: every trait key is built. The harness check above is what holds the keys now.)

- [ ] **Step 8: Run and watch them pass.**

Run: `"/c/Program Files (x86)/Lua/5.1/lua.exe" tools/_iron_court_harness.lua 2>&1 | tail -1`
Expected: `iron court harness: ok (980 checks)`.

- [ ] **Step 9: Checkpoint.** Run the Task 2 Step 8 block. Expected: unchanged lines (in particular `gen_iron_court.py --check` still `ok: 73 bundles, ...` and the importer `verify ok - ...`); harness 980.

---

### Task 5: Lookups by slug take the faction; lookups by a race-free key ask every race

**Files:**
- Modify: `zzz_derpy_iron_court.lua` - helper bodies 84-96, 865-884, 901-908, 1526-1553, 2300-2305, 2524-2528, 3076-3084, 3337-3347, 3412-3414, 3482-3483, 4462-4466, 4587-4602, 5634-5640 (+ new local above it), 6491-6506, 6681-6688; call sites in Step 5.
- Modify: `zzz_derpy_iron_court_parties.lua:1021`; `zzz_derpy_iron_court_ui.lua` call sites in Step 5.
- Modify: `tools/import_iron_court.py:586` (`check_rollers`) and `_selftest` (814).
- Test: `tools/_iron_court_harness.lua` (new check; `RACE_ARITY` extended).

**Interfaces:**
- Consumes: `IC.R`, `IC.RACE_ORDER`, `IC.RACES` (Task 2).
- Produces (contract): `IC.office_by_slug(slug, fk)`, `IC.law_opt(cat, opt, fk)`, `IC.is_party(slug, fk)`, `IC.rolled_name(slug, head, tail, fk)` - CONTRACT CORRECTION: the contract writes `rolled_name(head, tail, faction_key)`; the shipped function takes the party slug first, so the faction is appended after `tail`. ADDED trailing `faction_key` on `IC.law_stance(cat, opt, party, fk)`, `IC.gov_for_party(slug, fk)`, `IC.office_influence(office_slug, fk)`, `IC.office_rank(office_slug, fk)`, `IC.office_weight(office_slug, slug, fk)`, `IC.recruit_influence(rank, fk)`, `IC.rebel_draw(count, fk)`, `IC.roll_origin(fk)`, `IC.origin_for(character, fk)`, `IC.chd_factions(fk)` (the name is historic: it answers the living factions of the court's own race). Asked of every race: `IC.faction_for_origin`, `IC.origin_for_faction`, `IC.is_legend`, `IC.can_defect_hero`, `IC.can_defect`, `IC.rebel_rename_all`.

- [ ] **Step 1: Write the failing check and extend the arity table.** In `RACE_ARITY` add (inside its braces):

```lua
    office_by_slug = 2, law_opt = 3, law_stance = 4, is_party = 2, rolled_name = 4,
    gov_for_party = 2, office_influence = 2, office_rank = 2, office_weight = 3,
    recruit_influence = 2, rebel_draw = 2, roll_origin = 1, origin_for = 2,
    chd_factions = 1,
```
Append to the section:

```lua
check("race plumbing: a lookup by slug answers the faction's own race", function()
    with_test_race(function(T)
        IC.state = {}
        factions = {}
        make_faction(TST_F, T.subculture, {}, {})
        make_faction(F, IC.CHD_SUBCULTURE, {}, {})
        -- THE SAME SLUG, ANOTHER TIER: the Warden of the Roads sits on II in the
        -- hall and on III on the ziggurat.
        assert(IC.office_by_slug("roads", TST_F).tier == 2 and IC.office_by_slug("roads", F).tier == 3,
            "office_by_slug read one race for both")
        assert(IC.office_influence("roads", TST_F) == IC.tier_influence(2)
               and IC.office_rank("roads", TST_F) == IC.tier_rank(2)
               and IC.office_influence("roads", F) == IC.tier_influence(3),
            "a seat's bar is not its race's tier")
        assert(IC.law_opt("craft", "lash", TST_F) and not IC.law_opt("craft", "lash", F)
               and IC.law_opt("labour", "lash", F), "law_opt read one race for both")
        assert(IC.law_stance("craft", "lash", "chain", TST_F) == "aye", "law_stance missed the race")
        assert(IC.is_party("temple", TST_F) and not IC.is_party("tkarak", TST_F), "is_party is wrong")
        assert(IC.gov_for_party("forge", TST_F) == "forge", "gov_for_party is wrong")
        assert(IC.rolled_name("temple", 1, 1, TST_F) == "Kin of the Test Hall",
            "the name was rolled off " .. tostring(IC.rolled_name("temple", 1, 1, TST_F)))
        assert(IC.roll_origin(TST_F) == "thold", "the second race rolled a birthplace not its own")
        -- ASKED OF EVERY RACE: an origin slug names its faction, a subtype its legend.
        assert(IC.faction_for_origin("tkarak") == TST_F and IC.origin_for_faction(TST_F) == "tkarak"
               and IC.faction_for_origin("khorakk") == "cr_chd_house_of_khorakk",
            "an origin was not found across the races")
        assert(IC.is_legend(make_character(9202, ANY_SEAT, nil, nil, nil, nil, "tst_legend"))
               and IC.is_legend(make_character(9203, ANY_SEAT, nil, nil, nil, nil, "derpy_warrhak")),
            "a legend of one race was not known")
    end)
end)
```

- [ ] **Step 2: Run and watch it fail.**

Run: `IC_ONLY="race plumbing" IC_TEST_ALL=1 "/c/Program Files (x86)/Lua/5.1/lua.exe" tools/_iron_court_harness.lua 2>&1 | grep -A80 "^FAIL"`
Expected: `FAIL race plumbing: every call of a keyed helper names the faction: N call(s) leave the faction off:` listing the Step 5 sites, and `FAIL race plumbing: a lookup by slug answers the faction's own race: ... office_by_slug read one race for both`.

- [ ] **Step 3: Rewrite the helper bodies.**

```lua
function IC.rebel_rename_all()
    local keys = {}
    for _, rk in ipairs(IC.RACE_ORDER) do
        local R = IC.RACES[rk]
        for i = 1, #R.REBEL_POOL do keys[#keys + 1] = R.REBEL_POOL[i] end
        for i = 1, #R.ORIGINS do
            if R.ORIGINS[i].faction then keys[#keys + 1] = R.ORIGINS[i].faction end
        end
    end
```
(the rest of the function, from `    for i = 1, #keys do`, is unchanged).

```lua
function IC.law_opt(category, option, faction_key)
    local c = IC.R(faction_key).LAWS[category or ""]
    return c and c.opts[option or ""] or nil
end
```
In `IC.law_in_force`: `    if IC.law_opt(category, held, faction_key) then return held end`.

```lua
function IC.law_stance(category, option, party, faction_key)
    local o = IC.law_opt(category, option, faction_key)
```
```lua
function IC.gov_for_party(slug, faction_key)
    local R = IC.R(faction_key)
    for _, g in ipairs(R.GOV_ORDER) do
        for _, p in ipairs(R.GOVS[g].parties) do
            if p == slug then return g end
        end
    end
    return nil
end
```
```lua
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
```
```lua
function IC.office_by_slug(slug, faction_key)
    local R = IC.R(faction_key)
    for i = 1, #R.OFFICES do
        if R.OFFICES[i].slug == slug then return R.OFFICES[i] end
    end
    return nil
end
```
```lua
function IC.is_party(slug, faction_key)
    local R = IC.R(faction_key)
    for i = 1, #R.PARTIES do
        if R.PARTIES[i] == slug then return true end
    end
    return false
end
```
```lua
function IC.origin_for(character, faction_key)
    local fixed = IC.fixed_history(character)
    if fixed and fixed.origin then return fixed.origin end
    return IC.roll_origin(faction_key)
end
```
```lua
function IC.roll_origin(faction_key)
    local R = IC.R(faction_key)
    local places = {}
    for i = 1, #R.ORIGINS do
        if not R.ORIGINS[i].faction then
            places[#places + 1] = R.ORIGINS[i].slug
        end
    end
```
(rest unchanged).

```lua
function IC.office_influence(office_slug, faction_key)
    local office = IC.office_by_slug(office_slug, faction_key)
    if not office then return 0 end
    return IC.tier_influence(office.tier)
end

function IC.office_rank(office_slug, faction_key)
    local office = IC.office_by_slug(office_slug, faction_key)
```
(rest unchanged).

```lua
function IC.recruit_influence(rank, faction_key)
    local ladder = {}
    for _, t in ipairs(IC.R(faction_key).TIERS) do
```
```lua
function IC.office_weight(office_slug, slug, faction_key)
    local office = IC.office_by_slug(office_slug, faction_key)
```
```lua
function IC.rebel_draw(count, faction_key)
```
with, inside it, `local R = IC.R(faction_key)` as the first statement and the two lines

```lua
        local role = R.REBEL_DRAFT[(i - 1) % #R.REBEL_DRAFT + 1]
        local pool = R.REBEL_POOLS[role] or {}
```
```lua
-- EVERY LIVING FACTION OF THE COURT'S OWN RACE, in key order, off its origins.
-- The name is historic: it was the Chaos Dwarfs' list when they had the only court.
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
```
Directly above `function IC.is_legend(character)` add, and use it in the three subtype lookups:

```lua
-- A SUBTYPE KEY NAMES ONE RACE'S CHARACTER, so a lookup by it asks every race.
local function in_any_race(field, key)
    if key == nil then return nil end
    for _, rk in ipairs(IC.RACE_ORDER) do
        local v = IC.RACES[rk][field][key]
        if v ~= nil then return v end
    end
    return nil
end
```
| function | before | after |
|---|---|---|
| `IC.is_legend` | `    return key ~= nil and IC.LEGEND_SUBTYPES[key] == true` | `    return in_any_race("LEGEND_SUBTYPES", key) == true` |
| `IC.can_defect_hero` | `    return key ~= nil and IC.REBEL_HEROES[key] ~= nil` | `    return in_any_race("REBEL_HEROES", key) ~= nil` |
| `IC.can_defect` | `    return key ~= nil and IC.REBEL_GENERALS[key] == true` | `    return in_any_race("REBEL_GENERALS", key) == true` |

```lua
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
```

- [ ] **Step 4: Teach the importer's roller check the new call.** Add to `_selftest()` in `tools/import_iron_court.py`, before its `print`:

```python
    rollers = ('function IC.origin_for(character, faction_key)\n'
               '    return IC.roll_origin(faction_key)\nend\n'
               'function IC.background_for(character, faction_key, tally)\n'
               '    return IC.roll_background(faction_key, tally)\nend\n')
    assert check_rollers(rollers) == [], check_rollers(rollers)
```
Run: `py tools/import_iron_court.py --selftest`
Expected: `AssertionError: ['IC.roll_origin() is called from nowhere ...']`. Then in `check_rollers` replace `(("IC.roll_origin()", "IC.origin_for"),` with `(("IC.roll_origin(", "IC.origin_for"),` and run again. Expected: `import_iron_court selftest: ok`.

- [ ] **Step 5: Name the faction at every call site.**

| file:line | function | before | after |
|---|---|---|---|
| model 1857 | `IC.unpack` | `IC.law_opt(b[1], b[2])` | `IC.law_opt(b[1], b[2], faction_key)` |
| model 1863 | `IC.unpack` | `IC.law_opt(b[1], b[2])` | `IC.law_opt(b[1], b[2], faction_key)` |
| model 1954 | `IC.law_line` | `IC.law_stance(category, vote.option, party)` | `IC.law_stance(category, vote.option, party, faction_key)` |
| model 2027 | `IC.law_win_price` | `IC.law_stance(category, vote.option, man.party)` | `IC.law_stance(category, vote.option, man.party, faction_key)` |
| model 2102 | `IC.law_settle` | `IC.law_opt(category, vote.option)` | `IC.law_opt(category, vote.option, faction_key)` |
| model 2145 | `IC.law_can_propose` | `IC.law_opt(category, option)` | `IC.law_opt(category, option, faction_key)` |
| model 2185 | `IC.law_party_pick` | `IC.law_stance(cat, opt, slug)` | `IC.law_stance(cat, opt, slug, faction_key)` |
| model 2203 | `IC.law_party_push` | `IC.law_stance(category, vote.option, slug)` | `IC.law_stance(category, vote.option, slug, faction_key)` |
| model 2210 | `IC.law_party_push` | `IC.law_stance(category, vote.option, slug)` | `IC.law_stance(category, vote.option, slug, faction_key)` |
| model 2317 | `IC.court_rolled` | `IC.is_party(slug)` | `IC.is_party(slug, faction_key)` |
| model 3107 | `IC.stamp_court` | `IC.origin_for(character)` | `IC.origin_for(character, faction_key)` |
| model 3443 | `IC.price_recruit` | `IC.recruit_influence(character:rank())` | `IC.recruit_influence(character:rank(), faction_key)` |
| model 3449 | `IC.can_appoint` | `IC.office_by_slug(office_slug)` | `IC.office_by_slug(office_slug, faction_key)` |
| model 3454 | `IC.can_appoint` | `IC.office_rank(office_slug)` | `IC.office_rank(office_slug, faction_key)` |
| model 3509 | `IC.appoint` | `IC.office_by_slug(office_slug)` | `IC.office_by_slug(office_slug, faction_key)` |
| model 3523 | `IC.appoint` | `IC.office_weight(office_slug, slug)` | `IC.office_weight(office_slug, slug, faction_key)` |
| model 3550 | `IC.dismiss` | `IC.office_weight(office_slug, slug)` | `IC.office_weight(office_slug, slug, faction_key)` |
| model 4033 | `IC.income` | `IC.office_by_slug(office_slug)` | `IC.office_by_slug(office_slug, faction_key)` |
| model 4228 | `IC.drift_loyalty` | `IC.office_by_slug(snub_key)` | `IC.office_by_slug(snub_key, faction_key)` |
| model 4454 | `IC.rebel_kit` | `IC.rebel_draw(want - #kit)` | `IC.rebel_draw(want - #kit, faction_key)` |
| model 4619 | `IC.rebel_sour_all` | `IC.chd_factions()` | `IC.chd_factions(faction_key)` |
| model 4656 | `IC.rebel_force` | `IC.rebel_draw(IC.TUNE.rebel_units)` | `IC.rebel_draw(IC.TUNE.rebel_units, rebels)` |
| model 4963 | `IC.splinter` | `IC.office_weight(office_slug, IC.CROWN)` | `IC.office_weight(office_slug, IC.CROWN, faction_key)` |
| model 4964 | `IC.splinter` | `IC.office_weight(office_slug, slug)` | `IC.office_weight(office_slug, slug, faction_key)` |
| model 5990 | `IC.plot_costs_seat` | `IC.office_by_slug(office_slug)` | `IC.office_by_slug(office_slug, faction_key)` |
| model 6006 | `IC.enforce_bars` | `IC.office_by_slug(office_slug)` | `IC.office_by_slug(office_slug, faction_key)` |
| model 6042 | `IC.start_gov` | `IC.gov_for_party(best)` | `IC.gov_for_party(best, faction_key)` |
| model 6081 | `IC.gov_pull` | `IC.gov_for_party(top)` | `IC.gov_for_party(top, faction_key)` |
| model 6083 | `IC.gov_pull` | `IC.gov_for_party(top)` | `IC.gov_for_party(top, faction_key)` |
| model 6128 | `IC.party_purse` | `IC.office_by_slug(office_slug)` | `IC.office_by_slug(office_slug, faction_key)` |
| model 6678 | `IC.party_name` | `IC.rolled_name(slug, house.head, house.tail)` | `IC.rolled_name(slug, house.head, house.tail, faction_key)` |
| model 6695 | `IC.reconcile_houses` | `IC.is_party(slug)` | `IC.is_party(slug, faction_key)` |
| model 7085 | listener `ic_born` | `IC.origin_for(character)` | `IC.origin_for(character, faction_key)` |
| model 7226 | listener `ic_dead` | `IC.office_weight(office_slug, slug)` | `IC.office_weight(office_slug, slug, faction_key)` |
| parties 1021 | `IC.backing_target` | `IC.office_rank(office.slug)` | `IC.office_rank(office.slug, faction_key)` |
| ui 4350 | `ICUI.law_icon` | `IC.law_opt(category, option)` | `IC.law_opt(category, option, ICUI.player())` |
| ui 4398 | `ICUI.law_foot` | `IC.law_opt(cat, opt)` | `IC.law_opt(cat, opt, faction)` |
| ui 4468 | `ICUI.draw_law_pane` | `IC.law_opt(cat, opt)` | `IC.law_opt(cat, opt, faction)` |
| ui 4580 | `ICUI.draw_law_board` | `IC.law_opt(sel[1], sel[2])` | `IC.law_opt(sel[1], sel[2], faction)` |
| ui 4875 | `ICUI.law_title` | `IC.law_opt(cat, opt)` | `IC.law_opt(cat, opt, ICUI.player())` |
| ui 5277 | `ICUI.draw_offices` | `IC.office_influence(office.slug)` | `IC.office_influence(office.slug, faction)` |
| ui 5278 | `ICUI.draw_offices` | `IC.office_rank(office.slug)` | `IC.office_rank(office.slug, faction)` |
| ui 5624 | `ICUI.snub_name` | `IC.office_by_slug(key)` | `IC.office_by_slug(key, ICUI.player())` |
| ui 5646 | `ICUI.logged_name` | `IC.rolled_name(slug, tonumber(head), tonumber(tail))` | `IC.rolled_name(slug, tonumber(head), tonumber(tail), ICUI.player())` |
| ui 7006 | `ICUI.pick_cost` | `IC.office_influence(key)` | `IC.office_influence(key, ICUI.player())` |
| ui 7018 | `ICUI.pick_title` | `IC.office_influence(ICUI.pick.key)` | `IC.office_influence(ICUI.pick.key, ICUI.player())` |
| ui 7322 | `ICUI.picker_lines` | `IC.office_rank(ICUI.pick.key)` | `IC.office_rank(ICUI.pick.key, faction)` |

- [ ] **Step 6: Run and watch it pass.**

Run: `"/c/Program Files (x86)/Lua/5.1/lua.exe" tools/_iron_court_harness.lua 2>&1 | tail -1`
Expected: `iron court harness: ok (981 checks)`.

- [ ] **Step 7: Checkpoint.** Run the Task 2 Step 8 block (the importer line now also proves `check_rollers` found `IC.origin_for` as the one caller). Expected: unchanged lines; harness 981.

---

### Task 6: The model reads its tables off the faction's race

**Files:**
- Modify: `zzz_derpy_iron_court.lua` - the sites in Steps 3-5.
- Test: `tools/_iron_court_harness.lua` (two new checks).

**Interfaces:**
- Consumes: `IC.R`, `IC.RACE_FIELDS`, the helpers of Tasks 4-5.
- Produces: no new names. Every model read of a race field is `R.X` with `local R = IC.R(<faction>)`.

**The rewrite rule (Steps 3-5):** in each function listed, add `    local R = IC.R(<faction>)` as the first statement of the body, then on each listed line replace every `IC.<NAME>` with `R.<NAME>` for `NAME` in `IC.RACE_FIELDS` or `TIERS`, `TIER_SEATS`, `PARTY_OF_BG`. Nothing else on the line changes. The scan check below lists exactly the lines left, so a missed one fails the task.

- [ ] **Step 1: Write the failing checks** (append to the section):

```lua
-- EVERY READ OF A RACE TABLE GOES THROUGH THE FACTION'S RACE (plan 2026-10-04
-- phase 1). A site left on IC.X is identical for every Chaos Dwarf court, so no
-- behaviour check of this phase can see it; a Dwarf court would run on it.
-- A file joins RACE_SCAN_FILES when its sites are converted (Tasks 6-8).
-- RACE_SCAN_ALLOW: the trimmed line, and why it may read the Chaos Dwarf table.
local RACE_SCAN_FILES = {"zzz_derpy_iron_court.lua"}
local RACE_SCAN_ALLOW = {}

check("race plumbing: no site reads a race table off IC", function()
    local names = {"TIERS", "TIER_SEATS", "PARTY_OF_BG"}
    for _, k in ipairs(IC.RACE_FIELDS) do names[#names + 1] = k end
    local dir = "Modding Files/pack/script/campaign/mod/"
    local bad = {}
    for _, file in ipairs(RACE_SCAN_FILES) do
        local n = 0
        for line in io.lines(dir .. file) do
            n = n + 1
            local code = string.gsub(line, "%-%-.*$", "")
            local text = string.match(code, "^%s*(.-)%s*$")
            -- A TABLE'S OWN DEFINITION, at column 0, is where it lives.
            local defines = string.find(line, "^IC%.[%u_]+ = [{\"]")
            if text ~= "" and not defines and not RACE_SCAN_ALLOW[text] then
                for _, k in ipairs(names) do
                    if string.find(code .. " ", "IC%." .. k .. "[^%w_]") then
                        bad[#bad + 1] = file .. ":" .. n .. ": " .. text
                        break
                    end
                end
            end
        end
    end
    assert(#bad == 0, #bad .. " site(s) read a race table off IC:\n  " .. table.concat(bad, "\n  "))
end)

check("race plumbing: a court of another race runs on its own tables and keys", function()
    with_test_race(function(T)
        IC.state = {}
        factions = {}
        local saved_humans = cm.get_human_factions
        cm.get_human_factions = function() return {TST_F} end
        local ok, err = pcall(function()
            make_faction(TST_F, T.subculture, {}, {})
            IC.roll_court(TST_F)
            -- A SEAT FILLED WEARS THE RACE'S OWN BUNDLE.
            applied["derpy_ic_office_priest"] = nil
            IC.court(TST_F).offices.priest = 9301
            IC.apply_office_bundles(TST_F)
            assert(applied["derpy_ic_office_tst_priest"] == 1, "the seat wears no race bundle")
            assert(applied["derpy_ic_office_priest"] == nil, "the seat wears the Chaos Dwarf bundle")
            -- LAWS, BY THE RACE'S OWN CATEGORIES, through the save.
            IC.court(TST_F).laws.craft = "lash"
            IC.apply_law_bundles(TST_F)
            assert(applied["derpy_ic_law_tst_craft_lash"] == 1, "the law in force wears no race bundle")
            local packed = IC.pack(TST_F)
            IC.state[TST_F] = nil
            IC.unpack(TST_F, packed)
            assert(IC.court(TST_F).laws.craft == "lash", "the race's law did not survive the save")
            assert(IC.start_gov(TST_F) == "forge", "the race's start government was not read")
        end)
        cm.get_human_factions = saved_humans
        if not ok then error(err, 0) end
    end)
end)
```

- [ ] **Step 2: Run and watch them fail.**

Run: `IC_ONLY="race plumbing" IC_TEST_ALL=1 "/c/Program Files (x86)/Lua/5.1/lua.exe" tools/_iron_court_harness.lua 2>&1 | grep -A120 "^FAIL"`
Expected: `FAIL race plumbing: no site reads a race table off IC: N site(s) read a race table off IC:` listing the lines of Steps 3-5, and `FAIL race plumbing: a court of another race runs on its own tables and keys: ... the law in force wears no race bundle`.

- [ ] **Step 3: Laws, governments, deeds and the save.**

| function (pre-edit line) | `local R = IC.R(...)` | lines rewritten |
|---|---|---|
| `IC.law_in_force(faction_key, category)` (872) | `faction_key` | 876 |
| `IC.apply_law_bundles(faction_key)` (888) | `faction_key` | 890, 891 |
| `IC.gov_row(faction_key)` (911) | `faction_key` | 914 |
| `IC.deed(faction_key, code)` (1467) | `faction_key` | 1468 |
| `IC.unpack(faction_key, packed)` (1690) | `faction_key` | 1828, 1830, 1833, 1857 |
| `IC.law_settle(faction_key, category, passed)` (2089) | `faction_key` | 2096 |
| `IC.law_party_pick(faction_key, slug)` (2174) | `faction_key` | 2181, 2183 |
| `IC.law_turn(faction_key)` (2230) | `faction_key` | 2234 |
| `IC.start_gov(faction_key)` (6033) | `faction_key` | 6034 |
| `IC.apply_gov_bundle(faction_key)` (6045) | `faction_key` | 6047 |
| `IC.gov_change(faction_key, to, gain, loss, kind)` (6172) | `faction_key` | 6175, 6178 |
| `IC.can_force_gov(faction_key, to)` (6252) | `faction_key` | 6254 |

For example `IC.gov_row` becomes:

```lua
function IC.gov_row(faction_key)
    local R = IC.R(faction_key)
    if not IC.governments_on() then return nil end
    local court = faction_key and IC.state[faction_key]
    return court and R.GOVS[court.gov or ""] or nil
end
```

- [ ] **Step 4: Parties, origins and backgrounds.**

| function (pre-edit line) | `local R = IC.R(...)` | lines rewritten |
|---|---|---|
| `IC.rebel_faction(exclude)` (108) | `exclude` | 118, 119, 122, 123 |
| `IC.house_icon(slug, faction_key)` (1503) | `faction_key` | 1506, 1507 |
| `IC.present_houses(faction_key)` (2284) | `faction_key` | 2287, 2288, 2290, 2291, 2292 |
| `IC.fill_tally(tally, faction_key)` (2468) | `faction_key` | 2474 |
| `IC.roll_background(faction_key, tally)` (2504) | `faction_key` | 2509, 2512 |
| `IC.background_for(character, faction_key, tally)` (2530) | `faction_key` | 2539 |
| `IC.deed_room(faction_key)` (2549) | `faction_key` | 2551, 2552 |
| `IC.deed_waiting(faction_key)` (2560) | `faction_key` | 2564, 2565, 2567 |
| `IC.deed_join(character, faction_key)` (2577) | `faction_key` | 2588 |
| `IC.leaderless_bg(character, faction_key, tally)` (2606) | `faction_key` | 2613, 2618 |
| `IC.ensure_leaders(faction_key)` (2684) | `faction_key` | 2691, 2697, 2714 |
| `IC.field_leader(faction_key, slug)` (2753) | `faction_key` | 2761 |
| `IC.clear_gov_bundles(faction_key)` (3919) | `faction_key` | 3932, 3934 |
| `IC.apply_governor_bundles(faction_key)` (3968) | `faction_key` | 3986 |
| `IC.splinter(faction_key)` (4893) | `faction_key` | 4912, 4918, 4919 |
| `IC.roll_court(faction_key)` (6339) | `faction_key` | 6343, 6344 |

- [ ] **Step 5: Offices, tiers, traits, names and rebels.**

| function (pre-edit line) | `local R = IC.R(...)` | lines rewritten |
|---|---|---|
| `IC.standing_tier(faction_key, cqi)` (3208) | `faction_key` | 3210, 3211 |
| `IC.stamp_standing(faction_key, character)` (3218) | `faction_key` | 3224 |
| `IC.apply_office_bundles(faction_key)` (3567) | `faction_key` | 3572, 3573 |
| `IC.dismantle(faction_key)` (3945) | `faction_key` | 3948, 3949 |
| `IC.terms_ending(faction_key)` (4075) | `faction_key` | 4079, 4080 |
| `IC.loyalty_terms(faction_key, slug)` (4122) | `faction_key` | 4147, 4166, 4167, 4183 |
| `IC.rebel_general(faction_key, cqi)` (4401) | `faction_key` | 4408 |
| `IC.fill_plan(faction_key)` (5094) | `faction_key` | 5107, 5108 |
| `IC.name_party(faction_key, slug)` (6360) | `faction_key` | 6364, 6366 |
| `IC.roll_party_traits(faction_key, slug)` (6371) | `faction_key` | 6374 |
| `IC.party_lords(faction_key, slug)` (6441) | `faction_key` | 6459 |
| `IC.party_traits(faction_key, slug)` (6513) | `faction_key` | 6518 |
| `IC.leader_trait(faction_key, slug)` (6535) | `faction_key` | 6538 |

The temple deed (7159-7162, listener `ic_deed_building`) reads the building's own faction:

```lua
    on_deed("ic_deed_building", "BuildingCompleted", function(context)
        local building = context:building()
        local faction = building:faction()
        local fk = faction and not faction:is_null_interface() and faction:name() or nil
        return faction, IC.R(fk).TEMPLE_BUILDINGS[building:name()] and "temple" or nil
    end)
```

- [ ] **Step 6: Run and watch them pass.**

Run: `"/c/Program Files (x86)/Lua/5.1/lua.exe" tools/_iron_court_harness.lua 2>&1 | tail -1`
Expected: `iron court harness: ok (983 checks)`.

- [ ] **Step 7: Checkpoint.** Run the Task 2 Step 8 block. Expected: unchanged lines; harness 983.

---

### Task 7: The parties file reads the faction's race

**Files:**
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_parties.lua` - 205-209, 236-247, 419-424, 444-450, 691-697, 1011-1018, 1219-1230.
- Test: `tools/_iron_court_harness.lua` (`RACE_SCAN_FILES`).

**Interfaces:**
- Consumes: `IC.R`, `IC.RACE_ORDER`, `IC.RACES`.
- Produces: no new names.

- [ ] **Step 1: Widen the scan to the parties file.** Change the declaration to:

```lua
local RACE_SCAN_FILES = {"zzz_derpy_iron_court.lua", "zzz_derpy_iron_court_parties.lua"}
```

- [ ] **Step 2: Run and watch it fail.**

Run: `IC_ONLY="no site reads" "/c/Program Files (x86)/Lua/5.1/lua.exe" tools/_iron_court_harness.lua 2>&1 | grep -A20 "^FAIL"`
Expected: `FAIL race plumbing: no site reads a race table off IC: 15 site(s) read a race table off IC:` listing parties lines 208, 209, 246, 247, 422, 423, 424, 449, 450, 696, 697, 1017, 1018, 1229, 1230 (1229 holds two reads, one entry).

- [ ] **Step 3: Implement**, by the Task 6 rewrite rule:

| function (pre-edit line) | `local R = IC.R(...)` | lines rewritten |
|---|---|---|
| `crown_seat(faction_key, slug)` (205) | `faction_key` | 208, 209 |
| `IC.party_target(faction_key, slug, move, enemy)` (236) | `faction_key` | 246, 247 |
| `motive = function(faction_key, slug, _t)` (419) | `faction_key` | 422, 423, 424 |
| the function holding `local function free(s)` (its own `faction_key`, used at 448) | `faction_key` | 449, 450 |
| `IC.demand_target(faction_key, slug)` (691) | `faction_key` | 696, 697 |
| `IC.backing_target(faction_key)` (1011) | `faction_key` | 1017, 1018 |

and in `IC.party_turn_due` the rotation takes every race's courts and risings:

```lua
    local candidates = {}
    for _, rk in ipairs(IC.RACE_ORDER) do
        local R = IC.RACES[rk]
        for i = 1, #R.ORIGINS do candidates[#candidates + 1] = R.ORIGINS[i].faction end
        for i = 1, #R.REBEL_POOL do candidates[#candidates + 1] = R.REBEL_POOL[i] end
    end
```
(replacing `    local candidates = {}` and the two `for` lines at 1229-1230).

- [ ] **Step 4: Run and watch it pass.**

Run: `"/c/Program Files (x86)/Lua/5.1/lua.exe" tools/_iron_court_harness.lua 2>&1 | tail -1`
Expected: `iron court harness: ok (983 checks)`.

- [ ] **Step 5: Checkpoint.** Run the Task 2 Step 8 block. Expected: unchanged lines; harness 983.

---

### Task 8: The panel reads the player's race

**Files:**
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_ui.lua` - new `ICUI.race` after `ICUI.player` (1957-1962); sites in Step 4.
- Read-only: `zzz_derpy_iron_court_ui_map.lua` (no race site; it joins the scans).
- Test: `tools/_iron_court_harness.lua`.

**Interfaces:**
- Consumes: `IC.R`, `ICUI.player()`.
- Produces: `ICUI.race() -> IC.R(ICUI.player())` (contract). The ziggurat grid (`ICUI.CARD_XY`, 748-749) stays the Chaos Dwarfs' until phase 3 sets `ICUI.BASE.CARD_XY` from the race before `ICUI.apply_scale`; `ICUI.MAX_HOUSES = IC.MAX_SEATS` (187) and the dial loops (673, 681) need nothing - `IC.MAX_SEATS` is already the largest race's.

- [ ] **Step 1: Widen the scan, allow the grid, and write the failing panel check.**

```lua
local RACE_SCAN_FILES = {"zzz_derpy_iron_court.lua", "zzz_derpy_iron_court_parties.lua",
                         "zzz_derpy_iron_court_ui.lua", "zzz_derpy_iron_court_ui_map.lua"}
local RACE_SCAN_ALLOW = {
    ["for row = 1, #IC.TIERS do"] =
        "the ziggurat grid at load; phase 3 sets ICUI.BASE.CARD_XY from the race",
    ["local n = IC.TIER_SEATS[IC.TIERS[row]]"] = "the same loop",
}
```
Append to the section:

```lua
check("race plumbing: the panel reads the player's race", function()
    with_test_race(function(T)
        IC.state = {}
        factions = {}
        make_faction(TST_F, T.subculture, {}, {})
        local saved_local, saved_humans = cm.get_local_faction_name, cm.get_human_factions
        cm.get_local_faction_name = function() return TST_F end
        cm.get_human_factions = function() return {TST_F} end
        local ok, err = pcall(function()
            assert(ICUI.race() == T, "ICUI.race() is not the player's race")
            local text = ICUI.section_text("offices")
            assert(string.find(text, "(2/4/4/4)", 1, true), "the offices label reads " .. text)
            assert(ICUI.law_at(1) == "craft", "the board's first category is " .. tostring(ICUI.law_at(1)))
            assert(ICUI.law_default(TST_F)[1] == "craft", "the board opens on " .. tostring(ICUI.law_default(TST_F)[1]))
        end)
        cm.get_local_faction_name, cm.get_human_factions = saved_local, saved_humans
        if not ok then error(err, 0) end
    end)
end)
```

- [ ] **Step 2: Run and watch them fail.**

Run: `IC_ONLY="race plumbing" IC_TEST_ALL=1 "/c/Program Files (x86)/Lua/5.1/lua.exe" tools/_iron_court_harness.lua 2>&1 | grep -A40 "^FAIL"`
Expected: the scan lists the ui lines of Step 4, and `FAIL race plumbing: the panel reads the player's race: ... attempt to call field 'race' (a nil value)`.

- [ ] **Step 3: Add `ICUI.race`** directly after `ICUI.player`'s `end`:

```lua
-- THE PLAYER'S RACE: every table the panel draws is the race's, never IC.X.
function ICUI.race()
    return IC.R(ICUI.player())
end
```

- [ ] **Step 4: Rewrite the sites**, by the Task 6 rule (`local R = <source>` as the first statement):

| function (pre-edit line) | `local R =` | lines rewritten |
|---|---|---|
| `ICUI.court_state(faction)` (1612) | `IC.R(faction)` | 1620, 1621, 1658 |
| `ICUI.opener_tip(faction)` (1689) | `IC.R(faction)` | 1732 |
| `ICUI.section_text(view)` (2666) | `ICUI.race()` | 2671, 2672, 2676 |
| `ICUI.office_card(office_slug)` (3150) | `ICUI.race()` | 3153, 3154 |
| `ICUI.gov_icon(slug)` (4262) | `ICUI.race()` | 4263 |
| `ICUI.law_at(i)` (4276) | `ICUI.race()` | 4277, 4278 |
| `ICUI.law_icon(category, option)` (4347) | `ICUI.race()` | 4351 |
| `ICUI.law_default(faction)` (4372) | `IC.R(faction)` | 4373, 4375, 4380 |
| `ICUI.gov_choices(faction)` (4502) | `IC.R(faction)` | 4504, 4508, 4511 |
| `ICUI.draw_law_board(panel, faction)` (4576) | `IC.R(faction)` | 4583 |
| `ICUI.deeds_tip(faction, court)` (4891) | `IC.R(faction)` | 4894 |
| `ICUI.draw_offices(panel, faction, court)` (5249) | `IC.R(faction)` | 5254 |
| `ICUI.help_vars(faction)` (6375) | `IC.R(faction)` | 6384, 6385, 6389 |
| `ICUI.ANSWERS.dismiss = function(arg)` (8513) | `ICUI.race()` | 8514 |

Three need the faction from a local, not the first line:

- `ICUI.refresh()` 7632: `                           IC.filled_offices(faction), #IC.R(faction).OFFICES))`
- `ICUI.on_office_click` 8193: `    local office = IC.R(faction).OFFICES[slot]`
- `ICUI.register` 8581: `                for _, cat in ipairs(IC.R(me).LAW_ORDER) do`

`ICUI.law_at` becomes, for example:

```lua
function ICUI.law_at(i)
    local R = ICUI.race()
    local cat = R.LAW_ORDER[math.floor((i - 1) / 5) + 1]
    return cat, cat and R.LAWS[cat].order[(i - 1) % 5 + 1] or nil
end
```

- [ ] **Step 5: Run and watch them pass.**

Run: `"/c/Program Files (x86)/Lua/5.1/lua.exe" tools/_iron_court_harness.lua 2>&1 | tail -1`
Expected: `iron court harness: ok (984 checks)`.

- [ ] **Step 6: Checkpoint.** Run the Task 2 Step 8 block. Expected: unchanged lines; harness 984. The importer's `run_lua_card_grid` and `run_lua_scaled` still load the panel against their `IC = {TIERS, TIER_SEATS, MAX_SEATS}` stubs: the only load-time reads are the allowed grid loop and `IC.MAX_SEATS`.

---

### Task 9: `gen_iron_court.py` - races, tiers by race, keys by race, scrapers by prefix

**Files:**
- Modify: `tools/gen_iron_court.py` - delete 193 (`TIER_SEATS = ...`); add `RACES`, `tier_seats`, `race_lua`, `lua_table` above `def control_slugs()` (1428); `bundle_key` 1432-1433; key helpers 876-885 and 1537-1540; `build()` loc keys 1628-1698; `_model_lua` 1477-1482; scrapers `model_law_icons` 1415, `model_gov_icons` 1495, `model_tails` 1519, `_lua_rebel_generals` 1942, `_lua_rebel_heroes` 2067, `_lua_rebel_roster` 2135; `check_governments` 2465; `check_laws` 2496; `check_party_drawn` 2538; `selftest` 3213 and its tier block 3236-3250.
- Modify: `tools/gen_ic_ui.py:1083,1096`; `tools/preview_iron_court.py:1468` (the two other readers of `TIER_SEATS`).

**Interfaces:**
- Consumes: the module's `ORIGINS`, `PARTIES`, `BACKGROUNDS`, `OFFICES`, `GOVERNMENTS`, `LAWS`.
- Produces (contract): `RACES = {"chd": {...}}`, `tier_seats(race="chd") -> {tier: seats}`, `bundle_key(kind, slug, race="chd")`. ADDED: each race carries `"prefix"` (Lua table prefix, `"IC"`) and `"lua"` (its file); `race_lua(prefix="IC") -> str`, `lua_table(name, prefix="IC", src=None) -> body | None`; the scrapers take `prefix="IC"`; `check_governments(race="chd")`, `check_laws(race="chd")`; `origin_trait_key`, `bg_trait_key`, `office_trait_key`, `member_trait_key` take `race="chd"`. Phase 2 adds `"dwf"` with `"prefix": "DWF"` and `LUA_OF_PREFIX["DWF"]`.

- [ ] **Step 1: Write the failing selftest.** Add as the first statements of `selftest()`:

```python
    # THE RACE SEAM (plan 2026-10-04 phase 1). The tiers are counted off the
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
```

- [ ] **Step 2: Run and watch it fail.**

Run: `py tools/gen_iron_court.py --selftest`
Expected: `NameError: name 'tier_seats' is not defined`.

- [ ] **Step 3: Add the race table and its helpers** directly above `def control_slugs():`:

```python
# THE RACES (plan 2026-10-04 phase 1). Phase 2 adds "dwf". `prefix` is the Lua
# table prefix the race's tables are declared under; LUA_OF_PREFIX names the file.
RACES = {
    "chd": {"infix": "", "prefix": "IC",
            "ORIGINS": ORIGINS, "PARTIES": PARTIES, "BACKGROUNDS": BACKGROUNDS,
            "OFFICES": OFFICES, "GOVERNMENTS": GOVERNMENTS, "LAWS": LAWS},
}
LUA_OF_PREFIX = {"IC": "zzz_derpy_iron_court.lua"}
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
    m = re.search(r"%s\.%s = \{(.*?)\n\}" % (re.escape(prefix), name),
                  race_lua(prefix) if src is None else src, re.S)
    return m.group(1) if m else None
```
Delete line 193, `TIER_SEATS = {1: 2, 2: 3, 3: 4, 4: 5}`.

- [ ] **Step 4: Keys by race.**

```python
def bundle_key(kind, slug, race="chd"):
    return "derpy_ic_%s_%s%s" % (kind, RACES[race]["infix"], slug)
```
```python
def origin_trait_key(slug, race="chd"):
    return bundle_key("house", slug, race)


def bg_trait_key(slug, race="chd"):
    return bundle_key("bg", slug, race)


def office_trait_key(slug, race="chd"):
    return bundle_key("title", slug, race)
```
```python
def member_trait_key(slug, index=None, race="chd"):
    """The key IC.member_trait builds: the Crown, a confederate origin, or a tail."""
    key = bundle_key("member", slug, race)
    return key if index is None else "%s_%d" % (key, index)
```
In `build()`:

| line | before | after |
|---|---|---|
| 1628 | `"derpy_ic_control_name_" + slug` | `bundle_key("control_name", slug)` |
| 1639 | `"derpy_ic_doctrine_name_" + slug` | `bundle_key("doctrine_name", slug)` |
| 1641 | `"derpy_ic_doctrine_rule_" + slug` | `bundle_key("doctrine_rule", slug)` |
| 1649 | `"derpy_ic_law_cat_" + cat` | `bundle_key("law_cat", cat)` |
| 1651 | `key = "derpy_ic_law_%s_%s" % (cat, opt)` | `key = bundle_key("law", "%s_%s" % (cat, opt))` |
| 1653 | `"derpy_ic_law_name_%s_%s" % (cat, opt)` | `bundle_key("law_name", "%s_%s" % (cat, opt))` |
| 1656 | `"derpy_ic_law_fx%d_%s_%s" % (i, cat, opt)` | `bundle_key("law_fx%d" % i, "%s_%s" % (cat, opt))` |
| 1682 | `"derpy_ic_office_name_" + office["slug"]` | `bundle_key("office_name", office["slug"])` |
| 1689 | `"derpy_ic_party_name_" + slug` | `bundle_key("party_name", slug)` |
| 1695 | `"derpy_ic_origin_name_" + slug` | `bundle_key("origin_name", slug)` |
| 1698 | `"derpy_ic_bg_name_" + slug` | `bundle_key("bg_name", slug)` |

- [ ] **Step 5: Scrapers by prefix.**

```python
def _model_lua():
    return race_lua("IC")
```
```python
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
```
```python
def model_gov_icons(prefix="IC"):
    """{government slug: bare effect_bundles picture} from <prefix>.GOVS."""
    body = lua_table("GOVS", prefix)
    if body is None:
        raise RuntimeError("the model Lua declares no %s.GOVS" % prefix)
    return dict(re.findall(r'(\w+)\s*=\s*\{icon = "([^"]+)"', body))
```
```python
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
```
```python
def _lua_rebel_generals(prefix="IC"):
    """<prefix>.REBEL_GENERALS and IC.REBEL_LORD, read out of the shipped Lua."""
    body = lua_table("REBEL_GENERALS", prefix)
    keys = set(re.findall(r'\["([^"]+)"\]\s*=\s*true', body)) if body is not None else set()
    lord = re.search(r'IC\.REBEL_LORD = "([^"]+)"', _model_lua())
    return keys, (lord.group(1) if lord else None)
```
```python
def _lua_rebel_heroes(prefix="IC"):
    """<prefix>.REBEL_HEROES, read out of the shipped Lua."""
    body = lua_table("REBEL_HEROES", prefix)
    if body is None:
        return None
    return dict(re.findall(r'\["([^"]+)"\]\s*=\s*"([^"]+)"', body))
```
```python
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
```
`check_governments` takes the race (keep the Task 4 `kind` lines, and the rest of the loop as it is):

```python
def check_governments(race="chd"):
    """The model's governments and this file's are one list, in one order, and
    the bundle the model applies is one this file builds (spec 2026-10-02)."""
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
```
`check_laws` likewise - its head becomes:

```python
def check_laws(race="chd"):
    """The model's laws and this file's are one catalogue, in one order, each
    option's bundle built and wearing the model's picture (spec 2026-10-02 laws)."""
    prefix = RACES[race]["prefix"]
    lua = race_lua(prefix)
```
and inside it: `m = re.search(r"%s\.LAW_ORDER\s*=\s*\{([^}]*)\}" % re.escape(prefix), lua)`; `mine = [c[0] for c in RACES[race]["LAWS"]]`; the "is ... and LAWS is" message names `prefix`; `body = lua_table("LAWS", prefix, lua) or ""` (replacing the `block` two lines); `for cat, _name, _icon, options in RACES[race]["LAWS"]:`; `key = bundle_key("law", "%s_%s" % (cat, opt), race)`; `if loc.get(bundle_key("law_name", "%s_%s" % (cat, opt), race)) != name:`.

`check_party_drawn`'s first two lines become:

```python
def check_party_drawn(prefix="IC"):
    """Every party <prefix>.DEEDS can name has a party_drawn line (spec 2026-10-02 deeds)."""
    body = lua_table("DEEDS", prefix)
    named = set(re.findall(r'(?:party|alt) = "(\w+)"', body)) if body is not None else set()
```
and its no-table message `"the model Lua declares no %s.DEEDS" % prefix`.

- [ ] **Step 6: The tier block in `selftest` counts off the race.** Replace

```python
    seats = {}
    for office in OFFICES:
        seats[office["tier"]] = seats.get(office["tier"], 0) + 1
    assert seats == TIER_SEATS,         "the court is not a ziggurat: seats per tier %r, wanted %r" % (seats, TIER_SEATS)
    assert len(OFFICES) == sum(TIER_SEATS.values()), "an office outside every tier"
    widths = [TIER_SEATS[t] for t in sorted(TIER_SEATS)]
```
with
```python
    seats = tier_seats()
    assert len(OFFICES) == sum(seats.values()), "an office outside every tier"
    widths = [seats[t] for t in sorted(seats)]
```
and in the later line `assert sorted(TIER_MULT) == sorted(TIER_SEATS) == sorted(TIER_NAME),` write `sorted(seats)` for `sorted(TIER_SEATS)`. (The 2/3/4/5 pin moved into Step 1's block.)

- [ ] **Step 7: The other two readers of the deleted constant.** `tools/gen_ic_ui.py` 1083: `CARD_WIDEST = max(IC.tier_seats().values())`; 1096: `        n = IC.tier_seats()[tier]`. `tools/preview_iron_court.py` 1468: `            _widths = "/".join(str(G.IC.tier_seats()[t]) for t in _tiers)`.

- [ ] **Step 8: Run and watch it pass.**

Run: `py tools/gen_iron_court.py --selftest && py tools/gen_iron_court.py --check && py tools/preview_iron_court.py --check`
Expected: `selftest: ok (73 bundles, 112 junctions, 146 traits, 1116 loc)`, `ok: 73 bundles, 112 junctions, 146 traits, 1116 loc rows`, and the preview's check passing.

- [ ] **Step 9: Checkpoint.** Run the Task 2 Step 8 block. Expected: unchanged lines; harness 984.

---

### Task 10: `gen_ic_ui.py` - the grid by race, the ziggurat Chaos Dwarf only

**Files:**
- Modify: `tools/gen_ic_ui.py` - after `COMPACT = BOX_W < 1920` (~35); `at_box` 66-74; `CARD_TIERS`/`CARD_WIDEST` 1082-1083; `card_grid` 1093-1105; `ziggurat_boxes` 2341; `selftest` 8500.

**Interfaces:**
- Consumes: `gen_iron_court.RACES`, `gen_iron_court.tier_seats` (Task 9).
- Produces (contract): `card_grid(race="chd")`, `ziggurat_boxes(race="chd")` (Chaos Dwarf only), `at_box(bw, race="chd")`. ADDED: module global `RACE` (injected as `_RACE` by `at_box`, as `_BOX_W` is). `throne_box()` and the per-race checks are phase 3.

- [ ] **Step 1: Write the failing selftest.** Add as the first statements of `selftest()`:

```python
    # THE RACE SEAM (plan 2026-10-04 phase 1). card_grid lays out the race it is
    # given - a 2/4/4/4 race gets rows of 2, 4, 4 and 4 - and the ziggurat
    # refuses any race but the Chaos Dwarfs'.
    IC.RACES["tst"] = dict(IC.RACES["chd"], OFFICES=[
        dict(o, tier=t) for o, t in zip(IC.OFFICES, [1, 1, 2, 2, 2, 3, 3, 3, 2, 4, 4, 4, 3, 4])])
    try:
        rows = {}
        for _x, y in card_grid("tst"):
            rows[y] = rows.get(y, 0) + 1
        assert [rows[y] for y in sorted(rows)] == [2, 4, 4, 4], rows
    finally:
        del IC.RACES["tst"]
    try:
        ziggurat_boxes("tst")
    except AssertionError:
        pass
    else:
        raise AssertionError("ziggurat_boxes drew a ziggurat for a race without one")
```

- [ ] **Step 2: Run and watch it fail.**

Run: `py tools/gen_ic_ui.py --selftest`
Expected: `TypeError: card_grid() takes 0 positional arguments but 1 was given`.

- [ ] **Step 3: Implement.** After `COMPACT = BOX_W < 1920`:

```python
# THE RACE THIS COPY LAYS OUT (plan 2026-10-04 phase 1), injected by at_box as
# the box is. Phase 3 gives the Dwarf hall its grid.
RACE = globals().get("_RACE", "chd")
```
```python
def at_box(bw, race="chd"):
    """A fresh copy of this module with every layout number scaled to box bw,
    laid out for `race`."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("gen_ic_ui_at_%d_%s" % (bw, race),
                                                  os.path.abspath(__file__))
    mod = importlib.util.module_from_spec(spec)
    mod.__dict__["_BOX_W"] = bw
    mod.__dict__["_RACE"] = race
    spec.loader.exec_module(mod)
    return mod
```
```python
CARD_TIERS = sorted(IC.tier_seats(RACE))
CARD_WIDEST = max(IC.tier_seats(RACE).values())
```
```python
def card_grid(race="chd"):
    seats = IC.tier_seats(race)
    out = []
    for row, tier in enumerate(sorted(seats)):
        n = seats[tier]
        band = n * CARD_W + (n - 1) * CARD_GAP_X
        for col in range(n):
            out.append((CARDS_X + (CONTENT_W - band) // 2
                        + col * (CARD_W + CARD_GAP_X),
                        CARDS_Y + row * (CARD_H + CARD_GAP_Y)))
    return out


CARD_GRID = card_grid(RACE)
```
```python
def ziggurat_boxes(race="chd"):
    """The tower as (x0, y0, x1, y1) in panel pixels: a tier per card row, then the shrine."""
    assert race == "chd" and RACE == "chd", "the ziggurat is the Chaos Dwarfs' alone, not %s's" % race
```
(the rest of `ziggurat_boxes` unchanged).

- [ ] **Step 4: Run and watch it pass.**

Run: `py tools/gen_ic_ui.py --selftest && py tools/gen_ic_ui.py --check`
Expected: `selftest: ok (28 files, 1054 components, 3981 guids)` and `ok: 28 files, 1054 components`.

- [ ] **Step 5: Checkpoint.** Run the Task 2 Step 8 block. Expected: unchanged lines; harness 984.

---

### Task 11: `import_iron_court.py` - the race tables checked by prefix

**Files:**
- Modify: `tools/import_iron_court.py` - new `check_race_tables` above `def verify():` (864); `verify()` 959-1027 (the ORIGINS and OFFICES blocks); `_selftest` (814).

**Interfaces:**
- Consumes: `G.RACES`, `G.lua_table` (Task 9).
- Produces (contract: "scrapers take the table prefix"): ADDED `check_race_tables(lua, prefix="IC", race="chd") -> (problems, seq)`; phase 2 calls it with `("DWF", "dwf")` on the Dwarf file.

- [ ] **Step 1: Write the failing selftest.** Add to `_selftest()` before its `print`:

```python
    bad, seq = check_race_tables("IC.ORIGINS = {\n}\nIC.OFFICES = {\n}\n", prefix="DWF")
    assert any("no DWF.ORIGINS" in b for b in bad) and any("no DWF.OFFICES" in b for b in bad), bad
    assert seq == [], seq
```

- [ ] **Step 2: Run and watch it fail.**

Run: `py tools/import_iron_court.py --selftest`
Expected: `NameError: name 'check_race_tables' is not defined`.

- [ ] **Step 3: Implement.** Above `def verify():`:

```python
def check_race_tables(lua, prefix="IC", race="chd"):
    """<prefix>.ORIGINS and <prefix>.OFFICES against the generator's race (plan
    2026-10-04 phase 1). Returns (problems, seq): seq is the Lua's (office slug,
    tier) pairs in its own order, which the standing-band check reuses.

    THE FACTION BESIDE EACH ORIGIN is the half nothing else looks at: a key that
    names no faction never matches a confederation, and every lord of that house
    is stamped with a birthplace instead. THE TIER is what the office grants as
    well as where it is drawn, and the ORDER is half of what is checked: the
    panel fills the bands in the Lua's order.
    """
    problems, seq = [], []
    origins = G.RACES[race]["ORIGINS"]
    offices = G.RACES[race]["OFFICES"]
    body = G.lua_table("ORIGINS", prefix, lua)
    if body is None:
        problems.append("the Lua has no %s.ORIGINS table" % prefix)
    else:
        pairs = dict(re.findall(r'slug\s*=\s*"(\w+)"\s*,\s*faction\s*=\s*"([\w]+)"', body))
        for slug, faction, _d in origins:
            if faction is None:
                if slug in pairs:
                    problems.append("origin %s is a place and the Lua gives "
                                    "it faction %s" % (slug, pairs[slug]))
            elif slug not in pairs:
                problems.append("origin %s has no faction in the Lua" % slug)
            elif pairs[slug] != faction:
                problems.append("origin %s: Lua faction %s, generator %s"
                                % (slug, pairs[slug], faction))
        mine = [o[0] for o in origins]
        for slug in pairs:
            if slug not in mine:
                problems.append("origin %s is in the Lua and not the generator" % slug)
    body = G.lua_table("OFFICES", prefix, lua)
    if body is None:
        problems.append("the Lua has no %s.OFFICES table" % prefix)
        return problems, seq
    pairs = dict(re.findall(r'slug\s*=\s*"(\w+)"\s*,\s*affinity\s*=\s*"(\w+)"', body))
    by_slug = {o["slug"]: o for o in offices}
    for office in offices:
        if office["slug"] not in pairs:
            problems.append("office %s is in the generator and not the Lua" % office["slug"])
        elif pairs[office["slug"]] != office["affinity"]:
            problems.append("office %s: Lua affinity %s, generator %s"
                            % (office["slug"], pairs[office["slug"]], office["affinity"]))
    for slug in pairs:
        if slug not in by_slug:
            problems.append("office %s is in the Lua and not the generator" % slug)
    seq = [(slug, int(t)) for slug, t in re.findall(
        r'slug\s*=\s*"(\w+)"\s*,\s*affinity\s*=\s*"\w+"\s*,\s*tier\s*=\s*(\d+)', body)]
    tiers = dict(seq)
    for office in offices:
        if tiers.get(office["slug"]) != office["tier"]:
            problems.append("office %s: Lua tier %r, generator %d"
                            % (office["slug"], tiers.get(office["slug"]), office["tier"]))
    order = [t for _slug, t in seq]
    if order != sorted(order):
        problems.append("the Lua's offices are not grouped by tier: %s" % order)
    return problems, seq
```
In `verify()`, replace everything from the comment line `        # THE FACTION BESIDE EACH ORIGIN, which is the half nothing else` through `                problems.append("the Lua's offices are not grouped by tier: %s" % order)` with:

```python
        race_problems, seq = check_race_tables(lua)
        problems.extend(race_problems)
```

- [ ] **Step 4: Run and watch it pass.**

Run: `py tools/import_iron_court.py --selftest && py tools/import_iron_court.py | head -1`
Expected: `import_iron_court selftest: ok` and `verify ok - 73 bundles, 112 junctions, 146 traits, 1116 loc, 6 script(s), 28 ui file(s), 1740 generated png(s)`.

- [ ] **Step 5: Checkpoint.** Run the Task 2 Step 8 block. Expected: unchanged lines; harness 984.

---

### Task 12: Acceptance - the Chaos Dwarf output is byte-identical

**Files:**
- Read-only: `Modding Files/Backup/ic_phase1_baseline/` (Task 1).

**Interfaces:**
- Consumes: the baseline. Produces: the evidence that phase 1 changed no Chaos Dwarf output.

- [ ] **Step 1: Regenerate everything.**

```bash
py tools/gen_iron_court.py > /dev/null
py tools/gen_ic_ui.py > /dev/null
py tools/preview_iron_court.py > /dev/null
```

- [ ] **Step 2: Diff against the baseline.**

```bash
B="Modding Files/Backup/ic_phase1_baseline"
diff -r "Modding Files/source/iron_court" "$B/source" && echo SOURCE-IDENTICAL
for f in "$B/twui/"*.twui.xml; do cmp "$f" "Modding Files/pack/ui/campaign ui/$(basename "$f")" || echo "DIFF $f"; done
ls "Modding Files/pack/ui/campaign ui/"derpy_ic_*.twui.xml | wc -l
diff -r "Modding Files/pack/ui/derpy_ic" "$B/plates" && echo PLATES-IDENTICAL
for f in "$B/preview/"*.png; do cmp "$f" ".skilltree_cache/ui_preview/$(basename "$f")" || echo "DIFF $f"; done
```
Expected: `SOURCE-IDENTICAL`, no `DIFF` line, `28`, `PLATES-IDENTICAL`. A `DIFF` on a DB/loc/twui/plate file is a behaviour change: find it before going on. A `DIFF` on a preview PNG goes to the author with the before/after pair, and the phase does not ship until approved.

- [ ] **Step 3: Every gate line against the baseline.**

```bash
{
"/c/Program Files (x86)/Lua/5.1/lua.exe" tools/_iron_court_harness.lua 2>&1 | tail -1
py tools/gen_iron_court.py --check 2>&1 | tail -1
py tools/gen_iron_court.py --selftest 2>&1 | tail -1
py tools/gen_ic_ui.py --check 2>&1 | tail -1
py tools/gen_ic_ui.py --selftest 2>&1 | tail -1
py tools/import_iron_court.py 2>&1 | head -1
py tools/import_iron_court.py --selftest 2>&1 | tail -1
} > /tmp/ic_gates_after.txt
diff <(head -7 "$B/gates_before.txt") /tmp/ic_gates_after.txt
```
Expected: exactly one differing line, the harness: `iron court harness: ok (974 checks)` before, `iron court harness: ok (984 checks)` after.

---

### Task 13: The mutation runner - re-aim what moved, add the race mutants, run it all

**Files:**
- Modify: `tools/mutate_iron_court.py` (`MUTANTS`).

**Interfaces:**
- Consumes: the code of Tasks 2-8, byte for byte as this plan shows it.
- Produces: a mutation run with `0 unexplained`.

- [ ] **Step 1: List the stale anchors.**

```bash
py - <<'EOF'
import importlib.util
spec = importlib.util.spec_from_file_location("m", "tools/mutate_iron_court.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
for i, (what, path, old, new) in enumerate(m.MUTANTS):
    n = open(path, encoding="utf-8").read().count(old)
    if n != 1:
        print("%4d  %d  %s" % (i, n, what))
EOF
```
Expected: about 45 lines, the mutants of Step 2's table. A stale anchor is a finding, never a skip: each names a rule whose code moved.

- [ ] **Step 2: Re-aim each one.** Apply the same edit this plan made to the code to BOTH the anchor (third element) and the mutation (fourth element); the mistake the mutant names does not change. Expected set (index - edit):

| mutants | edit applied to anchor and mutation |
|---|---|
| 20, 554, 632, 646 | `IC.office_title_key(X)` -> `IC.office_title_key(X, faction_key)` |
| 23 | `IC.NAME_HEADS` -> `R.NAME_HEADS` (both occurrences) |
| 44 | anchor's last line -> `    return in_any_race("LEGEND_SUBTYPES", key) == true` (mutation unchanged) |
| 45 | `    return key ~= nil and IC.REBEL_GENERALS[key] == true` -> `    return in_any_race("REBEL_GENERALS", key) == true` |
| 53, 59 | `IC.REBEL_GENERALS[key]` -> `R.REBEL_GENERALS[key]` (59's `IC.REBEL_LORD` stays) |
| 126 | `IC.recruit_influence(character:rank())` -> `IC.recruit_influence(character:rank(), faction_key)` |
| 184 | `#IC.OFFICES` -> `#R.OFFICES` |
| 212, 213 | `key ~= nil and IC.REBEL_HEROES[key] ~= nil` -> `in_any_race("REBEL_HEROES", key) ~= nil` (213's mutation `return key ~= nil` stays) |
| 226 | `IC.REBEL_DRAFT` -> `R.REBEL_DRAFT` |
| 229 | `IC.rebel_draw(want - #kit)` -> `IC.rebel_draw(want - #kit, faction_key)` |
| 274, 276 | `IC.MILITARY_DOCTRINE` -> `R.MILITARY_DOCTRINE` |
| 288 | `IC.BACKGROUNDS` -> `R.BACKGROUNDS` |
| 318, 319 | `"derpy_ic_bg_" .. old` -> `IC.bg_trait(old)`; `"derpy_ic_bg_" .. list[cm:random_number(#list, 1)]` -> `IC.bg_trait(list[cm:random_number(#list, 1)])` |
| 407 | `IC.office_rank(office.slug)` -> `IC.office_rank(office.slug, faction_key)` |
| 540, 541, 740 | `IC.office_weight(office_slug, slug)` -> `IC.office_weight(office_slug, slug, faction_key)` |
| 739 | `IC.office_weight(office_slug, IC.CROWN)` -> `IC.office_weight(office_slug, IC.CROWN, faction_key)` |
| 647 | anchor `    return IC.key("member", slug .. "_" .. ((house.tail - 1) % #tails + 1), faction_key)`, mutation `    return IC.key("member", slug .. "_" .. house.tail, faction_key)` |
| 648 | anchor `    if house.confed then return IC.key("member", slug, faction_key) end` |
| 649 | anchor `        keys[#keys + 1] = IC.rkey("member", R.ORIGINS[i].slug, R)` |
| 650 | anchor `                keys[#keys + 1] = IC.rkey("member", slug .. "_" .. j, R)` |
| 729 | anchor `        for i = 1, #R.REBEL_POOL do candidates[#candidates + 1] = R.REBEL_POOL[i] end` |
| 741 | `IC.office_trait(seats[i])` -> `IC.office_trait(seats[i], faction_key)` |
| 743 | `"derpy_ic_house_" .. had` -> `IC.origin_trait(had)` |
| 780 | `IC.origin_for(character)` -> `IC.origin_for(character, faction_key)` |
| 784, 786 | `"derpy_ic_house_" .. slug` -> `IC.origin_trait(slug)` |
| 785 | `"derpy_ic_bg_" .. slug` -> `IC.bg_trait(slug)` |
| 1016 | anchor's `IC.GOVS[court.gov or ""]` -> `R.GOVS[court.gov or ""]` (mutation unchanged) |
| 1019 | `IC.START_GOV` -> `R.START_GOV` |
| 1021 | `IC.gov_for_party(top)` -> `IC.gov_for_party(top, faction_key)` |
| 1029 | `IC.GOVS[from]` -> `R.GOVS[from]` |
| 1037 | `IC.GOVS[g[1] or ""]` -> `R.GOVS[g[1] or ""]` |
| 1082 | `IC.law_stance(cat, opt, slug)` -> `IC.law_stance(cat, opt, slug, faction_key)` |

A stale mutant not in this table is code this plan moved without listing: re-aim it the same way and note it in the task's report.

- [ ] **Step 3: Add the race mutants** as the last entries of `MUTANTS` (above the `]` that closes it, before `def run():`):

```python
    # ---- race plumbing (plan 2026-10-04 phase 1) ---------------------------
    # Each makes a Dwarf court run on Chaos Dwarf data, which no Chaos Dwarf
    # check can tell from the truth.
    ("race: IC.R never asking the faction its race", M,
     '    local k = IC._race_cache[faction_key] or IC.race_key(faction_key)',
     '    local k = IC._race_cache[faction_key]'),
    ("race: a failed race lookup kept for the session", M,
     '    if k then IC._race_cache[faction_key] = k end',
     '    IC._race_cache[faction_key] = k or "chd"'),
    ("race: the race's tune layer skipped", M,
     '    if r ~= nil then base = tune_over(base, r) end',
     '    if false then base = tune_over(base, r) end'),
    ("race: a key written without its race's infix", M,
     '    return "derpy_ic_" .. kind .. "_" .. (R or IC.RACES.chd).infix .. slug',
     '    return "derpy_ic_" .. kind .. "_" .. slug'),
    ("race: a race switched off still holding a court", M,
     '    return r ~= nil and (r.switch == nil or IC.TUNE[r.switch] ~= false)',
     '    return r ~= nil'),
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
```

- [ ] **Step 4: Every anchor applies.**

Run: `py tools/mutate_iron_court.py --selftest`
Expected: `selftest ok: 1106 mutants all anchored, a survivor and a stale anchor are both reported, the tree is restored`.

- [ ] **Step 5: The race mutants are caught.**

Run: `py tools/mutate_iron_court.py "race:"`
Expected: nine `caught:` lines and `9 mutants, 0 unexplained`.

- [ ] **Step 6: The full run** (about two hours; run it in the background and wait for the notice).

Run: `py tools/mutate_iron_court.py > "Modding Files/Backup/ic_phase1_baseline/mutation_run.txt" 2>&1; tail -3 "Modding Files/Backup/ic_phase1_baseline/mutation_run.txt"`
Expected: `1106 mutants, 0 unexplained`. A `SURVIVOR` is a check the race plumbing quietly unbroke: write the check that catches it (failing first) before going on.

- [ ] **Step 7: Put back what the runs wrote, and re-prove Task 12.** The runner restores the Lua, not what it wrote.

```bash
py tools/gen_iron_court.py > /dev/null
py tools/gen_ic_ui.py > /dev/null
B="Modding Files/Backup/ic_phase1_baseline"
diff -r "Modding Files/source/iron_court" "$B/source" && echo SOURCE-IDENTICAL
diff -r "Modding Files/pack/ui/derpy_ic" "$B/plates" && echo PLATES-IDENTICAL
"/c/Program Files (x86)/Lua/5.1/lua.exe" tools/_iron_court_harness.lua 2>&1 | tail -1
```
Expected: `SOURCE-IDENTICAL`, `PLATES-IDENTICAL`, `iron court harness: ok (984 checks)`.

---

### Task 14: Deploy and smoke-check in game

**Files:**
- Build: `derpy_iron_court.pack` via `tools/deploy_iron_court.py`.

**Interfaces:**
- Consumes: everything above. Produces: the phase-1 pack in data/.

- [ ] **Step 1: RPFM is open.**

Run: `curl -s -m 4 http://127.0.0.1:45127/sessions && echo RPFM-UP`
Expected: `RPFM-UP`. Connection refused means RPFM is closed: say so and stop.

- [ ] **Step 2: Build and deploy.**

Run: `py tools/deploy_iron_court.py` (or `py tools/deploy_iron_court.py --wait` in the background if Warhammer3.exe is running)
Expected: the build verifies, backs the live pack up under `Modding Files/Backup/`, copies to data/ and byte-compares.

- [ ] **Step 3: In game, a Chaos Dwarf campaign plays as before.** Load a Chaos Dwarf save and start one new Chaos Dwarf campaign: the court button opens the panel, every tab draws as in the Task 1 previews, one end turn passes with the court ticking, and the script log shows no `IRON COURT:` failure line. A Dwarf campaign still shows no court button (the Dwarfs register in phase 2).

---

## Self-review

Spec coverage for this phase (section 9 points 1-5 and 7, section 11 phase 1):

- **9.1 `IC.RACES`, chd pointing at the existing tables, `build_race` deriving TIERS / TIER_SEATS / PARTY_OF_BG / MAX_SEATS:** Task 2. The tables stay where and as they are; the scrapers' `IC\.X = \{(.*?)\n\}` still matches (Tasks 9, 11 go through `lua_table`, which is that regex).
- **9.2 accessors `race_of`, `has_court` replacing `is_chd` at its sites, `R` cached and unsaved, `tune` gaining the race layer:** Tasks 2-3. `is_chd` is kept (chd only) and after this phase has no caller in the shipped Lua; phase 2+ uses it for Chaos Dwarf-only mechanics.
- **9.3 the ~190 reading sites; load-time derivations sized for the larger race; key-only helpers take the faction:** 204 lines measured (157 model, 16 parties, 36 ui, 0 ui_map, less the deleted derivations), converted in Tasks 5-8 and held by the source scan; `IC.MAX_SEATS` is the largest race's (Task 2); `office_by_slug`, `law_opt`, `is_party`, `rolled_name` take the faction (Task 5).
- **9.4 keys with a race segment, Chaos Dwarf keys unchanged:** Task 4 (Lua) and Task 9 (Python), proved byte-identical in Task 12.
- **9.5 save:** nothing saved changes; the whole-court check (Task 6) round-trips a second race's laws through `IC.pack`/`IC.unpack` on its own tables.
- **9.7 Python `RACES`, `TIER_SEATS` no longer typed, scrapers by prefix, card grid and ziggurat by race:** Tasks 9-11. `ic_zig_bg`/`ic_off_title` as functions of the race, `throne_box()` and every gen_ic_ui check taking `race` are phase 3 (the Dwarf grid does not exist yet); `ziggurat_boxes` already refuses a race without one.
- **Acceptance (section 11 phase 1):** harness 974 + 10 = 984 green (Task 12), every generator check line unchanged (Task 12 Step 3), Chaos Dwarf DB/loc/twui/plates byte-identical (Task 12 Step 2), mutation run clean with stale anchors re-aimed (Task 13).

Added to the contract by this plan (each named in its task's Interfaces): `IC.RACE_FIELDS`; race field `switch`; `register_race` appends to `IC.RACE_ORDER`; `IC.rkey`, `IC.origin_trait`, `IC.bg_trait`; `origin_of_character`/`bg_of_character` returning the race second; trailing `faction_key` on `law_stance`, `gov_for_party`, `office_influence`, `office_rank`, `office_weight`, `office_title_key`, `recruit_influence`, `rebel_draw`, `roll_origin`, `origin_for`, `chd_factions`, `member_trait_keys` and the bundle/trait builders; Python `RACES[race]["prefix"]`, `LUA_OF_PREFIX`, `race_lua`, `lua_table`, `check_race_tables`, gen_ic_ui's `RACE`. Contract correction: `IC.rolled_name(slug, head, tail, faction_key)` (the contract dropped `slug`).

Left on `IC` for phase 2 to decide (Chaos Dwarf data the contract's race field list does not name): `REBEL_LORD`, `REBEL_PERSONALITY`, `STORE_LORDS`, `LORD_HISTORY`, `NOT_DWARF`, `ENVOY_TASKS`, `ENSLAVE_RECORD`/`ENSLAVE_OUTCOME`, `RECRUIT_RANK`, `CONTROL`. Adding a name to `IC.RACE_FIELDS` extends the source scan to it automatically.
