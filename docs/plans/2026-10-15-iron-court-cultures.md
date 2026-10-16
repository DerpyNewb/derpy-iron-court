# Iron Court Cultures Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the rolled place origins of both Iron Court races with an always-rolled, quietly stamped culture trait that sets a governor's province effects, feeds a main and a side party, and gives each man a stance on laws.

**Architecture:** Eight cultures per race are data tables in the Lua model (`IC.CULTURES`, `DWF.CULTURES`) and in the generator (`CHD_CULTURES`, `DWF_CULTURES`); the generator turns one table into the trait text, the away bundle, the home bundle and the name loc, and `check_cultures` holds the Lua and the generator to one list. The party is dealt exactly as today, the culture is then drawn from the cultures that feed that party, and the trade is drawn last so a Kadrin man in the Legion can be dealt the new Slayer trade. Governing swaps the party bundle for a culture bundle (home, foreign or away, by province key); laws gain culture stances and a loyalty swing that follows a party's mix.

**Tech Stack:** Lua 5.1.5 campaign scripts under `Modding Files/pack/script/campaign/mod/`, the Python generator `tools/gen_iron_court.py`, the importer `tools/import_iron_court.py`, the Lua harness `tools/_iron_court_harness.lua` (run under `lua.exe`), `tools/mutate_iron_court.py`, `tools/preview_iron_court.py`, `tools/gen_ic_ui.py`, RPFM only through the importer and deployer.

**Spec:** `docs/superpowers/specs/2026-10-15-iron-court-cultures-design.md` (read it first; this plan uses its section numbers). Where the plan departs from it, section "Decisions where this plan departs from the spec" below says so.

## Global Constraints

- The workspace is not a git repository. Every "commit" step is a ledger line appended to `docs/superpowers/plans/2026-10-15-iron-court-cultures.ledger.md`, and Task 0 makes the backups that stand in for history.
- Lua 5.1.5. A number literal must never be on the LEFT of an arithmetic operator (the game's compiler miscompiles it in a function with over 255 constants); write `x * 2`, never `2 * x`. `tools/check_lua_literal_left.py` finds it.
- No `string.find(s, p, 1, true)` plain flag in shipped Lua. No floats stored in saves or tallies: use `math.floor` integer arithmetic.
- `cm:random_number(max, min)` is the only random source in shipped Lua.
- Every `IC.X = {` and `DWF.X = {` table closes with `}` at column 0; the generator and importer read them with `^PREFIX\.NAME = \{(.*?)\n\}`.
- A site reads a race table through `R.X` (`R = IC.R(faction_key)`), never `IC.X`. Only a column-0 `IC.X = {` definition may name it.
- Binary files (`db/`, `.loc`, `.pack`, `.dds`, `.xlsx`) are never edited as text. The importer is the only way into the pack and needs RPFM open.
- Player text uses plain words: Control, influence, loyalty. The words cap, caps, accrue, accrues, rep, AI, HUD and standing never appear in player text (`JARGON` in the generator). Dwarf text carries none of `hashut|zharr|hell-?forge|slave|labourer|hobgoblin|convoy|ziggurat|daemon|chaos dwarf` and never the word "guild" (`CHD_WORDS`, `check_dwf`).
- No emojis, no em dashes and no en dashes in code, comments, docs or replies. A step in an escalation is a tier, level, step or band; the author has banned the ladder word for it.
- Culture is always stamped quietly: `cm:force_add_trait(lookup, key, false)`. The trade keeps today's behaviour (a new recruit still sees its Trait Gained card).
- Home figure for a boon is 150% of the away figure, rounded to the nearest whole number with halves rounding up (`(150 * m + 50) // 100`). The drawback is the same at home. Friction is Control -4.
- A culture's trait text is built by the generator from the same table that builds its bundles. A mismatch between the trait text and the emitted bundle rows fails `--check`.
- Effects are vanilla effects at province scope only. Every (effect, scope) pair was read from CA's junction tables on 2026-10-15; `--check` re-reads them.
- Home provinces exist on the Old World map only (`cr_oldworld_province_*`). Immortal Empires, IEE and Realm of Chaos give every governor the away case.
- Place origin trait rows and the nine `derpy_ic_gov_house_*` bundles stay in the pack forever so an old save can remove them. They are never granted again.
- Back up to `Modding Files/Backup/`, never to `data/` or a Workshop folder. Deploy to `data/` when the game is shut (`py tools/deploy_iron_court.py`, RPFM open).
- Check for duplicate keys before packing (`gen_iron_court.py --check` does). A mutation run leaves generated files mutated: touch every restored file afterwards.
- Show the rendered preview of every touched view before calling the work done (`tools/preview_iron_court.py`, 1600 and 1920, both races). The preview cannot draw tooltips; say so.

## Decisions where this plan departs from the spec

1. The archetype "Guild Innovator" is "Engineer". `check_dwf` bans the word "guild" in Dwarf text.
2. `IC.TUNE.culture_main_pct = 70` is `IC.TUNE.culture_main_tenths = 7`, rolled as `cm:random_number(10, 1)`. The harness counts `random_number(100, ...)` calls to find ambition rolls (exactly three in one test), and a 1 to 100 roll would break that count.
3. Trade order. The spec's roll (4.3) picks the party, then the culture, then the trade, so the trade is drawn last. `IC.background_for` therefore returns `bg, culture, binding`, and `IC.stamp_culture` stamps what it is handed. The old `IC.roll_background` and `IC.leaderless_bg` split into a party picker (`IC.roll_party`, `IC.leaderless_party`) and a trade picker (`IC.trade_in`). The three harness checks that call `IC.roll_background` are rewritten to call `IC.trade_in(IC.roll_party(F), F)`.
4. Slayer rule (spec 4.4, open item 11). A Kadrin-born man seated in the Dwarf Legion is always dealt the Slayer trade. Slayer is excluded from every other draw (`R.RESERVED_BG`), so nobody else is ever a Slayer. A lord who joins through a deed (`IC.deed_join`) is never a Slayer. The author can change "always" to a draw by editing `IC.trade_in` only.
5. Out-of-range home values (spec 5.3, open item 9) are kept uncapped. `gen_iron_court.py --check` prints each as a NOTE (exit status unchanged). Capping a value below what the table says would make the trait text and the author's table disagree.
6. Confederated lords take their hold's culture (spec open item 4, proposed and not confirmed). The tables are `HOUSE_CULTURE`; deleting a line reverts one hold to a rolled culture.
7. Legend cultures (spec open item 2) are proposals for the author's review: each Chaos Dwarf legend takes the main culture of his fixed trade's party (Gorduz keeps `zornuzkul`, the culture of his retired place); the Dwarf ones are judgement calls listed in Task 1.
8. A governor with no culture trait gets the base bundle only (no party bundle, no error). Every lord is stamped at spawn, so this is the unstamped-for-a-moment case.
9. The picker line goes in the row tooltip (spec section 9, point 2). The cells are fixed width and fit-checked; the tooltip is not. The preview cannot draw a tooltip, so Task 10 carries an in-game checklist.
10. A party's loyalty swing on a law passing follows how its men voted (spec 7.2): the step times the influence of its aye men minus the influence of its nay men, over the influence of the men who voted, the half rounding away from zero. The Crown keeps the flat step, because its men's votes say nothing of where the Crown house stands, and so does a party none of whose men voted. A party's push multiplies only the men on the party's own line.
11. The overrule penalty (`IC.law_overrule`) and the parties' own proposals still read party lines (spec 7.2 is silent). They are listed under known gaps at the end of the plan.

## Review Focus

The five inputs the spec implies and no happy-path test would touch, most likely first. Each has a test in the task named.

1. **A map with no Old World province keys** (Immortal Empires, IEE, Realm of Chaos): every governor is the away case, no friction, no error, the boons still apply. Tested in Task 1 (`culture_case`) and Task 5 (bundles on an unlisted province).
2. **A lord with a place origin trait and a trade but no culture** (every lord in an existing save): converted on the next stamp, quietly, party and trade untouched; a Dwarf ranger becomes a Pass-Keeper; a man who already wears a culture is left alone. Tested in Task 4.
3. **A confederated man already wearing a rolled culture** (an AI court stamped him before the confederation): he takes the hold's culture, the old culture trait comes off, no Trait Gained card shows. Tested in Task 4.
4. **A law that passes while a party has no man who voted, or for the Crown's own step** (division by zero, a lost flat step): the flat step applies, no error. Tested in Task 6.
5. **A Kadrin man seated in the Dwarf Legion, a Kadrin man in another party, and a deed-joined Legion lord:** Slayer only for the first; the Slayer trade never appears in an ordinary draw. Tested in Task 4.

## File Structure

| File | Responsibility | Tasks |
|---|---|---|
| `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court.lua` | The model: culture data, keys, roll, stamping, governing, laws | 1, 4, 5, 6 |
| `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_dwarf.lua` | The Dwarf race's tables: cultures, laws, the Slayer trade | 1, 3, 6 |
| `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_ui.lua` | The vote panel's push level, the culture line, the Help page | 6, 7 |
| `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_ui_map.lua` | The governor picker card's tooltip | 7 |
| `tools/gen_iron_court.py` | Effect vocabulary, culture tables, bundle and trait rows, law stances, picker lines, checks, selftest | 2, 3, 6, 7 |
| `tools/import_iron_court.py` | Roller gates, builder presence, selftest | 8 |
| `tools/_iron_court_harness.lua` | Fixtures, the updated old checks and the new ones | 1, 4, 5, 6, 7 |
| `tools/mutate_iron_court.py` | Nine anchors moved, one mutant retired, 44 new mutants aimed at the new rules | 9 |
| `Modding Files/source/iron_court/*.tsv` | The generated rows; rewritten by the generator, never edited | 8, 10 |
| `Modding Files/Modpacks/derpy_iron_court.pack` and the game's `data/` copy | Built and copied by the deployer | 10 |
| `docs/SESSION_INDEX.md` | The existing one-line entry for this work, updated | 10 |
| `docs/MY_MODS.md` | The Iron Court row: counts and one sentence on cultures | 10 |
| `docs/superpowers/specs/2026-10-15-iron-court-cultures-design.md` | Its status paragraph | 10 |
| `Modding Files/Backup/iron_court_cultures_20261015/` | Copies of every edited file, and the Lua before the mutation run | 0, 9 |
| `docs/superpowers/plans/2026-10-15-iron-court-cultures.ledger.md` | One line per finished task (replaces commits) | all |

Nothing new is created in `Modding Files/pack/` besides edits to the four Lua files above. The generated TSVs under `Modding Files/source/iron_court/` are rewritten by `py tools/gen_iron_court.py` and are never edited by hand. Every Lua, Python and TSV file here has LF line endings; `docs/SESSION_INDEX.md` has CRLF, and Task 10 edits it with a script that keeps them.

## Harness fixes that run through several tasks

The harness (`tools/_iron_court_harness.lua`, baseline `iron court harness: ok (1093 checks)`) is run with:

```powershell
& "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua
$env:IC_TEST_ALL = "1"; & "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua 2> harness_fail.txt; Remove-Item Env:IC_TEST_ALL
```

The second form lists every failing check instead of stopping at the first. Run from the workspace root (`G:\Modding for resources`); the harness reads `Modding Files/pack/...` by relative path.

**Old checks that assert the old behaviour.** The task that changes a behaviour lists the checks it breaks as Replace/with pairs in its own step, with the exact old text. A pair is applied only where the old text appears exactly once in the harness; if it appears nowhere or twice, stop and read the harness, because it has moved. The one rule worth knowing in advance is about random queues. The old origin roll consumed one `cm:random_number(8, 1)` value per man at the start of his stamp and is gone, so an `rng({...})` queue that feeds `IC.stamp_court` loses the first value of each man's group. A queue is clamped to each call's range, so a value left in the wrong place is not an error, it is a different man. Task 4 has the one such queue (the ambition rolls: `rng({25, 26, 76})`).

## Ledger and backup convention

`docs/superpowers/plans/2026-10-15-iron-court-cultures.ledger.md` is created in Task 0. Each task ends by appending one line: `Task N done: <files touched>; harness <count> checks; <other gates run>`.

---

### Task 0: Backups, baselines, ledger

**Files:**
- Create: `Modding Files/Backup/iron_court_cultures_20261015/` (copies)
- Create: `docs/superpowers/plans/2026-10-15-iron-court-cultures.ledger.md`

**Interfaces:**
- Consumes: nothing.
- Produces: restorable copies of every file the plan edits, and the baseline numbers later tasks compare against.

- [ ] **Step 1: Back up every file the plan edits**

```powershell
$b = "Modding Files\Backup\iron_court_cultures_20261015"
New-Item -ItemType Directory -Force $b | Out-Null
foreach ($f in @(
  "Modding Files\pack\script\campaign\mod\zzz_derpy_iron_court.lua",
  "Modding Files\pack\script\campaign\mod\zzz_derpy_iron_court_dwarf.lua",
  "Modding Files\pack\script\campaign\mod\zzz_derpy_iron_court_ui.lua",
  "Modding Files\pack\script\campaign\mod\zzz_derpy_iron_court_ui_map.lua",
  "tools\gen_iron_court.py", "tools\import_iron_court.py",
  "tools\_iron_court_harness.lua", "tools\mutate_iron_court.py",
  "Modding Files\Modpacks\derpy_iron_court.pack", "docs\SESSION_INDEX.md")) {
  Copy-Item $f $b -Force
}
Copy-Item "Modding Files\source\iron_court" "$b\source_iron_court" -Recurse -Force
Get-ChildItem $b | Select-Object Name, Length
```

Expected: ten files and the `source_iron_court` folder listed. The backup folder is under `Modding Files/Backup/`, not `data/` or a Workshop folder.

- [ ] **Step 2: Record the baselines**

```powershell
& "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua
py tools\gen_iron_court.py --check
py tools\gen_iron_court.py --selftest
py tools\gen_ic_ui.py --check
```

Expected: `iron court harness: ok (1093 checks)`, then `ok: ... bundles, ... junctions, ... traits, ... loc rows`, `selftest: ok (...)`, and a clean `gen_ic_ui.py --check`. Write the exact lines into the ledger. If any is not green, stop: the plan assumes a green start.

- [ ] **Step 3: Create the ledger**

Write `docs/superpowers/plans/2026-10-15-iron-court-cultures.ledger.md`:

```markdown
# Iron Court cultures ledger

Task 0 done: backups in Modding Files/Backup/iron_court_cultures_20261015; baseline harness 1093 checks, gen --check and --selftest and gen_ic_ui --check green.
```

---

### Task 1: Lua culture data, keys, case and roll

**Files:**
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court.lua` (after `IC.ORIGINS`, `IC.LAWS` untouched here, `IC.TUNE`, `IC.RACE_FIELDS`, `IC.build_race`, near `IC.gov_bundle_house`, a new block after `IC.fewest`)
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_dwarf.lua` (new tables before `IC.register_race(DWF)`)
- Modify: `tools/_iron_court_harness.lua` (`make_character`, RACE_ARITY, new `do ... end` block before the final check)

**Interfaces:**
- Consumes: `IC.R(faction_key)`, `IC.rkey(kind, slug, R)`, `IC.key(kind, slug, faction_key)`, `IC.RACE_ORDER`, `IC.RACES`, `cm:random_number(max, min)`.
- Produces (later tasks call these by exactly these names):
  - Race fields (all required, registered through `IC.RACE_FIELDS`): `R.CULTURES` (list of `{slug, main, side, homes}`), `R.LEGEND_CULTURE` (`{[subtype] = slug}`), `R.HOUSE_CULTURE` (`{[house origin slug] = slug}`), `R.PLACE_CULTURE` (`{[place origin slug] = slug}`), `R.CULTURE_TRADE` (`{[culture slug] = {party = slug, bg = slug}}`).
  - Derived by `IC.build_race`: `R.CULTURE_BY_SLUG` (`{[slug] = entry}`), `R.HOME_OF` (`{[province key] = culture slug}`), `R.RESERVED_BG` (`{[trade slug] = true}`).
  - `IC.TUNE.culture_main_tenths` (7).
  - `IC.culture_trait(slug, faction_key) -> key`, `IC.gov_bundle_culture(slug, faction_key) -> key`, `IC.gov_bundle_culture_home(slug, faction_key) -> key`, `IC.gov_bundle_friction(faction_key) -> key`.
  - `IC.culture_of_character(character) -> slug, R | nil`.
  - `IC.culture_case(faction_key, culture, province_key) -> "home" | "foreign" | "away"`.
  - `IC.cultures_of(faction_key, party) -> main slug | nil, sides (list)`.
  - `IC.roll_culture(faction_key, party) -> slug`.
  - Harness: `make_character(cqi, rank, party, province_key, unique, origin, subtype, culture)`; the eighth argument stamps `derpy_ic_cult_<culture>` verbatim (a Dwarf test passes `"dwf_karaz"`).

- [ ] **Step 1: Write the failing harness checks**

First add the eighth argument to `make_character` in `tools/_iron_court_harness.lua`. Replace

```lua
local function make_character(cqi, rank, party, province_key, unique, origin,
                             subtype)
```

with

```lua
local function make_character(cqi, rank, party, province_key, unique, origin,
                             subtype, culture)
```

and replace

```lua
    if origin then c._traits["derpy_ic_house_" .. origin] = true end
    return c
```

with

```lua
    if origin then c._traits["derpy_ic_house_" .. origin] = true end
    -- AND A CULTURE only when a check asks for one: the slug verbatim, so a Dwarf
    -- check passes "dwf_karaz".
    if culture then c._traits["derpy_ic_cult_" .. culture] = true end
    return c
```

Then insert this block immediately above the line `check("no engine setter was ever handed anything but a boolean", function()` (that check must stay last; the block is a `do ... end` so its locals do not count against the main chunk):

```lua
-- CULTURES, task 1: the data, the keys, the case and the roll.
do
    local DF = "wh_main_dwf_dwarfs"

    check("cultures: each race has eight, every rival party has exactly one main culture and a feeder", function()
        for _, k in ipairs({"chd", "dwf"}) do
            local R = IC.RACES[k]
            assert(#R.CULTURES == 8, k .. " has " .. #R.CULTURES .. " cultures")
            local mains, feeds = {}, {}
            for _, c in ipairs(R.CULTURES) do
                assert(c.main ~= c.side, k .. "." .. c.slug .. " feeds one party twice")
                mains[c.main] = (mains[c.main] or 0) + 1
                feeds[c.main], feeds[c.side] = true, true
                assert(R.CULTURE_BY_SLUG[c.slug] == c, "no index entry for " .. c.slug)
            end
            for _, p in ipairs(R.PARTIES) do
                if p ~= IC.CROWN then
                    assert(mains[p] == 1, k .. "." .. p .. " has " .. tostring(mains[p]) .. " main cultures")
                    assert(feeds[p], k .. "." .. p .. " is fed by no culture")
                end
            end
            assert(not mains[IC.CROWN] and not feeds[IC.CROWN], "a culture feeds the Crown")
        end
    end)

    check("cultures: no province is home to two cultures and HOME_OF agrees", function()
        for _, k in ipairs({"chd", "dwf"}) do
            local R, seen = IC.RACES[k], {}
            for _, c in ipairs(R.CULTURES) do
                assert(#c.homes >= 1, k .. "." .. c.slug .. " has no home province")
                for _, p in ipairs(c.homes) do
                    assert(not seen[p], k .. ": " .. p .. " is home to " .. tostring(seen[p]) .. " and " .. c.slug)
                    seen[p] = c.slug
                    assert(R.HOME_OF[p] == c.slug, "HOME_OF disagrees on " .. p)
                    assert(string.find(p, "^cr_oldworld_province_"), p .. " is no Old World province key")
                end
            end
        end
    end)

    check("cultures: the retired places, the holds and the legends point at real cultures", function()
        for _, k in ipairs({"chd", "dwf"}) do
            local R = IC.RACES[k]
            local places = {}
            for _, o in ipairs(R.ORIGINS) do
                if not o.faction then places[o.slug] = true end
            end
            for place in pairs(places) do
                assert(R.CULTURE_BY_SLUG[R.PLACE_CULTURE[place] or ""], k .. ": place " .. place .. " converts to nothing")
            end
            for place, cult in pairs(R.PLACE_CULTURE) do
                assert(places[place], k .. ": PLACE_CULTURE names " .. place .. ", which is no place")
                assert(R.CULTURE_BY_SLUG[cult], k .. ": place " .. place .. " converts to " .. cult)
            end
            local houses = {}
            for _, o in ipairs(R.ORIGINS) do
                if o.faction then houses[o.slug] = true end
            end
            for house, cult in pairs(R.HOUSE_CULTURE) do
                assert(houses[house], k .. ": HOUSE_CULTURE names " .. house .. ", which is no house")
                assert(R.CULTURE_BY_SLUG[cult], k .. ": house " .. house .. " takes " .. cult)
            end
            for subtype, cult in pairs(R.LEGEND_CULTURE) do
                assert(R.CULTURE_BY_SLUG[cult], k .. ": legend " .. subtype .. " takes " .. cult)
            end
        end
        for key in pairs(IC.RACES.dwf.LEGEND_CULTURE) do
            assert(IC.RACES.dwf.LEGEND_SUBTYPES[key], "a Dwarf legend culture for " .. key .. ", who is no legend")
        end
        for key in pairs(IC.LORD_HISTORY) do
            assert(IC.RACES.chd.LEGEND_CULTURE[key], "legend " .. key .. " has no culture")
        end
    end)

    check("cultures: the keys carry the family and the race infix", function()
        make_faction(F, IC.CHD_SUBCULTURE, {}, {})
        make_faction(DF, IC.RACES.dwf.subculture, {}, {})
        assert(IC.culture_trait("zharr", F) == "derpy_ic_cult_zharr", IC.culture_trait("zharr", F))
        assert(IC.gov_bundle_culture("zharr", F) == "derpy_ic_gov_cult_zharr")
        assert(IC.gov_bundle_culture_home("zharr", F) == "derpy_ic_gov_cult_home_zharr")
        assert(IC.gov_bundle_friction(F) == "derpy_ic_gov_friction")
        assert(IC.culture_trait("karaz", DF) == "derpy_ic_cult_dwf_karaz", IC.culture_trait("karaz", DF))
        assert(IC.gov_bundle_culture_home("karaz", DF) == "derpy_ic_gov_cult_home_dwf_karaz")
        assert(IC.gov_bundle_friction(DF) == "derpy_ic_gov_dwf_friction")
    end)

    check("cultures: a man's culture is read off his trait, across the races", function()
        local none = make_character(9400, ANY_SEAT, "forge")
        local chd = make_character(9401, ANY_SEAT, "forge", nil, nil, nil, nil, "stump")
        local dwf = make_character(9402, ANY_SEAT, "forge", nil, nil, nil, nil, "dwf_azul")
        assert(IC.culture_of_character(none) == nil, "a man with no culture reads one")
        local slug, R = IC.culture_of_character(chd)
        assert(slug == "stump" and R == IC.RACES.chd, "Chaos Dwarf culture read as " .. tostring(slug))
        slug, R = IC.culture_of_character(dwf)
        assert(slug == "azul" and R == IC.RACES.dwf, "Dwarf culture read as " .. tostring(slug))
        assert(IC.culture_of_character(nil) == nil, "nil has a culture")
    end)

    check("cultures: home, foreign and away come from the province key alone", function()
        make_faction(F, IC.CHD_SUBCULTURE, {}, {})
        make_faction(DF, IC.RACES.dwf.subculture, {}, {})
        local R = IC.R(F)
        local home = R.CULTURE_BY_SLUG.zharr.homes[1]
        local other = R.CULTURE_BY_SLUG.gorgoth.homes[1]
        assert(IC.culture_case(F, "zharr", home) == "home")
        assert(IC.culture_case(F, "zharr", other) == "foreign")
        -- AN IMMORTAL EMPIRES OR IEE PROVINCE, a key on no list, and no key at all.
        assert(IC.culture_case(F, "zharr", "wh3_main_combi_province_the_plain_of_zharr") == "away")
        assert(IC.culture_case(F, "zharr", "cr_combi_province_somewhere") == "away")
        assert(IC.culture_case(F, "zharr", nil) == "away")
        assert(IC.culture_case(F, "zharr", "") == "away")
        -- The Dwarf race answers from its own table.
        local d = IC.R(DF).CULTURE_BY_SLUG.kadrin.homes[1]
        assert(IC.culture_case(DF, "kadrin", d) == "home")
        assert(IC.culture_case(DF, "karaz", d) == "foreign")
        assert(IC.culture_case(DF, "kadrin", home) == "away", "a Chaos Dwarf home is no Dwarf home")
    end)

    check("cultures: a party's new man is its main culture on 1 to 7 of ten and a side culture on 8 to 10", function()
        make_faction(F, IC.CHD_SUBCULTURE, {}, {})
        assert(IC.TUNE.culture_main_tenths == 7, "the split is " .. tostring(IC.TUNE.culture_main_tenths))
        -- The Ledger: Gash Kadrak is main, Tower of Gorgoth and Howling Wastes are sides.
        local main, sides = IC.cultures_of(F, "ledger")
        assert(main == "gash" and #sides == 2 and sides[1] == "gorgoth" and sides[2] == "wastes",
            "ledger is fed by " .. tostring(main) .. " and " .. #sides .. " sides")
        local mains = 0
        for r = 1, 10 do
            rng({r, 1})
            local got = IC.roll_culture(F, "ledger")
            if r <= 7 then
                assert(got == "gash", "roll " .. r .. " gave " .. got)
                mains = mains + 1
            else
                assert(got == "gorgoth", "roll " .. r .. " gave " .. got)
            end
        end
        assert(mains == 7, "main on " .. mains .. " of ten")
        rng({8, 2})
        assert(IC.roll_culture(F, "ledger") == "wastes", "the second side was never reached")
        rng(nil)
    end)

    check("cultures: a party with no side culture is its main culture and makes no random call", function()
        make_faction(F, IC.CHD_SUBCULTURE, {}, {})
        rng({10})
        assert(IC.roll_culture(F, "temple") == "zharr", "the Temple is not Heart of Zharrduk")
        assert(#rng_calls == 0, "a party with one feeder made " .. #rng_calls .. " random calls")
        rng(nil)
    end)

    check("cultures: the Crown, and a man with no party, draw uniformly from all eight", function()
        make_faction(F, IC.CHD_SUBCULTURE, {}, {})
        local R = IC.R(F)
        for i = 1, 8 do
            rng({i})
            assert(IC.roll_culture(F, IC.CROWN) == R.CULTURES[i].slug, "Crown draw " .. i)
            assert(rng_calls[1].max == 8 and rng_calls[1].min == 1, "the draw was not 1 to 8")
            rng({i})
            assert(IC.roll_culture(F, nil) == R.CULTURES[i].slug, "no-party draw " .. i)
        end
        rng(nil)
    end)

    check("cultures: the second race rolls its own cultures", function()
        make_faction(DF, IC.RACES.dwf.subculture, {}, {})
        rng({1})
        assert(IC.roll_culture(DF, "legion") == "kadrin", "the Dwarf Legion's main culture")
        rng({9, 1})
        assert(IC.roll_culture(DF, "legion") == "grey", "the Dwarf Legion's first side culture")
        rng(nil)
    end)
end

```

- [ ] **Step 2: Run the harness and confirm the new checks fail**

```powershell
$env:IC_TEST_ALL = "1"; & "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua 2> harness_fail.txt; Remove-Item Env:IC_TEST_ALL
Select-String -Path harness_fail.txt -Pattern "^FAIL cultures:"
```

Expected: ten `FAIL cultures: ...` lines (`attempt to index field 'CULTURES' (a nil value)` and similar). No other check fails. Delete `harness_fail.txt` afterwards.

- [ ] **Step 3: Add the Chaos Dwarf data**

In `zzz_derpy_iron_court.lua`, immediately after the `IC.ORIGINS` table (the `}` that follows `{slug = "wastes"},`) and before `IC.PARTIES = {`, insert:

```lua
-- THE CULTURES: where a man grew up. It decides how well he governs (the
-- generator's CULTURES tables hold the figures) and, with his party's draw, who
-- he sits beside. `main` is the party this culture mostly feeds and `side` the
-- party it feeds the rest of the time. `homes` are Old World map province keys:
-- a governor of this culture serves best in them. tools/gen_iron_court.py
-- model_cultures reads each entry back, so keep the one shape.
IC.CULTURES = {
    {slug = "zharr", main = "temple", side = "tower",
     homes = {"cr_oldworld_province_heart_of_zharrduk", "cr_oldworld_province_skull_cliffs"}},
    {slug = "stump", main = "forge", side = "legion",
     homes = {"cr_oldworld_province_foundry_district", "cr_oldworld_province_manufactory_district",
              "cr_oldworld_province_river_district", "cr_oldworld_province_daemons_ruin",
              "cr_oldworld_province_foundry_of_rage", "cr_oldworld_province_putrid_stump"}},
    {slug = "gorgoth", main = "chain", side = "ledger",
     homes = {"cr_oldworld_province_pits_district", "cr_oldworld_province_mount_azgorh",
              "cr_oldworld_province_the_crossroads"}},
    {slug = "zornuzkul", main = "legion", side = "road",
     homes = {"cr_oldworld_province_gate_district", "cr_oldworld_province_zorn_uzkul",
              "cr_oldworld_province_deaths_side", "cr_oldworld_province_river_ruin_lower",
              "cr_oldworld_province_river_ruin_upper", "cr_oldworld_province_skull_road"}},
    {slug = "plain", main = "tower", side = "chain",
     homes = {"cr_oldworld_province_market_district"}},
    {slug = "mines", main = "hearth", side = "forge",
     homes = {"cr_oldworld_province_zandri_road", "cr_oldworld_province_belyerovota",
              "cr_oldworld_province_west_death_pass"}},
    {slug = "wastes", main = "road", side = "ledger",
     homes = {"cr_oldworld_province_howling_district", "cr_oldworld_province_causeway_of_zharr",
              "cr_oldworld_province_howling_wastes_north", "cr_oldworld_province_howling_wastes_south",
              "cr_oldworld_province_the_black_field"}},
    {slug = "gash", main = "ledger", side = "legion",
     homes = {"cr_oldworld_province_gash_kadrak"}},
}

-- A LEGEND'S CULTURE IS FIXED, as his origin and trade are (IC.LORD_HISTORY).
-- Each takes the main culture of the party his fixed trade seats him in; Gorduz
-- keeps the culture of the place he used to be born in. Proposed, for review.
IC.LEGEND_CULTURE = {
    derpy_abnagg = "gash",
    derpy_azeros = "stump",
    derpy_balur = "zornuzkul",
    derpy_black_dwf = "zornuzkul",
    derpy_bzaark = "zornuzkul",
    derpy_gargath = "stump",
    derpy_ghorth = "zharr",
    derpy_snakebeard = "stump",
    derpy_tordrek = "stump",
    derpy_urzkhal = "gorgoth",
    derpy_vraznak = "zharr",
    derpy_gordak = "gorgoth",
    derpy_warrhak = "plain",
    wh3_dlc23_chd_astragoth = "zharr",
    wh3_dlc23_chd_drazhoath = "stump",
    wh3_dlc23_chd_zhatan = "zornuzkul",
    wh3_dlc23_chd_gorduz_backstabber = "zornuzkul",
}

-- A CONQUERED HOUSE'S MEN KEEP ITS CULTURE: house origin slug to culture. A
-- house not listed rolls like anyone else. Proposed, not confirmed.
IC.HOUSE_CULTURE = {
    uzkulak = "zornuzkul",
    conclave = "zharr",
    azgorh = "gorgoth",
}

-- THE RETIRED BIRTHPLACES: a saved lord wearing one of these place traits is
-- converted to the culture with the same slug, quietly. The place rows stay in
-- the pack so the removal resolves; they are never granted again.
IC.PLACE_CULTURE = {
    zharr = "zharr",
    plain = "plain",
    gorgoth = "gorgoth",
    stump = "stump",
    zornuzkul = "zornuzkul",
    gash = "gash",
    mines = "mines",
    wastes = "wastes",
}

-- A TRADE ONLY ONE CULTURE IS DEALT: culture slug to {party, bg}. None here.
IC.CULTURE_TRADE = {
}
```

In the same file, add the tuning value. Replace

```lua
    party_trait_scale   = 1,
```

with

```lua
    party_trait_scale   = 1,
    -- A PARTY'S NEW MAN is its main culture on this many of ten rolls and one of
    -- its side cultures on the rest. Not in IC.TUNE_ORDER: no MCT page for it.
    culture_main_tenths = 7,
```

Add the five names to the required race fields. Replace

```lua
    "MILITARY_DOCTRINE", "PARTY_TROOPS", "TROOPS_DEFAULT",
}
```

with

```lua
    "MILITARY_DOCTRINE", "PARTY_TROOPS", "TROOPS_DEFAULT",
    "CULTURES", "LEGEND_CULTURE", "HOUSE_CULTURE", "PLACE_CULTURE", "CULTURE_TRADE",
}
```

Extend `IC.build_race`. Replace

```lua
    r.MAX_SEATS = #r.PARTIES
    for i = 1, #r.ORIGINS do
        if r.ORIGINS[i].faction then r.MAX_SEATS = r.MAX_SEATS + 1 end
    end
    return r
end
```

with

```lua
    r.MAX_SEATS = #r.PARTIES
    for i = 1, #r.ORIGINS do
        if r.ORIGINS[i].faction then r.MAX_SEATS = r.MAX_SEATS + 1 end
    end
    -- THE CULTURE INDEXES: by slug, by home province, and the trades a culture
    -- reserves (a reserved trade never comes up in an ordinary draw).
    r.CULTURE_BY_SLUG, r.HOME_OF, r.RESERVED_BG = {}, {}, {}
    for i = 1, #r.CULTURES do
        local c = r.CULTURES[i]
        r.CULTURE_BY_SLUG[c.slug] = c
        for j = 1, #c.homes do r.HOME_OF[c.homes[j]] = c.slug end
    end
    for _, t in pairs(r.CULTURE_TRADE) do r.RESERVED_BG[t.bg] = true end
    return r
end
```

- [ ] **Step 4: Add the Dwarf data**

In `zzz_derpy_iron_court_dwarf.lua`, immediately above the comment block that starts `-- REGISTERED LAST, once:` insert:

```lua
-- THE DWARF CULTURES. Same shape as IC.CULTURES; slugs karaz, kadrin and
-- barakvarr also name Dwarf house origins, which is safe because the trait
-- family is part of the key (derpy_ic_cult_dwf_karaz, derpy_ic_house_dwf_karaz).
DWF.CULTURES = {
    {slug = "karaz", main = "temple", side = "tower",
     homes = {"cr_oldworld_province_agrildrin", "cr_oldworld_province_middle_mountains"}},
    {slug = "black", main = "forge", side = "ledger",
     homes = {"cr_oldworld_province_north_black_water", "cr_oldworld_province_black_mountains"}},
    {slug = "barakvarr", main = "ledger", side = "road",
     homes = {"cr_oldworld_province_varenka_hills"}},
    {slug = "kadrin", main = "legion", side = "temple",
     homes = {"cr_oldworld_province_peak_pass", "cr_oldworld_province_grim_kadrin"}},
    {slug = "azul", main = "tower", side = "forge",
     homes = {"cr_oldworld_province_karak_azul"}},
    {slug = "deeps", main = "chain", side = "forge",
     homes = {"cr_oldworld_province_shattered_teeth", "cr_oldworld_province_the_vaults",
              "cr_oldworld_province_delved_heights", "cr_oldworld_province_gianthome_mountains",
              "cr_oldworld_province_karak_azgal"}},
    {slug = "grey", main = "hearth", side = "legion",
     homes = {"cr_oldworld_province_north_grey_mountains", "cr_oldworld_province_south_grey_mountains",
              "cr_oldworld_province_crooked_corridor", "cr_oldworld_province_west_gate"}},
    {slug = "passkeeps", main = "road", side = "legion",
     homes = {"cr_oldworld_province_black_blood_pass", "cr_oldworld_province_black_fire_pass",
              "cr_oldworld_province_high_pass", "cr_oldworld_province_mondidier_pass",
              "cr_oldworld_province_eagles_peak", "cr_oldworld_province_west_gianthome_mountains",
              "cr_oldworld_province_helspire_mounts_east"}},
}

-- EACH DWARF LEGEND'S CULTURE, a judgement call for the author's review: the
-- hold each is best known for.
DWF.LEGEND_CULTURE = {
    wh_main_dwf_thorgrim_grudgebearer = "karaz",
    wh_main_dwf_ungrim_ironfist = "kadrin",
    wh_dlc06_dwf_belegar = "deeps",
    wh_pro01_dwf_grombrindal = "karaz",
    wh2_dlc17_dwf_thorek = "azul",
    wh3_dlc25_dwf_malakai_makaisson = "black",
    wh3_dlc25_dwf_garagrim_ironfist = "kadrin",
    wh3_dlc25_dwf_lord_mikael_leadstrong = "karaz",
    wh2_dlc17_dwf_thane_ghost_artifact = "karaz",
    wh_dlc06_dwf_master_engineer_ghost = "black",
    wh_dlc06_dwf_runesmith_ghost = "azul",
    wh_dlc06_dwf_thane_ghost_1 = "karaz",
    wh_dlc06_dwf_thane_ghost_2 = "karaz",
}

-- A CONQUERED HOLD'S MEN KEEP ITS CULTURE. Zhufbar and Karak Hirn are the Black
-- Holds; Kraka Drak sits among the Deeps. A hold not listed rolls like anyone.
DWF.HOUSE_CULTURE = {
    karaz = "karaz",
    kadrin = "kadrin",
    barakvarr = "barakvarr",
    zhufbar = "black",
    hirn = "black",
    krakadrak = "deeps",
    azul = "azul",
}

-- THE RETIRED BIRTHPLACES, converted to the culture of the same country.
DWF.PLACE_CULTURE = {
    rangers = "passkeeps",
    deeps = "deeps",
    grey = "grey",
    black = "black",
}

-- A KADRIN MAN SEATED IN THE LEGION IS A SLAYER, and nobody else is: the trade
-- is reserved, so it is never drawn for anyone else.
DWF.CULTURE_TRADE = {
    kadrin = {party = "legion", bg = "slayer"},
}

```

(The Slayer trade itself is added to `DWF.BACKGROUNDS.legion` in Task 3, together with its trait row, so the Lua list and the generator list change in one task.)

- [ ] **Step 5: Add the keys, the culture reader, the case and the roll**

In `zzz_derpy_iron_court.lua`, directly under `function IC.gov_bundle_house(slug, faction_key) return IC.key("gov_house", slug, faction_key) end` add:

```lua
-- THE CULTURE'S KEYS. The away bundle, the home bundle and the one shared
-- friction bundle are province bundles; the trait wears the culture.
function IC.culture_trait(slug, faction_key) return IC.key("cult", slug, faction_key) end
function IC.gov_bundle_culture(slug, faction_key) return IC.key("gov_cult", slug, faction_key) end
function IC.gov_bundle_culture_home(slug, faction_key) return IC.key("gov_cult_home", slug, faction_key) end
function IC.gov_bundle_friction(faction_key) return IC.key("gov", "friction", faction_key) end

-- HOME, FOREIGN OR AWAY for a man of `culture` governing `province_key`. A
-- province on another culture's list is foreign, one on his own list is home,
-- and one on no list (any other map, a province the table leaves neutral) is
-- away. A nil or empty key is away: the model asks, it does not assume.
function IC.culture_case(faction_key, culture, province_key)
    local owner = IC.R(faction_key).HOME_OF[province_key or ""]
    if not owner then return "away" end
    return owner == culture and "home" or "foreign"
end
```

Directly under `function IC.bg_of_character(character) ... end` (after its closing `end`) add:

```lua
-- WHICH CULTURE HE WEARS, and the race it belongs to; nil for a man with none.
function IC.culture_of_character(character)
    if not character or character:is_null_interface() then return nil end
    for _, k in ipairs(IC.RACE_ORDER) do
        local R = IC.RACES[k]
        for i = 1, #R.CULTURES do
            local slug = R.CULTURES[i].slug
            if character:has_trait(IC.rkey("cult", slug, R)) then return slug, R end
        end
    end
    return nil
end
```

Directly under `function IC.fewest(pool, tally) ... end` add:

```lua
-- THE CULTURES THAT FEED A PARTY: its one main culture (nil for the Crown) and
-- the cultures that list it as their side party, in IC.CULTURES order.
function IC.cultures_of(faction_key, party)
    local R = IC.R(faction_key)
    local main, sides = nil, {}
    for i = 1, #R.CULTURES do
        local c = R.CULTURES[i]
        if c.main == party then main = c.slug end
        if c.side == party then sides[#sides + 1] = c.slug end
    end
    return main, sides
end

-- A NEW MAN'S CULTURE, drawn for the party he was dealt to. The main culture
-- on culture_main_tenths of ten rolls, otherwise one of the side cultures; a
-- party with no side culture is its main culture and makes no random call. The
-- Crown (which no culture feeds) and a man with no party draw uniformly from
-- all of the race's cultures.
function IC.roll_culture(faction_key, party)
    local R = IC.R(faction_key)
    local main, sides = IC.cultures_of(faction_key, party)
    if not main then
        return R.CULTURES[cm:random_number(#R.CULTURES, 1)].slug
    end
    if #sides == 0 then return main end
    if cm:random_number(10, 1) <= IC.TUNE.culture_main_tenths then return main end
    return sides[cm:random_number(#sides, 1)]
end
```

- [ ] **Step 6: Add the harness arity entries**

In the harness `RACE_ARITY` table add a line after `standing_trait = 2, ambition_trait = 2, gov_bundle_base = 1, troop_key = 2,`:

```lua
    culture_trait = 2, gov_bundle_culture = 2, gov_bundle_culture_home = 2,
    gov_bundle_friction = 1, culture_case = 3, roll_culture = 2, cultures_of = 2,
```

(`stamp_culture`, `culture_stance` and `man_stance` are added to the table in Tasks 4 and 6, with the functions.)

Then, in the check `race plumbing: a race missing a required field is refused at registration`, replace

```lua
    local drops = {"key", "subculture", "infix", "tune", "OFFICES", "PARTY_TROOPS", "TROOPS_DEFAULT"}
```

with

```lua
    local drops = {"key", "subculture", "infix", "tune", "OFFICES", "PARTY_TROOPS", "TROOPS_DEFAULT", "CULTURES"}
```

so a race with no culture table is shown to be refused.

- [ ] **Step 7: Run the checks**

```powershell
& "C:\Program Files (x86)\Lua\5.1\luac.exe" -p "Modding Files\pack\script\campaign\mod\zzz_derpy_iron_court.lua"
& "C:\Program Files (x86)\Lua\5.1\luac.exe" -p "Modding Files\pack\script\campaign\mod\zzz_derpy_iron_court_dwarf.lua"
$env:IC_TEST_ALL = "1"; & "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua 2> harness_fail.txt; Remove-Item Env:IC_TEST_ALL
Get-Content harness_fail.txt
```

Expected: both `luac -p` exit 0. The ten `cultures:` checks pass, and so do the `race plumbing` checks, because the new fields are on `IC` and copied into `chd`. If `race plumbing: the Chaos Dwarf race is registered over the existing tables` fails, a field is missing from the `IC.X` definitions. Fix and rerun until the output is `iron court harness: ok (1103 checks)`. Delete `harness_fail.txt`.

- [ ] **Step 8: Run the Lua gates**

```powershell
foreach ($f in "zzz_derpy_iron_court","zzz_derpy_iron_court_dwarf") {
  py tools\check_lua_api.py "Modding Files\pack\script\campaign\mod\$f.lua"
}
py tools\check_lua_undeclared.py
py tools\check_lua_literal_left.py
```

Expected: `0 suspect call(s)` for each file and no findings from the other two. (`check_lua_api.py` with no argument scans every mod in the folder and reports three calls in `ai_test_tower_of_zharr.lua` and `derpy_more_resources_flows.lua`; those are not this work, so name the Iron Court files.)

- [ ] **Step 9: Ledger**

Append to the ledger: `Task 1 done: zzz_derpy_iron_court.lua, zzz_derpy_iron_court_dwarf.lua, _iron_court_harness.lua; harness 1103 checks; luac, check_lua_api (Iron Court files), check_lua_undeclared, check_lua_literal_left clean.`

---

### Task 2: Generator effect vocabulary

**Files:**
- Modify: `tools/gen_iron_court.py` (new constants before `ALL_EFFECTS`; `EFFECT_TEXT`, `EFFECT_SHORT`, `EFFECT_PERCENT`; `selftest()`)

**Interfaces:**
- Consumes: `signed_value(effect, magnitude, intent)`, `BOON`, `MALUS`, the existing `E_ENVOY_CTL`, `E_ENVOY_LAB`, `E_ENVOY_ARM`.
- Produces: the effect tuples `(key, scope, is_positive_value_good)` named below, `CULTURE_EFFECTS` (the eighteen tuples new to `ALL_EFFECTS`), and their wording in the three dicts. Task 3 builds every culture row from these names.

- [ ] **Step 1: Write the failing selftest block**

In `tools/gen_iron_court.py`, at the top of `selftest()` (directly under `def selftest():`, above the line `# THE RACE SEAM. The tiers are counted off the`) insert:

```python
    # THE CULTURE EFFECTS' SIGNS. A boon on a cost or loss effect is negative, a
    # drawback on a gain effect is negative, and the figures are the spec's.
    assert signed_value(E_C_LABOUR, 8, BOON) == -8
    assert signed_value(E_C_LABOUR, 10, MALUS) == 10
    assert signed_value(E_C_SIEGE, 20, BOON) == -20
    assert signed_value(E_C_BTIME, 1, BOON) == -1
    assert signed_value(E_C_BTIME, 1, MALUS) == 1
    assert signed_value(E_C_REPLEN_DOWN, 10, MALUS) == -10
    assert signed_value(E_C_ORDER, 4, MALUS) == -4
    assert signed_value(E_C_RECRUIT, 10, MALUS) == 10
    assert signed_value(E_C_RECRUIT, 10, BOON) == -10
    assert signed_value(E_C_GDP, 10, MALUS) == -10
    assert signed_value(E_C_BCOST, 10, BOON) == -10
    assert signed_value(E_C_UPKEEP, 10, BOON) == -10
    assert signed_value(E_C_RUSH, 10, BOON) == -10
    assert len(CULTURE_EFFECTS) == 18 and len(set(CULTURE_EFFECTS)) == 18, "the culture effects are not eighteen distinct tuples"
    for _e in CULTURE_EFFECTS:
        assert _e[0] in EFFECT_TEXT and _e[0] in EFFECT_SHORT, "no wording for %s" % _e[0]
        assert len(EFFECT_SHORT[_e[0]]) <= 20, "label too long for %s" % _e[0]
```

- [ ] **Step 2: Run it and confirm it fails**

```powershell
py tools\gen_iron_court.py --selftest
```

Expected: `NameError: name 'E_C_LABOUR' is not defined`.

- [ ] **Step 3: Add the effect tuples**

Directly above the line `ALL_EFFECTS = [E_ARMAMENTS, E_WORKLOAD, E_RAWMAT, E_ORDER, E_GDP, E_SLAVE_ORDER,` insert:

```python
# THE CULTURES' EFFECTS. Every pair below is one CA ships at a province_to_*
# scope in its effect bundles, read from the junction tables on 2026-10-15, and
# every flag is CA's own. Three are aliases of the envoy's pairs. Never write a
# sign: signed_value works it out from the flag and the intent.
E_C_ORDER = E_ENVOY_CTL
E_C_LABOUR = E_ENVOY_LAB
E_C_ARMS = E_ENVOY_ARM
E_C_WOM = ("wh3_main_effect_winds_of_magic_increase_chance_mod",
           "province_to_region_own_unseen", True)
E_C_BTIME = ("wh3_main_effect_building_construction_time_add_mod_all",
             "province_to_region_own", False)
E_C_RUSH = ("wh3_dlc23_effect_rush_construction_slave_cost",
            "province_to_region_own_unseen", False)
E_C_SIEGE = ("wh_main_effect_force_army_campaign_siege_defend_attrition",
             "province_to_force_own_provincewide_unseen", False)
E_C_LEAD = ("wh_main_effect_force_stat_leadership",
            "province_to_force_own_provincewide", True)
E_C_GDP = ("wh_main_effect_economy_gdp_mod_all",
           "province_to_region_own_unseen", True)
E_C_BCOST = ("wh_main_effect_building_construction_cost_mod",
             "province_to_region_own", False)
E_C_RECRUIT = ("wh_main_effect_force_all_campaign_recruitment_cost_all",
               "province_to_force_own_provincewide", False)
# THE SAME KEY AT TWO SCOPES: as a boon it reaches the province, as a drawback
# it reaches the armies standing in it (CA ships -200 to 20 on the second).
E_C_REPLEN = ("wh_main_effect_force_all_campaign_replenishment_rate",
              "province_to_province_own_unseen", True)
E_C_REPLEN_DOWN = ("wh_main_effect_force_all_campaign_replenishment_rate",
                   "province_to_force_own_provincewide", True)
E_C_UPKEEP = ("wh_main_effect_force_all_campaign_upkeep",
              "province_to_force_own_provincewide", False)
E_C_MOVE = ("wh2_dlc09_effect_force_own_campaign_movement_range_province",
            "province_to_force_own_provincewide_unseen", True)
E_C_AMBUSH = ("wh_main_effect_force_army_campaign_ambush_attack_success_chance",
              "province_to_force_own_provincewide_unseen", True)
E_C_LOOT = ("wh_main_effect_force_all_campaign_post_battle_loot_mod",
            "province_to_character_own_text", True)
E_C_SEA = ("wh_main_effect_economy_gdp_mod_trade_sea",
           "province_to_region_own_unseen", True)
E_C_RESEARCH = ("wh_main_effect_technology_research_rate_mod",
                "province_to_faction_unseen", True)
E_C_MDEF = ("wh_main_effect_force_stat_melee_defence",
            "province_to_force_own_provincewide", True)
E_C_MATK = ("wh_main_effect_force_stat_melee_attack",
            "province_to_force_own_provincewide", True)
# The eighteen tuples ALL_EFFECTS does not already hold (the three aliases above
# are in it as the envoy's).
CULTURE_EFFECTS = [E_C_WOM, E_C_BTIME, E_C_RUSH, E_C_SIEGE, E_C_LEAD, E_C_GDP,
                   E_C_BCOST, E_C_RECRUIT, E_C_REPLEN, E_C_REPLEN_DOWN, E_C_UPKEEP,
                   E_C_MOVE, E_C_AMBUSH, E_C_LOOT, E_C_SEA, E_C_RESEARCH,
                   E_C_MDEF, E_C_MATK]

```

Replace

```python
               E_ENVOY_CTL, E_ENVOY_ARM, E_ENVOY_RAW, E_ENVOY_LAB] + LAW_EFFECTS + DWF_EFFECTS
```

with

```python
               E_ENVOY_CTL, E_ENVOY_ARM, E_ENVOY_RAW, E_ENVOY_LAB] + LAW_EFFECTS + DWF_EFFECTS \
              + CULTURE_EFFECTS
```

Note: `E_C_GDP`, `E_C_RECRUIT`, `E_C_UPKEEP`, `E_C_LOOT`, `E_C_RESEARCH` and the two replenishment tuples share a KEY with an existing effect but differ in scope, so `len(set(CULTURE_EFFECTS)) == 18` holds (the set is of whole tuples).

- [ ] **Step 4: Add the wording**

CA's text for each new key was read from `local_en` on 2026-10-15; the existing check compares `EFFECT_TEXT` to it byte for byte. In `EFFECT_TEXT`, replace

```python
    E_DWF_ART_RANK[0]: "Recruit rank: %+n for Artillery and Flying War Machine units",
}
```

with

```python
    E_DWF_ART_RANK[0]: "Recruit rank: %+n for Artillery and Flying War Machine units",
    # THE CULTURES' NEW KEYS. The others they use already have a line above.
    E_C_WOM[0]: "Chance of Winds of Magic increasing in strength when changing: %+n%",
    E_C_BTIME[0]: "Construction time: %+n for all buildings (minimum of 1 turn)",
    E_C_RUSH[0]: "Rush Construction Slave cost: %+n%",
    E_C_SIEGE[0]: "Attrition: %+n% when under siege",
    E_C_LEAD[0]: "Leadership: %+n",
    E_C_BCOST[0]: "Construction cost: %+n% for all buildings",
    E_C_MOVE[0]: "Campaign movement range: %+n% for own armies starting their turn in this province",
    E_C_AMBUSH[0]: "Ambush success chance: %+n%",
    E_C_SEA[0]: "Income from Ports: %+n%",
    E_C_MDEF[0]: "Melee defence: %+n",
    E_C_MATK[0]: "Melee attack: %+n",
}
```

In `EFFECT_SHORT`, replace

```python
    E_DWF_ART_RANK[0]: "Artillery rank",
}
```

with

```python
    E_DWF_ART_RANK[0]: "Artillery rank",
    E_C_WOM[0]: "Winds of Magic",
    E_C_BTIME[0]: "Build time",
    E_C_RUSH[0]: "Rush labour cost",
    E_C_SIEGE[0]: "Siege attrition",
    E_C_LEAD[0]: "Leadership",
    E_C_BCOST[0]: "Construction cost",
    E_C_MOVE[0]: "Movement range",
    E_C_AMBUSH[0]: "Ambush success",
    E_C_SEA[0]: "Port income",
    E_C_MDEF[0]: "Melee defence",
    E_C_MATK[0]: "Melee attack",
}
```

(`E_C_BCOST`'s key differs from `E_CONSTRUCT`'s, and `E_C_MOVE`'s from `E_MOVEMENT`'s, so these are new entries and not duplicates.)

In `EFFECT_PERCENT`, replace

```python
    E_ENVOY_GROW[0]: False, E_DWF_SETTLER_SRC[0]: False, E_DWF_ART_RANK[0]: False,
}
```

with

```python
    E_ENVOY_GROW[0]: False, E_DWF_SETTLER_SRC[0]: False, E_DWF_ART_RANK[0]: False,
    E_C_BTIME[0]: False, E_C_LEAD[0]: False, E_C_MDEF[0]: False, E_C_MATK[0]: False,
}
```

- [ ] **Step 5: Run the selftest and the check**

```powershell
py tools\gen_iron_court.py --selftest
py tools\gen_iron_court.py --check
```

Expected: `selftest: ok (146 bundles, 216 junctions, 280 traits, 2066 loc)` after about four minutes, and `ok: 146 bundles, 216 junctions, 280 traits, 2066 loc rows`. Task 2 adds words and no rows, so the counts are the baseline's. `--check` item 1 (vanilla key and flag), item 2 (shipped pair) and the wording check all read the eighteen new tuples; a wrong flag, scope or word fails by name. If the wording check names a key, copy CA's exact text from the failure message.

- [ ] **Step 6: Ledger**

Append: `Task 2 done: tools/gen_iron_court.py; gen --selftest and --check green (18 effects added).`

---

### Task 3: Generator culture rows, Dwarf rows, Slayer trade, checks

**Files:**
- Modify: `tools/gen_iron_court.py` (data before `RACES`, `TRAIT_CATS`, `RACES` entries, `DWF_BACKGROUNDS`, `DWF_BG_COLOUR`, `emit_cultures`, calls in `build()` and `emit_dwf`, `model_*` scrapers, `check_cultures`, `culture_range_notes`, `check()`, `main()`, `selftest()`)
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_dwarf.lua` (`DWF.BACKGROUNDS.legion`)

**Interfaces:**
- Consumes: Task 1's Lua tables and keys; Task 2's `E_C_*`.
- Produces: `CHD_CULTURES`, `DWF_CULTURES` (lists of dicts with `slug`, `name`, `archetype`, `colour`, `boons` as `[(effect, magnitude)]`, `drawback` as `(effect, magnitude)`); `CULTURE_HOME_PCT = 150`, `CULTURE_FRICTION = 4`; `home_value(m)`, `culture_effects(c) -> (away, home)`, `culture_explanation(c)`, `emit_cultures(emit, emit_trait, loc, race)`; `model_cultures(prefix)`, `model_pairs(name, prefix)`, `ow_province_keys()`, `check_cultures(race)`, `culture_range_notes()`. Generated keys, per race infix `I`: bundles `derpy_ic_gov_cult_<I><slug>`, `derpy_ic_gov_cult_home_<I><slug>`, `derpy_ic_gov_<I>friction`; trait `derpy_ic_cult_<I><slug>`; loc `derpy_ic_cult_name_<I><slug>`; line loc `derpy_ic_effects_<bundle key>`.

- [ ] **Step 1: Write the failing selftest block**

At the top of `selftest()`, directly after the Task 2 block, insert:

```python
    # THE CULTURE SEAM. Home figures round half up; both races' tables agree with
    # the Lua; and the checks are shown to fail on a planted fault.
    assert (home_value(15), home_value(25), home_value(1), home_value(4),
            home_value(8), home_value(5)) == (23, 38, 2, 6, 12, 8), "home rounding"
    assert check_cultures("chd") == [], check_cultures("chd")
    assert check_cultures("dwf") == [], check_cultures("dwf")
    _kept = list(RACES["chd"]["CULTURES"])
    try:
        RACES["chd"]["CULTURES"].pop()
        assert check_cultures("chd"), "a culture missing from the generator was not reported"
    finally:
        RACES["chd"]["CULTURES"][:] = _kept
    _real_ow = ow_province_keys
    try:
        globals()["ow_province_keys"] = lambda: set()
        _bad = check_cultures("chd")
        assert any("is not an Old World province" in p for p in _bad), \
            "a home province off the Old World map was not reported"
    finally:
        globals()["ow_province_keys"] = _real_ow
    _real_ex = culture_explanation
    try:
        globals()["culture_explanation"] = lambda c: "Hierophant. Governing: nothing."
        _bad = check_cultures("chd")
        assert any("does not quote" in p for p in _bad), \
            "a trait text that omits the bundle's figures was not reported"
    finally:
        globals()["culture_explanation"] = _real_ex
    assert check_cultures("chd") == [], "the planted faults were not restored"
```

- [ ] **Step 2: Run it and confirm it fails**

```powershell
py tools\gen_iron_court.py --selftest
```

Expected: `NameError: name 'home_value' is not defined`.

- [ ] **Step 3: Add the trait category**

In `TRAIT_CATS`, replace

```python
    "derpy_ic_cat_ambition": "ui/campaign ui/effect_bundles/chd_conclave_influence.png",
}
```

with

```python
    "derpy_ic_cat_ambition": "ui/campaign ui/effect_bundles/chd_conclave_influence.png",
    # WHERE HE GREW UP, on a picture CA already ships (the old birthplace's).
    "derpy_ic_cat_culture": "ui/campaign ui/effect_bundles/settlement.png",
}
```

- [ ] **Step 4: Add the culture data and helpers**

Directly above the comment line `# THE RACES. `prefix` is the Lua table prefix the race's tables are declared` insert:

```python
# THE CULTURES (spec 5.2). One dict per culture; the trait text, the away bundle,
# the home bundle and the name loc are all built from it, and check_cultures
# holds the Lua's tables (slug, main, side, homes) to the same list. `boons` are
# (effect, magnitude) and `drawback` is one (effect, magnitude); never a sign.
# The first four Chaos Dwarf drawbacks are the source document's; the other
# four and every Dwarf one are the author's to adjust.
CHD_CULTURES = [
    {"slug": "zharr", "name": "Heart of Zharrduk", "archetype": "Hierophant",
     "colour": "He grew up in the shadow of the Great Temple of Hashut.",
     "boons": [(E_C_WOM, 20), (E_C_ORDER, 3)], "drawback": (E_C_LABOUR, 10)},
    {"slug": "stump", "name": "Foundry Districts", "archetype": "Foundry Baron",
     "colour": "He grew up among the factory forges, where the machine shops never cool.",
     "boons": [(E_C_ARMS, 10), (E_C_BTIME, 1)], "drawback": (E_C_ORDER, 4)},
    {"slug": "gorgoth", "name": "Tower of Gorgoth", "archetype": "Labour Master",
     "colour": "He grew up in the mining colony around the Tower of Gorgoth.",
     "boons": [(E_C_LABOUR, 8), (E_C_RUSH, 10)], "drawback": (E_C_ORDER, 4)},
    {"slug": "zornuzkul", "name": "Zorn Uzkul", "archetype": "Infernal Warden",
     "colour": "He grew up among the border guards of the Black Fortress.",
     "boons": [(E_C_SIEGE, 20), (E_C_LEAD, 6)], "drawback": (E_C_GDP, 10)},
    {"slug": "plain", "name": "Market District", "archetype": "Clerk",
     "colour": "He grew up in the Market District, counting stalls and tallies.",
     "boons": [(E_C_GDP, 8), (E_C_BCOST, 10)], "drawback": (E_C_RECRUIT, 10)},
    {"slug": "mines", "name": "Mines of Mingol", "archetype": "Deep-Hearth",
     "colour": "He grew up by the Mingol mines and keeps a hearth of his own.",
     "boons": [(E_C_REPLEN, 4), (E_C_UPKEEP, 10)], "drawback": (E_C_BTIME, 1)},
    {"slug": "wastes", "name": "Howling Wastes", "archetype": "Pathfinder",
     "colour": "He grew up on the Howling Wastes, where a road is only as safe as its last traveller.",
     "boons": [(E_C_MOVE, 10), (E_C_AMBUSH, 10)], "drawback": (E_C_REPLEN_DOWN, 10)},
    {"slug": "gash", "name": "Gash Kadrak", "archetype": "Tribute-taker",
     "colour": "He grew up in Gash Kadrak, where tribute goes to the man who can collect it.",
     "boons": [(E_C_LOOT, 15), (E_C_GDP, 6)], "drawback": (E_C_ORDER, 4)},
]

DWF_CULTURES = [
    {"slug": "karaz", "name": "Karaz-a-Karak", "archetype": "Royal Traditionalist",
     "colour": "He grew up where the High King sits, and he quotes precedent before he quotes prices.",
     "boons": [(E_C_GDP, 8), (E_C_ORDER, 3)], "drawback": (E_C_BTIME, 1)},
    {"slug": "black", "name": "The Black Holds", "archetype": "Engineer",
     "colour": "He grew up among the toolmakers and gyro hangars of the Black Holds.",
     "boons": [(E_C_RECRUIT, 10), (E_C_BTIME, 1)], "drawback": (E_C_ORDER, 4)},
    {"slug": "barakvarr", "name": "Barak Varr", "archetype": "Merchant Lord",
     "colour": "He grew up on the quays of Barak Varr, the sea-gate of the Karaz Ankor.",
     "boons": [(E_C_SEA, 25), (E_C_GDP, 6)], "drawback": (E_C_RECRUIT, 10)},
    {"slug": "kadrin", "name": "Karak Kadrin", "archetype": "Slayer",
     "colour": "He grew up in the Slayer Keep, where a man's best day is his last.",
     "boons": [(E_C_MATK, 5), (E_C_REPLEN, 4)], "drawback": (E_C_GDP, 15)},
    {"slug": "azul", "name": "Karak Azul", "archetype": "Runesmith",
     "colour": "He grew up in a hold renowned for the quality of its weapons.",
     "boons": [(E_C_RESEARCH, 5), (E_C_MDEF, 5)], "drawback": (E_C_BCOST, 10)},
    {"slug": "deeps", "name": "The Deeps", "archetype": "Deep-Miner",
     "colour": "He grew up near the gem and silver mines and trusts what is dug out of the rock.",
     "boons": [(E_C_GDP, 8), (E_C_BCOST, 10)], "drawback": (E_C_ORDER, 3)},
    {"slug": "grey", "name": "Grey Mountains", "archetype": "Hold-Keeper",
     "colour": "He grew up in a hold that struggles to keep its numbers up and wastes no one.",
     "boons": [(E_C_SIEGE, 20), (E_C_UPKEEP, 10)], "drawback": (E_C_REPLEN_DOWN, 10)},
    {"slug": "passkeeps", "name": "The Pass-Keeps", "archetype": "Pass-Warden",
     "colour": "He grew up in a keep that guards a pass or an entrance to the Underway.",
     "boons": [(E_C_MOVE, 10), (E_C_AMBUSH, 10)], "drawback": (E_C_GDP, 8)},
]

# A BOON IS 150% OF ITS AWAY FIGURE AT HOME, rounded to the nearest whole number
# with halves rounding up, in integers. The drawback is the same at home. A
# governor in another culture's home loses CULTURE_FRICTION Control on top.
CULTURE_HOME_PCT = 150
CULTURE_FRICTION = 4


def home_value(magnitude):
    """A boon's magnitude at home. Integer arithmetic: 15 -> 23, 25 -> 38, 1 -> 2."""
    return (CULTURE_HOME_PCT * magnitude + 50) // 100


def culture_effects(c):
    """(away, home): the effect lists of a culture's two bundles, boons first
    and the drawback last. The same shape emit() takes."""
    effect, magnitude = c["drawback"]
    drawback = [(effect, magnitude, MALUS)]
    away = [(e, m, BOON) for e, m in c["boons"]] + drawback
    home = [(e, home_value(m), BOON) for e, m in c["boons"]] + drawback
    return away, home


def culture_explanation(c):
    """The trait's tooltip: archetype, the figures in CA's wording, and the two
    rules. Built from culture_effects, so it cannot differ from the away bundle."""
    away, _home = culture_effects(c)
    boons = ", ".join(effect_line(e, m, i) for e, m, i in away[:-1])
    drawback = effect_line(*away[-1])
    return ("%s. Governing: %s. Drawback: %s. At home the benefits are %d%% stronger; "
            "in a province another culture calls home he loses %d Control."
            % (c["archetype"], boons, drawback, CULTURE_HOME_PCT - 100, CULTURE_FRICTION))


```

- [ ] **Step 5: Wire the tables into the race dicts**

In the `RACES = {` literal replace

```python
            "OFFICES": OFFICES, "GOVERNMENTS": GOVERNMENTS, "LAWS": LAWS},
}
```

with

```python
            "OFFICES": OFFICES, "GOVERNMENTS": GOVERNMENTS, "LAWS": LAWS,
            "CULTURES": CHD_CULTURES, "BUNDLE_ICON": BUNDLE_ICON},
}
```

In `RACES["dwf"] = {` replace

```python
    "BUNDLE_ICON": "trait_dwarf.png",
}
```

with

```python
    "BUNDLE_ICON": "trait_dwarf.png",
    "CULTURES": DWF_CULTURES,
}
```

- [ ] **Step 6: Add the Slayer trade (generator and Lua together)**

In `DWF_BACKGROUNDS` replace

```python
    "legion": [("longbeard",    "Longbeard"),
               ("ironbreaker",  "Ironbreaker"),
               ("thane",        "Thane of a Clan")],
```

with

```python
    "legion": [("longbeard",    "Longbeard"),
               ("ironbreaker",  "Ironbreaker"),
               ("thane",        "Thane of a Clan"),
               ("slayer",       "Slayer")],
```

In `DWF_BG_COLOUR`, directly under the `"ironbreaker":` line (`"ironbreaker":  "He has held the underways against things that never come up to the light.",`) insert:

```python
    "slayer":       "He gave up his hold and his name to seek a death worthy of his grudge.",
```

In `zzz_derpy_iron_court_dwarf.lua` replace

```lua
    legion = {"longbeard", "ironbreaker", "thane"},
```

with

```lua
    legion = {"longbeard", "ironbreaker", "thane", "slayer"},
```

(The Dwarf `CULTURE_TRADE` that reserves it is already in place from Task 1. The trait row, the name loc and the colour come out of the existing background loop in `emit_dwf`.)

- [ ] **Step 7: Emit the culture rows**

Directly above `def emit_dwf(emit, emit_trait, emit_member, loc):` insert:

```python
def emit_cultures(emit, emit_trait, loc, race):
    """One race's culture rows: per culture an away bundle, a home bundle, a name
    loc and the trait; and one friction bundle for the race. Both bundles are
    province bundles (the envoy's shape), applied with
    cm:apply_effect_bundle_to_faction_province."""
    R = RACES[race]
    icon = R["BUNDLE_ICON"]

    def K(kind, slug):
        return bundle_key(kind, slug, race)

    for c in R["CULTURES"]:
        away, home = culture_effects(c)
        emit(K("gov_cult", c["slug"]), "Governor: " + c["name"],
             "The %s's way of governing." % c["archetype"], "province", away, icon=icon)
        emit(K("gov_cult_home", c["slug"]), "Governor at Home: " + c["name"],
             "At home the benefits are %d%% stronger." % (CULTURE_HOME_PCT - 100),
             "province", home, icon=icon)
        loc.append({"key": K("cult_name", c["slug"]), "text": c["name"], "tooltip": "false"})
        emit_trait(K("cult", c["slug"]), "Culture: " + c["name"], c["colour"],
                   culture_explanation(c), "His culture has been struck from the rolls.",
                   "derpy_ic_cat_culture")
    emit(K("gov", "friction"), "Governor: Foreign Province",
         "He governs a province another culture calls home.", "province",
         [(E_C_ORDER, CULTURE_FRICTION, MALUS)], icon=icon)


```

In `build()`, directly above the comment line `    # WHAT HE IS, which is the whole of the membership rule. A background` insert:

```python
    # WHERE HE GREW UP (the Chaos Dwarf cultures; the Dwarf ones come out of
    # emit_dwf). The place origins above stay so an old save's trait resolves.
    emit_cultures(emit, emit_trait, loc, "chd")

```

In `emit_dwf`, directly above the line `    for party, _d, _e, _m in R["PARTIES"]:\n        for slug, display in R["BACKGROUNDS"][party]:` (the Dwarf backgrounds loop) insert:

```python
    emit_cultures(emit, emit_trait, loc, "dwf")
```

- [ ] **Step 8: Add the scrapers and the checks**

Directly above `def check_dwf():` insert (after the `_bare` helper):

```python
# THE OLD WORLD CAMPAIGN PACK (Workshop 3081800026, "TOW" by ChaosRobie). Its
# province loc names every province the map has, so a home key that is not in it
# names nothing.
OW_PACK = r"F:\SteamLibrary\steamapps\workshop\content\1142710\3081800026\!cr_oldworld_campaign.pack"
_OW_KEYS = []


def ow_province_keys():
    """Every province key the Old World pack names. Its loc rows are
    provinces_onscreen_<key> and the key keeps its own cr_oldworld_province_ prefix."""
    if _OW_KEYS:
        return _OW_KEYS[0]
    import read_pack_index as _rpi
    import read_vanilla_loc as _rvl
    hits = _rpi.read(OW_PACK, "!cr_oldworld_provinces__.loc")
    if len(hits) != 1:
        raise RuntimeError("expected one province loc in the Old World pack, found %d" % len(hits))
    _path, compressed, data = hits[0]
    if compressed != 0:
        raise RuntimeError("the Old World province loc is compressed")
    stem = "provinces_onscreen_"
    keys = set(k[len(stem):] for k in dict(_rvl.parse(data)) if k.startswith(stem))
    if not keys:
        raise RuntimeError("the Old World province loc named no province")
    _OW_KEYS.append(keys)
    return keys


def model_cultures(prefix="IC"):
    """[(slug, main, side, [home keys])] from <prefix>.CULTURES, in its order.
    Raises rather than returning nothing: a silent empty list is a check that
    passes over a table it cannot read."""
    body = lua_table("CULTURES", prefix)
    if body is None:
        raise RuntimeError("the model Lua declares no %s.CULTURES" % prefix)
    out = []
    for slug, main, side, homes in re.findall(
            r'\{slug = "(\w+)", main = "(\w+)", side = "(\w+)",\s*homes = \{([^}]*)\}\}', body):
        out.append((slug, main, side, re.findall(r'"(\w+)"', homes)))
    if not out:
        raise RuntimeError("%s.CULTURES parsed to no culture" % prefix)
    return out


def model_pairs(name, prefix="IC"):
    """{key: value} from a `<prefix>.<name> = { key = "value", ... }` table.
    Comment lines are dropped so a comment cannot add a pair."""
    body = lua_table(name, prefix)
    if body is None:
        raise RuntimeError("the model Lua declares no %s.%s" % (prefix, name))
    body = "\n".join(l for l in body.splitlines() if not l.strip().startswith("--"))
    return dict(re.findall(r'(\w+)\s*=\s*"(\w+)"', body))


def model_culture_trades(prefix="IC"):
    """{culture: (party, bg)} from <prefix>.CULTURE_TRADE."""
    body = lua_table("CULTURE_TRADE", prefix)
    if body is None:
        raise RuntimeError("the model Lua declares no %s.CULTURE_TRADE" % prefix)
    return dict((c, (p, b)) for c, p, b in
                re.findall(r'(\w+)\s*=\s*\{party = "(\w+)", bg = "(\w+)"\}', body))


def _junctions_by_bundle(tables):
    out = {}
    for j in tables["effect_bundles_to_effects_junctions"]:
        out.setdefault(j["effect_bundle_key"], []).append(j)
    return out


def _quoted_line(junction):
    """The line the trait text must hold for one junction row, rebuilt from the
    ROW (the emitted value) and CA's wording, not from the culture table."""
    v = int(float(junction["value"]))
    return EFFECT_TEXT[junction["effect_key"]].replace("%+n", "%+d" % v).replace("%n", "%d" % v)


def check_cultures(race="chd"):
    """The culture tables: the Lua's and this file's are one list, every rival
    party is fed, the home provinces are on the Old World map, the places, houses
    and legends point at cultures, and the trait text quotes the figures the
    bundle carries. The law stances are check_culture_laws (Task 6)."""
    out = []
    R = RACES[race]
    prefix = R["prefix"]
    mine = R["CULTURES"]
    model = model_cultures(prefix)
    if [c["slug"] for c in mine] != [m[0] for m in model]:
        return ["%s.CULTURES is %s and the generator's list is %s"
                % (prefix, [m[0] for m in model], [c["slug"] for c in mine])]
    slugs = set(c["slug"] for c in mine)
    rivals = [p[0] for p in R["PARTIES"] if p[0] != CROWN]

    # 1. Who feeds whom, and where each culture is at home.
    mains, feeders, homes_of = {}, {}, {}
    for slug, main, side, homes in model:
        for p in (main, side):
            if p not in rivals:
                out.append("culture %s feeds %s, which is no rival party" % (slug, p))
        if main == side:
            out.append("culture %s feeds %s as both main and side" % (slug, main))
        mains[main] = mains.get(main, 0) + 1
        feeders.setdefault(main, set()).add(slug)
        feeders.setdefault(side, set()).add(slug)
        if not homes:
            out.append("culture %s has no home province" % slug)
        for h in homes:
            if h in homes_of:
                out.append("%s is home to both %s and %s" % (h, homes_of[h], slug))
            homes_of[h] = slug
    for p in rivals:
        if mains.get(p, 0) != 1:
            out.append("party %s has %d main cultures, not 1" % (p, mains.get(p, 0)))
        if not feeders.get(p):
            out.append("party %s is fed by no culture" % p)

    # 2. The homes are on the Old World map.
    try:
        known = ow_province_keys()
    except Exception as exc:
        out.append("the Old World pack is unreadable, so home provinces cannot be checked: %r" % (exc,))
    else:
        for h, slug in sorted(homes_of.items()):
            if not h.startswith("cr_oldworld_province_") or h not in known:
                out.append("%s (home of %s) is not an Old World province" % (h, slug))

    # 3. The retired places, the holds and the legends point at real cultures.
    places = set(o[0] for o in R["ORIGINS"] if o[1] is None)
    houses = set(o[0] for o in R["ORIGINS"] if o[1] is not None)
    place_map = model_pairs("PLACE_CULTURE", prefix)
    if set(place_map) != places:
        out.append("%s.PLACE_CULTURE covers %s and the places are %s"
                   % (prefix, sorted(place_map), sorted(places)))
    for place, cult in place_map.items():
        if cult not in slugs:
            out.append("place %s converts to %s, which is no culture" % (place, cult))
    for house, cult in model_pairs("HOUSE_CULTURE", prefix).items():
        if house not in houses:
            out.append("HOUSE_CULTURE names %s, which is no house origin" % house)
        if cult not in slugs:
            out.append("house %s takes %s, which is no culture" % (house, cult))
    legend = model_pairs("LEGEND_CULTURE", prefix)
    for subtype, cult in legend.items():
        if cult not in slugs:
            out.append("legend %s takes %s, which is no culture" % (subtype, cult))
    if race == "chd":
        want = set(re.findall(r"\n    (\w+)\s*=\s*\{(?:origin|bg)", lua_table("LORD_HISTORY", "IC") or ""))
        if not want:
            out.append("IC.LORD_HISTORY parsed to no legend")
        elif set(legend) != want:
            out.append("IC.LEGEND_CULTURE covers %s and IC.LORD_HISTORY has %s"
                       % (sorted(legend), sorted(want)))
    else:
        subs = set(re.findall(r'\["(\w+)"\]', _dwf_block("LEGEND_SUBTYPES")))
        stray = sorted(set(legend) - subs)
        if stray:
            out.append("DWF.LEGEND_CULTURE names %s, who are no legend" % stray)

    # 4. A reserved trade names a real culture, party and trade.
    for cult, (party, bg) in model_culture_trades(prefix).items():
        if cult not in slugs:
            out.append("CULTURE_TRADE names %s, which is no culture" % cult)
        if bg not in [b[0] for b in R["BACKGROUNDS"].get(party, [])]:
            out.append("culture %s reserves %s, which is no trade of party %s" % (cult, bg, party))

    # 5. The rows: home is the away bundle with its boons raised, the trait text
    #    quotes every figure, the friction bundle exists, the plain-words rule holds.
    tables = build()
    bundles = dict((r["key"], r) for r in tables["effect_bundles"])
    traits = dict((r["key"], r) for r in tables["character_traits"])
    by = _junctions_by_bundle(tables)
    loc = dict((r["key"], r["text"]) for r in tables["loc"])
    for c in mine:
        slug = c["slug"]
        away_key = bundle_key("gov_cult", slug, race)
        home_key = bundle_key("gov_cult_home", slug, race)
        trait_key = bundle_key("cult", slug, race)
        for key in (away_key, home_key):
            if key not in bundles:
                out.append("no bundle %s" % key)
            elif bundles[key]["bundle_target"] != "province":
                out.append("%s is not a province bundle" % key)
        if trait_key not in traits:
            out.append("no trait %s" % trait_key)
        if bundle_key("cult_name", slug, race) not in loc:
            out.append("no name loc for culture %s" % slug)
        away, home = by.get(away_key, []), by.get(home_key, [])
        if len(away) != len(home) or not away:
            out.append("%s and %s carry %d and %d effects" % (away_key, home_key, len(away), len(home)))
            continue
        for n, (a, h) in enumerate(zip(away, home)):
            if (a["effect_key"], a["effect_scope"]) != (h["effect_key"], h["effect_scope"]):
                out.append("%s and %s differ in effect %d" % (away_key, home_key, n + 1))
            av, hv = int(float(a["value"])), int(float(h["value"]))
            if n < len(away) - 1:
                if (hv > 0) != (av > 0) or abs(hv) != home_value(abs(av)):
                    out.append("%s: home %+d is not %d%% of away %+d" % (home_key, hv, CULTURE_HOME_PCT, av))
            elif hv != av:
                out.append("%s: the drawback changes at home (%+d against %+d)" % (home_key, hv, av))
        text = loc.get("character_trait_levels_explanation_text_" + trait_key, "")
        for j in away:
            if _quoted_line(j) not in text:
                out.append("trait %s does not quote %r from its bundle" % (trait_key, _quoted_line(j)))
        for key in (away_key, home_key, trait_key):
            for lk in ("derpy_ic_effects_" + key, "effect_bundles_localised_title_" + key,
                       "effect_bundles_localised_description_" + key,
                       "character_trait_levels_onscreen_name_" + key,
                       "character_trait_levels_colour_text_" + key,
                       "character_trait_levels_explanation_text_" + key):
                for w in JARGON:
                    if re.search(r"\b%s\b" % w, loc.get(lk, "")):
                        out.append("%s says %r, which the plain-words rule bans" % (lk, w))
    friction = by.get(bundle_key("gov", "friction", race), [])
    if len(friction) != 1 or int(float(friction[0]["value"])) != -CULTURE_FRICTION:
        out.append("the %s friction bundle is not Control -%d" % (race, CULTURE_FRICTION))
    return out


def culture_range_notes():
    """NOT FAILURES: every culture figure (away and home) outside the range CA
    ships for that exact (effect, scope) pair. The spec keeps them uncapped."""
    junc = _cache_table("effect_bundles_to_effects_junctions")
    if junc is None:
        return []
    f, rows = junc
    ei, si, vi = f.index("effect_key"), f.index("effect_scope"), f.index("value")
    seen = {}
    for r in rows:
        try:
            seen.setdefault((r[ei], r[si]), []).append(float(r[vi]))
        except ValueError:
            pass
    notes = []
    for race in ("chd", "dwf"):
        for c in RACES[race]["CULTURES"]:
            away, home = culture_effects(c)
            for label, effects in (("away", away), ("home", home)):
                for e, m, i in effects:
                    v = signed_value(e, m, i)
                    vals = seen.get((e[0], e[1]))
                    if vals and (v > max(vals) or v < min(vals)):
                        notes.append("%s %s %s: %s %+d is outside CA's %g to %g"
                                     % (race, c["slug"], label, EFFECT_SHORT[e[0]], v,
                                        min(vals), max(vals)))
    return notes


```

- [ ] **Step 9: Wire the checks and the notes**

In `check()`, replace

```python
    out.extend(check_race_effects())
    out.extend(check_dwf())
```

with

```python
    out.extend(check_race_effects())
    out.extend(check_dwf())
    out.extend(check_cultures("chd"))
    out.extend(check_cultures("dwf"))
```

In `main()`, replace

```python
    tables = build()
    print("ok: %d bundles, %d junctions, %d traits, %d loc rows"
```

with

```python
    for note in culture_range_notes():
        print("NOTE %s" % note)
    tables = build()
    print("ok: %d bundles, %d junctions, %d traits, %d loc rows"
```

- [ ] **Step 10: Count the cultures in the selftest's own totals**

The selftest asserts how many bundles and traits each race ships. Without these four edits it stops at `one office and one vacancy bundle per office ...` with the old total. In `selftest()`:

Replace:

```python
    want = (n_offices * 2 + 1 + n_parties + len(CONTROL_BANDS) + n_envoy
            + len(GOVERNMENTS) + n_laws)
```

with:

```python
    # AND THE CULTURES' BUNDLES: an away and a home bundle per culture and one
    # friction bundle for the race. Both races have eight cultures.
    assert len(CHD_CULTURES) == len(DWF_CULTURES), "the two races' culture counts differ"
    n_cult = 2 * len(CHD_CULTURES) + 1
    want = (n_offices * 2 + 1 + n_parties + len(CONTROL_BANDS) + n_envoy
            + len(GOVERNMENTS) + n_laws + n_cult)
```

Replace:

```python
    n_traits = (n_origins + n_backgrounds + n_offices + n_bands + len(AMBITION_BANDS)
                + n_members)
```

with:

```python
    n_traits = (n_origins + n_backgrounds + n_offices + n_bands + len(AMBITION_BANDS)
                + n_members + len(CHD_CULTURES))
```

Replace:

```python
        ("one trait per origin, per background, per office, per standing band "
         "and per party: expected %d, got %d"
```

with:

```python
        ("one trait per origin, per background, per office, per standing band, "
         "per party and per culture: expected %d, got %d"
```

Replace:

```python
              + len(D["TIER_NAME"]) + 1 + len(AMBITION_BANDS) + d_members)
```

with:

```python
              + len(D["TIER_NAME"]) + 1 + len(AMBITION_BANDS) + d_members
              + len(DWF_CULTURES))
```

- [ ] **Step 11: Run the selftest and the check**

```powershell
py tools\gen_iron_court.py --selftest
py tools\gen_iron_court.py --check
```

Expected: `selftest: ok (180 bundles, 314 junctions, 297 traits, 2253 loc)` after about four minutes. `--check` prints these ten lines, the home figures outside the range CA ships (decision 5 keeps them), and then `ok: 180 bundles, 314 junctions, 297 traits, 2253 loc rows`:

```
NOTE chd stump home: Armaments +15 is outside CA's 10 to 10
NOTE chd gorgoth away: Labour loss -8 is outside CA's 3 to 20
NOTE chd gorgoth home: Labour loss -12 is outside CA's 3 to 20
NOTE chd gorgoth home: Rush labour cost -15 is outside CA's -10 to -10
NOTE chd mines home: Replenishment +6 is outside CA's 1 to 5
NOTE chd gash home: Post-battle loot +23 is outside CA's 15 to 20
NOTE dwf barakvarr home: Port income +38 is outside CA's 25 to 25
NOTE dwf kadrin home: Melee attack +8 is outside CA's 5 to 5
NOTE dwf kadrin home: Replenishment +6 is outside CA's 1 to 5
NOTE dwf azul home: Melee defence +8 is outside CA's 5 to 5
```

From the baseline that is 34 more bundles (an away and a home bundle for each of the 16 cultures, and one friction bundle a race), 98 more junctions, 17 more traits (16 cultures and the Slayer trade) and 187 more loc rows. If `check_dwf` item 4 names a Dwarf string, the word it names is banned in Dwarf text: change the colour line, not the check.

If `--check` reports `the Old World pack is unreadable`, the Workshop pack is not at `OW_PACK`: open the Mod Manager or Steam to confirm the Workshop item 3081800026 is installed, and fix the path constant, not the check.

- [ ] **Step 12: Write the TSVs**

```powershell
py tools\gen_iron_court.py
```

Expected: the ten `NOTE` lines, the `ok:` line and fourteen `wrote ...` lines, one for each TSV under `Modding Files\source\iron_court\`. The harness reads `character_traits.tsv` and `loc.tsv` from that folder to prove every key a court wears is a row the pack ships, so Task 4 needs them current.

- [ ] **Step 13: Ledger**

Append: `Task 3 done: tools/gen_iron_court.py, zzz_derpy_iron_court_dwarf.lua (Slayer trade); gen --selftest and --check green (180 bundles, 314 junctions, 297 traits, 2253 loc); ten NOTE lines; TSVs written.`

---

### Task 4: The deal, the culture roll and quiet stamping

**Files:**
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court.lua` (`IC.roll_background` becomes `IC.roll_party` and `IC.trade_in`; `IC.origin_for`; new `IC.fixed_culture` and `IC.culture_for`; `IC.background_for`; `IC.deed_join`; `IC.leaderless_bg` becomes `IC.leaderless_party`; `IC.ensure_leaders`; `IC.seed_step`; `IC.field_leader`; `IC.roll_origin` deleted; `IC.stamp_court`, whose origin stamp is deleted as dead code; `IC.stamp_bg` and the new `IC.stamp_culture` and `IC.fit_culture`; `IC.stamp_incoming`; the `ic_born` listener; Gorduz in `IC.LORD_HISTORY`)
- Modify: `tools/_iron_court_harness.lua` (twelve old checks rewritten, the `RACE_ARITY` table, one new `do ... end` block of sixteen checks)

**Interfaces:**
- Consumes (Task 1): `R.CULTURES`, `R.LEGEND_CULTURE`, `R.HOUSE_CULTURE`, `R.PLACE_CULTURE`, `R.CULTURE_TRADE`, `R.RESERVED_BG`, `IC.culture_of_character(character) -> slug, R | nil`, `IC.cultures_of(faction_key, party) -> main | nil, sides`, `IC.roll_culture(faction_key, party) -> slug`, `IC.culture_trait(slug, faction_key)`, `IC.rkey`. Already in the file: `IC.fixed_history`, `IC.bg_of_character`, `IC.origin_of_character`, `IC.fill_tally`, `IC.fewest`, `IC.present_houses`, `IC.can_lead`, `IC.stamp_origin`.
- Produces:
  - `IC.roll_party(faction_key, tally) -> party slug`: the seated party with the fewest members, the Crown when nothing else is seated.
  - `IC.leaderless_party(character, faction_key, tally) -> party slug | nil`: a seated party with no man who can lead it.
  - `IC.trade_in(party, faction_key, culture) -> trade slug | nil`: one random call, none when the culture reserves the trade; reserved trades are never drawn otherwise.
  - `IC.fixed_culture(character, faction_key) -> slug | nil`: a legend's own culture.
  - `IC.culture_for(character, faction_key, party, origin) -> slug, binding`.
  - `IC.background_for(character, faction_key, tally, origin) -> trade | nil, culture, binding` (it returned only the trade).
  - `IC.stamp_culture(faction_key, character, slug, binding) -> boolean`: always quiet.
  - `IC.fit_culture(faction_key, character, party) -> boolean`.
  - `IC.origin_for(character, faction_key)` now answers only a legend's own origin.
  - Removed: `IC.roll_origin`, `IC.roll_background`, `IC.leaderless_bg`.

The rule behind all of it is the spec's roll (4.3): the party is dealt exactly as today, the culture is then drawn from the cultures that feed that party, and the trade is drawn last, so a culture can reserve a trade. Six decisions are worth reading before the code.

1. **Binding or drawn.** `IC.culture_for` answers a culture and whether it is binding. A legend's own culture and the culture of a hold a man arrived from are binding: they replace whatever he wears. The culture he already wears, the culture of a retired birthplace and a fresh draw are not: they never replace one. That is why a second court pass changes nobody.
2. **A retired birthplace comes off with the culture.** `IC.stamp_culture` removes every place origin trait from either race, quietly, which is how an old save is converted: the place becomes the culture of the same country (`R.PLACE_CULTURE`) and the man's party and trade are untouched. A house origin (a record of confederation) stays.
3. **Culture is never a card.** Every `force_add_trait` for a culture passes `false` for the card. A recruit still sees the Trait Gained card for his trade.
4. **Gorduz has no birthplace.** `correct_history` puts a legend's table origin back on him every turn, and `IC.stamp_culture` would take a retired place off every turn. His row loses its `origin`; `R.LEGEND_CULTURE` fixes `zornuzkul` for him instead. The harness check that every legend has an origin is rewritten to allow exactly him.
5. **A confederation names the hold.** `IC.stamp_incoming` hands the hold to `IC.background_for` as `origin` instead of leaving `IC.culture_for` to read the origin trait stamped a line earlier: CA does not document whether `has_trait` sees a trait added in the same moment. One new check swallows the origin trait to hold this.
6. **The importer refuses from here to Task 8.** `check_rollers` in `tools/import_iron_court.py` names `IC.roll_origin(` and `IC.roll_background(`, which no longer exist. Nothing in Tasks 4 to 7 runs the importer.

- [ ] **Step 1: Rewrite the old checks that assert the old behaviour**

Twelve existing checks call a function this task removes or expect a birthplace on a man the model stamped. Each pair is applied once, to `tools/_iron_court_harness.lua`; the old text must appear exactly once.

Replace:

```lua
        local bg = IC.roll_background(F)
        assert(bg, "no background was rolled at all")
```

with:

```lua
        local bg = IC.trade_in(IC.roll_party(F), F)
        assert(bg, "no background was rolled at all")
```

Replace:

```lua
        local bg = IC.roll_background(F)
        assert(bg, "no trade was rolled at all")
```

with:

```lua
        local bg = IC.trade_in(IC.roll_party(F), F)
        assert(bg, "no trade was rolled at all")
```

Replace:

```lua
        local bg = IC.roll_background(F)
        local party = IC.PARTY_OF_BG[bg]
```

with:

```lua
        local bg = IC.trade_in(IC.roll_party(F), F)
        local party = IC.PARTY_OF_BG[bg]
```

Replace:

```lua
    -- stamp_court still asks the origin roller before its stamp refuses, then
    -- ambition. A man who already has a background is not rolled another, so
    -- party and background draw nothing here.
    rng({1, 25, 1, 26, 1, 76})
```

with:

```lua
    -- stamp_court rolls each man's ambition first, in order. A man who already
    -- has a background is dealt no other, so party and trade draw nothing; his
    -- culture is drawn after all three ambitions, from an empty queue.
    rng({25, 26, 76})
```

Replace:

```lua
    assert(IC.origin_of_character(born),
        "a new recruit arrived from nowhere at all")
```

with:

```lua
    assert(IC.culture_of_character(born),
        "a new recruit arrived from nowhere at all")
    assert(IC.origin_of_character(born) == nil,
        "a new recruit was dealt a birthplace as well as a culture")
```

Replace:

```lua
check("a man raised at home is born in a place, never in a house", function()
    -- A HOUSE ORIGIN IS A RECORD OF CONFEDERATION. Rolling one for a lord you
    -- recruited yourself would say he came from a faction he has never seen,
    -- and that faction is very likely still alive on the map under its own name.
    for i = 1, 40 do
        rng({i})
        local slug = IC.roll_origin()
        assert(slug, "no origin was rolled at all")
        assert(IC.faction_for_origin(slug) == nil,
            slug .. " is a house, and a man raised at home came from a place")
    end
    rng(nil)
end)
```

with:

```lua
check("a man raised at home is dealt a culture and no origin at all", function()
    -- A HOUSE ORIGIN IS A RECORD OF CONFEDERATION. Dealing one to a lord you
    -- recruited yourself would say he came from a faction he has never seen,
    -- and that faction is very likely still alive on the map under its own name.
    -- The birthplaces are retired: a man raised at home is dealt a culture.
    IC.state = {}
    factions = {}
    local men = {}
    for i = 1, 8 do men[i] = make_character(8700 + i, ANY_SEAT, nil, nil) end
    make_faction(F, IC.CHD_SUBCULTURE, men, {})
    IC.add_house(F, IC.CROWN)
    IC.add_house(F, "forge")
    IC.stamp_court(F)
    for i = 1, #men do
        assert(IC.culture_of_character(men[i]), "man " .. i .. " was dealt no culture")
        assert(IC.origin_of_character(men[i]) == nil,
            "man " .. i .. " was dealt the origin " .. tostring(IC.origin_of_character(men[i])))
    end
end)
```

Replace:

```lua
        assert(type(who) == "table" and who.origin and who.bg,
            subtype .. " has no origin and trade")
        assert(places[who.origin],
            subtype .. " is born in " .. who.origin
            .. ", which is not one of IC.ORIGINS")
```

with:

```lua
        -- GORDUZ HAS NO BIRTHPLACE: the places are retired, and correct_history
        -- would put his old one back on him every turn.
        assert(type(who) == "table" and who.bg
               and (who.origin or subtype == "wh3_dlc23_chd_gorduz_backstabber"),
            subtype .. " has no origin and trade")
        assert(who.origin == nil or places[who.origin],
            subtype .. " is born in " .. tostring(who.origin)
            .. ", which is not one of IC.ORIGINS")
        -- A LEGEND'S ORIGIN IS A HOUSE, never a retired place: correct_history
        -- would re-add the place every turn and IC.stamp_culture would take it
        -- off, once a turn for the rest of the campaign.
        assert(who.origin == nil or IC.faction_for_origin(who.origin),
            subtype .. " is born in " .. tostring(who.origin) .. ", a retired place")
```

Replace:

```lua
        assert(lord:has_trait("derpy_ic_house_" .. want.origin),
            subtype .. " was not born in " .. want.origin)
        assert(lord:has_trait("derpy_ic_bg_" .. want.bg),
            subtype .. " did not come up through " .. want.bg)
```

with:

```lua
        if want.origin then
            assert(lord:has_trait("derpy_ic_house_" .. want.origin),
                subtype .. " was not born in " .. want.origin)
        end
        assert(lord:has_trait("derpy_ic_bg_" .. want.bg),
            subtype .. " did not come up through " .. want.bg)
        -- AND HE WEARS THE CULTURE THE TABLE FIXES FOR HIM, and no other.
        assert(IC.culture_of_character(lord) == IC.LEGEND_CULTURE[subtype],
            subtype .. " wears " .. tostring(IC.culture_of_character(lord))
            .. " and not " .. tostring(IC.LEGEND_CULTURE[subtype]))
```

Replace:

```lua
    assert(IC.origin_for(nobody), "origin_for rolled a generic lord nothing")
    assert(IC.background_for(nobody, F),
        "background_for rolled a generic lord nothing")
```

with:

```lua
    assert(IC.origin_for(nobody) == nil, "origin_for dealt a generic lord a birthplace")
    local bg, culture = IC.background_for(nobody, F)
    assert(bg, "background_for rolled a generic lord nothing")
    assert(culture, "background_for dealt a generic lord no culture")
```

Replace:

```lua
check("a generic lord's rolled past is left alone", function()
    -- THE OTHER HALF OF THE MIGRATION. A lord nobody wrote a history for has a
    -- rolled one and that IS his real one; correcting him every turn would
    -- shuffle his card at random for the rest of the campaign.
```

with:

```lua
check("a generic lord's trade is left alone and his old birthplace becomes its culture", function()
    -- THE OTHER HALF OF THE MIGRATION. A lord nobody wrote a history for has a
    -- rolled trade and that IS his real one; correcting him every turn would
    -- shuffle his card at random for the rest of the campaign. His old
    -- birthplace is converted once, to the culture of the same country.
```

Replace:

```lua
    assert(nobody:has_trait("derpy_ic_house_gash"),
        "a generic lord lost the birthplace he was dealt")
```

with:

```lua
    assert(not nobody:has_trait("derpy_ic_house_gash"),
        "the retired birthplace was left on him")
    assert(nobody:has_trait("derpy_ic_cult_gash"),
        "the birthplace did not become the culture of the same country")
```

Replace:

```lua
    assert(IC.origin_of_character(nobody),
        "a generic lord came out of a turn with no birthplace at all")
```

with:

```lua
    assert(IC.culture_of_character(nobody),
        "a generic lord came out of a turn with no culture at all")
```

Replace:

```lua
    loud = cards("cqi:" .. born:command_queue_index() .. "=")
    assert(loud == 2, "a recruit's origin and background raised " .. loud .. " cards, not 2")
```

with:

```lua
    loud = cards("cqi:" .. born:command_queue_index() .. "=")
    assert(loud == 1, "a recruit's trade raised " .. loud .. " cards, not 1")
    -- THE CULTURE IS NEVER A CARD, for a recruit or for anyone else.
    local culture_loud, culture_quiet = cards("cqi:" .. born:command_queue_index() .. "=derpy_ic_cult_")
    assert(culture_loud == 0 and culture_quiet == 1,
        "a recruit's culture raised " .. culture_loud .. " cards and " .. culture_quiet .. " quiet stamps")
```

Replace:

```lua
        assert(IC.roll_origin(TST_F) == "thold", "the second race rolled a birthplace not its own")
```

with:

```lua
        rng({1})
        local culture = IC.roll_culture(TST_F, "legion")
        rng(nil)
        assert(culture == "zornuzkul", "the second race rolled " .. tostring(culture) .. " for its Legion")
        assert(IC.culture_trait(culture, TST_F) == "derpy_ic_cult_tst_zornuzkul",
            "a culture trait was not keyed to the second race")
```

Replace:

```lua
    recruit_influence = 2, rebel_draw = 2, roll_origin = 1, origin_for = 2,
```

with:

```lua
    recruit_influence = 2, rebel_draw = 2, origin_for = 2,
    stamp_culture = 4, fixed_culture = 2, fit_culture = 3, leaderless_party = 3,
```

- [ ] **Step 2: Write the failing checks**

Add this block to `tools/_iron_court_harness.lua` immediately above the final `check("no engine setter was ever handed anything but a boolean", ...)`. It has sixteen checks.

```lua
-- CULTURES, task 4: stamping, conversion, legends, houses and the Slayer.
do
    local DF = "wh_main_dwf_dwarfs"

    -- ALL OF A MAN'S CULTURE TRAITS, across both races.
    local function cults(man)
        local out = {}
        for _, k in ipairs(IC.RACE_ORDER) do
            local R = IC.RACES[k]
            for _, c in ipairs(R.CULTURES) do
                if man:has_trait(IC.rkey("cult", c.slug, R)) then out[#out + 1] = c.slug end
            end
        end
        return out
    end

    -- A DWARF COURT with the Crown and the named parties seated.
    local function dwarf_court(men, ...)
        IC.state = {}
        factions = {}
        rng(nil)
        make_faction(DF, IC.RACES.dwf.subculture, men, {})
        IC.add_house(DF, IC.CROWN)
        for _, slug in ipairs({...}) do IC.add_house(DF, slug) end
    end

    check("cultures: a stamped court gives every man one culture, quietly, and no birthplace", function()
        rng(nil)
        IC.state = {}
        factions = {}
        for k in pairs(traits_shown) do traits_shown[k] = nil end
        local men = {}
        for i = 1, 6 do men[i] = make_character(9500 + i, ANY_SEAT, nil, nil) end
        make_faction(F, IC.CHD_SUBCULTURE, men, {})
        IC.add_house(F, IC.CROWN)
        IC.add_house(F, "forge")
        IC.add_house(F, "ledger")
        IC.stamp_court(F)
        for i, man in ipairs(men) do
            assert(#cults(man) == 1, "man " .. i .. " wears " .. #cults(man) .. " cultures")
            assert(IC.origin_of_character(man) == nil, "man " .. i .. " was dealt a birthplace")
            -- HIS CULTURE FEEDS THE PARTY HIS TRADE SEATS HIM IN: with no random
            -- answers to pick otherwise, the party's main culture.
            local party = IC.house_of_character(man, F)
            local main = IC.cultures_of(F, party)
            if party ~= IC.CROWN then
                assert(cults(man)[1] == main, "man " .. i .. " of " .. party .. " wears " .. cults(man)[1]
                    .. " and not " .. tostring(main))
            end
        end
        local n = 0
        for key, shown in pairs(traits_shown) do
            if string.find(key, "derpy_ic_cult_", 1, true) then
                n = n + 1
                assert(shown == false, key .. " raised a Trait Gained card")
            end
        end
        assert(n == 6, "only " .. n .. " culture stamps were seen")
    end)

    check("cultures: a Kadrin man dealt to the Dwarf Legion is a Slayer", function()
        rng(nil)
        dwarf_court({make_character(9510, ANY_SEAT, nil, nil)}, "legion")
        local man = IC.character_by_cqi(DF, 9510)
        -- fewest, then the culture roll (1 of 10: the main culture), no trade draw.
        rng({1, 1})
        local bg, culture, binding = IC.background_for(man, DF, {})
        assert(culture == "kadrin" and binding == false, "culture " .. tostring(culture))
        assert(bg == "slayer", "a Kadrin man in the Legion was dealt " .. tostring(bg))
        for _, call in ipairs(rng_calls) do
            assert(call.max ~= 3 and call.max ~= 4, "the Slayer's trade was drawn, not dealt")
        end
        rng(nil)
    end)

    check("cultures: a Grey Mountains man in the Legion draws an ordinary trade", function()
        rng(nil)
        dwarf_court({make_character(9511, ANY_SEAT, nil, nil)}, "legion")
        local man = IC.character_by_cqi(DF, 9511)
        rng({1, 8, 1, 1})
        local bg, culture = IC.background_for(man, DF, {})
        assert(culture == "grey", "culture " .. tostring(culture))
        assert(bg == "longbeard", "a Grey Mountains man was dealt " .. tostring(bg))
        assert(rng_calls[#rng_calls].max == 3, "the trade was drawn from " .. tostring(rng_calls[#rng_calls].max)
            .. " trades, not the three ordinary ones")
        rng(nil)
    end)

    check("cultures: a Kadrin man in another party is no Slayer", function()
        rng(nil)
        dwarf_court({make_character(9512, ANY_SEAT, nil, nil)}, "temple")
        local man = IC.character_by_cqi(DF, 9512)
        -- fewest, culture roll 8 (a side), the first side (Kadrin feeds the Temple), trade 1.
        rng({1, 8, 1, 1})
        local bg, culture = IC.background_for(man, DF, {})
        assert(culture == "kadrin", "culture " .. tostring(culture))
        assert(bg ~= "slayer" and IC.R(DF).PARTY_OF_BG[bg] == "temple",
            "a Kadrin man in the Temple was dealt " .. tostring(bg))
        rng(nil)
    end)

    check("cultures: the Slayer trade is never drawn for anyone", function()
        rng(nil)
        make_faction(DF, IC.RACES.dwf.subculture, {}, {})
        for r = 1, 6 do
            rng({r})
            local bg = IC.trade_in("legion", DF)
            assert(bg and bg ~= "slayer", "an ordinary draw gave " .. tostring(bg))
            assert(IC.R(DF).PARTY_OF_BG[bg] == "legion", bg .. " is no Legion trade")
        end
        rng(nil)
        assert(IC.trade_in("legion", DF, "kadrin") == "slayer", "the dealt trade is gone")
        assert(IC.trade_in("temple", DF, "kadrin") ~= "slayer", "Kadrin is a Slayer outside the Legion")
        assert(IC.trade_in(nil, DF) == nil and IC.trade_in("no_such_party", DF) == nil)
    end)

    check("cultures: a legend wears his own culture and replaces a wrong one", function()
        rng(nil)
        IC.state = {}
        factions = {}
        local tordrek = make_character(9520, ANY_SEAT, nil, nil, true, nil, "derpy_tordrek", "gash")
        make_faction(F, IC.CHD_SUBCULTURE, {tordrek}, {})
        IC.add_house(F, IC.CROWN)
        assert(IC.fixed_culture(tordrek, F) == "stump", "Tordrek's culture is " .. tostring(IC.fixed_culture(tordrek, F)))
        rng({})
        IC.stamp_court(F)
        assert(tordrek:has_trait("derpy_ic_cult_stump"), "Tordrek does not wear his own culture")
        assert(not tordrek:has_trait("derpy_ic_cult_gash"), "the wrong culture was left on him")
        for _, call in ipairs(rng_calls) do
            assert(call.max ~= 10 and call.max ~= 8, "a legend's culture was rolled")
        end
        rng(nil)
        local nobody = make_character(9521, ANY_SEAT, nil, nil)
        assert(IC.fixed_culture(nobody, F) == nil and IC.fixed_culture(nil, F) == nil)
    end)

    check("cultures: an old save's birthplace becomes the culture of the same country", function()
        rng(nil)
        IC.state = {}
        factions = {}
        local ranger = make_character(9530, ANY_SEAT, "forge", nil, nil, "stump")
        make_faction(F, IC.CHD_SUBCULTURE, {ranger}, {})
        IC.add_house(F, IC.CROWN)
        IC.add_house(F, "forge")
        traits_added = {}
        IC.stamp_court(F)
        assert(not ranger:has_trait("derpy_ic_house_stump"), "the retired birthplace was left on him")
        assert(ranger:has_trait("derpy_ic_cult_stump"), "the birthplace did not become its culture")
        assert(IC.bg_of_character(ranger) == IC.BACKGROUNDS.forge[1], "his trade moved")
        assert(IC.house_of_character(ranger, F) == "forge", "his party moved")
        -- A SECOND PASS ADDS NOTHING: the conversion is done once.
        traits_added = {}
        IC.stamp_court(F)
        for _, entry in ipairs(traits_added) do
            assert(not string.find(entry, "derpy_ic_cult_", 1, true), "a second pass stamped " .. entry)
        end
        assert(#cults(ranger) == 1)
    end)

    check("cultures: a man with a birthplace and a culture loses only the birthplace", function()
        rng(nil)
        IC.state = {}
        factions = {}
        local man = make_character(9531, ANY_SEAT, "forge", nil, nil, "stump", nil, "gash")
        make_faction(F, IC.CHD_SUBCULTURE, {man}, {})
        IC.add_house(F, IC.CROWN)
        IC.add_house(F, "forge")
        IC.stamp_court(F)
        assert(not man:has_trait("derpy_ic_house_stump"), "the birthplace stayed")
        assert(#cults(man) == 1 and man:has_trait("derpy_ic_cult_gash"), "his culture changed to " .. tostring(cults(man)[1]))
    end)

    check("cultures: a Dwarf ranger becomes a Pass-Keeper", function()
        rng(nil)
        dwarf_court({make_character(9532, ANY_SEAT, nil, nil, nil, "dwf_rangers")}, "road")
        local man = IC.character_by_cqi(DF, 9532)
        man._traits["derpy_ic_bg_dwf_ranger"] = true
        IC.stamp_court(DF)
        assert(not man:has_trait("derpy_ic_house_dwf_rangers"), "the ranger's birthplace stayed")
        assert(man:has_trait("derpy_ic_cult_dwf_passkeeps"), "he is " .. tostring(cults(man)[1]))
    end)

    check("cultures: a confederated man takes his hold's culture and drops a rolled one, quietly", function()
        rng(nil)
        IC.state = {}
        factions = {}
        for k in pairs(traits_shown) do traits_shown[k] = nil end
        local man = make_character(9540, ANY_SEAT, nil, nil, nil, nil, nil, "stump")
        make_faction(F, IC.CHD_SUBCULTURE, {man}, {})
        IC.add_house(F, IC.CROWN)
        IC.stamp_incoming(F, "uzkulak", 0, {}, 50)
        assert(man:has_trait("derpy_ic_cult_zornuzkul"), "he is " .. tostring(cults(man)[1]))
        assert(not man:has_trait("derpy_ic_cult_stump"), "the rolled culture stayed")
        assert(#cults(man) == 1)
        assert(traits_shown["cqi:9540=derpy_ic_cult_zornuzkul"] == false, "the culture raised a card")
        -- A HOLD NOBODY LISTED leaves a man his rolled culture.
        local other = make_character(9541, ANY_SEAT, nil, nil, nil, nil, nil, "stump")
        factions = {}
        make_faction(F, IC.CHD_SUBCULTURE, {other}, {})
        IC.state = {}
        IC.add_house(F, IC.CROWN)
        IC.stamp_incoming(F, "khorakk", 0, {}, 50)
        assert(other:has_trait("derpy_ic_cult_stump") and #cults(other) == 1, "khorakk changed a culture")
    end)

    check("cultures: a confederation takes the culture from the hold it names, not from traits it can see yet", function()
        -- stamp_incoming stamps the origin and asks for the culture in the same
        -- frame. CA does not document whether has_trait shows a trait added that
        -- moment, so the culture must come from the hold the call names. Here the
        -- origin trait is swallowed, as it would be if the engine showed it late.
        rng(nil)
        IC.state = {}
        factions = {}
        local man = make_character(9542, ANY_SEAT, nil, nil, nil, nil, nil, "stump")
        make_faction(F, IC.CHD_SUBCULTURE, {man}, {})
        IC.add_house(F, IC.CROWN)
        local add = cm.force_add_trait
        cm.force_add_trait = function(self, lookup, key, ...)
            if string.find(key, "derpy_ic_house_", 1, true) then return end
            return add(self, lookup, key, ...)
        end
        local ok, err = pcall(IC.stamp_incoming, F, "uzkulak", 0, {}, 50)
        cm.force_add_trait = add
        assert(ok, err)
        assert(man:has_trait("derpy_ic_cult_zornuzkul"), "he is " .. tostring(cults(man)[1]))
        assert(not man:has_trait("derpy_ic_cult_stump"), "the rolled culture stayed")
    end)

    check("cultures: a recruit's culture is quiet while his trade still shows", function()
        rng(nil)
        IC.state = {}
        factions = {}
        for k in pairs(traits_shown) do traits_shown[k] = nil end
        local faction = make_faction(F, IC.CHD_SUBCULTURE, {}, {})
        IC.add_house(F, IC.CROWN)
        IC.add_house(F, "forge")
        IC.register()
        local born = cm._spawn_into(faction)
        core.listeners["ic_born"]({character = function() return born end})
        local cult = cults(born)[1]
        assert(cult and #cults(born) == 1, "a recruit has " .. #cults(born) .. " cultures")
        assert(traits_shown["cqi:" .. born:command_queue_index() .. "=derpy_ic_cult_" .. cult] == false,
            "his culture raised a card")
        local bg = IC.bg_of_character(born)
        assert(bg and traits_shown["cqi:" .. born:command_queue_index() .. "=derpy_ic_bg_" .. bg] == true,
            "his trade stopped showing")
    end)

    check("cultures: a starting lord is born into a culture that feeds his party", function()
        rng(nil)
        IC.state = {}
        factions = {}
        local faction = make_faction(F, IC.CHD_SUBCULTURE, {}, {})
        IC.add_house(F, IC.CROWN)
        IC.add_house(F, "forge")
        IC.register()
        IC._seed_bg[F] = "gunnery"
        local born = cm._spawn_into(faction)
        core.listeners["ic_born"]({character = function() return born end})
        assert(IC.bg_of_character(born) == "gunnery")
        assert(cults(born)[1] == "stump", "a seeded forge lord is " .. tostring(cults(born)[1]))
        IC._seed_bg[F] = nil
    end)

    check("cultures: stamp_culture replaces only when it is told to", function()
        rng(nil)
        IC.state = {}
        factions = {}
        local man = make_character(9550, ANY_SEAT, nil, nil, nil, nil, nil, "gash")
        make_faction(F, IC.CHD_SUBCULTURE, {man}, {})
        assert(IC.stamp_culture(F, man, nil, false) == false and IC.stamp_culture(F, nil, "stump", false) == false)
        assert(IC.stamp_culture(F, man, "stump", false) == false and man:has_trait("derpy_ic_cult_gash"),
            "a drawn culture replaced a worn one")
        assert(IC.stamp_culture(F, man, "gash", true) == false, "the same culture was stamped twice")
        assert(IC.stamp_culture(F, man, "stump", true) == true, "a binding culture did not replace")
        assert(man:has_trait("derpy_ic_cult_stump") and not man:has_trait("derpy_ic_cult_gash") and #cults(man) == 1)
    end)

    check("cultures: a man moved to another party keeps a culture that feeds it and loses one that does not", function()
        rng(nil)
        IC.state = {}
        factions = {}
        local keeps = make_character(9560, ANY_SEAT, nil, nil, nil, nil, nil, "gash")
        local loses = make_character(9561, ANY_SEAT, nil, nil, nil, nil, nil, "stump")
        local bound = make_character(9562, ANY_SEAT, nil, nil, nil, "uzkulak", nil, "zornuzkul")
        local legend = make_character(9563, ANY_SEAT, nil, nil, true, nil, "derpy_tordrek", "stump")
        local none = make_character(9564, ANY_SEAT, nil, nil)
        local side = make_character(9565, ANY_SEAT, nil, nil, nil, nil, nil, "wastes")
        make_faction(F, IC.CHD_SUBCULTURE, {keeps, loses, bound, legend, none, side}, {})
        -- The Ledger is fed by Gash Kadrak (main), the Tower of Gorgoth and the Howling Wastes.
        rng({})
        assert(IC.fit_culture(F, keeps, "ledger") == false and keeps:has_trait("derpy_ic_cult_gash"))
        assert(IC.fit_culture(F, side, "ledger") == false and side:has_trait("derpy_ic_cult_wastes"),
            "a side culture of the party was taken from him")
        assert(#rng_calls == 0, "a culture that already feeds the party was redrawn")
        assert(IC.fit_culture(F, loses, "ledger") == true and loses:has_trait("derpy_ic_cult_gash")
               and not loses:has_trait("derpy_ic_cult_stump"), "he is " .. tostring(cults(loses)[1]))
        assert(IC.fit_culture(F, bound, "ledger") == false and bound:has_trait("derpy_ic_cult_zornuzkul"),
            "a conquered hold's man lost his hold's culture")
        assert(IC.fit_culture(F, legend, "ledger") == false and legend:has_trait("derpy_ic_cult_stump"),
            "a legend lost his own culture")
        assert(IC.fit_culture(F, none, "ledger") == false and #cults(none) == 0)
        assert(IC.fit_culture(F, loses, IC.CROWN) == false)
        rng(nil)
    end)

    check("cultures: background_for reports the culture of a man whose trade is already stamped", function()
        rng(nil)
        IC.state = {}
        factions = {}
        local plain = make_character(9570, ANY_SEAT, "forge", nil, nil, nil, nil, nil)
        local placed = make_character(9571, ANY_SEAT, "forge", nil, nil, "mines")
        local housed = make_character(9572, ANY_SEAT, "forge", nil, nil, "uzkulak")
        local worn = make_character(9573, ANY_SEAT, "forge", nil, nil, nil, nil, "gash")
        make_faction(F, IC.CHD_SUBCULTURE, {plain, placed, housed, worn}, {})
        IC.add_house(F, IC.CROWN)
        IC.add_house(F, "forge")
        local bg, culture, binding = IC.background_for(plain, F, {})
        assert(bg == nil and culture == "stump" and binding == false, "plain: " .. tostring(culture))
        bg, culture, binding = IC.background_for(placed, F, {})
        assert(bg == nil and culture == "mines" and binding == false, "placed: " .. tostring(culture))
        bg, culture, binding = IC.background_for(housed, F, {})
        assert(bg == nil and culture == "zornuzkul" and binding == true, "housed: " .. tostring(culture))
        -- A MAN WHO WEARS A CULTURE IS ANSWERED WITH IT, not with a fresh draw for his party.
        bg, culture, binding = IC.background_for(worn, F, {})
        assert(bg == nil and culture == "gash" and binding == false, "worn: " .. tostring(culture))
        -- A CONFEDERATION NAMES THE HOUSE before any trait says so.
        bg, culture, binding = IC.background_for(plain, F, {}, "azgorh")
        assert(culture == "gorgoth" and binding == true, "incoming: " .. tostring(culture))
    end)
end

```

- [ ] **Step 3: Run the harness and confirm the failures**

```powershell
$env:IC_TEST_ALL = "1"; & "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua 2> harness_fail.txt; Remove-Item Env:IC_TEST_ALL
Get-Content harness_fail.txt
```

Expected: `28 failing`. Twelve are the rewritten old checks:

- `who is already seated DOES decide what a new man can be`
- `ambition uses the 25 50 25 roll bands`
- `a trade is never drawn from a bloc`
- `a lord recruited this turn has a party before End Turn`
- `a background is rolled only from the parties that are seated`
- `a man raised at home is dealt a culture and no origin at all`
- `every legendary lord's history names a real place and a real trade`
- `every lord in the table gets the pair the table promises`
- `the two pickers hand back a legend's own past, not a roll`
- `a generic lord's trade is left alone and his old birthplace becomes its culture`
- `a lord nobody has written a past for still gets one`
- `a whole court stamped at once raises no Trait Gained card, and a recruit's own traits still do`

and sixteen are the new `cultures:` checks (a stamped court, three Kadrin cases, the Slayer never drawn, a legend, an old save, a man with both, a ranger, two confederations, a recruit, a starting lord, `stamp_culture`, a moved man and `background_for`). The messages are of two kinds: a missing function (`attempt to call field 'roll_party' (a nil value)`, and the same for `trade_in`, `fixed_culture`, `stamp_culture` and `fit_culture`) or a man who wears no culture (`man 1 wears 0 cultures`); the last check fails with `plain: nil`. If the count differs, read the failing line before going on.

- [ ] **Step 4: Edit the Lua**

All in `zzz_derpy_iron_court.lua`. Do the edits in this order; each is a replacement of the exact text shown, and the old text must appear once.

Replace `IC.roll_background` (the whole function):

```lua
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
```

with:

```lua
-- THE PARTY A NEW MAN IS DEALT TO: the seated party with the fewest members,
-- ties rolled; the Crown when nothing else is seated. The trade comes after the
-- culture (IC.trade_in), so a culture can reserve one.
function IC.roll_party(faction_key, tally)
    local R = IC.R(faction_key)
    tally = IC.fill_tally(tally or {}, faction_key)
    local seated = IC.present_houses(faction_key)
    local pool = {}
    for i = 1, #seated do
        if R.BACKGROUNDS[seated[i]] then pool[#pool + 1] = seated[i] end
    end
    if #pool == 0 then pool = {IC.CROWN} end
    return IC.fewest(pool, tally)
end

-- A TRADE FROM A PARTY'S LIST. A culture that reserves a trade for this party is
-- dealt it (a Kadrin man in the Dwarf Legion is a Slayer); every other draw is
-- from the list less the reserved trades, so nobody else is ever one. One random
-- call, as the plain draw always was, and none when the trade is reserved.
function IC.trade_in(party, faction_key, culture)
    local R = IC.R(faction_key)
    local list = party and R.BACKGROUNDS[party]
    if not list or #list == 0 then return nil end
    local own = culture and R.CULTURE_TRADE[culture]
    if own and own.party == party then return own.bg end
    local pool = {}
    for i = 1, #list do
        if not R.RESERVED_BG[list[i]] then pool[#pool + 1] = list[i] end
    end
    if #pool == 0 then return nil end
    return pool[cm:random_number(#pool, 1)]
end
```

Replace `IC.origin_for` and `IC.background_for`:

```lua
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
```

with:

```lua
-- A LEGEND'S OWN HOUSE OR PLACE, and nobody else's. A man raised at home is no
-- longer dealt a birthplace: he is dealt a culture (IC.culture_for).
function IC.origin_for(character, faction_key)
    local fixed = IC.fixed_history(character)
    return fixed and fixed.origin or nil
end

-- A LEGEND'S OWN CULTURE (R.LEGEND_CULTURE), by subtype.
function IC.fixed_culture(character, faction_key)
    if not character or character:is_null_interface() then return nil end
    local ok, key = pcall(function() return character:character_subtype_key() end)
    if not ok or not key then return nil end
    return IC.R(faction_key).LEGEND_CULTURE[key]
end

-- THE CULTURE A MAN SHOULD WEAR, and whether that answer is BINDING: a binding
-- culture replaces the one he wears, a drawn one never does. In order: a
-- legend's own; the culture of the house he arrived from (`origin` is passed by
-- a confederation, which has stamped nothing yet; otherwise it is read off his
-- traits); the culture he already wears; the culture of a retired birthplace
-- (an old save); a draw for the party he was dealt to.
function IC.culture_for(character, faction_key, party, origin)
    local R = IC.R(faction_key)
    local fixed = IC.fixed_culture(character, faction_key)
    if fixed then return fixed, true end
    origin = origin or IC.origin_of_character(character)
    local house = origin and R.HOUSE_CULTURE[origin]
    if house then return house, true end
    local has = IC.culture_of_character(character)
    if has then return has, false end
    local place = origin and R.PLACE_CULTURE[origin]
    if place then return place, false end
    return IC.roll_culture(faction_key, party), false
end

-- THE TRADE, THE CULTURE AND WHETHER THE CULTURE IS BINDING, for one man. The
-- trade is nil for a man who wears one already (stamp_bg would refuse) and a
-- legend's own for a legend. The order is party, then culture, then trade, so a
-- culture can reserve a trade of the party he was dealt to. `origin` is a
-- confederation's way of naming the house the man arrived from.
function IC.background_for(character, faction_key, tally, origin)
    local R = IC.R(faction_key)
    local fixed = IC.fixed_history(character)
    local worn = IC.bg_of_character(character)
    if worn or (fixed and fixed.bg) then
        local trade = fixed and fixed.bg or nil
        local culture, binding = IC.culture_for(character, faction_key,
            R.PARTY_OF_BG[trade or worn], origin)
        return trade, culture, binding
    end
    tally = IC.fill_tally(tally or {}, faction_key)
    local party = IC.leaderless_party(character, faction_key, tally)
                  or IC.roll_party(faction_key, tally)
    local culture, binding = IC.culture_for(character, faction_key, party, origin)
    local bg = IC.trade_in(party, faction_key, culture)
    if bg and party and tally.count[party] then
        tally.count[party] = tally.count[party] + 1
        if IC.can_lead(character) then tally.led[party] = true end
    end
    return bg, culture, binding
end
```

Replace `IC.deed_join`:

```lua
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
```

with:

```lua
function IC.deed_join(character, faction_key)
    if not IC.can_lead(character) or IC.fixed_history(character) then return nil end
    if IC.bg_of_character(character) then return nil end
    local party = IC.deed_waiting(faction_key)
    if not party or not IC.add_house(faction_key, party) then return nil end
    IC.name_party(faction_key, party)
    IC.roll_party_traits(faction_key, party)
    IC.log(faction_key, "drawn", party, nil, IC.renown(faction_key, party))
    IC.feed(faction_key, "party_drawn", IC.party_drawn_key(faction_key, party))
    IC.save(faction_key)
    return IC.trade_in(party, faction_key)
end
```

Replace `IC.leaderless_bg`:

```lua
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
```

with:

```lua
function IC.leaderless_party(character, faction_key, tally)
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
    return IC.fewest(pool, tally)
end
```

Replace in `IC.ensure_leaders` the idle Crown lord branch:

```lua
            elseif man then
                local list = R.BACKGROUNDS[slug]
                local lookup = cm:char_lookup_str(man)
                local old = IC.bg_of_character(man)
                if old then cm:force_remove_trait(lookup, IC.bg_trait(old)) end
                cm:force_add_trait(lookup, IC.bg_trait(list[cm:random_number(#list, 1)]), false)
                taken[man:command_queue_index()] = true
```

with:

```lua
            elseif man then
                local lookup = cm:char_lookup_str(man)
                local old = IC.bg_of_character(man)
                if old then cm:force_remove_trait(lookup, IC.bg_trait(old)) end
                cm:force_add_trait(lookup, IC.bg_trait(IC.trade_in(slug, faction_key)), false)
                IC.fit_culture(faction_key, man, slug)
                taken[man:command_queue_index()] = true
```

Replace in `IC.ensure_leaders` the pool-lord draw:

```lua
                local subtype = lords[cm:random_number(#lords, 1)]
                local list = R.BACKGROUNDS[slug]
                local bg = list[cm:random_number(#list, 1)]
                local ok, err = pcall(function()
                    local details = cm:spawn_character_to_pool(faction_key, "", "", "",
```

with:

```lua
                local subtype = lords[cm:random_number(#lords, 1)]
                local bg = IC.trade_in(slug, faction_key)
                local ok, err = pcall(function()
                    local details = cm:spawn_character_to_pool(faction_key, "", "", "",
```

Replace in `IC.seed_step`:

```lua
    local slug = plan[i]
    local R = IC.R(faction_key)
    local region = IC.hire_region(real_faction(faction_key))
    local x, y = -1, -1
```

with:

```lua
    local slug = plan[i]
    local region = IC.hire_region(real_faction(faction_key))
    local x, y = -1, -1
```

Replace in `IC.seed_step`:

```lua
    local subtype = lords[cm:random_number(#lords, 1)]
    local list = R.BACKGROUNDS[slug]
    local bg = list[cm:random_number(#list, 1)]
    local token = {}
```

with:

```lua
    local subtype = lords[cm:random_number(#lords, 1)]
    local bg = IC.trade_in(slug, faction_key)
    local token = {}
```

Replace in `IC.field_leader`:

```lua
function IC.field_leader(faction_key, slug)
    local R = IC.R(faction_key)
    local region = IC.hire_region(real_faction(faction_key))
```

with:

```lua
function IC.field_leader(faction_key, slug)
    local region = IC.hire_region(real_faction(faction_key))
```

Replace in `IC.field_leader`:

```lua
    local subtype = lords[cm:random_number(#lords, 1)]
    local list = R.BACKGROUNDS[slug]
    local bg = list[cm:random_number(#list, 1)]
    local okr, rank = pcall(IC.recruit_rank, faction_key, region_key)
```

with:

```lua
    local subtype = lords[cm:random_number(#lords, 1)]
    local bg = IC.trade_in(slug, faction_key)
    local okr, rank = pcall(IC.recruit_rank, faction_key, region_key)
```

Replace in `IC.field_leader`:

```lua
                        cm:force_add_trait(lookup, IC.bg_trait(bg), false)
                    end
                    -- BY, NOT TO: CA's wrapper calls level_up_agent_rank.
```

with:

```lua
                        cm:force_add_trait(lookup, IC.bg_trait(bg), false)
                    end
                    IC.fit_culture(faction_key, man, slug)
                    -- BY, NOT TO: CA's wrapper calls level_up_agent_rank.
```

Delete `IC.roll_origin`:

```lua
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
```

with:

```lua
function IC.stamp_court(faction_key, attempts)
```

Replace the second loop of `IC.stamp_court`:

```lua
    for i = 1, #men do
        local character = men[i].man
        if IC.stamp_bg(character,
                       IC.background_for(character, faction_key, tally), true) then
            stamped = stamped + 1
        end
    end
    return stamped
end
```

with:

```lua
    for i = 1, #men do
        local character = men[i].man
        local bg, culture, binding = IC.background_for(character, faction_key, tally)
        if IC.stamp_bg(character, bg, true) then
            stamped = stamped + 1
        end
        if IC.stamp_culture(faction_key, character, culture, binding) then
            stamped = stamped + 1
        end
    end
    return stamped
end
```

Delete the origin stamp from the first loop of `IC.stamp_court`. It can no longer stamp anything: `IC.origin_for` now answers only a legend's own origin, `IC.correct_history` has put that on him two lines earlier, and `IC.stamp_origin` refuses a man who wears one. Task 9 retires the mutant aimed at it.

```lua
            if IC.correct_history(character) then
                stamped = stamped + 1
            end
            -- Use the fixed-history readers so legendary lords are never rerolled.
            if IC.stamp_origin(character, IC.origin_for(character, faction_key), true) then
                stamped = stamped + 1
            end
            if IC.stamp_ambition(faction_key, character) then
```

with:

```lua
            if IC.correct_history(character) then
                stamped = stamped + 1
            end
            if IC.stamp_ambition(faction_key, character) then
```

Replace `IC.stamp_bg` (whole function):

```lua
function IC.stamp_bg(character, slug, quiet)
    if not slug then return false end
    if not character or character:is_null_interface() then return false end
    if IC.bg_of_character(character) then return false end
    cm:force_add_trait(cm:char_lookup_str(character),
                       IC.bg_trait(slug), not quiet)
    return true
end
```

with:

```lua
function IC.stamp_bg(character, slug, quiet)
    if not slug then return false end
    if not character or character:is_null_interface() then return false end
    if IC.bg_of_character(character) then return false end
    cm:force_add_trait(cm:char_lookup_str(character),
                       IC.bg_trait(slug), not quiet)
    return true
end

-- THE CULTURE TRAIT, ALWAYS QUIET. A binding culture replaces the one he wears;
-- a drawn one never does. Every retired birthplace he wears comes off with it
-- (a place origin has no faction behind it), which is how an old save is
-- converted: the place becomes the culture of the same country
-- (R.PLACE_CULTURE, chosen in IC.culture_for) and his party and trade are
-- untouched. True when a trait moved.
function IC.stamp_culture(faction_key, character, slug, binding)
    if not slug then return false end
    if not character or character:is_null_interface() then return false end
    local lookup = cm:char_lookup_str(character)
    local moved = false
    for _, k in ipairs(IC.RACE_ORDER) do
        local R = IC.RACES[k]
        for i = 1, #R.ORIGINS do
            local o = R.ORIGINS[i]
            if not o.faction and character:has_trait(IC.rkey("house", o.slug, R)) then
                cm:force_remove_trait(lookup, IC.rkey("house", o.slug, R))
                moved = true
            end
        end
    end
    local has, hasR = IC.culture_of_character(character)
    if has == slug then return moved end
    if has and not binding then return moved end
    if has then cm:force_remove_trait(lookup, IC.rkey("cult", has, hasR)) end
    cm:force_add_trait(lookup, IC.culture_trait(slug, faction_key), false)
    return true
end

-- A MAN MOVED TO ANOTHER PARTY (an idle Crown lord taking over a leaderless one,
-- a leader put in the field) keeps his culture when it feeds that party or is
-- bound to him, and is dealt one that does when it does not. Quiet. A man with
-- no culture is left for the next court pass.
function IC.fit_culture(faction_key, character, party)
    local has = IC.culture_of_character(character)
    if not has then return false end
    local main, sides = IC.cultures_of(faction_key, party)
    if not main or has == main then return false end
    for i = 1, #sides do
        if sides[i] == has then return false end
    end
    local _, binding = IC.culture_for(character, faction_key, party)
    if binding then return false end
    return IC.stamp_culture(faction_key, character, IC.roll_culture(faction_key, party), true)
end
```

Replace in `IC.stamp_incoming`:

```lua
        IC.stamp_bg(man, IC.background_for(man, faction_key, tally), true)
```

with:

```lua
        local bg, culture, binding = IC.background_for(man, faction_key, tally, want)
        IC.stamp_bg(man, bg, true)
        IC.stamp_culture(faction_key, man, culture, binding)
```

Replace in the `ic_born` listener:

```lua
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
```

with:

```lua
            local seeded = IC._seed_bg[faction_key]
            if seeded then
                IC._seed_bg[faction_key] = nil
                IC.stamp_origin(character, IC.origin_for(character, faction_key), true)
                IC.stamp_bg(character, seeded, true)
                local culture, binding = IC.culture_for(character, faction_key,
                    IC.R(faction_key).PARTY_OF_BG[seeded])
                IC.stamp_culture(faction_key, character, culture, binding)
                return
            end
            -- A GARRISON CAPTAIN joins quietly: one is made at every capture,
            -- and each would show two Trait Gained entries. The culture is
            -- always quiet.
            local quiet = IC.is_colonel(character)
            IC.stamp_origin(character, IC.origin_for(character, faction_key), quiet)
            local bg = IC.deed_join(character, faction_key)
            local culture, binding
            if bg then
                culture, binding = IC.culture_for(character, faction_key,
                    IC.R(faction_key).PARTY_OF_BG[bg])
            else
                bg, culture, binding = IC.background_for(character, faction_key)
            end
            IC.stamp_bg(character, bg, quiet)
            IC.stamp_culture(faction_key, character, culture, binding)
```

Replace Gorduz in `IC.LORD_HISTORY`:

```lua
    wh3_dlc23_chd_gorduz_backstabber = {origin = "zornuzkul", bg = "wrangler"},
```

with:

```lua
    wh3_dlc23_chd_gorduz_backstabber = {bg = "wrangler"},
```

- [ ] **Step 5: Run the harness**

```powershell
& "C:\Program Files (x86)\Lua\5.1\luac.exe" -p "Modding Files\pack\script\campaign\mod\zzz_derpy_iron_court.lua"
& "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua
```

Expected: a clean `luac -p`, then `iron court harness: ok (1119 checks)`. One check reads the generated `character_traits.tsv` to prove every key a Dwarf court wears is a row the generator ships (`dwarfs: every key a Dwarf court wears is a Dwarf row the generator ships`). It fails with `a Dwarf lord was given derpy_ic_cult_dwf_karaz, which no character_traits row declares` when the TSVs were not rewritten after Task 3: run `py tools\gen_iron_court.py` and the harness again.

- [ ] **Step 6: Run the Lua gates**

```powershell
py tools\check_lua_api.py "Modding Files\pack\script\campaign\mod\zzz_derpy_iron_court.lua"
py tools\check_lua_undeclared.py
py tools\check_lua_literal_left.py
```

Expected: `0 suspect call(s)` and no findings from the other two.

- [ ] **Step 7: Ledger**

Append: `Task 4 done: zzz_derpy_iron_court.lua, _iron_court_harness.lua; harness 1119 checks; luac, check_lua_api, check_lua_undeclared, check_lua_literal_left clean. The importer refuses until Task 8.`

---

### Task 5: What a governor's culture does to his province

**Files:**
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court.lua` (new `IC.apply_gov_culture` after `IC.apply_gov_base`, `IC.clear_gov_bundles`, the head and body of `IC.apply_governor_bundles`)
- Modify: `tools/_iron_court_harness.lua` (two old checks rewritten in four edits, one new `do ... end` block of seven checks)

**Interfaces:**
- Consumes (Tasks 1 and 3): `IC.culture_of_character(character) -> slug, R | nil`, `IC.culture_case(faction_key, culture, province_key) -> "home" | "foreign" | "away"`, `IC.gov_bundle_culture(slug, faction_key)`, `IC.gov_bundle_culture_home(slug, faction_key)`, `IC.gov_bundle_friction(faction_key)`, `R.CULTURES`; the bundles themselves, which the generator emits (16 culture and home bundles a race and one friction bundle a race). Already in the file: `IC.apply_gov_base`, `IC.gov_bundle_base`, `IC.gov_bundle_house`.
- Produces: `IC.apply_gov_culture(faction_key, character, province_key, region) -> "home" | "away" | "foreign" | nil`. A governor now wears the base bundle and his culture's bundle; the nine party bundles `derpy_ic_gov_house_*` are no longer applied, only removed.

A governor used to wear the base bundle and a bundle for his party. He now wears the base bundle and one culture bundle, chosen by the province he governs: the home bundle in a province his culture calls home, the away bundle anywhere else, and in a province another culture calls home the away bundle and the friction bundle together (Control -4). A man with no culture, or one whose culture belongs to the other race, wears the base bundle only. `IC.clear_gov_bundles` removes every culture bundle, both cases, and the friction bundle before each pass, so a governor who moves, or whose province changes hands, leaves nothing behind. It still removes the nine party bundles, because a save made before the cultures may carry one.

- [ ] **Step 1: Rewrite the old checks that expect a party bundle**

Two existing checks expect the party bundle `derpy_ic_gov_house_crown` on a governor. Four edits give each governor a culture and expect that culture's bundle instead. Each pair is applied once, to `tools/_iron_court_harness.lua`.

Replace:

```lua
    local gov = make_character(9, ANY_SEAT, "crown", "prov_a")
```

with:

```lua
    local gov = make_character(9, ANY_SEAT, "crown", "prov_a", nil, nil, nil, "zharr")
```

Replace:

```lua
    assert(province_applied["derpy_ic_gov_house_crown"],
        "and so must his party's flavour")
```

with:

```lua
    assert(province_applied["derpy_ic_gov_cult_zharr"],
        "and so must his culture's bundle")
```

Replace:

```lua
check("a governor inside his province applies base and house bundles", function()
    IC.state = {}
    province_applied = {}
    local nakh = make_character(5, ANY_SEAT, "crown", "prov_a")
```

with:

```lua
check("a governor inside his province applies base and culture bundles", function()
    IC.state = {}
    province_applied = {}
    local nakh = make_character(5, ANY_SEAT, "crown", "prov_a", nil, nil, nil, "zharr")
```

Replace:

```lua
    assert(province_applied["derpy_ic_gov_house_crown"], "his party's flavour applied")
```

with:

```lua
    assert(province_applied["derpy_ic_gov_cult_zharr"], "his culture's bundle applied")
    assert(not province_applied["derpy_ic_gov_house_crown"],
        "the retired party flavour was applied again")
```

- [ ] **Step 2: Write the failing checks**

Add this block to `tools/_iron_court_harness.lua` immediately above the final `check("no engine setter was ever handed anything but a boolean", ...)`. It has seven checks. `govern()` appoints one governor through the model and records the bundles he caused.

```lua
-- CULTURES, task 5: what a governor's culture does to his province.
do
    local DF = "wh_main_dwf_dwarfs"
    -- The Foundry Districts are the Stump's home; the Gorgoth Pits are Gorgoth's.
    local FOUNDRY = "cr_oldworld_province_foundry_district"
    local PITS = "cr_oldworld_province_pits_district"

    -- ONE GOVERNOR wearing `culture` (the trait suffix, so "dwf_kadrin" for a
    -- Dwarf) in `province`, appointed through the model, with the bundles he
    -- caused recorded in province_applied. Returns the faction key.
    local function govern(faction_key, subculture, culture, province)
        IC.state = {}
        factions = {}
        rng(nil)
        province_applied = {}
        province_removed = {}
        local man = make_character(9800, ANY_SEAT, nil, province, nil, nil, nil, culture)
        make_faction(faction_key, subculture, {man}, {province})
        IC.add_house(faction_key, IC.CROWN)
        endow(faction_key)
        assert(IC.assign_governor(faction_key, province, 9800), "the governor was refused")
        return faction_key
    end

    local function applied_culture_bundles()
        local out = {}
        for key in pairs(province_applied) do
            if string.find(key, "derpy_ic_gov_cult_", 1, true) or string.find(key, "friction", 1, true) then
                out[#out + 1] = key
            end
        end
        table.sort(out)
        return table.concat(out, ",")
    end

    check("governing: a governor in his culture's home wears the home bundle and nothing else", function()
        govern(F, IC.CHD_SUBCULTURE, "stump", FOUNDRY)
        assert(province_applied["derpy_ic_gov_base"], "the base bundle is gone")
        assert(applied_culture_bundles() == "derpy_ic_gov_cult_home_stump", applied_culture_bundles())
    end)

    check("governing: in another culture's home he wears his away bundle and the friction", function()
        govern(F, IC.CHD_SUBCULTURE, "stump", PITS)
        assert(applied_culture_bundles() == "derpy_ic_gov_cult_stump,derpy_ic_gov_friction", applied_culture_bundles())
    end)

    check("governing: on a map with no Old World keys every governor is away, with no friction", function()
        for _, province in ipairs({"prov_a", "wh3_main_combi_province_the_plain_of_zharr", "cr_combi_province_x"}) do
            govern(F, IC.CHD_SUBCULTURE, "stump", province)
            assert(province_applied["derpy_ic_gov_base"], province .. ": the base bundle is gone")
            assert(applied_culture_bundles() == "derpy_ic_gov_cult_stump", province .. ": " .. applied_culture_bundles())
        end
    end)

    check("governing: a governor with no culture gives the base bundle and nothing more", function()
        govern(F, IC.CHD_SUBCULTURE, nil, FOUNDRY)
        assert(province_applied["derpy_ic_gov_base"], "the base bundle is gone")
        assert(applied_culture_bundles() == "", applied_culture_bundles())
        assert(not province_applied["derpy_ic_gov_house_crown"], "the retired party flavour came back")
    end)

    check("governing: the Dwarf race reads its own provinces and its own keys", function()
        govern(DF, IC.RACES.dwf.subculture, "dwf_kadrin", "cr_oldworld_province_peak_pass")
        assert(applied_culture_bundles() == "derpy_ic_gov_cult_home_dwf_kadrin", applied_culture_bundles())
        govern(DF, IC.RACES.dwf.subculture, "dwf_kadrin", "cr_oldworld_province_agrildrin")
        assert(applied_culture_bundles() == "derpy_ic_gov_cult_dwf_kadrin,derpy_ic_gov_dwf_friction", applied_culture_bundles())
        -- A CHAOS DWARF HOME IS NO DWARF HOME.
        govern(DF, IC.RACES.dwf.subculture, "dwf_kadrin", FOUNDRY)
        assert(applied_culture_bundles() == "derpy_ic_gov_cult_dwf_kadrin", applied_culture_bundles())
    end)

    check("governing: a culture of the other race applies nothing", function()
        govern(DF, IC.RACES.dwf.subculture, "stump", FOUNDRY)
        assert(province_applied[IC.gov_bundle_base(DF)], "the base bundle is gone")
        assert(applied_culture_bundles() == "", applied_culture_bundles())
    end)

    check("governing: every culture bundle comes off the province before the pass re-applies", function()
        local fk = govern(F, IC.CHD_SUBCULTURE, "stump", FOUNDRY)
        province_removed = {}
        IC.apply_governor_bundles(fk)
        local gone = {}
        for _, entry in ipairs(province_removed) do gone[entry] = true end
        local at = "@region_" .. FOUNDRY
        local count = 0
        for _, c in ipairs(IC.R(fk).CULTURES) do
            assert(gone[IC.gov_bundle_culture(c.slug, fk) .. at], c.slug .. " away bundle is never removed")
            assert(gone[IC.gov_bundle_culture_home(c.slug, fk) .. at], c.slug .. " home bundle is never removed")
            count = count + 2
        end
        assert(gone[IC.gov_bundle_friction(fk) .. at], "the friction bundle is never removed")
        for _, party in ipairs(IC.R(fk).PARTIES) do
            assert(gone[IC.gov_bundle_house(party, fk) .. at], party .. " party flavour of an old save is never removed")
        end
        assert(count == 16)
    end)
end

```

- [ ] **Step 3: Run the harness and confirm the failures**

```powershell
$env:IC_TEST_ALL = "1"; & "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua 2> harness_fail.txt; Remove-Item Env:IC_TEST_ALL
Get-Content harness_fail.txt
```

Expected: `7 failing`. Two are the rewritten checks, `appointing an overseer applies his bundle on the CLICK` (`and so must his culture's bundle`) and `a governor inside his province applies base and culture bundles` (`his culture's bundle applied`). Five are new `governing:` checks: the home case, the foreign case, the map with no Old World keys, the Dwarf keys, and the clearing (`zharr away bundle is never removed`). The other two new checks pass at once, because they guard what must not happen: a governor with no culture gives only the base bundle, and a culture of the other race applies nothing. Task 9 breaks the second with the mutant `culture: another race's culture governs`.

- [ ] **Step 4: Edit the Lua**

All in `zzz_derpy_iron_court.lua`. Do the edits in this order; each is a replacement of the exact text shown, and the old text must appear once.

Replace the end of `IC.apply_gov_base`:

```lua
    -- THE PLAIN BUNDLE IF THE RUNTIME ONE FAILED: a governor still governs.
    if not ok then
        cm:apply_effect_bundle_to_faction_province(IC.gov_bundle_base(fk), region, -1)
    end
end
```

with:

```lua
    -- THE PLAIN BUNDLE IF THE RUNTIME ONE FAILED: a governor still governs.
    if not ok then
        cm:apply_effect_bundle_to_faction_province(IC.gov_bundle_base(fk), region, -1)
    end
end

-- THE GOVERNOR'S CULTURE, on his province. In a province his culture calls home
-- he wears the home bundle (his benefits 50% stronger, the drawback unchanged);
-- anywhere else the away bundle; and in a province another culture calls home
-- the friction bundle as well. A man with no culture, or one of another race's,
-- wears nothing here: the base bundle is all he gives. Returns "home", "away" or
-- "foreign", or nil when nothing was applied.
function IC.apply_gov_culture(faction_key, character, province_key, region)
    local culture, race = IC.culture_of_character(character)
    if not culture or race ~= IC.R(faction_key) then return nil end
    local case = IC.culture_case(faction_key, culture, province_key)
    if case == "home" then
        cm:apply_effect_bundle_to_faction_province(
            IC.gov_bundle_culture_home(culture, faction_key), region, -1)
        return case
    end
    cm:apply_effect_bundle_to_faction_province(
        IC.gov_bundle_culture(culture, faction_key), region, -1)
    if case == "foreign" then
        cm:apply_effect_bundle_to_faction_province(
            IC.gov_bundle_friction(faction_key), region, -1)
    end
    return case
end
```

Replace in `IC.clear_gov_bundles`:

```lua
                cm:remove_effect_bundle_from_faction_province(IC.gov_bundle_base(faction_key), region)
                for j = 1, #R.PARTIES do
                    cm:remove_effect_bundle_from_faction_province(
                        IC.gov_bundle_house(R.PARTIES[j], faction_key), region)
                end
```

with:

```lua
                cm:remove_effect_bundle_from_faction_province(IC.gov_bundle_base(faction_key), region)
                -- THE OLD PARTY FLAVOUR, which no governor is given any more: a
                -- save made before the cultures may still carry one.
                for j = 1, #R.PARTIES do
                    cm:remove_effect_bundle_from_faction_province(
                        IC.gov_bundle_house(R.PARTIES[j], faction_key), region)
                end
                for j = 1, #R.CULTURES do
                    local slug = R.CULTURES[j].slug
                    cm:remove_effect_bundle_from_faction_province(
                        IC.gov_bundle_culture(slug, faction_key), region)
                    cm:remove_effect_bundle_from_faction_province(
                        IC.gov_bundle_culture_home(slug, faction_key), region)
                end
                cm:remove_effect_bundle_from_faction_province(
                    IC.gov_bundle_friction(faction_key), region)
```

Replace the head of `IC.apply_governor_bundles`:

```lua
function IC.apply_governor_bundles(faction_key)
    local R = IC.R(faction_key)
    local court = IC.court(faction_key)
```

with:

```lua
function IC.apply_governor_bundles(faction_key)
    local court = IC.court(faction_key)
```

Replace in `IC.apply_governor_bundles`:

```lua
            IC.apply_gov_base(character, region)
            local slug = IC.house_of_character(character, faction_key)
            if slug and R.BACKGROUNDS[slug] then
                cm:apply_effect_bundle_to_faction_province(
                    IC.gov_bundle_house(slug, faction_key), region, -1)
            end
```

with:

```lua
            IC.apply_gov_base(character, region)
            IC.apply_gov_culture(faction_key, character, province_key, region)
```

- [ ] **Step 5: Run the harness**

```powershell
& "C:\Program Files (x86)\Lua\5.1\luac.exe" -p "Modding Files\pack\script\campaign\mod\zzz_derpy_iron_court.lua"
& "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua
```

Expected: a clean `luac -p`, then `iron court harness: ok (1126 checks)`.

- [ ] **Step 6: Run the Lua gates**

```powershell
py tools\check_lua_api.py "Modding Files\pack\script\campaign\mod\zzz_derpy_iron_court.lua"
py tools\check_lua_undeclared.py
py tools\check_lua_literal_left.py
```

Expected: `0 suspect call(s)` and no findings from the other two.

- [ ] **Step 7: Ledger**

Append: `Task 5 done: zzz_derpy_iron_court.lua, _iron_court_harness.lua; harness 1126 checks; luac, check_lua_api, check_lua_undeclared, check_lua_literal_left clean.`

---

### Task 6: Laws, culture stances and the party swing

**Files:**
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court.lua` (the `IC.LAWS` option rows, new `IC.culture_stance` and `IC.man_stance` after `IC.law_stance`, `IC.law_voters`, `IC.law_line`, `IC.law_tally`, `IC.law_win_price`, new `IC.law_swing`, the pass loop of `IC.law_settle`)
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_dwarf.lua` (the `DWF.LAWS` option rows)
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_ui.lua` (`ICUI.law_groups`, `ICUI.fill_law_block`)
- Modify: `tools/gen_iron_court.py` (`CULTURE_STANCES`, `_law_rows`, `model_law_cultures`, `check_culture_laws`, `check()`, the selftest)
- Modify: `tools/_iron_court_harness.lua` (`law_court`, `RACE_ARITY`, one new `do ... end` block of eleven checks)

**Interfaces:**
- Consumes: `IC.culture_of_character(character) -> slug, R | nil` and `R.CULTURES` (Task 1); the generator's `RACES[race]["CULTURES"]` and `check_cultures` (Task 3); `IC.R(faction_key)`; `IC.law_opt`; `IC.law_stance(category, option, party, faction_key)`.
- Produces:
  - Each non-start option row of `IC.LAWS` and `DWF.LAWS` may carry `cpro` and `ccon`, lists of culture slugs beside the parties' `pro` and `con`.
  - `IC.culture_stance(category, option, culture, faction_key) -> "aye" | "nay" | nil`.
  - `IC.man_stance(category, option, party, culture, faction_key) -> "aye" | "nay" | nil`: the culture's stance where it has one, the party's otherwise.
  - `IC.law_line(faction_key, vote, category, party, culture)`: the fifth argument is optional; without it the answer is the party's own line, as before.
  - `IC.law_voters` records and `IC.law_tally` men carry `culture`; tally men also carry `level`, the push that multiplied the man (nil when none did).
  - `IC.law_swing(tally, slug, flat) -> integer`: the loyalty a party moves on a passed law.
  - `ICUI.law_groups` blocks carry `level` (0 when the block's men were not multiplied).
  - Harness: `law_court(men, weights)` reads a fourth element of each man as his culture (the trait suffix, as `make_character` takes it).
  - Generator: `CULTURE_STANCES[race][culture] = (for_options, against_options)` with options as `"category.option"`, `model_law_cultures(prefix)`, `check_culture_laws(race)`.

Four decisions are made here and are worth reading before the code.

1. **A man's line is his culture's stance where it has one and his party's otherwise** (spec 7.2). The Crown is the exception: its men vote as the player chooses, whatever their culture says.
2. **A party's push multiplies only the men on the party's own line.** A man whose culture sends him the other way is not carried along by a push he is against. The tally records the push that multiplied each man in `level`, and the vote panel reads it, so a block of dissenters does not claim the party's multiplier.
3. **The loyalty swing follows how a party's men voted** (spec 7.2): the step (5) times the influence of its aye men minus the influence of its nay men, over the influence of the men who voted, the half rounding away from zero. A united party moves the whole step and a 50/50 party does not move. The Crown keeps the flat step, because its men's votes say nothing of where the Crown house stands: the Crown is on the against list for Open Roads, and passing Open Roads over its objection costs the house whichever way its men voted. A party none of whose men voted keeps the flat step too (the old rule).
4. **Not changed, and said so:** the overrule penalty (`IC.law_overrule`, loyalty -10 to every party whose line loses) still reads party lines, and parties still propose and push laws on their party stance alone. Both are listed under known gaps at the end of this plan.

- [ ] **Step 1: Teach the harness fixture about cultures, and the arity table about the new readers**

Replace:

```lua
        chars[#chars + 1] = make_character(9000 + i, ANY_SEAT, m[1], nil, m[3])
```

with:

```lua
        chars[#chars + 1] = make_character(9000 + i, ANY_SEAT, m[1], nil, m[3], nil, nil, m[4])
```

Replace:

```lua
-- A PLAYER COURT FOR THE LAWS, past its grace period.
-- `men` is {{party, influence}, ...}; man i is cqi 9000 + i.
```

with:

```lua
-- A PLAYER COURT FOR THE LAWS, past its grace period.
-- `men` is {{party, influence, unique, culture}, ...}; man i is cqi 9000 + i, and
-- a culture is the trait suffix as make_character takes it.
```

Replace:

```lua
    office_by_slug = 2, law_opt = 3, law_stance = 4, is_party = 2, rolled_name = 4,
```

with:

```lua
    office_by_slug = 2, law_opt = 3, law_stance = 4, culture_stance = 4, man_stance = 5,
    is_party = 2, rolled_name = 4,
```

- [ ] **Step 2: Write the failing checks**

Add this block to `tools/_iron_court_harness.lua` immediately above the final `check("no engine setter was ever handed anything but a boolean", ...)`. It has eleven checks. Seven fail until the implementation is in. Four guard behaviour that must not change and pass at once: the Crown's man ignoring his culture, a culture of the other race counting for nothing, a party with no voting man keeping the flat step, and the Crown keeping the flat step. Task 9 breaks each of those four with a mutant and watches the harness fail, because a check that has never failed proves nothing.

```lua
-- CULTURES, task 6: a man's culture beats his party on a law.
do
    -- On the Ash Harvest (labour.ash) the Legion is for and the Ledger against.
    -- Gash Kadrak is for it, the Mines of Mingol against, the Heart of Zharrduk
    -- has no stance.
    local function man_of(tally, cqi)
        for _, m in ipairs(tally.men) do
            if m.cqi == cqi then return m end
        end
        return nil
    end

    check("culture laws: every stance names a culture of its race and an option, on one side only", function()
        for _, key in ipairs(IC.RACE_ORDER) do
            local R = IC.RACES[key]
            local seen = {}
            for _, c in ipairs(R.CULTURES) do seen[c.slug] = {pro = 0, con = 0} end
            for _, cat in ipairs(R.LAW_ORDER) do
                for i, opt in ipairs(R.LAWS[cat].order) do
                    local o = R.LAWS[cat].opts[opt]
                    if i == 1 then
                        assert(not o.cpro and not o.ccon, key .. " " .. cat .. "." .. opt .. ": the start option has a stance")
                    end
                    local here = {}
                    for _, side in ipairs({"cpro", "ccon"}) do
                        for _, slug in ipairs(o[side] or {}) do
                            assert(seen[slug], key .. " " .. cat .. "." .. opt .. ": " .. slug .. " is no culture of the race")
                            assert(not here[slug], key .. " " .. cat .. "." .. opt .. ": " .. slug .. " is listed twice")
                            here[slug] = true
                            local count = side == "cpro" and "pro" or "con"
                            seen[slug][count] = seen[slug][count] + 1
                        end
                    end
                end
            end
            for slug, n in pairs(seen) do
                assert(n.pro >= 2 and n.con >= 1, key .. " " .. slug .. " is for " .. n.pro .. " and against " .. n.con)
            end
        end
    end)

    check("culture laws: a man votes his culture's side, and a culture with no stance leaves him with his party", function()
        local court = law_court({{"legion", 100, nil, "mines"}, {"legion", 60, nil, "zharr"},
                                 {"ledger", 50, nil, "gash"}, {"ledger", 30}})
        law_vote(court, "ash", "aye")
        local t = IC.law_tally(F, "labour")
        local a, b, c, d = man_of(t, 9001), man_of(t, 9002), man_of(t, 9003), man_of(t, 9004)
        assert(a.side == "nay" and a.why == "against", "the Mines man in the Legion: " .. tostring(a.side))
        assert(b.side == "aye" and b.why == "for", "a culture with no stance moved the Legion man: " .. tostring(b.side))
        assert(c.side == "aye" and c.why == "for", "the Gash man in the Ledger: " .. tostring(c.side))
        assert(d.side == "nay" and d.why == "against", "a Ledger man with no culture: " .. tostring(d.side))
        assert(t.aye == 60 + 50 and t.nay == 100 + 30, "aye " .. t.aye .. " nay " .. t.nay)
        assert(a.culture == "mines" and d.culture == nil, "the tally dropped the culture")
    end)

    check("culture laws: a culture stance beats the loyalty rule for a party with no stance", function()
        -- The Temple has no stance on the Ash Harvest, so a Temple man with no culture
        -- follows his party's loyalty; one of the Mines votes against it whatever it is.
        local court = law_court({{"crown", 10}, {"temple", 100}, {"temple", 70, nil, "mines"}},
                                {crown = 10, legion = 10, ledger = 10, temple = 10})
        law_vote(court, "ash", "aye")
        court.houses.temple.loyalty = IC.TUNE.law_loyal_line
        local t = IC.law_tally(F, "labour")
        assert(man_of(t, 9002).side == "aye" and man_of(t, 9002).why == "loyal", "a loyal Temple man")
        assert(man_of(t, 9003).side == "nay" and man_of(t, 9003).why == "against", "the Mines man in the Temple")
        court.houses.temple.loyalty = IC.TUNE.law_disloyal_line
        t = IC.law_tally(F, "labour")
        assert(man_of(t, 9002).side == nil and man_of(t, 9003).side == "nay",
            "a torn Temple party drew its Mines man with it")
    end)

    check("culture laws: the Crown's man votes as the Crown whatever his culture says", function()
        local court = law_court({{"crown", 100, nil, "mines"}, {"crown", 40, nil, "gash"}})
        law_vote(court, "ash", "aye")
        local t = IC.law_tally(F, "labour")
        assert(t.aye == 140 and t.nay == 0, "aye " .. t.aye .. " nay " .. t.nay)
        court.votes.labour.stance = "abstain"
        t = IC.law_tally(F, "labour")
        assert(t.aye == 0 and t.nay == 0 and t.abstain == 140, "an abstaining Crown's men voted: " .. t.aye .. "/" .. t.nay)
    end)

    check("culture laws: a culture of the other race is no culture of this court", function()
        local court = law_court({{"legion", 100, nil, "dwf_deeps"}})
        law_vote(court, "ash", "aye")
        local m = man_of(IC.law_tally(F, "labour"), 9001)
        assert(m.culture == nil and m.side == "aye", "a Dwarf culture was read in a Chaos Dwarf court: " .. tostring(m.culture))
    end)

    check("culture laws: a push multiplies the men on their party's line and not the man whose culture votes against it", function()
        local court = law_court({{"legion", 100}, {"legion", 40, nil, "mines"}, {"legion", 30, nil, "gash"}})
        local v = law_vote(court, "ash", "nay")
        v.push.legion = 2
        local t = IC.law_tally(F, "labour")
        local mult = IC.TUNE.law_push_mult[2]
        local a, b, c = man_of(t, 9001), man_of(t, 9002), man_of(t, 9003)
        assert(a.side == "aye" and a.level == 2 and a.w == math.floor(100 * mult / 100), "the party man: " .. a.w)
        assert(b.side == "nay" and b.level == nil and b.w == 40, "the Mines man was pushed: " .. b.w)
        assert(c.side == "aye" and c.level == 2 and c.w == math.floor(30 * mult / 100), "the Gash man: " .. c.w)
    end)

    check("culture laws: the vote panel shows the push only on the block that carries it", function()
        local court = law_court({{"crown", 10}, {"legion", 100}, {"legion", 40, nil, "mines"}})
        local v = law_vote(court, "ash", "aye")
        v.push.legion = 2
        local groups = ICUI.law_groups(IC.law_tally(F, "labour"))
        assert(#groups.aye == 2 and #groups.nay == 1, "blocks: " .. #groups.aye .. " aye, " .. #groups.nay .. " nay")
        local legion_aye = nil
        for _, g in ipairs(groups.aye) do if g.party == "legion" then legion_aye = g end end
        assert(legion_aye and legion_aye.level == 2, "the Legion's aye block lost its push")
        assert(groups.nay[1].party == "legion" and groups.nay[1].level == 0, "the dissenters wear the party's push")
        with_fake_panel(function(panel)
            ICUI.view, ICUI.law_cat = "laws", "labour"
            ICUI.refresh()
            local ayes = panel.children[ICUI.LAWBLOCK .. "_1"].children.ic_lb_level.text
            local nays = panel.children[ICUI.LAWBLOCK .. "_" .. (ICUI.LB_PER_SIDE + 1)].children.ic_lb_level.text
            assert(string.find(ayes, "x%d") or string.find(ayes, "Votes"), "the aye block says nothing: " .. tostring(ayes))
            assert(not string.find(nays, "x%d"), "the dissenters' block shows a multiplier: " .. tostring(nays))
        end)
        gov_done()
    end)

    check("culture laws: a man's price is doubled by his own stance, and a man his culture sides with you cannot be won", function()
        local weights = {crown = 10, legion = 10, ledger = 10, temple = 10}
        local court = law_court({{"crown", 2000}, {"temple", 200, nil, "mines"}, {"temple", 200},
                                 {"legion", 200, nil, "mines"}, {"ledger", 200, nil, "gash"}}, weights)
        law_vote(court, "ash", "aye")
        court.houses.temple.loyalty = 50
        for cqi = 9002, 9005 do court.ambition[cqi] = "cautious" end
        local base = math.floor(200 * IC.TUNE.law_win_rate * IC.TUNE.law_win_ambition.cautious / 10000)
        -- A TEMPLE MAN WITH A CULTURE AGAINST: the Temple has no stance, his culture does.
        assert(IC.law_win_price(F, "labour", 9002) == 2 * base,
            "the Mines man in the Temple costs " .. tostring(IC.law_win_price(F, "labour", 9002)))
        assert(IC.law_win_price(F, "labour", 9003) == base,
            "a torn Temple man with no culture costs " .. tostring(IC.law_win_price(F, "labour", 9003)))
        -- A LEGION MAN WHOSE CULTURE IS AGAINST: his party is for you, he is not.
        assert(IC.law_win_price(F, "labour", 9004) == 2 * base,
            "the Mines man in the Legion costs " .. tostring(IC.law_win_price(F, "labour", 9004)))
        -- A LEDGER MAN WHOSE CULTURE IS FOR: already voting your way.
        local p, why = IC.law_win_price(F, "labour", 9005)
        assert(p == nil and why == "law_with_you", "the Gash man in the Ledger: " .. tostring(p) .. " " .. tostring(why))
        gov_done()
    end)

    check("culture laws: a passed law moves a party by how its men voted, rounding the half away from zero", function()
        local court = law_court({{"crown", 500}, {"legion", 60}, {"legion", 40, nil, "mines"}, {"ledger", 80}})
        law_vote(court, "ash", "aye")
        local l0, d0 = court.houses.legion.loyalty, court.houses.ledger.loyalty
        assert(IC.law_settle(F, "labour", true), "the law did not pass")
        assert(court.houses.legion.loyalty == l0 + 1, "a 60/40 Legion moved " .. (court.houses.legion.loyalty - l0))
        assert(court.houses.ledger.loyalty == d0 + IC.TUNE.law_pass_loss, "a united Ledger moved "
            .. (court.houses.ledger.loyalty - d0))
        gov_done()
        court = law_court({{"crown", 500}, {"legion", 75}, {"legion", 25, nil, "mines"},
                           {"ledger", 75}, {"ledger", 25, nil, "gash"}})
        law_vote(court, "ash", "aye")
        l0, d0 = court.houses.legion.loyalty, court.houses.ledger.loyalty
        assert(IC.law_settle(F, "labour", true), "the law did not pass")
        assert(court.houses.legion.loyalty == l0 + 3, "a 75/25 Legion moved " .. (court.houses.legion.loyalty - l0))
        assert(court.houses.ledger.loyalty == d0 - 3, "a 25/75 Ledger moved " .. (court.houses.ledger.loyalty - d0))
        gov_done()
    end)

    check("culture laws: a party none of whose men voted keeps the flat step", function()
        -- Only the Crown has a man here, so the Legion and the Ledger have no vote to read.
        local court = law_court({{"crown", 500}})
        law_vote(court, "ash", "aye")
        local l0, d0 = court.houses.legion.loyalty, court.houses.ledger.loyalty
        assert(IC.law_settle(F, "labour", true), "the law did not pass")
        assert(court.houses.legion.loyalty == l0 + IC.TUNE.law_pass_gain, "the Legion moved "
            .. (court.houses.legion.loyalty - l0))
        assert(court.houses.ledger.loyalty == d0 + IC.TUNE.law_pass_loss, "the Ledger moved "
            .. (court.houses.ledger.loyalty - d0))
        gov_done()
    end)

    check("culture laws: the Crown's swing is the law's own, whichever way its men voted", function()
        -- The Crown is against Open Roads (tribute.roads) and its man votes aye: the
        -- house still pays, because its men speak for the player and not for it.
        local court = law_court({{"crown", 500}, {"road", 100}}, {crown = 10, road = 10})
        court.votes.tribute = {option = "roads", proposer = IC.CROWN, ends = turn,
                               stance = "aye", won = {}, push = {}}
        local c0, r0 = court.houses.crown.loyalty, court.houses.road.loyalty
        assert(IC.law_settle(F, "tribute", true), "Open Roads did not pass")
        assert(court.houses.crown.loyalty == c0 + IC.TUNE.law_pass_loss, "the Crown moved "
            .. (court.houses.crown.loyalty - c0))
        assert(court.houses.road.loyalty == r0 + IC.TUNE.law_pass_gain, "the Roads party moved "
            .. (court.houses.road.loyalty - r0))
        gov_done()
    end)
end

```

- [ ] **Step 3: Run the harness and confirm the seven fail**

```powershell
$env:IC_TEST_ALL = "1"; & "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua 2> harness_fail.txt; Remove-Item Env:IC_TEST_ALL
Get-Content harness_fail.txt
```

Expected: `7 failing`, and exactly these `culture laws:` checks, nothing else:

- every stance names a culture of its race and an option, on one side only (`chd wastes is for 0 and against 0`)
- a man votes his culture's side, and a culture with no stance leaves him with his party
- a culture stance beats the loyalty rule for a party with no stance
- a push multiplies the men on their party's line and not the man whose culture votes against it
- the vote panel shows the push only on the block that carries it
- a man's price is doubled by his own stance, and a man his culture sides with you cannot be won
- a passed law moves a party by how its men voted, rounding the half away from zero

The other four `culture laws:` checks pass at once, as the Step 2 note says. If your run shows a different count, read the failing line before going on.

- [ ] **Step 4: Add the option rows**

The rows are the two tables of spec 7.1, written as `cpro` and `ccon` beside each option's `pro` and `con`. Chaos Dwarf, in `zzz_derpy_iron_court.lua`:

Replace:

```lua
        measure = {icon = "chd_workload.png"},
        lash    = {icon = "dlc23_region_action_set_example.png", pro = {"chain"}, con = {"hearth"}},
        kept    = {icon = "slaves.png", pro = {"hearth"}, con = {"chain"}},
        quota   = {icon = "wh3_dlc23_edict_chd_higher_quotas.png", pro = {"forge"}, con = {"hearth"}},
        ash     = {icon = "wh3_dlc23_edict_chd_smoke_stacks.png", pro = {"legion"}, con = {"ledger"}},
```

with:

```lua
        measure = {icon = "chd_workload.png"},
        lash    = {icon = "dlc23_region_action_set_example.png", pro = {"chain"}, con = {"hearth"},
                   cpro = {"gorgoth"}, ccon = {"plain"}},
        kept    = {icon = "slaves.png", pro = {"hearth"}, con = {"chain"},
                   cpro = {"mines"}, ccon = {"zharr", "gorgoth"}},
        quota   = {icon = "wh3_dlc23_edict_chd_higher_quotas.png", pro = {"forge"}, con = {"hearth"},
                   cpro = {"stump"}, ccon = {"zharr"}},
        ash     = {icon = "wh3_dlc23_edict_chd_smoke_stacks.png", pro = {"legion"}, con = {"ledger"},
                   cpro = {"gash"}, ccon = {"mines"}},
```

Replace:

```lua
        tithe   = {icon = "edict_collect_tribute.png"},
        roads   = {icon = "convoy_icon.png", pro = {"road"}, con = {"crown"}},
        tariff  = {icon = "trade_agreement.png", pro = {"ledger"}, con = {"road"}},
        mines   = {icon = "chd_raw_materials.png", pro = {"forge"}, con = {"road"}},
        charter = {icon = "wh3_dlc23_edict_chd_architects.png", pro = {"road"}, con = {"legion"}},
```

with:

```lua
        tithe   = {icon = "edict_collect_tribute.png"},
        roads   = {icon = "convoy_icon.png", pro = {"road"}, con = {"crown"},
                   cpro = {"gorgoth", "wastes"}, ccon = {"gash"}},
        tariff  = {icon = "trade_agreement.png", pro = {"ledger"}, con = {"road"},
                   cpro = {"wastes"}, ccon = {"zornuzkul"}},
        mines   = {icon = "chd_raw_materials.png", pro = {"forge"}, con = {"road"},
                   cpro = {"mines"}, ccon = {"wastes"}},
        charter = {icon = "wh3_dlc23_edict_chd_architects.png", pro = {"road"}, con = {"legion"},
                   cpro = {"plain"}},
```

Replace:

```lua
        rites   = {icon = "chd_conclave_influence.png"},
        fires   = {icon = "wh3_dlc23_unit_passive_burning_bright.png", pro = {"temple"}, con = {"tower"}},
        seats   = {icon = "chd_toz_tier.png", pro = {"tower"}, con = {"temple"}},
        lore    = {icon = "loremaster.png", pro = {"tower"}, con = {"hearth"}},
        licence = {icon = "hellforged.png", pro = {"forge"}, con = {"temple"}},
```

with:

```lua
        rites   = {icon = "chd_conclave_influence.png"},
        fires   = {icon = "wh3_dlc23_unit_passive_burning_bright.png", pro = {"temple"}, con = {"tower"},
                   cpro = {"zharr"}, ccon = {"stump"}},
        seats   = {icon = "chd_toz_tier.png", pro = {"tower"}, con = {"temple"},
                   cpro = {"plain"}, ccon = {"zornuzkul"}},
        lore    = {icon = "loremaster.png", pro = {"tower"}, con = {"hearth"},
                   cpro = {"zharr"}},
        licence = {icon = "hellforged.png", pro = {"forge"}, con = {"temple"}},
```

Replace:

```lua
        levy      = {icon = "edict_levy_conscripts.png"},
        hellforge = {icon = "chd_armaments.png", pro = {"forge"}, con = {"legion"}},
        legions   = {icon = "chd_toz_district_t3_military.png", pro = {"legion"}, con = {"forge"}},
        grudge    = {icon = "wh3_dlc23_unit_passive_oath_of_contempt.png", pro = {"legion"}, con = {"ledger"}},
        gunnery   = {icon = "artillery.png", pro = {"forge"}, con = {"hearth"}},
```

with:

```lua
        levy      = {icon = "edict_levy_conscripts.png"},
        hellforge = {icon = "chd_armaments.png", pro = {"forge"}, con = {"legion"},
                     cpro = {"stump"}},
        legions   = {icon = "chd_toz_district_t3_military.png", pro = {"legion"}, con = {"forge"},
                     cpro = {"zornuzkul"}},
        grudge    = {icon = "wh3_dlc23_unit_passive_oath_of_contempt.png", pro = {"legion"}, con = {"ledger"},
                     cpro = {"zornuzkul", "gash"}},
        gunnery   = {icon = "artillery.png", pro = {"forge"}, con = {"hearth"}},
```

Dwarf, in `zzz_derpy_iron_court_dwarf.lua`:

Replace:

```lua
        measure = {icon = "angrund_ancestors.png"},
        lash    = {icon = "resource_gold.png", pro = {"chain"}, con = {"hearth"}},
        kept    = {icon = "growth.png", pro = {"hearth"}, con = {"chain"}},
        quota   = {icon = "oathgold.png", pro = {"forge"}, con = {"hearth"}},
        ash     = {icon = "construction.png", pro = {"legion"}, con = {"ledger"}},
```

with:

```lua
        measure = {icon = "angrund_ancestors.png"},
        lash    = {icon = "resource_gold.png", pro = {"chain"}, con = {"hearth"},
                   cpro = {"deeps"}, ccon = {"grey"}},
        kept    = {icon = "growth.png", pro = {"hearth"}, con = {"chain"},
                   cpro = {"grey"}, ccon = {"deeps"}},
        quota   = {icon = "oathgold.png", pro = {"forge"}, con = {"hearth"},
                   cpro = {"azul"}, ccon = {"black"}},
        ash     = {icon = "construction.png", pro = {"legion"}, con = {"ledger"}},
```

Replace:

```lua
        tithe   = {icon = "edict_collect_tribute.png"},
        roads   = {icon = "icon_underway_network.png", pro = {"road"}, con = {"crown"}},
        tariff  = {icon = "trade_agreement.png", pro = {"ledger"}, con = {"road"}},
        mines   = {icon = "oathgold_bundle.png", pro = {"forge"}, con = {"road"}},
        charter = {icon = "resource_gemstones.png", pro = {"road"}, con = {"legion"}},
```

with:

```lua
        tithe   = {icon = "edict_collect_tribute.png"},
        roads   = {icon = "icon_underway_network.png", pro = {"road"}, con = {"crown"},
                   cpro = {"barakvarr", "passkeeps"}},
        tariff  = {icon = "trade_agreement.png", pro = {"ledger"}, con = {"road"},
                   ccon = {"kadrin"}},
        mines   = {icon = "oathgold_bundle.png", pro = {"forge"}, con = {"road"},
                   cpro = {"deeps"}, ccon = {"barakvarr", "passkeeps"}},
        charter = {icon = "resource_gemstones.png", pro = {"road"}, con = {"legion"},
                   cpro = {"karaz", "barakvarr"}},
```

Replace:

```lua
        rites   = {icon = "edict_venerate_the_ancestors.png"},
        fires   = {icon = "god_effect_valaya.png", pro = {"temple"}, con = {"tower"}},
        seats   = {icon = "runesmith.png", pro = {"tower"}, con = {"temple"}},
        lore    = {icon = "loremaster.png", pro = {"tower"}, con = {"hearth"}},
        licence = {icon = "god_effect_grungni.png", pro = {"forge"}, con = {"temple"}},
```

with:

```lua
        rites   = {icon = "edict_venerate_the_ancestors.png"},
        fires   = {icon = "god_effect_valaya.png", pro = {"temple"}, con = {"tower"},
                   cpro = {"karaz"}},
        seats   = {icon = "runesmith.png", pro = {"tower"}, con = {"temple"},
                   cpro = {"azul"}},
        lore    = {icon = "loremaster.png", pro = {"tower"}, con = {"hearth"}},
        licence = {icon = "god_effect_grungni.png", pro = {"forge"}, con = {"temple"}},
```

Replace:

```lua
        levy      = {icon = "edict_levy_conscripts.png"},
        grudge    = {icon = "grudges.png", pro = {"legion"}, con = {"ledger"}},
        hellforge = {icon = "artillery.png", pro = {"forge"}, con = {"legion"}},
        legions   = {icon = "waaagh_reward_dwarfs.png", pro = {"legion"}, con = {"forge"}},
        gunnery   = {icon = "engineer.png", pro = {"forge"}, con = {"hearth"}},
```

with:

```lua
        levy      = {icon = "edict_levy_conscripts.png"},
        grudge    = {icon = "grudges.png", pro = {"legion"}, con = {"ledger"},
                     cpro = {"kadrin"}},
        hellforge = {icon = "artillery.png", pro = {"forge"}, con = {"legion"},
                     cpro = {"black"}},
        legions   = {icon = "waaagh_reward_dwarfs.png", pro = {"legion"}, con = {"forge"},
                     cpro = {"kadrin", "grey", "passkeeps"}},
        gunnery   = {icon = "engineer.png", pro = {"forge"}, con = {"hearth"},
                     cpro = {"black"}, ccon = {"karaz", "azul"}},
```

- [ ] **Step 5: Add the logic**

All in `zzz_derpy_iron_court.lua`. Do the edits in this order; each is a replacement of the exact text shown.

Add the two stance readers after `IC.law_stance`:

```lua
function IC.law_stance(category, option, party, faction_key)
    local o = IC.law_opt(category, option, faction_key)
    for _, p in ipairs(o and o.pro or {}) do if p == party then return "aye" end end
    for _, p in ipairs(o and o.con or {}) do if p == party then return "nay" end end
    return nil
end
```

```lua
function IC.law_stance(category, option, party, faction_key)
    local o = IC.law_opt(category, option, faction_key)
    for _, p in ipairs(o and o.pro or {}) do if p == party then return "aye" end end
    for _, p in ipairs(o and o.con or {}) do if p == party then return "nay" end end
    return nil
end

-- WHAT A CULTURE WANTS: "aye" for an option it is for, "nay" for one it is
-- against, nil for neither. The lists are cpro and ccon on the option's row,
-- beside the parties' pro and con.
function IC.culture_stance(category, option, culture, faction_key)
    local o = IC.law_opt(category, option, faction_key)
    for _, c in ipairs(o and o.cpro or {}) do if c == culture then return "aye" end end
    for _, c in ipairs(o and o.ccon or {}) do if c == culture then return "nay" end end
    return nil
end

-- A MAN'S OWN STANCE: his culture's where it has one, his party's otherwise.
function IC.man_stance(category, option, party, culture, faction_key)
    return IC.culture_stance(category, option, culture, faction_key)
        or IC.law_stance(category, option, party, faction_key)
end
```

`law_voters` carries each man's culture:

```lua
                local party = IC.house_of_character(man, faction_key)
                if n > 0 and party then out[#out + 1] = {cqi = cqi, party = party, n = n} end
```

```lua
                local party = IC.house_of_character(man, faction_key)
                if n > 0 and party then
                    -- ANOTHER RACE'S CULTURE IS NO CULTURE OF THIS COURT.
                    local culture, race = IC.culture_of_character(man)
                    if race ~= IC.R(faction_key) then culture = nil end
                    out[#out + 1] = {cqi = cqi, party = party, n = n, culture = culture}
                end
```

`law_line` takes the culture:

```lua
-- HIS PARTY'S LINE: the side its men vote, or nil, and why.
function IC.law_line(faction_key, vote, category, party)
    if party == IC.CROWN then
        if vote.stance == "abstain" then return nil, "crown" end
        return vote.stance, "crown"
    end
    local s = IC.law_stance(category, vote.option, party, faction_key)
```

```lua
-- HIS LINE: the side a man of `party` votes, or nil, and why. With a `culture`
-- that has a stance on the option it is his culture's side, otherwise his
-- party's. Asked with no culture it is the party's own line.
function IC.law_line(faction_key, vote, category, party, culture)
    if party == IC.CROWN then
        if vote.stance == "abstain" then return nil, "crown" end
        return vote.stance, "crown"
    end
    local s = IC.man_stance(category, vote.option, party, culture, faction_key)
```

The tally reads each man's own line and multiplies only the men on their party's line:

```lua
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
```

```lua
-- THE TALLY. A man won votes his won side at his own influence. A man votes his
-- culture's side where it has one and his party's otherwise, and is multiplied by
-- his party's push level only when he is on his party's own line: a man whose
-- culture sends him the other way is not carried along by a push he is against.
-- Each man carries `level`, the push that multiplied him, for the vote panel.
function IC.law_tally(faction_key, category, vote)
    vote = vote or (IC.court(faction_key).votes or {})[category]
    local t = {aye = 0, nay = 0, abstain = 0, men = {}}
    if not vote then return t end
    local party_side, lines = {}, {}
    for _, m in ipairs(IC.law_voters(faction_key)) do
        if party_side[m.party] == nil then
            party_side[m.party] = IC.law_line(faction_key, vote, category, m.party) or false
        end
        local key = m.party .. "|" .. (m.culture or "")
        if not lines[key] then
            lines[key] = {IC.law_line(faction_key, vote, category, m.party, m.culture)}
        end
        local side, why = lines[key][1], lines[key][2]
        local w, level = m.n, nil
        local won = vote.won and vote.won[m.cqi]
        if won then
            side, why = won, "won"
        elseif side and side == party_side[m.party] then
            level = (vote.push or {})[m.party]
            w = math.floor(m.n * IC.law_mult(level) / 100)
        end
        t.men[#t.men + 1] = {cqi = m.cqi, party = m.party, n = m.n, side = side, why = why, w = w,
                             level = level, culture = m.culture}
        if side then t[side] = t[side] + w else t.abstain = t.abstain + m.n end
    end
    return t
end
```

A price follows the man's own stance:

```lua
    local s = IC.law_stance(category, vote.option, man.party, faction_key)
    if s and s ~= vote.stance then price = price * 2 end
```

```lua
    local s = IC.man_stance(category, vote.option, man.party, man.culture, faction_key)
    if s and s ~= vote.stance then price = price * 2 end
```

A passed law moves each party by how its men voted:

```lua
-- THE END OF A VOTE, by tally or by overrule.
function IC.law_settle(faction_key, category, passed)
```

```lua
-- A PARTY'S SWING ON A PASSED LAW: the step times how united its men voted,
-- (aye influence minus nay influence) over the influence of the men who voted.
-- All on one side is the whole step, a split party moves less, and the half
-- rounds away from zero. `flat` is the whole step for the side the law's own
-- list puts the party on. The Crown keeps it too: its men vote as the player
-- chooses, so how they voted says nothing of where the Crown house stands, and
-- passing Open Roads over its objection costs it whichever way they voted.
-- So does a party none of whose men voted.
function IC.law_swing(tally, slug, flat)
    if slug == IC.CROWN then return flat end
    local aye, nay = 0, 0
    for _, m in ipairs(tally.men) do
        if m.party == slug then
            if m.side == "aye" then aye = aye + m.n elseif m.side == "nay" then nay = nay + m.n end
        end
    end
    if aye + nay == 0 then return flat end
    local share = (aye - nay) / (aye + nay)
    local step = share >= 0 and IC.TUNE.law_pass_gain or -IC.TUNE.law_pass_loss
    local size = math.floor(math.abs(share) * step + 0.5)
    return share < 0 and -size or size
end

-- THE END OF A VOTE, by tally or by overrule.
function IC.law_settle(faction_key, category, passed)
```

```lua
        local o = IC.law_opt(category, vote.option, faction_key) or {}
        for _, slug in ipairs(o.pro or {}) do
            if court.houses[slug] then IC.move_loyalty(faction_key, slug, IC.TUNE.law_pass_gain) end
        end
        for _, slug in ipairs(o.con or {}) do
            if court.houses[slug] then IC.move_loyalty(faction_key, slug, IC.TUNE.law_pass_loss) end
        end
```

```lua
        local o = IC.law_opt(category, vote.option, faction_key) or {}
        local tally = IC.law_tally(faction_key, category, vote)
        for _, slug in ipairs(o.pro or {}) do
            if court.houses[slug] then
                IC.move_loyalty(faction_key, slug, IC.law_swing(tally, slug, IC.TUNE.law_pass_gain))
            end
        end
        for _, slug in ipairs(o.con or {}) do
            if court.houses[slug] then
                IC.move_loyalty(faction_key, slug, IC.law_swing(tally, slug, IC.TUNE.law_pass_loss))
            end
        end
```

- [ ] **Step 6: Make the vote panel read the push each block carries**

In `zzz_derpy_iron_court_ui.lua`:

Replace:

```lua
            g = {party = m.party, side = side, w = 0, n = 0, won = m.why == "won", men = {}}
```

with:

```lua
            g = {party = m.party, side = side, w = 0, n = 0, won = m.why == "won", men = {},
                 level = m.level or 0}
```

Replace:

```lua
    local level = g.won and 0 or ((vote.push or {})[g.party] or 0)
```

with:

```lua
    -- THE PUSH IS WHAT HIS MEN WERE MULTIPLIED BY: a block of men whose culture
    -- votes against their party wears none, though the party pushed.
    local level = g.won and 0 or g.level
```

- [ ] **Step 7: Run the harness**

```powershell
& "C:\Program Files (x86)\Lua\5.1\luac.exe" -p "Modding Files\pack\script\campaign\mod\zzz_derpy_iron_court.lua"
& "C:\Program Files (x86)\Lua\5.1\luac.exe" -p "Modding Files\pack\script\campaign\mod\zzz_derpy_iron_court_dwarf.lua"
& "C:\Program Files (x86)\Lua\5.1\luac.exe" -p "Modding Files\pack\script\campaign\mod\zzz_derpy_iron_court_ui.lua"
& "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua
```

Expected: three clean `luac -p`, then `iron court harness: ok (1137 checks)`. One older check that this task touches by design is `laws: a passed law pays its party, then angers the one against, in that order`; it stays green because a fixture with only a Crown man leaves every other party with no voting man, which keeps the flat step. If it fails with `road:5 crown:5`, the Crown line in `IC.law_swing` is missing.

- [ ] **Step 8: Add the generator's mirror and its check**

In `tools/gen_iron_court.py`:

The mirror, after `DWF_CULTURES`:

```python
     "boons": [(E_C_MOVE, 10), (E_C_AMBUSH, 10)], "drawback": (E_C_GDP, 8)},
]

# A BOON IS 150% OF ITS AWAY FIGURE AT HOME, rounded to the nearest whole number
```

```python
     "boons": [(E_C_MOVE, 10), (E_C_AMBUSH, 10)], "drawback": (E_C_GDP, 8)},
]

# THE CULTURES' STANCES ON THE LAWS (spec 7.1): culture -> (options it is for,
# options it is against), each "category.option". The Lua carries them as cpro
# and ccon on the option's row, beside the parties' pro and con;
# check_culture_laws() holds the two together.
CULTURE_STANCES = {
    "chd": {
        "zharr":     (["worship.fires", "worship.lore"], ["labour.quota", "labour.kept"]),
        "stump":     (["labour.quota", "war.hellforge"], ["worship.fires"]),
        "gorgoth":   (["labour.lash", "tribute.roads"], ["labour.kept"]),
        "zornuzkul": (["war.legions", "war.grudge"], ["tribute.tariff", "worship.seats"]),
        "plain":     (["worship.seats", "tribute.charter"], ["labour.lash"]),
        "mines":     (["tribute.mines", "labour.kept"], ["labour.ash"]),
        "wastes":    (["tribute.roads", "tribute.tariff"], ["tribute.mines"]),
        "gash":      (["labour.ash", "war.grudge"], ["tribute.roads"]),
    },
    "dwf": {
        "karaz":     (["worship.fires", "tribute.charter"], ["war.gunnery"]),
        "black":     (["war.hellforge", "war.gunnery"], ["labour.quota"]),
        "barakvarr": (["tribute.roads", "tribute.charter"], ["tribute.mines"]),
        "kadrin":    (["war.grudge", "war.legions"], ["tribute.tariff"]),
        "azul":      (["worship.seats", "labour.quota"], ["war.gunnery"]),
        "deeps":     (["labour.lash", "tribute.mines"], ["labour.kept"]),
        "grey":      (["labour.kept", "war.legions"], ["labour.lash"]),
        "passkeeps": (["tribute.roads", "war.legions"], ["tribute.mines"]),
    },
}

# A BOON IS 150% OF ITS AWAY FIGURE AT HOME, rounded to the nearest whole number
```

The reader and the check, before `check_party_drawn`:

```python
def check_party_drawn(prefix="IC"):
    """Every party <prefix>.DEEDS can name has a party_drawn line."""
```

```python
def _law_rows(body):
    """{option: the text inside its row's braces} for every `name = {icon = ...}`
    row of an opts body. A row may run to a second line, so the end is found by
    counting braces and not by the end of the line."""
    out = {}
    for m in re.finditer(r"(\w+)\s*=\s*\{(?=icon = )", body):
        depth, i = 1, m.end()
        while depth:
            depth += (body[i] == "{") - (body[i] == "}")
            i += 1
        out[m.group(1)] = body[m.end():i - 1]
    return out


def model_law_cultures(prefix="IC"):
    """{(category, option): {"cpro": [culture, ...], "ccon": [...]}} read from
    <prefix>.LAWS, for the options that carry a stance. Raises rather than
    returning nothing: an empty answer is a check that passes over a table it
    cannot read."""
    body = lua_table("LAWS", prefix)
    if body is None:
        raise RuntimeError("the model Lua declares no %s.LAWS" % prefix)
    out = {}
    for cm in re.finditer(r"\n    (\w+) = \{icon = \"[^\"]+\",\s*\n\s*order = \{[^}]*\},\s*\n\s*opts = \{(.*?)\n    \}\}",
                          body, re.S):
        for opt, row in _law_rows(cm.group(2)).items():
            stance = {}
            for side in ("cpro", "ccon"):
                m = re.search(r"\b%s = \{([^}]*)\}" % side, row)
                if m:
                    stance[side] = re.findall(r'"(\w+)"', m.group(1))
            if stance:
                out[(cm.group(1), opt)] = stance
    if not out:
        raise RuntimeError("%s.LAWS carries no culture stance" % prefix)
    return out


def check_culture_laws(race="chd"):
    """The cultures' law stances: the Lua's rows and CULTURE_STANCES are one list,
    every culture and option named exists, a start option carries none, no culture
    stands on both sides of one option or twice on one side, and every culture is
    for something and against something."""
    out = []
    cultures = set(c["slug"] for c in RACES[race]["CULTURES"])
    options = {}
    for cat, _name, _icon, opts in RACES[race]["LAWS"]:
        for k, opt in enumerate(opts):
            options["%s.%s" % (cat, opt[0])] = k
    stances = CULTURE_STANCES[race]
    if set(stances) != cultures:
        out.append("%s: the stances cover %s and the cultures are %s"
                   % (race, sorted(stances), sorted(cultures)))
    want = {}
    for culture, (pro, con) in sorted(stances.items()):
        if not pro or not con:
            out.append("%s %s is for %d options and against %d" % (race, culture, len(pro), len(con)))
        for side, listed in (("cpro", pro), ("ccon", con)):
            for name in listed:
                if name not in options:
                    out.append("%s %s names %s, which is no option" % (race, culture, name))
                elif options[name] == 0:
                    out.append("%s %s names %s, a category's start option" % (race, culture, name))
                else:
                    cat, opt = name.split(".")
                    want.setdefault((cat, opt), {}).setdefault(side, []).append(culture)
    for (cat, opt), sides in sorted(want.items()):
        for side, listed in sides.items():
            if len(listed) != len(set(listed)):
                out.append("%s %s.%s lists a culture twice in %s" % (race, cat, opt, side))
        both = set(sides.get("cpro", [])) & set(sides.get("ccon", []))
        if both:
            out.append("%s %s.%s: %s is both for and against it" % (race, cat, opt, sorted(both)))
    have = model_law_cultures(RACES[race]["prefix"])
    for key in sorted(set(want) | set(have)):
        for side in ("cpro", "ccon"):
            mine, theirs = sorted(want.get(key, {}).get(side, [])), sorted(have.get(key, {}).get(side, []))
            if mine != theirs:
                out.append("%s %s.%s %s: the generator has %s, the Lua %s"
                           % (race, key[0], key[1], side, mine, theirs))
    return out


def check_party_drawn(prefix="IC"):
    """Every party <prefix>.DEEDS can name has a party_drawn line."""
```

Called from `check()`:

```python
    out.extend(check_cultures("chd"))
    out.extend(check_cultures("dwf"))
```

```python
    out.extend(check_cultures("chd"))
    out.extend(check_cultures("dwf"))
    out.extend(check_culture_laws("chd"))
    out.extend(check_culture_laws("dwf"))
```

And proved to fail in the selftest, after the culture seam:

```python
    assert check_cultures("chd") == [], "the planted faults were not restored"
```

```python
    assert check_cultures("chd") == [], "the planted faults were not restored"
    # THE LAW STANCES. Both races agree with the Lua, and the check is shown to
    # fail on a planted fault: a culture on both sides of one option, an option
    # that does not exist, and a stance the Lua carries and the mirror lacks.
    assert check_culture_laws("chd") == [], check_culture_laws("chd")
    assert check_culture_laws("dwf") == [], check_culture_laws("dwf")
    _stump = CULTURE_STANCES["chd"]["stump"]
    try:
        CULTURE_STANCES["chd"]["stump"] = (_stump[0], _stump[1] + ["labour.quota"])
        assert any("both for and against" in p for p in check_culture_laws("chd")), \
            "a culture for and against one option was not reported"
        CULTURE_STANCES["chd"]["stump"] = (_stump[0] + ["labour.nonesuch"], _stump[1])
        assert any("labour.nonesuch" in p for p in check_culture_laws("chd")), \
            "an option that does not exist was not reported"
        CULTURE_STANCES["chd"]["stump"] = (["war.hellforge"], _stump[1])
        assert any("labour.quota" in p and "the Lua" in p for p in check_culture_laws("chd")), \
            "a stance the Lua carries and the generator lacks was not reported"
    finally:
        CULTURE_STANCES["chd"]["stump"] = _stump
    assert check_culture_laws("chd") == [], "the planted law faults were not restored"
```

Then:

```powershell
py tools\gen_iron_court.py --check
py tools\gen_iron_court.py --selftest
```

Expected: `ok: 180 bundles, 314 junctions, 297 traits, 2253 loc rows` after the ten `NOTE` lines from Task 3, and `selftest: ok (180 bundles, 314 junctions, 297 traits, 2253 loc)` (about four minutes). Neither count moves, because laws add no rows. `check_culture_laws("chd")` and `check_culture_laws("dwf")` both return an empty list.

- [ ] **Step 9: Run the Lua gates**

```powershell
foreach ($f in "zzz_derpy_iron_court","zzz_derpy_iron_court_dwarf","zzz_derpy_iron_court_ui") {
  py tools\check_lua_api.py "Modding Files\pack\script\campaign\mod\$f.lua"
}
py tools\check_lua_undeclared.py
py tools\check_lua_literal_left.py
```

Expected: `0 suspect call(s)` for each file and no findings from the other two. (`check_lua_api.py` with no argument scans every mod in the folder and reports three calls in `ai_test_tower_of_zharr.lua` and `derpy_more_resources_flows.lua`; those are not this work, so name the Iron Court files.)

- [ ] **Step 10: Ledger**

Append: `Task 6 done: zzz_derpy_iron_court.lua, zzz_derpy_iron_court_dwarf.lua, zzz_derpy_iron_court_ui.lua, gen_iron_court.py, _iron_court_harness.lua; harness 1137 checks; gen --check and --selftest, luac, check_lua_api (Iron Court files), check_lua_undeclared, check_lua_literal_left clean.`

---

### Task 7: The governor picker line and the Help page

**Files:**
- Modify: `tools/gen_iron_court.py` (`culture_picker_line` before `RACES`, `emit_cultures`, `check_cultures`, the selftest)
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_ui.lua` (`ICUI.culture_line` after `ICUI.man_line`, `ICUI.picker_lines`, `ICUI.HELP`)
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_ui_map.lua` (`ICUI.gm_picker_rows`)
- Modify: `tools/_iron_court_harness.lua` (one new `do ... end` block of three checks; the preview's demo court in the `IC_DUMP` block)

**Interfaces:**
- Consumes: `culture_effects`, `effect_line`, `CULTURE_FRICTION`, `emit_cultures`, `check_cultures` (Task 3); `IC.culture_of_character` (Task 1); `IC.culture_case` (Task 1); `IC.key`, `IC.R`.
- Produces:
  - Three loc rows a culture, `derpy_ic_cult_gov_<slug>`, `derpy_ic_cult_gov_home_<slug>` and `derpy_ic_cult_gov_foreign_<slug>` (with the `dwf_` infix for a Dwarf culture): 48 more rows, `2301 loc rows` in all.
  - `culture_picker_line(c, case)` in the generator, and `check_cultures` holds every line to the bundle it stands for.
  - `ICUI.culture_line(faction, character, province_key) -> string | nil`.
  - Governor picker lines (`ICUI.picker_lines`) carry `culture`, which the Governors column's card tooltip prints.

The spec (section 9) asks for three touch points. The first, the culture trait on the character panel with the figures in it, was built in Task 3: the trait's explanation text is made from the same rows as the bundle. This task does the other two. The picker line goes in the card's tooltip and not in a cell (departure 9): the cells are fixed width and fit-checked, and a tooltip is not. The Help page has a tighter limit than the spec assumes: a line must measure inside 1244 px at 1600, and `gen_ic_ui.py --check` fails a longer one, so the Laws sentence is a line of its own and the Governors sentence is short.

- [ ] **Step 1: Write the failing checks**

Add this block to `tools/_iron_court_harness.lua` immediately above the final `check("no engine setter was ever handed anything but a boolean", ...)`.

```lua
-- CULTURES, task 7: the governor picker names a man's culture, and the Help page says so.
do
    local FOUNDRY = "cr_oldworld_province_foundry_district"
    local PITS = "cr_oldworld_province_pits_district"

    -- THE PICKER LINE OF ONE CANDIDATE for a governor pick on `province`.
    local function picker_line(cqi, province)
        ICUI.pick = {kind = "gov", key = province}
        local lines = ICUI.picker_lines(F, IC.court(F))
        ICUI.pick = nil
        for _, line in ipairs(lines) do
            if line.sort.cqi == cqi then return line end
        end
        return nil
    end

    check("culture picker: a candidate's line speaks for home, a foreign province and any other", function()
        IC.state = {}
        local men = {make_character(3601, ANY_SEAT, "legion", nil, nil, nil, nil, "stump")}
        make_faction(F, IC.CHD_SUBCULTURE, men, {FOUNDRY, PITS, "prov_x"})
        IC.add_house(F, IC.CROWN)
        IC.add_house(F, "legion")
        local seeded = IC_TEST_LOC
        IC_TEST_LOC = {derpy_ic_cult_gov_stump = "AWAY LINE", derpy_ic_cult_gov_home_stump = "HOME LINE",
                       derpy_ic_cult_gov_foreign_stump = "FOREIGN LINE"}
        local ok, err = pcall(function()
            assert(picker_line(3601, FOUNDRY).culture == "HOME LINE", "the Foundry Districts are his home")
            assert(picker_line(3601, PITS).culture == "FOREIGN LINE", "the Gorgoth Pits are another culture's home")
            assert(picker_line(3601, "prov_x").culture == "AWAY LINE", "a province on no list is away")
            -- AND THE COLUMN'S CARD CARRIES IT in its tooltip, between the refusal and the influence.
            ICUI.pick = {kind = "gov", key = FOUNDRY}
            local rows = ICUI.gm_picker_rows(F)
            ICUI.pick = nil
            assert(#rows == 1 and string.find(rows[1].tip, "HOME LINE", 1, true),
                "the card's tooltip hides the culture line: " .. tostring(rows[1] and rows[1].tip))
        end)
        IC_TEST_LOC = seeded
        ICUI.pick = nil
        assert(ok, err)
    end)

    check("culture picker: no culture, or another race's, gives no line, and the Dwarf court reads its own keys", function()
        IC.state = {}
        local DF = "wh_main_dwf_dwarfs"
        local plain = make_character(3602, ANY_SEAT, "legion")
        local foreign = make_character(3603, ANY_SEAT, "legion", nil, nil, nil, nil, "dwf_deeps")
        make_faction(F, IC.CHD_SUBCULTURE, {plain, foreign}, {FOUNDRY})
        IC.add_house(F, IC.CROWN)
        IC.add_house(F, "legion")
        local seeded = IC_TEST_LOC
        IC_TEST_LOC = {derpy_ic_cult_gov_home_dwf_kadrin = "DWARF HOME LINE",
                       derpy_ic_cult_gov_dwf_kadrin = "DWARF AWAY LINE",
                       derpy_ic_cult_gov_deeps = "WRONG RACE LINE", derpy_ic_cult_gov_home_deeps = "WRONG RACE LINE",
                       derpy_ic_cult_gov_foreign_deeps = "WRONG RACE LINE"}
        local ok, err = pcall(function()
            assert(picker_line(3602, FOUNDRY).culture == nil, "a man with no culture got a line")
            assert(picker_line(3603, FOUNDRY).culture == nil, "a Dwarf culture got a line in a Chaos Dwarf court")
            local kadrin = make_character(3604, ANY_SEAT, nil, nil, nil, nil, nil, "dwf_kadrin")
            make_faction(DF, IC.RACES.dwf.subculture, {kadrin}, {})
            assert(ICUI.culture_line(DF, kadrin, "cr_oldworld_province_peak_pass") == "DWARF HOME LINE",
                "the Dwarf court did not read its own home line")
            assert(ICUI.culture_line(DF, kadrin, FOUNDRY) == "DWARF AWAY LINE",
                "a Chaos Dwarf home was read as a Dwarf one")
        end)
        IC_TEST_LOC = seeded
        ICUI.pick = nil
        assert(ok, err)
    end)

    check("culture help: the retired party claim is gone and the court, governors and laws pages name the culture", function()
        local want = {["The court"] = true, Governors = true, Laws = true}
        for _, topic in ipairs(ICUI.HELP) do
            for _, line in ipairs(topic.lines) do
                assert(not string.find(line, "party adds its own bonus", 1, true),
                    topic.title .. " still says a party gives a governor a bonus")
            end
            if want[topic.title] then
                local hit = false
                for _, line in ipairs(topic.lines) do
                    if string.find(line, "culture", 1, true) then hit = true end
                end
                assert(hit, topic.title .. " says nothing of culture")
                want[topic.title] = nil
            end
        end
        assert(next(want) == nil, "no help topic is called " .. tostring(next(want)))
    end)
end

```

- [ ] **Step 2: Run the harness and confirm the three fail**

```powershell
$env:IC_TEST_ALL = "1"; & "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua 2> harness_fail.txt; Remove-Item Env:IC_TEST_ALL
Get-Content harness_fail.txt
```

Expected: `3 failing`, all three `culture picker:` or `culture help:` checks, the first with `the Foundry Districts are his home`, the second with `attempt to call field 'culture_line' (a nil value)`, the third with `The court says nothing of culture`.

- [ ] **Step 3: Add the generator's picker lines**

In `tools/gen_iron_court.py`:

Replace:

```python
# THE RACES. `prefix` is the Lua table prefix the race's tables are declared
# under; LUA_OF_PREFIX names the file.
RACES = {
```

with:

```python
def culture_picker_line(c, case):
    """The governor picker's tooltip line for a culture in a province of `case`
    ("away", "home" or "foreign"). Built from the rows culture_effects hands
    emit(), so its figures are the bundle's: CA's wording of every effect, the
    drawback last, and for a foreign province the friction on top."""
    away, home = culture_effects(c)
    rows = home if case == "home" else away
    boons = ", ".join(effect_line(e, m, i) for e, m, i in rows[:-1])
    drawback = effect_line(*rows[-1])
    where = {"away": "", "home": ", at home here",
             "foreign": ", in a province another culture calls home"}[case]
    line = "%s%s. Governing: %s. Drawback: %s." % (c["name"], where, boons, drawback)
    if case == "foreign":
        line += " He also loses %d Control." % CULTURE_FRICTION
    return line


# THE RACES. `prefix` is the Lua table prefix the race's tables are declared
# under; LUA_OF_PREFIX names the file.
RACES = {
```

Replace:

```python
        loc.append({"key": K("cult_name", c["slug"]), "text": c["name"], "tooltip": "false"})
```

with:

```python
        loc.append({"key": K("cult_name", c["slug"]), "text": c["name"], "tooltip": "false"})
        for case, kind in (("away", "cult_gov"), ("home", "cult_gov_home"),
                           ("foreign", "cult_gov_foreign")):
            loc.append({"key": K(kind, c["slug"]), "text": culture_picker_line(c, case),
                        "tooltip": "false"})
```

Replace:

```python
        text = loc.get("character_trait_levels_explanation_text_" + trait_key, "")
        for j in away:
            if _quoted_line(j) not in text:
                out.append("trait %s does not quote %r from its bundle" % (trait_key, _quoted_line(j)))
```

with:

```python
        text = loc.get("character_trait_levels_explanation_text_" + trait_key, "")
        for j in away:
            if _quoted_line(j) not in text:
                out.append("trait %s does not quote %r from its bundle" % (trait_key, _quoted_line(j)))
        # THE PICKER'S THREE LINES quote the bundle they stand for: the away line
        # and the foreign line the away bundle, the home line the home bundle, and
        # the foreign line says what the friction costs.
        for kind, rows in (("cult_gov", away), ("cult_gov_home", home), ("cult_gov_foreign", away)):
            lk = bundle_key(kind, slug, race)
            line = loc.get(lk, "")
            if not line:
                out.append("no picker line %s" % lk)
            for j in rows:
                if _quoted_line(j) not in line:
                    out.append("picker line %s does not quote %r from its bundle" % (lk, _quoted_line(j)))
            for w in JARGON:
                if re.search(r"\b%s\b" % w, line):
                    out.append("%s says %r, which the plain-words rule bans" % (lk, w))
        if "loses %d Control" % CULTURE_FRICTION not in loc.get(bundle_key("cult_gov_foreign", slug, race), ""):
            out.append("picker line %s does not say what the friction costs" % bundle_key("cult_gov_foreign", slug, race))
```

Replace:

```python
    finally:
        globals()["culture_explanation"] = _real_ex
    assert check_cultures("chd") == [], "the planted faults were not restored"
```

with:

```python
    finally:
        globals()["culture_explanation"] = _real_ex
    _real_pl = culture_picker_line
    try:
        globals()["culture_picker_line"] = lambda c, case: c["name"]
        _bad = check_cultures("chd")
        assert any("picker line" in p and "does not quote" in p for p in _bad), \
            "a picker line that omits the bundle's figures was not reported"
    finally:
        globals()["culture_picker_line"] = _real_pl
    assert check_cultures("chd") == [], "the planted faults were not restored"
```

- [ ] **Step 4: Add the picker line and the Help text**

In `zzz_derpy_iron_court_ui.lua`:

Replace:

```lua
function ICUI.man_line(character)
    local name = ICUI.character_name(character)
    local bg = ICUI.bg_name(character)
    if not bg then return name end
    return name .. ", " .. bg
end
```

with:

```lua
function ICUI.man_line(character)
    local name = ICUI.character_name(character)
    local bg = ICUI.bg_name(character)
    if not bg then return name end
    return name .. ", " .. bg
end

-- WHAT A GOVERNOR'S CULTURE DOES IN A PROVINCE, in the generator's own words
-- (cult_gov, cult_gov_home, cult_gov_foreign): the culture, whether the province
-- is its home, and the figures. Nil for a man with no culture of this court. The
-- case is the model's (IC.culture_case), so the line cannot say home where the
-- bundle applied is not the home one.
ICUI.CULTURE_CASE_LOC = {away = "cult_gov", home = "cult_gov_home", foreign = "cult_gov_foreign"}
function ICUI.culture_line(faction, character, province_key)
    local culture, race = IC.culture_of_character(character)
    if not culture or race ~= IC.R(faction) then return nil end
    local case = IC.culture_case(faction, culture, province_key)
    local text = loc(IC.key(ICUI.CULTURE_CASE_LOC[case], culture, faction), "")
    return text ~= "" and text or nil
end
```

Replace:

```lua
            plate = cand.slug,
            -- WHAT ICUI.sort_picker ORDERS ON, recorded here because two of the
```

with:

```lua
            plate = cand.slug,
            -- WHAT HIS CULTURE DOES IN THIS PROVINCE, for the Governors column's
            -- tooltip. Only a governor pick has a province to ask about.
            culture = ICUI.pick.kind == "gov"
                      and ICUI.culture_line(faction, cand.character, ICUI.pick.key) or nil,
            -- WHAT ICUI.sort_picker ORDERS ON, recorded here because two of the
```

Replace:

```lua
        "{@party}His party adds its own bonus. The governorship earns party loyalty just as a seat does.",
```

with:

```lua
        "{@party}His culture adds its own bonus, half as strong again at home. Governing another culture's home costs him Control.",
```

Replace:

```lua
        "{@party}Each man's influence counts toward his party's vote. Parties vote for, against, or according to loyalty.",
```

with:

```lua
        "{@party}Each man's influence counts toward his party's vote. Parties vote for, against, or according to loyalty.",
        "{@party}A man whose culture has a view on a law votes it, whatever his party does.",
```

Replace:

```lua
        "{@trait}Rival parties are chosen at random on turn one. Each has a name, two party traits and a leader with his own trait.",
```

with:

```lua
        "{@trait}Rival parties are chosen at random on turn one. Each has a name, two party traits and a leader with his own trait.",
        "{@trait}Every man also has a culture, rolled when he spawns. It feeds his party and decides how he governs.",
```

In `zzz_derpy_iron_court_ui_map.lua`:

Replace:

```lua
        if line.tip then tip[#tip + 1] = line.tip end
        tip[#tip + 1] = string.format("%d influence. Holds: %s.", line.sort.standing, line.holds)
```

with:

```lua
        if line.tip then tip[#tip + 1] = line.tip end
        if line.culture then tip[#tip + 1] = line.culture end
        tip[#tip + 1] = string.format("%d influence. Holds: %s.", line.sort.standing, line.holds)
```

- [ ] **Step 5: Run the checks**

```powershell
& "C:\Program Files (x86)\Lua\5.1\luac.exe" -p "Modding Files\pack\script\campaign\mod\zzz_derpy_iron_court_ui.lua"
& "C:\Program Files (x86)\Lua\5.1\luac.exe" -p "Modding Files\pack\script\campaign\mod\zzz_derpy_iron_court_ui_map.lua"
& "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua
py tools\gen_iron_court.py --check
py tools\gen_iron_court.py --selftest
py tools\gen_ic_ui.py --check
py tools\preview_iron_court.py --check
```

Expected: two clean `luac -p`; `iron court harness: ok (1140 checks)`; `ok: 180 bundles, 314 junctions, 297 traits, 2301 loc rows`; `selftest: ok (180 bundles, 314 junctions, 297 traits, 2301 loc)`; `ok: 30 files, 1906 components` from `gen_ic_ui.py`; `30 file(s) checked by TWUI Studio's reader`. If `gen_ic_ui.py` reports `help line measures ... px in a ... px row`, the line is too long: shorten it, do not widen the row.

- [ ] **Step 6: Give the preview's demo court a split party, render, and look**

The preview draws the vote screen from the harness's demo court (the `IC_DUMP` block near the end of `tools/_iron_court_harness.lua`), which gives no man a culture. That court cannot show what Task 6 changed: a party split by culture, whose dissenters vote against their party and carry no push. One Gash Kadrak man in the Ledger is that case, since his culture is for the Ash Harvest and his party against it. It is not a check and does not change the count. In `tools/_iron_court_harness.lua`:

Replace:

```lua
    -- {party, loyalty, {influence of each man}}
```

with:

```lua
    -- {party, loyalty, {influence of each man}, {[man] = culture}}
```

Replace:

```lua
        {"ledger", 50,  {425, 230, 64}},
```

with:

```lua
        -- A GASH KADRAK MAN IN THE LEDGER: his culture is for the Ash Harvest
        -- and his party against it, so the Ledger draws a block on each side
        -- and only the block on its own line carries the push.
        {"ledger", 50,  {425, 230, 64}, {[1] = "gash"}},
```

Replace:

```lua
        for _, inf in ipairs(d[3]) do
            n = n + 1
            local c = make_character(9500 + n, ANY_SEAT, d[1], nil)
```

with:

```lua
        for i, inf in ipairs(d[3]) do
            n = n + 1
            local c = make_character(9500 + n, ANY_SEAT, d[1], nil, nil, nil, nil, d[4] and d[4][i])
```

```powershell
& "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua
py tools\preview_iron_court.py
```

Expected: `iron court harness: ok (1140 checks)`, then one `wrote ...` line per picture into `.skilltree_cache\ui_preview\`. Open `ic_law_vote.png` with the Read tool. Covenant of the Black Ledger now has a block on each side. On the Enact side it reads `Votes for enacting it`, 425, with no multiplier. On the Keep side it reads `Slightly favours keeping the law in force` with the Ledger's `x1.5`, and 345 (230 x 1.5). Then open `ic_law_board.png` and the `_dwf` and `_1600` copies of both. Look for text off its plate and for a block label that runs past its box. The preview draws no tooltips and no Help page; the in-game checklist in Task 10 covers both. Say so when reporting.

- [ ] **Step 7: Ledger**

Append: `Task 7 done: gen_iron_court.py, zzz_derpy_iron_court_ui.lua, zzz_derpy_iron_court_ui_map.lua, _iron_court_harness.lua; harness 1140 checks; gen --check and --selftest (2301 loc), gen_ic_ui --check, preview --check clean; preview viewed, the split Ledger drawn on both sides.`

---

### Task 8: The importer refuses what the new rules can break

**Files:**
- Modify: `tools/import_iron_court.py` (`ROLLER_GATES` and `check_rollers`, new `check_culture_loc`, `check_trait_keys`, `verify`, `_selftest`)
- Regenerate: `Modding Files/source/iron_court/*.tsv` (written by `py tools\gen_iron_court.py`, never by hand)

**Interfaces:**
- Consumes: the roller functions of Task 4 (`IC.roll_party`, `IC.leaderless_party`, `IC.trade_in`, `IC.roll_culture`) and their callers; `IC.key("cult", ...)`, `IC.rkey("cult", ...)`, `IC.key("gov_cult", ...)`, `IC.key("gov_cult_home", ...)`, `IC.gov_bundle_friction` (Tasks 1 and 5); `ICUI.CULTURE_CASE_LOC` and the three picker loc kinds (Task 7); `G.bundle_key(kind, slug, race)`.
- Produces: `ROLLER_GATES` (roller -> the only functions that may call it), `check_culture_loc(ui, loc_keys) -> [problem]`, and an importer that exits 0 on the finished Lua, generator and TSVs.

`tools/import_iron_court.py` is the gate that refuses to pack. It does not pack: `tools/deploy_iron_court.py` does that in Task 10, and calls this file first. One check in it names functions this work removed, and three rules need a new line of defence.

1. `check_rollers` insists that `IC.roll_origin(` and `IC.roll_background(` are each called from one place. Both functions are gone. The replacement is a table, `ROLLER_GATES`, naming for each random draw the only functions that may reach it. A legend dealt a random culture or trade is silent: he just has the wrong line on his card for the rest of the campaign. `IC.trade_in(` has five callers. `IC.background_for` and `IC.deed_join` ask whether the man is a legend first; the other three deal to a leader the court places, seeds or fields itself. Listing all five means a sixth, new caller fails here until someone has read it.
2. The trait-builder presence check does not know the culture trait, and the literal scan does not look for `derpy_ic_cult_`.
3. The bundle-builder presence check does not know the two culture bundle builders or the friction bundle, which is one fixed slug a race and is tied to its generated row the way the governor's base bundle already is.
4. The picker's three loc kinds are built by concatenation in the UI, so no scan of the Lua can see them. `check_culture_loc` reads `ICUI.CULTURE_CASE_LOC` and demands a shipped line for every culture of both races in every case.

- [ ] **Step 1: Write the TSVs and watch the importer refuse**

```powershell
py tools\gen_iron_court.py
py tools\import_iron_court.py
```

Expected: the first prints `ok: 180 bundles, 314 junctions, 297 traits, 2301 loc rows` (after the ten `NOTE` lines) and then one `wrote ...` line per TSV. The second exits 1 with exactly two lines:

```
REFUSING: IC.roll_origin( is called from nowhere and may only be called from IC.origin_for - every other caller rolls a legendary lord a past he already has
REFUSING: IC.roll_background( is called from nowhere and may only be called from IC.background_for - every other caller rolls a legendary lord a past he already has
```

Those two are the old gates looking for functions that no longer exist. Anything else in the list is a real fault in Tasks 1 to 7: stop and fix it there.

- [ ] **Step 2: Edit the importer**

In `tools/import_iron_court.py`:

Replace:

```python
def check_rollers(src):
    """The rollers may be reached from one place each, and it is the place that
    asks whether the man is a legend first.
```

with:

```python
# WHO MAY DRAW, per roller: the places that have already asked whether the man is
# a legend (IC.fixed_history, IC.fixed_culture), or that deal only to a leader
# the court places, seeds or fields itself.
# IC.fit_culture may draw because it returns early for a man whose culture is
# binding, and a legend's always is. A new caller fails here until somebody has
# read it for that.
ROLLER_GATES = (
    ("IC.roll_party(", ["IC.background_for"]),
    ("IC.leaderless_party(", ["IC.background_for"]),
    ("IC.roll_culture(", ["IC.culture_for", "IC.fit_culture"]),
    ("IC.trade_in(", ["IC.background_for", "IC.deed_join", "IC.ensure_leaders",
                      "IC.field_leader", "IC.seed_step"]),
)


def check_rollers(src):
    """The rollers may be reached from one place each, and it is the place that
    asks whether the man is a legend first.
```

Replace:

```python
    out = []
    for roller, gate in (("IC.roll_origin(", "IC.origin_for"),
                         ("IC.roll_background(", "IC.background_for")):
        callers = sorted(set(_roller_callers(src, roller)))
        if callers != [gate]:
            out.append("%s is called from %s and may only be called from %s - "
                       "every other caller rolls a legendary lord a past he "
                       "already has"
                       % (roller, ", ".join(callers) or "nowhere", gate))
    return out
```

with:

```python
    out = []
    for roller, gates in ROLLER_GATES:
        callers = sorted(set(_roller_callers(src, roller)))
        if callers != sorted(gates):
            out.append("%s is called from %s and may only be called from %s - "
                       "every other caller rolls a legendary lord a past he "
                       "already has"
                       % (roller, ", ".join(callers) or "nowhere", ", ".join(sorted(gates))))
    return out
```

Replace:

```python
def check_character_stub(harness_src, docs=None):
```

with:

```python
def check_culture_loc(ui, loc_keys):
    """The governor picker reads one loc line a culture for each case it names in
    ICUI.CULTURE_CASE_LOC. Each must be a row the generator emits for every culture
    of both races: a line the UI asks for and the pack does not ship is a tooltip
    that quietly says nothing."""
    m = re.search(r"ICUI\.CULTURE_CASE_LOC\s*=\s*\{([^}]*)\}", ui)
    if not m:
        return ["the UI no longer declares ICUI.CULTURE_CASE_LOC"]
    kinds = dict(re.findall(r'(\w+)\s*=\s*"(\w+)"', m.group(1)))
    out = []
    if sorted(kinds) != ["away", "foreign", "home"]:
        out.append("ICUI.CULTURE_CASE_LOC names %s, not away, home and foreign" % sorted(kinds))
    for case, kind in sorted(kinds.items()):
        for race in sorted(G.RACES):
            for c in G.RACES[race]["CULTURES"]:
                key = G.bundle_key(kind, c["slug"], race)
                if key not in loc_keys:
                    out.append("the picker reads %s (%s) and the pack ships no such line" % (key, case))
    return out


def check_character_stub(harness_src, docs=None):
```

Replace:

```python
    # 0e. EVERY EFFECT A BAND CAN SHOW HAS CA's ICON FOR IT. See check_fx_icons.
    if os.path.isfile(UI_LUA):
        problems.extend(check_fx_icons(io.open(UI_LUA, encoding="utf-8").read()))
```

with:

```python
    # 0e. EVERY EFFECT A BAND CAN SHOW HAS CA's ICON FOR IT. See check_fx_icons.
    if os.path.isfile(UI_LUA):
        problems.extend(check_fx_icons(io.open(UI_LUA, encoding="utf-8").read()))

    # 0f. THE PICKER'S CULTURE LINES ARE SHIPPED. See check_culture_loc.
    if os.path.isfile(UI_LUA):
        problems.extend(check_culture_loc(io.open(UI_LUA, encoding="utf-8").read(),
                                          set(r["key"] for r in built["loc"])))
```

Replace:

```python
    for key in sorted(set(re.findall(r'"(derpy_ic_(?:house|title)_\w+)"', lua))):
```

with:

```python
    for key in sorted(set(re.findall(r'"(derpy_ic_(?:house|title|cult)_\w+)"', lua))):
```

Replace:

```python
    for builder in ('IC.rkey("house"', 'IC.rkey("bg"', 'IC.key("title"', 'IC.key("member"'):
```

with:

```python
    for builder in ('IC.rkey("house"', 'IC.rkey("bg"', 'IC.key("title"', 'IC.key("member"',
                    'IC.rkey("cult"', 'IC.key("cult"'):
```

Replace:

```python
        for prefix in ('IC.key("office"', 'IC.key("vacant"', 'IC.key("gov_house"'):
```

with:

```python
        for prefix in ('IC.key("office"', 'IC.key("vacant"', 'IC.key("gov_house"',
                       'IC.key("gov_cult"', 'IC.key("gov_cult_home"'):
```

Replace:

```python
        if G.bundle_key("gov", "base") not in defined:
            problems.append("the generator does not emit the governor's base bundle %s"
                            % G.bundle_key("gov", "base"))
```

with:

```python
        if G.bundle_key("gov", "base") not in defined:
            problems.append("the generator does not emit the governor's base bundle %s"
                            % G.bundle_key("gov", "base"))
        if not re.search(r'^function IC\.gov_bundle_friction\(faction_key\) return '
                         r'IC\.key\("gov", "friction", faction_key\) end$', lua, re.M):
            problems.append("the Lua no longer builds the friction bundle as "
                            'IC.key("gov", "friction", faction_key)')
        for race in sorted(G.RACES):
            friction = G.bundle_key("gov", "friction", race)
            if friction not in defined:
                problems.append("the generator does not emit the %s friction bundle %s"
                                % (race, friction))
```

Replace:

```python
    rollers = ('function IC.origin_for(character, faction_key)\n'
               '    return IC.roll_origin(faction_key)\nend\n'
               'function IC.background_for(character, faction_key, tally)\n'
               '    return IC.roll_background(faction_key, tally)\nend\n')
    assert check_rollers(rollers) == [], check_rollers(rollers)
```

with:

```python
    rollers = ('function IC.background_for(character, faction_key, tally)\n'
               '    local party = IC.leaderless_party(character, faction_key, tally)\n'
               '                  or IC.roll_party(faction_key, tally)\n'
               '    return IC.trade_in(party, faction_key, IC.culture_for(character, faction_key, party))\nend\n'
               'function IC.culture_for(character, faction_key, party)\n'
               '    return IC.roll_culture(faction_key, party)\nend\n'
               'function IC.fit_culture(faction_key, character, party)\n'
               '    return IC.roll_culture(faction_key, party)\nend\n'
               'function IC.deed_join(character, faction_key)\n'
               '    return IC.trade_in("legion", faction_key)\nend\n'
               'function IC.ensure_leaders(faction_key)\n'
               '    return IC.trade_in("legion", faction_key)\nend\n'
               'function IC.field_leader(faction_key, slug)\n'
               '    return IC.trade_in(slug, faction_key)\nend\n'
               'function IC.seed_step(faction_key, i)\n'
               '    return IC.trade_in("legion", faction_key)\nend\n')
    assert check_rollers(rollers) == [], check_rollers(rollers)
    # A STRAY CALLER IS REFUSED, and so is a roller nobody calls any more.
    bad = check_rollers(rollers + 'function IC.stray(f) return IC.trade_in("forge", f) end\n')
    assert len(bad) == 1 and "IC.trade_in(" in bad[0] and "IC.stray" in bad[0], bad
    bad = check_rollers(rollers.replace("IC.leaderless_party(", "IC.other("))
    assert len(bad) == 1 and "IC.leaderless_party(" in bad[0] and "nowhere" in bad[0], bad
```

Replace:

```python
    builders = 'IC.rkey("house", f) IC.rkey("bg", f) IC.key("title", s) IC.key("member", s)\n'
    assert check_trait_keys(builders, {"derpy_ic_house_a"}) == []
    bad = check_trait_keys(builders + 'x = "derpy_ic_house_zz"\n', {"derpy_ic_house_a"})
    assert len(bad) == 1 and "derpy_ic_house_zz" in bad[0], bad
    for gone in ('IC.rkey("house"', 'IC.rkey("bg"', 'IC.key("title"', 'IC.key("member"'):
        bad = check_trait_keys(builders.replace(gone, "IC.other("), set())
        assert len(bad) == 1 and gone in bad[0], (gone, bad)
    print("import_iron_court selftest: ok")
```

with:

```python
    builders = ('IC.rkey("house", f) IC.rkey("bg", f) IC.key("title", s) IC.key("member", s)\n'
                'IC.rkey("cult", s, R) IC.key("cult", s, f)\n')
    assert check_trait_keys(builders, {"derpy_ic_house_a"}) == []
    bad = check_trait_keys(builders + 'x = "derpy_ic_house_zz"\n', {"derpy_ic_house_a"})
    assert len(bad) == 1 and "derpy_ic_house_zz" in bad[0], bad
    bad = check_trait_keys(builders + 'x = "derpy_ic_cult_zz"\n', {"derpy_ic_house_a"})
    assert len(bad) == 1 and "derpy_ic_cult_zz" in bad[0], bad
    for gone in ('IC.rkey("house"', 'IC.rkey("bg"', 'IC.key("title"', 'IC.key("member"',
                 'IC.rkey("cult"', 'IC.key("cult"'):
        bad = check_trait_keys(builders.replace(gone, "IC.other("), set())
        assert len(bad) == 1 and gone in bad[0], (gone, bad)
    ui = ('ICUI.CULTURE_CASE_LOC = {away = "cult_gov", home = "cult_gov_home", '
          'foreign = "cult_gov_foreign"}\n')
    shipped = set(G.bundle_key(k, c["slug"], race) for race in G.RACES
                  for c in G.RACES[race]["CULTURES"]
                  for k in ("cult_gov", "cult_gov_home", "cult_gov_foreign"))
    assert check_culture_loc(ui, shipped) == [], check_culture_loc(ui, shipped)
    bad = check_culture_loc(ui, shipped - {G.bundle_key("cult_gov_home", "karaz", "dwf")})
    assert len(bad) == 1 and "cult_gov_home_dwf_karaz" in bad[0], bad
    assert check_culture_loc("local x = 1", shipped) != []
    print("import_iron_court selftest: ok")
```

- [ ] **Step 3: Run its selftest and the verification**

```powershell
py tools\import_iron_court.py --selftest
py tools\import_iron_court.py
```

Expected: `import_iron_court selftest: ok`, then `verify ok - 180 bundles, 314 junctions, 297 traits, 2301 loc, 7 script(s), 30 ui file(s), 1786 generated png(s)` and the destination list. The selftest plants a stray `IC.trade_in(` caller, a roller nobody calls, a missing culture builder, a hand-written `derpy_ic_cult_` key and a missing picker line, and each must be reported.

- [ ] **Step 4: Ledger**

Append: `Task 8 done: import_iron_court.py, TSVs regenerated; import selftest and verify ok (2301 loc).`

---

### Task 9: Nine anchors move, one mutant retires, forty-four arrive

**Files:**
- Modify: `tools/mutate_iron_court.py` (nine entries of `MUTANTS` repaired in place, one retired, forty-four added at its end)

**Interfaces:**
- Consumes: the `MUTANTS` list of `(name, file, old, new)` entries, where `file` is `M` (the model), `U` (the UI file) or `UM` (the UI map file), and `old` must appear in that file exactly once; the runner's name filter (`py tools\mutate_iron_court.py <substring>`), its `--selftest`, and the code of Tasks 4 to 7.
- Produces: 1267 mutants (the 1224 already there less the one retired, and 44 named `culture: ...`), no stale anchor, and every one of the 44 killed by a named harness check.

The harness is the only tool here with no selftest of its own, and a check nobody has watched fail proves nothing. Tasks 1 to 7 add 47 checks, and Tasks 4 and 6 rewrite or remove code that ten existing mutants were aimed at. A mutant whose anchor no longer matches is a finding, not a skip: the runner reports it exactly like a survivor and exits 1. So this task does three things. It moves nine anchors onto the code that now does the job. It retires `the court's roll asking a card for every origin`, which was aimed at the origin stamp in `IC.stamp_court` that Task 4 deletes as dead code. And it breaks each new rule once, in the way a plausible mistake would, and watches the harness fail.

The 44 mutants are grouped by the rule each attacks, never by the check meant to catch it:

- home, away and foreign (5): swapping the first and last, calling every unlisted province a home, and the picker's three lines
- the roll (4): the odds, the Crown's draw, the race infix on the trait key
- stamping (12): the card, the replace rule, the retired birthplace, a legend, a house, a court pass, a seeded lord, a confederation
- the Slayer trade (3)
- a man moved to another party (3)
- governing (6): the home bundle, the friction bundle, the race test, and what is left on a province
- laws (11): culture before party, for and against swapped, the Crown, the push, the price, the swing's rounding and its weighting

- [ ] **Step 1: Copy the four Lua files aside**

The runner writes each mutation into the shipped Lua and restores it in a `finally`, but a run killed by the machine leaves a mutant in the source. Keep copies to compare against.

```powershell
$b = "Modding Files\Backup\iron_court_cultures_20261015\pre_mutation"
New-Item -ItemType Directory -Force $b | Out-Null
$mod = "Modding Files\pack\script\campaign\mod"
foreach ($f in "zzz_derpy_iron_court.lua","zzz_derpy_iron_court_dwarf.lua","zzz_derpy_iron_court_ui.lua","zzz_derpy_iron_court_ui_map.lua") {
  Copy-Item "$mod\$f" $b -Force
}
Get-FileHash "$b\*.lua" | Select-Object Hash, @{n="File";e={Split-Path $_.Path -Leaf}}
```

Expected: four hashes. They are the reference for Step 8.

- [ ] **Step 2: Find the stale anchors**

```powershell
py -c "import sys,io; sys.path.insert(0,'tools'); import mutate_iron_court as m; [print(w) for w,p,o,n in m.MUTANTS if io.open(p,encoding='utf-8').read().count(o)!=1]"
```

Expected: exactly these ten names, one line each, in file order:

```
a lord dealt anywhere while a party has nobody to lead it
deal: every man rolled at random again
a moved lord keeping his old trade too
the court's roll asking a card for every origin
the court's roll asking a card for every background
a confederation asking a card for every background
law: a man with no influence votes
law: a won man is multiplied too
law: a passed law pays the party against it
law: a passed law angers before it pays
```

An eleventh name means Tasks 4 to 7 moved code this plan did not expect: read that mutant before going on, because the rule it attacks may now be unwatched.

- [ ] **Step 3: Move the nine anchors and retire one**

Each moved entry keeps its name and its intent. The retired entry is replaced by a comment that says why. In `tools/mutate_iron_court.py`:

Replace:

```python
    ("a lord dealt anywhere while a party has nobody to lead it", M,
     """    local bg = IC.leaderless_bg(character, faction_key, tally)
               or IC.roll_background(faction_key, tally)""",
     """    local bg = IC.roll_background(faction_key, tally)"""),
```

with:

```python
    ("a lord dealt anywhere while a party has nobody to lead it", M,
     """    local party = IC.leaderless_party(character, faction_key, tally)
                  or IC.roll_party(faction_key, tally)""",
     """    local party = IC.roll_party(faction_key, tally)"""),
```

Replace:

```python
    ("deal: every man rolled at random again", M,
     """    local list = R.BACKGROUNDS[IC.fewest(pool, tally)]
    if not list or #list == 0 then return nil end""",
     """    local list = R.BACKGROUNDS[pool[cm:random_number(#pool, 1)]]
    if not list or #list == 0 then return nil end"""),
```

with:

```python
    ("deal: every man rolled at random again", M,
     """    if #pool == 0 then pool = {IC.CROWN} end
    return IC.fewest(pool, tally)""",
     """    if #pool == 0 then pool = {IC.CROWN} end
    return pool[cm:random_number(#pool, 1)]"""),
```

Replace:

```python
    ("a moved lord keeping his old trade too", M,
     """                if old then cm:force_remove_trait(lookup, IC.bg_trait(old)) end
                cm:force_add_trait(lookup, IC.bg_trait(list[cm:random_number(#list, 1)]), false)""",
     """                cm:force_add_trait(lookup, IC.bg_trait(list[cm:random_number(#list, 1)]), false)"""),
```

with:

```python
    ("a moved lord keeping his old trade too", M,
     """                if old then cm:force_remove_trait(lookup, IC.bg_trait(old)) end
                cm:force_add_trait(lookup, IC.bg_trait(IC.trade_in(slug, faction_key)), false)""",
     """                cm:force_add_trait(lookup, IC.bg_trait(IC.trade_in(slug, faction_key)), false)"""),
```

Replace:

```python
    # Card prompts at roll time, gifts, and a governor's public order.
    ("the court's roll asking a card for every origin", M,
     """            if IC.stamp_origin(character, IC.origin_for(character, faction_key), true) then""",
     """            if IC.stamp_origin(character, IC.origin_for(character, faction_key)) then"""),
```

with:

```python
    # Card prompts at roll time, gifts, and a governor's public order. The
    # court's roll stamps no origin any more: IC.correct_history does, for a
    # legend, and IC.origin_for answers nobody else.
```

Replace:

```python
    ("the court's roll asking a card for every background", M,
     """                       IC.background_for(character, faction_key, tally), true) then""",
     """                       IC.background_for(character, faction_key, tally)) then"""),
```

with:

```python
    ("the court's roll asking a card for every background", M,
     """        if IC.stamp_bg(character, bg, true) then""",
     """        if IC.stamp_bg(character, bg) then"""),
```

Replace:

```python
    ("a confederation asking a card for every background", M,
     """        IC.stamp_bg(man, IC.background_for(man, faction_key, tally), true)""",
     """        IC.stamp_bg(man, IC.background_for(man, faction_key, tally))"""),
```

with:

```python
    ("a confederation asking a card for every background", M,
     """        IC.stamp_bg(man, bg, true)
        IC.stamp_culture(faction_key, man, culture, binding)""",
     """        IC.stamp_bg(man, bg)
        IC.stamp_culture(faction_key, man, culture, binding)"""),
```

Replace:

```python
    ("law: a man with no influence votes", M,
     """                if n > 0 and party then out[#out + 1] = {cqi = cqi, party = party, n = n} end""",
     """                if n >= 0 and party then out[#out + 1] = {cqi = cqi, party = party, n = n} end"""),
```

with:

```python
    ("law: a man with no influence votes", M,
     """                if n > 0 and party then""",
     """                if n >= 0 and party then"""),
```

Replace:

```python
    ("law: a won man is multiplied too", M,
     """        if won then
            side, why = won, "won"
        elseif side then""",
     """        if won then
            side, why = won, "won"
        end
        if side then"""),
```

with:

```python
    ("law: a won man is multiplied too", M,
     """        if won then
            side, why = won, "won"
        elseif side and side == party_side[m.party] then""",
     """        if won then
            side, why = won, "won"
        end
        if side then"""),
```

Replace:

```python
    ("law: a passed law pays the party against it", M,
     """            if court.houses[slug] then IC.move_loyalty(faction_key, slug, IC.TUNE.law_pass_loss) end""",
     """            if court.houses[slug] then IC.move_loyalty(faction_key, slug, IC.TUNE.law_pass_gain) end"""),
```

with:

```python
    ("law: a passed law pays the party against it", M,
     """                IC.move_loyalty(faction_key, slug, IC.law_swing(tally, slug, IC.TUNE.law_pass_loss))""",
     """                IC.move_loyalty(faction_key, slug, IC.law_swing(tally, slug, IC.TUNE.law_pass_gain))"""),
```

Replace:

```python
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
```

with:

```python
    ("law: a passed law angers before it pays", M,
     """        for _, slug in ipairs(o.pro or {}) do
            if court.houses[slug] then
                IC.move_loyalty(faction_key, slug, IC.law_swing(tally, slug, IC.TUNE.law_pass_gain))
            end
        end
        for _, slug in ipairs(o.con or {}) do
            if court.houses[slug] then
                IC.move_loyalty(faction_key, slug, IC.law_swing(tally, slug, IC.TUNE.law_pass_loss))
            end
        end""",
     """        for _, slug in ipairs(o.con or {}) do
            if court.houses[slug] then
                IC.move_loyalty(faction_key, slug, IC.law_swing(tally, slug, IC.TUNE.law_pass_loss))
            end
        end
        for _, slug in ipairs(o.pro or {}) do
            if court.houses[slug] then
                IC.move_loyalty(faction_key, slug, IC.law_swing(tally, slug, IC.TUNE.law_pass_gain))
            end
        end"""),
```

- [ ] **Step 4: Add the forty-four**

They go at the end of `MUTANTS`, after the entry `a garrison captain stamped with his cards showing`. Every name starts with `culture:` so one run covers them. Their anchors are code lines, never comments, and are written in `'''` quotes because the Lua is full of `"`.

Replace:

```python
    ("a garrison captain stamped with his cards showing", M,
     """            local quiet = IC.is_colonel(character)""",
     """            local quiet = false"""),
]
```

with:

```python
    ("a garrison captain stamped with his cards showing", M,
     """            local quiet = IC.is_colonel(character)""",
     """            local quiet = false"""),

    # THE CULTURES (docs/superpowers/specs/2026-10-15-iron-court-cultures-design.md).
    # Home, away and foreign: the three cases a governor can be in, and the two
    # mistakes that matter most are swapping the first and last and calling every
    # province nobody listed a home.
    ("culture: home and foreign swapped", M,
     '''    return owner == culture and "home" or "foreign"''',
     '''    return owner == culture and "foreign" or "home"'''),
    ("culture: a province on no list is a home", M,
     '''    if not owner then return "away" end''',
     '''    if not owner then return "home" end'''),
    ("culture: the picker says home for a foreign province", U,
     '''ICUI.CULTURE_CASE_LOC = {away = "cult_gov", home = "cult_gov_home", foreign = "cult_gov_foreign"}''',
     '''ICUI.CULTURE_CASE_LOC = {away = "cult_gov", home = "cult_gov_foreign", foreign = "cult_gov_home"}'''),
    ("culture: the picker reads another race's culture", U,
     '''    if not culture or race ~= IC.R(faction) then return nil end''',
     '''    if not culture then return nil end'''),
    ("culture: the card tooltip drops the culture line", UM,
     '''        if line.culture then tip[#tip + 1] = line.culture end''',
     ''''''),

    # The roll: seven in ten to the main culture, the rest to a side culture, a
    # Crown man from any.
    ("culture: the main culture on every roll", M,
     '''    if cm:random_number(10, 1) <= IC.TUNE.culture_main_tenths then return main end''',
     '''    if true then return main end'''),
    ("culture: the odds inverted", M,
     '''    if cm:random_number(10, 1) <= IC.TUNE.culture_main_tenths then return main end''',
     '''    if cm:random_number(10, 1) > IC.TUNE.culture_main_tenths then return main end'''),
    ("culture: the Crown draws only the first culture", M,
     '''        return R.CULTURES[cm:random_number(#R.CULTURES, 1)].slug''',
     '''        return R.CULTURES[1].slug'''),
    ("culture: the culture trait keyed for the Chaos Dwarfs in every court", M,
     '''function IC.culture_trait(slug, faction_key) return IC.key("cult", slug, faction_key) end''',
     '''function IC.culture_trait(slug, faction_key) return IC.key("cult", slug) end'''),

    # Stamping: always quiet, a binding culture replaces and a drawn one does
    # not, a retired birthplace comes off, a legend or a house is binding.
    ("culture: the culture shown on a card", M,
     '''    cm:force_add_trait(lookup, IC.culture_trait(slug, faction_key), false)''',
     '''    cm:force_add_trait(lookup, IC.culture_trait(slug, faction_key), true)'''),
    ("culture: a drawn culture replaces the one he wears", M,
     '''    if has and not binding then return moved end''',
     ''''''),
    ("culture: a binding culture leaves the old one on him", M,
     '''    if has then cm:force_remove_trait(lookup, IC.rkey("cult", has, hasR)) end''',
     ''''''),
    ("culture: a retired birthplace stays on the man", M,
     '''            if not o.faction and character:has_trait(IC.rkey("house", o.slug, R)) then''',
     '''            if false and character:has_trait(IC.rkey("house", o.slug, R)) then'''),
    ("culture: a legend's culture is not binding", M,
     '''    if fixed then return fixed, true end''',
     '''    if fixed then return fixed, false end'''),
    ("culture: a house's culture is not binding", M,
     '''    if house then return house, true end''',
     '''    if house then return house, false end'''),
    ("culture: the culture he wears is rolled over", M,
     '''    if has then return has, false end''',
     ''''''),
    ("culture: an old save's birthplace is rolled over", M,
     '''    if place then return place, false end''',
     ''''''),
    ("culture: the court pass stamps no culture", M,
     '''        if IC.stamp_culture(faction_key, character, culture, binding) then
            stamped = stamped + 1
        end''',
     ''''''),
    ("culture: a seeded lord is given no culture", M,
     '''                IC.stamp_culture(faction_key, character, culture, binding)
                return''',
     '''                return'''),
    ("culture: a confederation stamps no culture", M,
     '''        IC.stamp_culture(faction_key, man, culture, binding)''',
     ''''''),
    ("culture: a confederation forgets the house it came from", M,
     '''IC.background_for(man, faction_key, tally, want)''',
     '''IC.background_for(man, faction_key, tally)'''),

    # The trade: a Kadrin man in the Dwarf Legion is a Slayer, and nobody else.
    ("culture: the Slayer in every ordinary draw", M,
     '''        if not R.RESERVED_BG[list[i]] then pool[#pool + 1] = list[i] end''',
     '''        pool[#pool + 1] = list[i]'''),
    ("culture: a Kadrin man is a Slayer in any party", M,
     '''    if own and own.party == party then return own.bg end''',
     '''    if own then return own.bg end'''),
    ("culture: a Kadrin man in the Legion is never a Slayer", M,
     '''    if own and own.party == party then return own.bg end''',
     ''''''),

    # A man moved to another party: keep a culture that feeds it or is bound to
    # him, otherwise draw one that does.
    ("culture: a moved man is re-dealt a culture that binds him", M,
     '''    if binding then return false end''',
     ''''''),
    ("culture: a moved man keeps a culture that does not feed his party", M,
     '''    if not main or has == main then return false end''',
     '''    if true then return false end'''),
    ("culture: a moved man loses a side culture", M,
     '''        if sides[i] == has then return false end''',
     ''''''),

    # Governing: the home bundle, the friction, the race, the clearing.
    ("culture: the home bundle never applied", M,
     '''    if case == "home" then''',
     '''    if false then'''),
    ("culture: the friction on every away province too", M,
     '''    if case == "foreign" then''',
     '''    if case ~= "home" then'''),
    ("culture: the friction never applied", M,
     '''    if case == "foreign" then''',
     '''    if false then'''),
    ("culture: another race's culture governs", M,
     '''    if not culture or race ~= IC.R(faction_key) then return nil end''',
     '''    if not culture then return nil end'''),
    ("culture: the home bundles left on a province", M,
     '''                    cm:remove_effect_bundle_from_faction_province(
                        IC.gov_bundle_culture_home(slug, faction_key), region)''',
     ''''''),
    ("culture: the friction bundle left on a province", M,
     '''                cm:remove_effect_bundle_from_faction_province(
                    IC.gov_bundle_friction(faction_key), region)''',
     ''''''),

    # Laws: a man's culture outranks his party, never the Crown, and a push
    # reaches only the men on their party's line.
    ("culture: the party's stance outranks the culture's", M,
     '''    return IC.culture_stance(category, option, culture, faction_key)
        or IC.law_stance(category, option, party, faction_key)''',
     '''    return IC.law_stance(category, option, party, faction_key)
        or IC.culture_stance(category, option, culture, faction_key)'''),
    ("culture: a culture's for and against swapped", M,
     '''    for _, c in ipairs(o and o.cpro or {}) do if c == culture then return "aye" end end''',
     '''    for _, c in ipairs(o and o.cpro or {}) do if c == culture then return "nay" end end'''),
    ("culture: a culture outvotes the Crown", M,
     '''    if party == IC.CROWN then
        if vote.stance == "abstain" then return nil, "crown" end
        return vote.stance, "crown"
    end
    local s = IC.man_stance(category, vote.option, party, culture, faction_key)
    if s then return s, s == "aye" and "for" or "against" end''',
     '''    local s = IC.man_stance(category, vote.option, party, culture, faction_key)
    if s then return s, s == "aye" and "for" or "against" end
    if party == IC.CROWN then
        if vote.stance == "abstain" then return nil, "crown" end
        return vote.stance, "crown"
    end'''),
    ("culture: another race's culture reaches a law vote", M,
     '''                    if race ~= IC.R(faction_key) then culture = nil end''',
     ''''''),
    ("culture: a push carries the man whose culture votes against it", M,
     '''        elseif side and side == party_side[m.party] then''',
     '''        elseif side then'''),
    ("culture: dissenters wear their party's push", U,
     '''    local level = g.won and 0 or g.level''',
     '''    local level = g.won and 0 or ((vote.push or {})[g.party] or 0)'''),
    ("culture: a price follows the party's stance", M,
     '''    local s = IC.man_stance(category, vote.option, man.party, man.culture, faction_key)''',
     '''    local s = IC.law_stance(category, vote.option, man.party, faction_key)'''),
    ("culture: the Crown's swing follows its men", M,
     '''    if slug == IC.CROWN then return flat end''',
     ''''''),
    ("culture: a party none of whose men voted divides by nothing", M,
     '''    if aye + nay == 0 then return flat end''',
     ''''''),
    ("culture: a swing's half rounds toward zero", M,
     '''    local size = math.floor(math.abs(share) * step + 0.5)''',
     '''    local size = math.floor(math.abs(share) * step)'''),
    ("culture: a swing counts men and not their influence", M,
     '''            if m.side == "aye" then aye = aye + m.n elseif m.side == "nay" then nay = nay + m.n end''',
     '''            if m.side == "aye" then aye = aye + 1 elseif m.side == "nay" then nay = nay + 1 end'''),
]
```

- [ ] **Step 5: Run the runner's selftest**

```powershell
py tools\mutate_iron_court.py --selftest
```

Expected: `selftest ok: 1267 mutants all anchored, a survivor and a stale anchor are both reported, the tree is restored`. It runs the harness four times (about a minute). It fails with `<name>: anchor matches 0 times, not 1` if a block above was copied wrongly or the Lua differs from the plan; read that name first.

- [ ] **Step 6: Run the repaired nine**

```powershell
py tools\mutate_iron_court.py "a lord dealt anywhere" "deal: every man rolled" "a moved lord keeping" "the court's roll asking" "a confederation asking" "law: a man with no influence" "law: a won man" "law: a passed law"
```

Expected: eleven `caught:` lines and `11 mutants, 0 unexplained`, in about four minutes. The filter is a substring match, so it also runs two neighbours that never went stale, `a confederation asking a card for every origin` and `law: a won man follows the Crown's new side`; they must be caught too.

- [ ] **Step 7: Run the forty-four**

```powershell
py tools\mutate_iron_court.py culture
```

Expected: one `caught:` line for each, ending `44 mutants, 0 unexplained`. It takes about 13 minutes (each mutant runs the harness once, about 17 seconds). A `SURVIVOR` line is a missing assertion, not a bad mutant. Do not weaken the mutant: add the assertion to the `do ... end` block of the task that owns the rule (Task 1 for the keys and the case, Task 4 for the roll and the stamping, Task 5 for governing, Task 6 for laws, Task 7 for the picker), run the harness, and run that mutant again by its name.

- [ ] **Step 8: Check the tree came back byte for byte**

```powershell
$mod = "Modding Files\pack\script\campaign\mod"
foreach ($f in "zzz_derpy_iron_court.lua","zzz_derpy_iron_court_dwarf.lua","zzz_derpy_iron_court_ui.lua","zzz_derpy_iron_court_ui_map.lua") {
  $a = (Get-FileHash "$mod\$f").Hash
  $c = (Get-FileHash "Modding Files\Backup\iron_court_cultures_20261015\pre_mutation\$f").Hash
  "{0}  {1}" -f $(if ($a -eq $c) {"same"} else {"DIFFERENT"}), $f
}
& "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua
```

Expected: four lines starting `same`, then `iron court harness: ok (1140 checks)`. A `DIFFERENT` line means a run was killed with a mutant applied: copy that file back from the backup folder, then touch it (`(Get-Item <file>).LastWriteTime = Get-Date`) so nothing downstream keeps the mutant.

- [ ] **Step 9: The full suite, in the background**

This is optional for finishing the plan and worth starting before the in-game test. The whole list is 1267 mutants, about six hours. It answers a question the 44 cannot: whether the old mutants, anchored on code the new rules did not touch, are still caught now that the harness has 47 more checks and some rewritten ones.

```powershell
py tools\mutate_iron_court.py > mutation_full.txt
```

Expected: `1267 mutants, 0 unexplained`. Any survivor is handled as in Step 7. Do not edit the Lua or the harness while it runs, and do not run the generator, because the runner mutates the shipped Lua in place.

- [ ] **Step 10: Ledger**

Append: `Task 9 done: mutate_iron_court.py; 9 anchors moved, 1 retired, 44 culture mutants, selftest 1267 anchored, culture run 44 caught, harness 1140 checks, tree restored byte for byte.`

---

### Task 10: Release gate, build, deploy, documents and the in-game checklist

**Files:**
- Run only: `tools/check_ic_release.py`, `tools/deploy_iron_court.py`
- Modify: `docs/SESSION_INDEX.md` (the one existing line about the cultures; the file has CRLF line endings)
- Modify: `docs/MY_MODS.md` (the Iron Court row; LF)
- Modify: `docs/superpowers/specs/2026-10-15-iron-court-cultures-design.md` (its status paragraph; LF)

**Interfaces:**
- Consumes: everything above, the importer's `verify()` (it is the deployer's first gate), RPFM's MCP server at `127.0.0.1:45127` for the build.
- Produces: a built `Modding Files/Modpacks/derpy_iron_court.pack`, a copy of it in the game's `data/` folder with the old one backed up under `Modding Files/Backup/deployed_auto/`, and three documents that say what was built.

Nothing in this task changes a mod file. It proves the whole set once more, builds the pack, checks the saved pack against the generator, deploys it, and ends with a list of things only a running game can show. The preview and the harness cannot draw a tooltip, apply a province bundle to a real settlement, or tell whether CA's engine accepts a negative Labour lost, and the list says so.

- [ ] **Step 1: Run every offline gate**

```powershell
foreach ($f in "zzz_derpy_iron_court","zzz_derpy_iron_court_dwarf","zzz_derpy_iron_court_ui","zzz_derpy_iron_court_ui_map") {
  & "C:\Program Files (x86)\Lua\5.1\luac.exe" -p "Modding Files\pack\script\campaign\mod\$f.lua"
}
& "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua
py tools\gen_iron_court.py --check
py tools\gen_ic_ui.py --check
py tools\preview_iron_court.py --check
py tools\import_iron_court.py
py tools\check_ic_release.py
```

Expected, in order: four clean `luac -p`; `iron court harness: ok (1140 checks)`; `ok: 180 bundles, 314 junctions, 297 traits, 2301 loc rows` after ten `NOTE` lines (the home figures outside the range CA ships, kept on purpose); `ok: 30 files, 1906 components`; `30 file(s) checked by TWUI Studio's reader`; `verify ok - 180 bundles, 314 junctions, 297 traits, 2301 loc, 7 script(s), 30 ui file(s), 1786 generated png(s)` and the destination list; and from the release gate six `fit` lines and six `contrast` lines (both races at 1600, 1920 and 2560) ending `0 finding(s)`. Any other result stops here.

- [ ] **Step 2: Confirm RPFM is open**

```powershell
Invoke-WebRequest http://127.0.0.1:45127/sessions -TimeoutSec 4 -UseBasicParsing
```

Expected: a response. `Connection refused` means RPFM is closed: say so and stop. The build goes through RPFM's server, and a binary is never written any other way.

- [ ] **Step 3: Build the pack into Modpacks only**

```powershell
py tools\deploy_iron_court.py --no-copy
```

Expected: `gates green`, one indented line per table and file as it is added, `saved ...\Modding Files\Modpacks\derpy_iron_court.pack (<n> bytes)` (about 15 MB) and `verified 1867 file(s) in the saved pack`. 1867 is the file count of the pack it replaces: this work adds rows and loc lines and no file. A different count means a table or file was added or lost; read the list before going on.

- [ ] **Step 4: Read the saved pack back against the generator**

```powershell
py tools\check_ic_release.py --pack
```

Expected: the fit and contrast lines of Step 1, then `snapshot  ...derpy_iron_court.pack.reviewed_633093F9` and `0 finding(s)`. This reads the saved pack with RPFM shut and checks two things: every table and loc line equals what `gen_iron_court.build()` writes, and every row and loc line of the reviewed baseline (MD5 633093f9, found under `Modding Files/Backup/`) is still there unchanged. Added rows and lines are allowed; a changed or lost one is reported as `changed or gone` or `loc <key>: ... became ...`.

If the gate reports changed baseline rows or lines, read each one. This work is meant to add and not to change, so a changed row is a fault in Tasks 2, 3 or 7. Do not re-pin `SNAPSHOT_MD5`: the comment above it says to do that only after reading every finding, and it is the author's call.

- [ ] **Step 5: Deploy to the game's data folder**

Only while the game is shut. The deployer checks, backs the live pack up to `Modding Files/Backup/deployed_auto/` (never beside the live file) and byte-compares the copy.

```powershell
py tools\deploy_iron_court.py --deploy-only
```

Expected: `backed up the live pack to ...\Modding Files\Backup\deployed_auto\derpy_iron_court.pack.bak_pre_auto_<date>_<time>`, then `deployed ...\data\derpy_iron_court.pack (<n> bytes), byte-identical to the build`. If the game is running the deployer refuses and leaves the live pack alone; run it again with `--wait` in the background and it deploys the moment `Warhammer3` exits. This pack is not hosted on the Workshop, so `data/` is the right place for it.

- [ ] **Step 6: Update the three documents**

`docs/SESSION_INDEX.md` has CRLF line endings. Use the Edit tool on the one line, which contains no line break, so every ending stays as it is. Replace

```
- [Iron Court cultures, spec and plan 2026-10-15](superpowers/specs/2026-10-15-iron-court-cultures-design.md): plan at [superpowers/plans/2026-10-15-iron-court-cultures.md](superpowers/plans/2026-10-15-iron-court-cultures.md), written for the author's review, not built.
```

with the day you ran Step 5 in place of `YYYY-MM-DD` (`Get-Date -Format yyyy-MM-dd`):

```
- [Iron Court cultures, spec and plan 2026-10-15](superpowers/specs/2026-10-15-iron-court-cultures-design.md): plan at [superpowers/plans/2026-10-15-iron-court-cultures.md](superpowers/plans/2026-10-15-iron-court-cultures.md), built and copied to data/ on YYYY-MM-DD; the in-game checklist (plan Task 10 Step 8) has not been run.
```

Then check the endings are untouched:

```powershell
py -c "b=open('docs/SESSION_INDEX.md','rb').read(); print(b.count(b'\r\n'), b.count(b'\n'))"
```

Expected: two equal numbers, the same as before the edit (1276 and 1276 when this plan was written; a line another session adds raises both).

In `docs/MY_MODS.md` (LF), the Iron Court row. Each old text appears once in the file; use the Edit tool for each. Replace `146 effect bundles, 280 traits including one per party name, 14 trait categories` with `180 effect bundles, 297 traits including one per party name and one per culture, 15 trait categories`. Replace `2,062 loc lines` with `2,301 loc lines`. Replace `(1,070 checks)` with `(1,140 checks)` and `(1,179 mutants)` with `(1,267 mutants)`. Then replace `MCT switch "Dwarf courts".` with:

```
MCT switch "Dwarf courts". Cultures (2026-10-15, spec and plan under superpowers/): every lord is dealt one of eight cultures a race, quietly, in place of the old rolled birthplaces; the culture sets the governor's province effects (stronger in a province his culture calls home on the Old World map, Control -4 in another culture's home), feeds a main and a side party, and gives each man a stance on laws, so a party's loyalty moves by how its men voted.
```

In the spec, replace its `Status:` paragraph (the two lines from `Status: agreed in conversation` to `Nothing in this file has been run in game.`) with:

```
Status: built and copied to data/ (see docs/superpowers/plans/2026-10-15-iron-court-cultures.md). Nothing in this
file has been run in game until the plan's Task 10 checklist is ticked. Section 12 lists what is still open.
```

- [ ] **Step 7: Not done here**

These need the author's say-so and are left alone: the push to the public mirror (`tools\sync_iron_court_repo.py`, which copies the workspace and has no `--help`), and any Workshop upload. The Iron Court has no Workshop entry yet.

- [ ] **Step 8: The in-game checklist**

For the author, with the game started on the Old World map (`cr_oldworld`), a Chaos Dwarf faction and the pack ticked. Each line names what to look at and what a failure looks like. Report back which lines failed; do not tick one you did not see.

1. **A new campaign gives every lord a culture, quietly.** Open the character details of the starting lords. Each wears one culture trait, and the explanation text lists the same figures the province effects show later. No Trait Gained card for a culture appeared at the start. Failure: a lord with no culture, two cultures, or a culture card.
2. **A new recruit shows his trade and not his culture.** Recruit a lord. One Trait Gained card appears, for the trade. His character panel also shows a culture. Failure: two cards.
3. **A governor in his culture's home province.** Make a Foundry Districts lord governor of the Foundry District. The province effects list his culture's home bundle at the stronger figures and no friction. Move him to the Pits District: the away bundle replaces it and the friction bundle (Control -4) appears. Failure: either bundle missing, the friction at home, or a bundle left on the province after he leaves.
4. **The governor picker.** Open the Governors tab and hover a candidate card. The tooltip carries one culture line saying home, away or foreign for that province, with the figures. The preview cannot draw a tooltip, so this is the only look at it.
5. **The Help page.** The Governors topic and the Laws topic each read their new sentence and fit their box.
6. **A law vote.** Open the vote on a law that one culture is for and its main party is against. That culture's lord votes the other way from his party. A passed law moves a party's loyalty by how its men voted: a split party moves less than the full step. The Crown's men vote as you chose.
7. **An older save.** Load a save made before this build and end the turn. Every lord has one culture, the old place trait is gone, his party and trade are as they were, and no card showed. Failure: a lord with his old place and a culture, or a changed party.
8. **Another map.** Start an Immortal Empires campaign. Every governor gets the away bundle and no friction, and the script log holds no error naming the Iron Court.
9. **A confederation.** Confederate a faction whose house is in `HOUSE_CULTURE`: the lords it brings take the hold's culture, and one who wore another culture lost it.
10. **A Dwarf court (Dwarf faction).** A Karak Kadrin man seated in the Dwarf Legion is a Slayer. Nobody else is, and a man from an older save who was a ranger is now a Pass-Keeper.
11. **The four effects nobody has seen run** (spec section 12, items 5 to 8): Labour lost -8 on a province (CA ships that effect with positive values only), the research rate (two Karak Azul governors stack), post-battle loot (whether it reaches only the governor), and Wind of Magic for the Hierophant. For each, note what the province effects list shows and whether the number moves in play.

Items 1 to 3 and 7 are the ones whose failure would be silent in a long campaign. If any fails, the script log is the first place to look, and the harness check of the same name is the first place to add the assertion that should have caught it.

- [ ] **Step 9: Ledger**

Append: `Task 10 done: release gate clean (fit, contrast, saved pack against build()), pack built and copied to data/ on <the day>, SESSION_INDEX, MY_MODS and the spec updated; in-game checklist handed to the author.`

---

## Known gaps

What this plan leaves as it is, so nobody mistakes a gap for a fault.

1. **Laws still read party lines in two places.** The overrule penalty (`IC.law_overrule`, loyalty -10 to every party whose line loses) and the parties' own proposals and pushes use the party's stance and not the men's cultures. Spec section 7.2 does not mention either. Changing them is a later piece of work with its own checks.
2. **No home provinces outside the Old World map.** Immortal Empires, IEE and Realm of Chaos give every governor the away case (spec section 11). The model needs no change to add them: `R.HOME_OF` is built from the culture tables.
3. **Four effects have never been seen in a running game** (spec section 12, items 5 to 8): Labour lost -8, the research rate, post-battle loot and Wind of Magic. Task 10 Step 8 item 11 is how they get looked at.
4. **The legend and hold cultures are the plan's proposals** (decisions 6 and 7). They are data: one line each in `R.LEGEND_CULTURE` and `R.HOUSE_CULTURE`, and the harness reads them from there.
5. **Ten home figures are outside the range CA ships** (decision 5). The generator prints them as `NOTE` lines on every run; capping one is a one-number change in the culture table.
6. **A recruit's trade still shows its Trait Gained card** (spec section 12, item 10). Only the culture is quiet.
7. **Out of scope by the spec** (section 11): the Mirror of Spite, recruiting in a district to tilt the roll, culture effects scaling with rank, and an MCT switch for cultures.
8. **The public mirror and the Workshop are not touched** (Task 10 Step 7).
9. **The preview cannot draw a tooltip or the Help page.** Both are on the Task 10 checklist, items 4 and 5.
