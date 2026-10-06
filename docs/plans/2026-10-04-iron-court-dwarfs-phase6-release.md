# Iron Court for Dwarfs - Phase 6: release pass Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship phases 1-5 as one release: every mutant caught or ruled, both races proved at 1600x900, 1920x1080 and 2560x1440, a Chaos Dwarf court and a Dwarf court proved not to talk across each other for fifty turns, every preview approved by the author, the pack built, deployed and read back offline against the generator and against F4C63911 (the last pre-phase-1 build), and the in-game checklist, patch notes, docs and public repo written.

**Architecture:** Nothing new ships to players. The work is three test additions and one release gate: a both-races block appended to `tools/_iron_court_harness.lua` (two fifty-turn scenarios and the mid-campaign switch-off), a "both races" mutant block in `tools/mutate_iron_court.py` anchored on the CONTRACT's signatures, and `tools/check_ic_release.py` (race x screen matrix for text fit and backdrop contrast, plus the saved pack decoded with RPFM shut and compared with `gen_iron_court.build()` and with F4C63911). Then the existing build, deploy, docs and repo routine.

**Tech Stack:** Lua 5.1, Python 3 (py), RPFM MCP, git (repos/derpy-iron-court only)
**Spec:** docs/superpowers/specs/2026-10-04-iron-court-dwarfs-design.md (and the CONTRACT file)

## Global Constraints

- Order: the brief lists the mutation run first. It runs second here, because the full run must include the both-races mutants and those need the both-races checks to exist. Brief item -> task: 3 -> Task 1, 1 -> Task 2, 2 -> Task 3, 4-9 -> Tasks 4-9.
- The workspace is NOT a git repo. Git runs only inside `repos/derpy-iron-court`, and only in Task 9 after the author says to push. A "checkpoint" is the gate list below, never a commit.
- Run every command from the workspace root `G:\Modding for resources` (the mutation runner reports a false "harness not green" from `tools/`). Commands are PowerShell.
- Gates (CONTRACT "Rules every phase keeps"): `luac -p` on every court Lua file; `& "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua`; `py tools\check_lua_api.py`; `py tools\check_lua_literal_left.py`; the undeclared-global check as the importer runs it (inside `deploy_iron_court.py`'s `V.verify()`); `py tools\gen_ic_ui.py --check` and `--selftest`; `py tools\gen_iron_court.py --check`.
- `tools/*.py` misbehave on an unknown flag (memory: import tools BUILD on one). Pass only the flags written here.
- Build and deploy only with `py tools\deploy_iron_court.py` (RPFM open). Backups go under `Modding Files\Backup\` only, never into `data\` or a Workshop folder. If `Warhammer3` is running, `--wait` in the background; never leave a build waiting on the author.
- After any mutation run, re-run the generators before reading or packing a generated file (the runner restores the source, not what the source wrote). A killed run leaves the SOURCE mutated: copy the shipped Lua aside first (Task 2 Step 1).
- Every new check is watched failing for its own reason: here, by the mutants of Task 1 Step 4.
- "Byte-identical Chaos Dwarf rows" means: every DB row and every loc line of F4C63911 (MD5 `f4c6391183a7aa76309558640068318b`, 10,914,962 bytes) is present and unchanged in the new pack. Dwarf rows may be added; nothing may move.
- Player text: no emojis anywhere; never the word "rung"; plain words ("loyalty", "relations", never "standing", "cap", "AI", "accrue"). Patch notes: one short phrase per change, ONE flat BBCode `[list]`, no section headers, no "why"; MCT may be abbreviated there.
- Outward-facing steps wait for the author: the preview approval (Task 4), the commit and push (Task 9). The Workshop upload is NOT in this plan.
- Every key named in a fixture (`wh_main_dwf_karak_kadrin`, `wh_main_sc_dwf_dwarfs`, `wh_main_grn_greenskins`, `wh_main_sc_grn_greenskins`) is harness-only and never ships.

## Review Focus

1. **The Chaos Dwarf court did not move.** `check_ic_release.py --pack` reports zero changed or lost rows and loc lines against F4C63911, found by MD5 under `Modding Files\Backup\`, not by a name somebody typed. Pinned in Task 5 Step 6.
2. **The saved pack is the generator's, cell for cell.** Every table decoded out of the saved `.pack` with RPFM shut, row counts and cells compared with `gen_iron_court.build()`, with no table exempt. Pinned in Task 5 Step 6.
3. **No cross-talk, and the checks that say so can fail.** Each of the seven "both races" mutants is caught (Task 1 Step 4); the fifty-turn scenarios refuse to pass on a court that applied nothing or a Book nobody read.
4. **The mutation run left nothing behind.** The shipped Lua matches the guard copies byte for byte and every generated file hashes the same before and after (Task 2 Steps 4-5).
5. **Dwarf courts switched off mid-campaign** take every Dwarf bundle and save off by the next turn, stop the Dwarf court's turn, and leave the Chaos Dwarf court ticking. Pinned in Task 1.

---

### Task 1: Both races in one campaign (harness scenario and its mutants)

**Files:**
- Modify: `tools/_iron_court_harness.lua` (a `do ... end` block inserted directly before `check("no parties' turn failed anywhere in the run", function()`)
- Modify: `tools/mutate_iron_court.py` (the `D` alias if missing, two helpers above `MUTANTS`, a "both races" block appended inside `MUTANTS` before its closing `]`)
- Possibly modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court.lua` (only if Step 3 finds the switch-off fault described there)

**Interfaces:**
- Consumes (CONTRACT): `IC.R`, `IC.race_key`, `IC.race_of`, `IC.is_chd`, `IC.has_court`, `IC.key`, `IC.RACES.dwf`, `IC.grudges`, `IC.grudge_write`, `IC.book_weight`, `IC.book_tick` (called from the model's turn), `IC.TUNE.dwarf_courts` (in `IC.LIVE_TUNE`), `IC.TUNE.grudge_max`, `IC.TUNE.book_bands`, `IC.TUNE.book_penalty`, save fields 19 (grudges, `slug:code.turn;...` joined by `/`) and 20 (Book bands, `other_faction_key:n` joined by `/`).
- Consumes (harness, file-level): `check`, `make_faction`, `make_character`, `ANY_SEAT`, `F`, `saved`, `applied`, `factions`, `bonuses`, `turn`, `stub_mct`, `with_mct`, `with_frozen`, `core.listeners`.
- Produces: three harness checks named `both races: ...`; seven mutants named `both races: ...`; `_holder(sig)` and `_as_dwarf(call)` in the mutation runner. No later phase consumes them.

- [ ] **Step 1: Record the starting count.**

Run: `& "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua`
Expected: `iron court harness: ok (N0 checks)`. Write N0 down; Step 3 expects N0 + 3. If it is not green, stop: phase 5 is not finished.

- [ ] **Step 2: Insert the both-races block.** In `tools/_iron_court_harness.lua`, directly before the line `check("no parties' turn failed anywhere in the run", function()`, insert:

```lua
-- ---------------------------------------------------------------------------
-- BOTH RACES IN ONE CAMPAIGN (plan 2026-10-04 Iron Court for Dwarfs, phase 6).
-- A Chaos Dwarf court and a Dwarf court tick side by side for fifty turns, and
-- every assertion here is about CROSS-TALK: what one court's turns did to the
-- other's bundles, save, grudges or Book bands. Each race's own rules are the
-- phase 2-5 checks' business. One local (BR), so the main chunk's local count
-- does not grow by ten.
-- ---------------------------------------------------------------------------
do
    local BR = {CHD = F, DWF = "wh_main_dwf_karak_kadrin",
                GRN = "wh_main_grn_greenskins"}

    -- CA's grudge points on the greenskins as the Dwarf court reads them: 45 a
    -- turn, so 500, 1,000 and 2,000 are crossed on turns 12, 23 and 45.
    function BR.points(t) return 45 * t end

    -- Field i of a court's save string, "" when the save is shorter or absent.
    function BR.field(fk, i)
        local parts = {}
        for p in ((saved["derpy_ic_" .. fk] or "") .. "|"):gmatch("(.-)|") do
            parts[#parts + 1] = p
        end
        return parts[i] or ""
    end

    -- A fresh two-court world. `humans` is what cm:get_human_factions answers.
    function BR.world(humans)
        IC.state, factions, applied, bonuses = {}, {}, {}, {}
        saved["derpy_ic_" .. BR.CHD], saved["derpy_ic_" .. BR.DWF] = nil, nil
        local function men(base)
            local out = {}
            for i = 1, 6 do out[i] = make_character(base + i, ANY_SEAT, nil, nil) end
            return out
        end
        local w = {asked = {}, by = {}, ticked = {}, now = 0}
        w.chd = make_faction(BR.CHD, IC.CHD_SUBCULTURE, men(9100), {"prov_a", "prov_b"})
        w.dwf = make_faction(BR.DWF, "wh_main_sc_dwf_dwarfs", men(9200), {"prov_c", "prov_d"})
        make_faction(BR.GRN, "wh_main_sc_grn_greenskins", {}, {})
        w.chd._met, w.dwf._met = {BR.DWF, BR.GRN}, {BR.CHD, BR.GRN}
        w.keep = {humans = cm.get_human_factions, apply = cm.apply_effect_bundle,
                  weight = IC.book_weight, turn = IC.turn, govs = IC_GOVS_ON}
        cm.get_human_factions = function() return humans end
        IC_GOVS_ON = true
        -- WHO EACH BUNDLE WENT TO. The stub keys `applied` by bundle alone,
        -- which cannot tell the two courts apart.
        cm.apply_effect_bundle = function(self, bundle, faction_key, turns)
            w.by[#w.by + 1] = {f = faction_key, b = bundle}
            return w.keep.apply(self, bundle, faction_key, turns)
        end
        -- WHAT CA'S POOLED RESOURCES WOULD SAY, and who asked.
        IC.book_weight = function(fk, other)
            w.asked[fk] = (w.asked[fk] or 0) + 1
            if fk == BR.DWF and other == BR.GRN then return BR.points(w.now) end
            return 0
        end
        -- WHOSE TURN RAN. The listener calls IC.turn by field, so this sees it.
        IC.turn = function(fk, ...)
            w.ticked[fk] = (w.ticked[fk] or 0) + 1
            return w.keep.turn(fk, ...)
        end
        IC.register()
        return w
    end

    function BR.done(w)
        cm.get_human_factions, cm.apply_effect_bundle = w.keep.humans, w.keep.apply
        IC.book_weight, IC.turn, IC_GOVS_ON = w.keep.weight, w.keep.turn, w.keep.govs
    end

    -- Turns a..b, both courts each turn, the order swapped every other turn so a
    -- value cached by whichever court went first is caught either way round.
    function BR.turns(w, a, b)
        for t = a, b do
            turn, w.now = t, t
            local first, second = w.chd, w.dwf
            if t % 2 == 0 then first, second = w.dwf, w.chd end
            core.listeners["ic_turn"]({faction = function() return first end})
            core.listeners["ic_turn"]({faction = function() return second end})
        end
    end

    -- The penalties applied against the greenskins, "from:n" in order. Only
    -- negative ones: Send Diplomats' goodwill is positive and is not the Book.
    function BR.book()
        local out = {}
        for _, x in ipairs(bonuses) do
            if x.b == BR.GRN and x.n < 0 then out[#out + 1] = x.a .. ":" .. x.n end
        end
        return table.concat(out, ",")
    end

    function BR.three_bands()
        local want = {}
        for i = 1, #IC.TUNE.book_bands do
            want[i] = BR.DWF .. ":" .. IC.TUNE.book_penalty[i]
        end
        return table.concat(want, ",")
    end

    function BR.dwarf_bundles_on()
        local n = 0
        for k, c in pairs(applied) do
            if c and c > 0 and k:find("^derpy_ic_") and k:find("_dwf_", 1, true) then
                n = n + 1
            end
        end
        return n
    end

    function BR.side_by_side(humans, dwf_human)
        local w = BR.world(humans)
        local ok, err = pcall(function()
            BR.turns(w, 1, 50)

            -- 1. KEYS: every court bundle went to the court of its own race.
            local n = {}
            for _, x in ipairs(w.by) do
                if x.b:find("^derpy_ic_") then
                    local dwarf = x.b:find("_dwf_", 1, true) ~= nil
                    n[x.f] = (n[x.f] or 0) + 1
                    assert(x.f ~= BR.CHD or not dwarf,
                        "the Chaos Dwarf court was given a Dwarf bundle: " .. x.b)
                    assert(x.f ~= BR.DWF or dwarf,
                        "the Dwarf court was given a Chaos Dwarf bundle: " .. x.b)
                end
            end
            assert((n[BR.CHD] or 0) > 0 and (n[BR.DWF] or 0) > 0,
                "fifty turns applied " .. tostring(n[BR.CHD]) .. " Chaos Dwarf and "
                .. tostring(n[BR.DWF]) .. " Dwarf court bundles: a court that applies "
                .. "nothing proves nothing here")

            -- 2. THE BOOK: never read for the Chaos Dwarf court; for a Dwarf
            -- player, each band once, in order.
            assert(not w.asked[BR.CHD], "the Book was read for the Chaos Dwarf court "
                .. tostring(w.asked[BR.CHD]) .. " times")
            if dwf_human then
                assert((w.asked[BR.DWF] or 0) > 0,
                    "the Dwarf court never asked IC.book_weight about anyone")
                assert(BR.book() == BR.three_bands(), "the Book's bands against the "
                    .. "greenskins were [" .. BR.book() .. "], wanted ["
                    .. BR.three_bands() .. "]")
            else
                -- WHETHER AN AI DWARF COURT KEEPS A BOOK is phase 5's call; what it
                -- may never do is fire a band twice or out of order.
                local got = BR.book()
                assert(got == "" or got == BR.three_bands(),
                    "a Dwarf court run by the game fired [" .. got .. "]")
            end
            for _, x in ipairs(bonuses) do
                local pair = (x.a == BR.CHD and x.b == BR.DWF)
                          or (x.a == BR.DWF and x.b == BR.CHD)
                assert(not (pair and x.n < 0), "the courts soured the two factions on "
                    .. "each other: " .. x.a .. " -> " .. x.b .. " " .. x.n)
            end

            -- 3. GRUDGES, on a party both courts have, so a book keyed by slug
            -- alone would land in both.
            for _, fk in ipairs({BR.CHD, BR.DWF}) do
                if not IC.court(fk).houses.forge then IC.add_house(fk, "forge") end
            end
            IC.grudge_write(BR.CHD, "forge", "castout")
            for _ = 1, IC.TUNE.grudge_max + 2 do
                IC.grudge_write(BR.DWF, "forge", "castout")
            end
            for slug in pairs(IC.court(BR.CHD).houses) do
                assert(#IC.grudges(BR.CHD, slug) == 0, "the Chaos Dwarf " .. slug
                    .. " holds " .. #IC.grudges(BR.CHD, slug) .. " grudge(s)")
            end
            assert(#IC.grudges(BR.DWF, "forge") == IC.TUNE.grudge_max,
                "the Dwarf Forgewrights hold " .. #IC.grudges(BR.DWF, "forge")
                .. " grudges, not " .. IC.TUNE.grudge_max)

            -- 4. THE SAVES: the Chaos Dwarf string carries neither Dwarf field.
            IC.save(BR.CHD)
            IC.save(BR.DWF)
            assert(BR.field(BR.CHD, 19) == "" and BR.field(BR.CHD, 20) == "",
                "the Chaos Dwarf save carries grudges [" .. BR.field(BR.CHD, 19)
                .. "] or Book bands [" .. BR.field(BR.CHD, 20) .. "]")
            assert(BR.field(BR.DWF, 19):find("forge:", 1, true),
                "the Dwarf save's grudge field is [" .. BR.field(BR.DWF, 19) .. "]")
            if dwf_human then
                assert(BR.field(BR.DWF, 20):find(BR.GRN .. ":", 1, true),
                    "the Dwarf save's Book field is [" .. BR.field(BR.DWF, 20) .. "]")
            end

            -- 5. THROUGH A RELOAD: the grudges stay, the Chaos Dwarf court gains
            -- none, and no band fires again. Turns 51-52 read 2,295 and 2,340,
            -- above every band, so a lost field 20 re-fires all three here.
            local before = BR.book()
            IC.state = {}
            IC.load(BR.CHD)
            IC.load(BR.DWF)
            assert(#IC.grudges(BR.DWF, "forge") == IC.TUNE.grudge_max,
                "the Dwarf grudges did not survive the save: "
                .. #IC.grudges(BR.DWF, "forge"))
            assert(#IC.grudges(BR.CHD, "forge") == 0,
                "the Chaos Dwarf court read a grudge back")
            BR.turns(w, 51, 52)
            assert(BR.book() == before, "a Book band fired again after the reload: ["
                .. BR.book() .. "]")
        end)
        BR.done(w)
        if not ok then error(err, 0) end
    end

    check("both races: a Dwarf player beside a Chaos Dwarf court, fifty turns, no cross-talk",
    function() BR.side_by_side({BR.DWF}, true) end)

    check("both races: a Chaos Dwarf player beside a Dwarf court, fifty turns, no cross-talk",
    function() BR.side_by_side({BR.CHD}, false) end)

    check("both races: Dwarf courts switched off mid-campaign, the Chaos Dwarf court runs on",
    function()
        local values = {}
        for k, v in pairs(IC.TUNE_DEFAULTS) do values[k] = v end
        with_mct(stub_mct(values), function()
            with_frozen({}, function()
                local w = BR.world({BR.CHD})
                local ok, err = pcall(function()
                    BR.turns(w, 1, 10)
                    assert(BR.dwarf_bundles_on() > 0, "ten turns put no Dwarf court "
                        .. "bundle on: the off case below would pass on a court that "
                        .. "never ran")
                    assert(BR.field(BR.DWF, 1) ~= "", "the Dwarf court was never saved")
                    values.dwarf_courts = false
                    core.listeners["ic_live_tune"]({})
                    assert(IC.TUNE.dwarf_courts == false,
                        "the Dwarf courts switch did not follow MCT's Finalize")
                    local chd0, dwf0 = w.ticked[BR.CHD] or 0, w.ticked[BR.DWF] or 0
                    BR.turns(w, 11, 12)
                    assert(BR.dwarf_bundles_on() == 0,
                        BR.dwarf_bundles_on() .. " Dwarf court bundle(s) stayed on")
                    assert((saved["derpy_ic_" .. BR.DWF] or "") == "",
                        "the switched-off Dwarf court is still in the save")
                    assert((w.ticked[BR.DWF] or 0) == dwf0,
                        "a switched-off Dwarf court still ran its turn")
                    assert((w.ticked[BR.CHD] or 0) == chd0 + 2, "the Chaos Dwarf court "
                        .. "ran " .. ((w.ticked[BR.CHD] or 0) - chd0) .. " of its two "
                        .. "turns with Dwarf courts off")
                    values.dwarf_courts = true
                    core.listeners["ic_live_tune"]({})
                    BR.turns(w, 13, 13)
                    assert((w.ticked[BR.DWF] or 0) == dwf0 + 1,
                        "switched back on, the Dwarf court did not run its turn")
                end)
                BR.done(w)
                if not ok then error(err, 0) end
            end)
        end)
    end)
end

```

- [ ] **Step 3: Run the harness.**

Run: `$env:IC_TEST_ALL = "1"; & "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua; Remove-Item Env:IC_TEST_ALL`
Expected: `iron court harness: ok (N0 + 3 checks)`.
A FAIL is a cross-talk fault in phases 1-5, not a fixture to loosen. Known shapes and their fix:
- `a switched-off Dwarf court still ran its turn` or `... bundle(s) stayed on` / `still in the save`: the `ic_turn` listener in `zzz_derpy_iron_court.lua` dismantles only `IC.is_chd(faction)` courts. Change that inner test to `IC.race_of(faction)` (a court of any race that the settings switched off), so the line reads `if IC.race_of(faction) then`. If a Dwarf-only bundle survives `IC.dismantle` (kinship, grudges), add its removal to `IC.dismantle`.
- `the Dwarf court was given a Chaos Dwarf bundle: derpy_ic_...` for a Dwarf-only key: the key skips `IC.key` (CONTRACT "Keys"). Build it through `IC.key(kind, slug, faction_key)`; never exempt it here.
- `the Dwarf court never asked IC.book_weight`: `IC.book_tick` reads the points without going through `IC.book_weight` (CONTRACT "Book of Grudges"). Route it through `IC.book_weight`.
- `the Dwarf courts switch did not follow MCT's Finalize`: `"dwarf_courts"` is missing from `IC.LIVE_TUNE`. Append it at the end of that list.
After any model fix, re-run Step 3 and every gate in Global Constraints.

- [ ] **Step 4: The mutants.** In `tools/mutate_iron_court.py`:

(a) Run `Select-String -Path tools\mutate_iron_court.py -Pattern 'zzz_derpy_iron_court_dwarf.lua'`. Expected: one line, `D = os.path.join(MOD, "zzz_derpy_iron_court_dwarf.lua")` (phase 2). If there is none, add exactly that line directly after the `P = os.path.join(MOD, "zzz_derpy_iron_court_parties.lua")` line. If phase 2 used another name for it, use that name for `D` in (b).

(b) Directly above `MUTANTS = [`, insert:

```python
# THE CONTRACT'S SIGNATURES (docs/superpowers/plans/2026-10-04-iron-court-dwarfs-CONTRACT.md).
# The "both races" mutants anchor on these and not on lines inside them: phases 2-5
# own the bodies, the contract fixes the names. Each renames the real function to a
# body and wraps it, which is how a mistake AROUND a function - a cache keyed by
# nothing, the wrong faction, a guard nobody runs - is written without knowing what
# the function says inside.
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

```

(c) Inside `MUTANTS`, directly before its closing `]`, append:

```python
    # ---- both races in one campaign (plan 2026-10-04 dwarfs phase 6) ---------
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
```

- [ ] **Step 5: Run them.**

Run: `py tools\mutate_iron_court.py --selftest`
Expected: `selftest ok: N mutants all anchored, a survivor and a stale anchor are both reported, the tree is restored`. An `anchor matches 0 times` line names a signature that differs from the CONTRACT: fix the code to the contract's signature (the contract wins), not the mutant.

Run: `py tools\mutate_iron_court.py "both races"`
Expected: seven `caught:` lines and `7 mutants, 0 unexplained`. A SURVIVOR means an assertion is missing: add it to the both-races block, watch that mutant caught, re-run.

- [ ] **Step 6: Checkpoint.** Run every gate in Global Constraints. Expected: all green; harness `N0 + 3`.

---

### Task 2: The full mutation run

**Files:**
- Create: `Modding Files/Backup/mutation_guard_<yyyyMMdd>/` (guard copies, hash lists, the run log)
- Modify: `tools/_iron_court_harness.lua` (one assertion per survivor), `tools/mutate_iron_court.py` (only a ruled mutant, Step 6)

**Interfaces:**
- Consumes: `MUTANTS` (1,097 from F4C63911, plus phases 2-5's, plus Task 1's seven).
- Produces: the run's count and its survivors' outcome, for the handoff (Task 8).

- [ ] **Step 1: Guard copies.**

```powershell
$D = Get-Date -Format yyyyMMdd
$G = "Modding Files\Backup\mutation_guard_$D"
New-Item -ItemType Directory -Force $G | Out-Null
Copy-Item "Modding Files\pack\script\campaign\mod\zzz_derpy_iron_court*.lua", "Modding Files\pack\script\mct\settings\derpy_iron_court.lua" $G
Get-ChildItem $G -Filter *.lua | Select-Object Name
```
Expected: six names (`derpy_iron_court.lua`, `zzz_derpy_iron_court.lua`, `zzz_derpy_iron_court_dwarf.lua`, `zzz_derpy_iron_court_parties.lua`, `zzz_derpy_iron_court_ui.lua`, `zzz_derpy_iron_court_ui_map.lua`).

- [ ] **Step 2: Regenerate, then hash every generated file.**

```powershell
py tools\gen_iron_court.py; py tools\gen_ic_ui.py; py tools\make_ic_backdrop.py
$gen = @(Get-ChildItem "Modding Files\source\iron_court\*.tsv", "Modding Files\pack\ui\campaign ui\derpy_ic_*.twui.xml", "Modding Files\pack\script\mct\settings\derpy_iron_court.lua", "Modding Files\pack\script\campaign\mod\zzz_derpy_iron_court*.lua") + @(Get-ChildItem "Modding Files\pack\ui\derpy_ic" -Recurse -Filter *.png)
$gen | Get-FileHash -Algorithm MD5 | Select-Object Path, Hash | Export-Csv "$G\before.csv" -NoTypeInformation
(Import-Csv "$G\before.csv").Count
```
Expected: each generator ends `ok` / `wrote`; `make_ic_backdrop.py` prints no `PROBLEM:`; the count is the number of files hashed (record it).

- [ ] **Step 3: The run, in the background.** It takes about two hours (one harness run of ~5 s per mutant).

Run with `run_in_background: true`: `py tools\mutate_iron_court.py *> "Modding Files\Backup\mutation_guard_$D\run.log"`
Wait for the completion notice; do not poll. Then:
`Select-String -Path "Modding Files\Backup\mutation_guard_$D\run.log" -Pattern '^SURVIVOR|mutants, '`
Expected: `M mutants, 0 unexplained`, or SURVIVOR lines for Step 6. Record M.
If the run was killed: copy the six guard files back over the shipped ones (Step 1's paths, reversed) before anything else.

- [ ] **Step 4: The source came back.**

```powershell
foreach ($f in Get-ChildItem $G -Filter *.lua) {
  $live = if ($f.Name -eq "derpy_iron_court.lua") { "Modding Files\pack\script\mct\settings\$($f.Name)" } else { "Modding Files\pack\script\campaign\mod\$($f.Name)" }
  if ((Get-FileHash $f.FullName).Hash -ne (Get-FileHash $live).Hash) { "DIFFERS $live" }
}
```
Expected: no output.

- [ ] **Step 5: Regenerate and compare.**

```powershell
py tools\gen_iron_court.py; py tools\gen_ic_ui.py; py tools\make_ic_backdrop.py
$gen = @(Get-ChildItem "Modding Files\source\iron_court\*.tsv", "Modding Files\pack\ui\campaign ui\derpy_ic_*.twui.xml", "Modding Files\pack\script\mct\settings\derpy_iron_court.lua", "Modding Files\pack\script\campaign\mod\zzz_derpy_iron_court*.lua") + @(Get-ChildItem "Modding Files\pack\ui\derpy_ic" -Recurse -Filter *.png)
$gen | Get-FileHash -Algorithm MD5 | Select-Object Path, Hash | Export-Csv "$G\after.csv" -NoTypeInformation
Compare-Object (Import-Csv "$G\before.csv") (Import-Csv "$G\after.csv") -Property Path, Hash
```
Expected: no output. A difference is a generator that is not deterministic or a file the run left changed: find which, before anything is packed.

- [ ] **Step 6: Every survivor ends caught or ruled.** For each `SURVIVOR: <name> - <why>` (including the three survivors the UI_POLISH handoff section 1 carried over):
  1. `STALE ANCHOR`: the code moved. Find where the rule now lives (`Select-String` for a distinctive line of the old anchor's code), re-aim the mutant's `old`/`new` at it, re-run it by name.
  2. `SURVIVED`: find the check that owns the rule (search the harness for the rule's words), add the assertion that measures its observable consequence (a bundle applied, a field saved, a loyalty moved - never a restated formula or a call count), then run `py tools\mutate_iron_court.py "<the mutant's name>"` and see `caught:`.
  3. Equivalent (it cannot change behaviour, e.g. a guard whose input is unreachable): rewrite the mutant to the nearest non-equivalent mistake and see that one caught. Deleting a mutant needs the author's word, and the handoff records the name and the reason.
  4. `ERROR - harness exited without a FAIL assertion`: the mutant breaks parsing; make its `new` valid Lua so it tests a rule.
After the last one: `py tools\mutate_iron_court.py <every survivor name, quoted>` -> `K mutants, 0 unexplained`; Step 4's comparison again (no output); the harness green.

- [ ] **Step 7: Checkpoint.** Every gate in Global Constraints, green.

---

### Task 3: Text fit and contrast, both races, three screens

**Files:**
- Create: `tools/check_ic_release.py`
- Possibly modify: `tools/make_ic_backdrop.py` (Step 4 note), `tools/gen_ic_ui.py` (a fix a finding needs), and the panel Lua's mirrored tables (through the scratch-sync route the UI_POLISH handoff section 3 describes)

**Interfaces:**
- Consumes: `gen_ic_ui.at_box(bw, race=...)` (CONTRACT), `gen_ic_ui.art_paths()`, `gen_ic_ui.PANEL_BG/PANEL_W/PANEL_H`, `gen_iron_court.RACES/TSV_META/PACK_NAME/build()`, `make_ic_backdrop.contrast(img, G)` and `MIN_RATIO`, `read_pack_index.paths/read`, `read_vanilla_db.load/defs`, `read_vanilla_loc.parse`, `deploy_iron_court.OUT/GAME_DATA`.
- Produces: `fit_problems()`, `grounds()`, `contrast_problems(found=None, boxes=BOXES)`, `pack_tables(pack)`, `find_snapshot()`, `chd_unchanged(old, new)`, `matches_generator(new, built=None, meta=None)`. Task 5 consumes the last four through `--pack`.

- [ ] **Step 1: Write `tools/check_ic_release.py`:**

```python
# -*- coding: utf-8 -*-
"""The Iron Court's release gate: both races, three screens, and the saved pack read back.

WHY IT EXISTS (plan 2026-10-04, Iron Court for Dwarfs phase 6). gen_ic_ui.py --check and
make_ic_backdrop.py --check each prove what they were written for. A release needs the
matrix - Chaos Dwarf and Dwarf, at 1600x900, 1920x1080 and 2560x1440 - and a release that
promised "the Chaos Dwarf court does not change" needs that measured on the pack that
ships, not on the plan that built it.

    py tools/check_ic_release.py            # fit and contrast, both races, three screens
    py tools/check_ic_release.py --pack     # and the saved Modpacks pack: every table read
                                            # back against gen_iron_court.build(), and every
                                            # row and loc line of F4C63911 unchanged
    py tools/check_ic_release.py --selftest

Exit 1 on any finding. An unknown flag is refused.

THE PACK IS READ WITH RPFM SHUT (read_vanilla_db, read_vanilla_loc), so the read-back is
not RPFM's session vouching for its own save.
"""
import copy
import hashlib
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import deploy_iron_court as DEP       # noqa: E402
import gen_iron_court as G            # noqa: E402
import gen_ic_ui as U                 # noqa: E402
import make_ic_backdrop as B          # noqa: E402
import read_pack_index as RPI         # noqa: E402
import read_vanilla_db as RVD         # noqa: E402
import read_vanilla_loc as RVL        # noqa: E402

BOXES = (1600, 1920, 2560)
PACK_DIR = os.path.join(ROOT, "Modding Files", "pack")
LIVE = os.path.join(DEP.GAME_DATA, G.PACK_NAME + ".pack")
# F4C63911, the last build before phase 1 (HANDOFF_20261004_IRON_COURT_DWARFS_DESIGN.md s1).
SNAPSHOT_MD5 = "f4c6391183a7aa76309558640068318b"
SNAPSHOT_SIZE = 10914962


def fit_problems():
    """gen_ic_ui's whole check() - text fit (20k), crossings, the scale rules - once per
    race at each screen, so neither race is passed at a size only by inference."""
    out = []
    for race in sorted(G.RACES):
        for bw in BOXES:
            got = U.at_box(bw, race=race).check()
            print("fit       %s %4d: %d finding(s)" % (race, bw, len(got)))
            out += ["fit %s at %d: %s" % (race, bw, p) for p in got]
    return out


def grounds():
    """{race: [backdrop PNG on disk]}. The Chaos Dwarf one is PANEL_BG; the Dwarf one is
    every OTHER panel-sized picture gen_ic_ui ships - found, not named, so this does not
    depend on what phase 3 called it. Exactly one is the only right answer."""
    from PIL import Image
    found = {"chd": [os.path.join(PACK_DIR, *U.PANEL_BG.split("/"))], "dwf": []}
    for p in sorted(U.art_paths()):
        name = os.path.basename(p)
        if p == U.PANEL_BG or name.startswith("wedge_") or not name.endswith(".png"):
            continue
        full = os.path.join(PACK_DIR, *p.split("/"))
        if os.path.isfile(full):
            with Image.open(full) as im:
                if im.size == (U.PANEL_W, U.PANEL_H):
                    found["dwf"].append(full)
    return found


def contrast_problems(found=None, boxes=BOXES):
    """make_ic_backdrop's per-cell measure (Rec.709, p95, MIN_RATIO) for each race's
    ground at each screen. The picture is scaled to that screen's panel with LANCZOS, as
    make_ic_backdrop's own 1600 leg does; the 2560 leg is new here."""
    from PIL import Image
    found = grounds() if found is None else found
    out = []
    for race in sorted(found):
        if len(found[race]) != 1:
            out.append("contrast %s: %d panel-sized grounds in art_paths(), wanted 1: %s"
                       % (race, len(found[race]), found[race]))
            continue
        img = Image.open(found[race][0]).convert("RGB")
        for bw in boxes:
            m = U.at_box(bw, race=race)
            pic = img if img.size == (m.PANEL_W, m.PANEL_H) else img.resize(
                (m.PANEL_W, m.PANEL_H), Image.LANCZOS)
            rows = B.contrast(pic, m)
            if not rows:
                out.append("contrast %s at %d: no cell measured" % (race, bw))
                continue
            print("contrast  %s %4d: %d cells, worst %s %.2f:1"
                  % (race, bw, len(rows), rows[-1][0], rows[-1][3]))
            out += ["contrast %s at %dx%d: %s reads %.2f:1 (p95 %.0f), under %.1f:1"
                    % (race, m.PANEL_W, m.PANEL_H, n, r, p, B.MIN_RATIO)
                    for n, _mean, p, r in rows if r < B.MIN_RATIO]
    return out


def pack_tables(pack):
    """{table: (version, rows, {field: type})} and {"loc": {key: text}} out of a saved pack."""
    out = {}
    for path in RPI.paths(pack):
        parts = path.split("/")
        if len(parts) == 3 and parts[0] == "db" and parts[2] == G.PACK_NAME:
            (_p, ver, rows), = RVD.load(pack, parts[1])
            out[parts[1]] = (ver, rows, dict(RVD.defs(parts[1])[ver]))
    (_p, _c, data), = RPI.read(pack, "text/db/%s.loc" % G.PACK_NAME)
    out["loc"] = RVL.parse(data)
    return out


def find_snapshot():
    """F4C63911 wherever a deploy backed it up under Modding Files/Backup, by MD5."""
    for top, _dirs, files in os.walk(os.path.join(ROOT, "Modding Files", "Backup")):
        for n in files:
            p = os.path.join(top, n)
            if n.startswith(G.PACK_NAME + ".pack") and os.path.getsize(p) == SNAPSHOT_SIZE:
                if hashlib.md5(open(p, "rb").read()).hexdigest() == SNAPSHOT_MD5:
                    return p
    return None


def chd_unchanged(old, new):
    """Every row and loc line of the snapshot is in the new pack, unchanged. New rows are
    allowed - they are the Dwarf ones; nothing the Chaos Dwarf court shipped may move."""
    out = []
    for t in sorted(k for k in old if k != "loc"):
        ver, rows = old[t][0], old[t][1]
        if t not in new:
            out.append("%s: the whole table is gone" % t)
            continue
        if new[t][0] != ver:
            out.append("%s: version %d became %d" % (t, ver, new[t][0]))
            continue
        have = set(tuple(r.items()) for r in new[t][1])
        lost = [r for r in rows if tuple(r.items()) not in have]
        out += ["%s: changed or gone: %s" % (t, list(r.values())[:3]) for r in lost[:5]]
        if len(lost) > 5:
            out.append("%s: and %d more" % (t, len(lost) - 5))
    moved = [k for k in sorted(old["loc"]) if new["loc"].get(k) != old["loc"][k]]
    out += ["loc %s: %r became %r" % (k, old["loc"][k], new["loc"].get(k)) for k in moved[:20]]
    if len(moved) > 20:
        out.append("loc: and %d more" % (len(moved) - 20))
    return out


def _same(packed, text, ftype):
    if ftype == "ColourRGB":
        return packed == int(text, 16)
    if isinstance(packed, bool):
        return text.lower() == ("true" if packed else "false")
    if isinstance(packed, float):
        return abs(packed - float(text or 0)) < 1e-4
    if isinstance(packed, int):
        return packed == int(float(text or 0))
    return packed == text


def matches_generator(new, built=None, meta=None):
    """The saved pack holds what gen_iron_court.build() writes: the same tables, the same
    row counts, every cell equal, the loc whole. RPFM's derived *_colour_hex columns are
    not in the binary; they are printed, not compared, and no table is exempt."""
    built = G.build() if built is None else built
    meta = G.TSV_META if meta is None else meta
    out, skipped = [], set()
    for t, rows in sorted(built.items()):
        if t == "loc":
            want = dict((r["key"], r["text"]) for r in rows)
            if len(rows) != len(new["loc"]) or want != new["loc"]:
                out.append("loc: %d lines saved, the generator writes %d, %d differ"
                           % (len(new["loc"]), len(rows),
                              sum(1 for k in want if new["loc"].get(k) != want[k])))
            continue
        name = meta[t][0]
        if not rows and name not in new:
            continue
        if name not in new:
            out.append("%s: not in the saved pack" % name)
            continue
        _ver, got, types = new[name]
        if len(got) != len(rows):
            out.append("%s: %d rows saved, the generator writes %d" % (name, len(got), len(rows)))
            continue
        for i, (g, b) in enumerate(zip(got, rows)):
            skipped.update(c for c in b if c not in g)
            bad = [c for c in b if c in g and not _same(g[c], b[c], types.get(c))]
            if bad:
                out.append("%s row %d differs in %s" % (name, i + 1, ", ".join(bad)))
                break
    names = set(meta[t][0] for t in built if t != "loc")
    out += ["%s: in the saved pack, not in the generator" % t
            for t in sorted(set(new) - names - {"loc"})]
    if skipped:
        print("not stored in the binary, not compared: %s" % ", ".join(sorted(skipped)))
    return out


def selftest():
    import tempfile
    from PIL import Image
    assert sorted(G.RACES) == ["chd", "dwf"], sorted(G.RACES)
    # 1. EVERY TABLE THE PACK SHIPS DECODES - on the copy in data/, so a field type the
    #    decoder does not know fails here and not half way through a release.
    t = pack_tables(LIVE)
    assert len(t) >= 14 and t["loc"] and all(t[k][1] for k in t if k != "loc"), sorted(t)
    # 2. THE SNAPSHOT DIFF CAN SAY NO, and does not object to a row being added.
    name = sorted(k for k in t if k != "loc")[0]
    ver, rows, types = t[name]
    first = dict(rows[0])
    k0 = next(k for k, v in first.items() if isinstance(v, str))
    first[k0] += "_x"
    assert chd_unchanged(t, t) == []
    grown = copy.deepcopy(t)
    grown[name] = (ver, rows + [first], types)
    assert chd_unchanged(t, grown) == [], "an added row was reported"
    moved = copy.deepcopy(t)
    moved[name] = (ver, rows[1:] + [first], types)
    assert chd_unchanged(t, moved), "a changed row was not reported"
    lost = copy.deepcopy(t)
    lost["loc"].pop(sorted(lost["loc"])[0])
    assert chd_unchanged(t, lost), "a lost loc line was not reported"
    # 3. THE GENERATOR COMPARE CAN SAY NO.
    meta = {"x": ("x_tables", 0)}
    built = {"x": [{"key": "a", "n": "2", "c": "555555", "c_hex": "555555"}],
             "loc": [{"key": "k", "text": "v", "tooltip": "false"}]}
    ok = {"x_tables": (0, [{"key": "a", "n": 2, "c": 5592405}], {"c": "ColourRGB"}),
          "loc": {"k": "v"}}
    assert matches_generator(ok, built, meta) == []
    wrong = copy.deepcopy(ok)
    wrong["x_tables"][1][0]["n"] = 3
    assert matches_generator(wrong, built, meta), "a changed cell was not reported"
    short = copy.deepcopy(ok)
    short["x_tables"] = (0, [], {})
    assert matches_generator(short, built, meta), "a short table was not reported"
    extra = copy.deepcopy(ok)
    extra["y_tables"] = (0, [{}], {})
    assert matches_generator(extra, built, meta), "a table nobody generates was not reported"
    # 4. THE CONTRAST LEG CAN SAY NO: a white ground fails, a race with no ground fails.
    with tempfile.TemporaryDirectory() as tmp:
        white = os.path.join(tmp, "white.png")
        Image.new("RGB", (U.PANEL_W, U.PANEL_H), (255, 255, 255)).save(white)
        assert contrast_problems({"chd": [white]}, boxes=(1920,)), "a white ground passed"
    assert contrast_problems({"dwf": []}, boxes=(1920,)), "a race with no ground passed"
    print("selftest ok: %d tables decode; the snapshot diff, the generator compare and "
          "the contrast leg each report a planted fault" % (len(t) - 1))


def main(argv):
    unknown = set(argv) - {"--pack", "--selftest"}
    if unknown:
        sys.stderr.write("REFUSING: unknown argument(s) %s\n" % " ".join(sorted(unknown)))
        return 2
    if "--selftest" in argv:
        selftest()
        return 0
    problems = fit_problems() + contrast_problems()
    if "--pack" in argv:
        new = pack_tables(DEP.OUT)
        problems += matches_generator(new)
        snap = find_snapshot()
        if snap:
            print("snapshot  %s" % snap)
            problems += chd_unchanged(pack_tables(snap), new)
        else:
            problems.append("no F4C63911 snapshot (MD5 %s) under Modding Files/Backup"
                            % SNAPSHOT_MD5)
    for p in problems:
        sys.stderr.write("FAIL %s\n" % p)
    print("%d finding(s)" % len(problems))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```

- [ ] **Step 2: Its selftest.**

Run: `py tools\check_ic_release.py --selftest`
Expected: `selftest ok: 13 tables decode; the snapshot diff, the generator compare and the contrast leg each report a planted fault` (13 or more: phase 2 may add a table). An `AssertionError: ['chd']` means `gen_iron_court.RACES` lacks `dwf`: phase 2 is not done.

- [ ] **Step 3: The ribbons are phase 3's gate; prove it is there.**

Run: `Select-String -Path tools\gen_ic_ui.py -Pattern 'ribbon' | Select-Object -First 8`
Expected: a check function that measures the label ink against the blue and the gold Dwarf tab ribbons at 4.5:1 (spec section 10), called from `check()` or `main()`. If there is none: STOP and tell the author "phase 3 shipped no contrast check for the Dwarf tab ribbons"; do not invent the ink colour here.

- [ ] **Step 4: Run the existing gates, then the matrix.**

```powershell
py tools\gen_ic_ui.py --check; py tools\gen_ic_ui.py --selftest; py tools\make_ic_backdrop.py --check
py tools\check_ic_release.py
```
Expected: `gen_ic_ui.py --check` ends `ok: N files, M components`; `--selftest` ends ok; `make_ic_backdrop.py --check` prints no `PROBLEM:`; `check_ic_release.py` prints six `fit` lines each `0 finding(s)`, six `contrast` lines (chd and dwf at 1600, 1920, 2560) and `0 finding(s)`.
Fixes, by finding:
- `KeyError: 'ic_off_title'` (or another Chaos Dwarf-only cell) out of `B.contrast`: `make_ic_backdrop.text_cells` names a cell the Dwarf layout has not got. In `text_cells`, replace `+ ("ic_off_title",)` with `+ tuple(n for n in ("ic_off_title",) if n in G.PANEL_LAYOUT)`; the Chaos Dwarf list is unchanged by it (its layout has the cell).
- `contrast dwf: 0 panel-sized grounds`: the Dwarf backdrop is not in `art_paths()` (and `write_plates()` will prune it) or is not 1920x1080. Fix in phase 3's code, never by naming the file here.
- `contrast <race> at WxH: <cell> reads X:1`: dim that race's ground to the largest hundredth that clears 4.5:1 on every cell at all three screens (the rule `make_ic_backdrop.DIM` documents), regenerate, re-run.
- `fit <race> at <bw>: ...` (20k text fit or a crossing): the per-cell small-end corrections in `gen_ic_ui.py` (the block beginning `# PER-CELL CORRECTIONS AT THE SMALL END`) or a wider cell; never a font below CA's sizes. Then sync the Lua's mirrored `ICUI.PANEL_XY` entries and let the importer's comparison (inside the deploy) confirm.
After any fix: Step 4 again, the harness, and Task 4's previews are drawn after it.

- [ ] **Step 5: Checkpoint.** Every gate in Global Constraints, green.

---

### Task 4: The full preview set, approved by the author

**Files:**
- Create: `Modding Files/source/iron_court_preview/release_sheet.py`, and its two pictures `release_sheet_chd.png`, `release_sheet_dwf.png` beside it (not packed, not synced)

**Interfaces:**
- Consumes: `tools/preview_iron_court.py` (every view at 1600, 1920, 2560, drawn from the shipped Lua; phase 3 made it draw the Dwarf court, demo faction Karak Kadrin).
- Produces: the author's approval, quoted in the handoff (Task 8).

- [ ] **Step 1: Render.**

Run: `py tools\preview_iron_court.py --selftest; py tools\preview_iron_court.py`
Expected: `selftest ok: ...`; then one `wrote ...png` line per view per size, no `PROBLEM:` and no `art not found` line.

Run: `Get-ChildItem .skilltree_cache\ui_preview\ic_*.png | Where-Object Name -match 'dwf' | Measure-Object | Select-Object Count`
Expected: a count AT LEAST the Chaos Dwarf set's (every view at every size; the Dwarf set also draws the Record and Help tabs, so 39 against 33 at phase 3's count). Zero: STOP, tell the author phase 3's preview draws no Dwarf court.

- [ ] **Step 2: Two contact sheets at 1920,** one per race, so the author can see every tab at once. Write `Modding Files/source/iron_court_preview/release_sheet.py`:

```python
"""Every 1920 Iron Court preview on one sheet per race, for the author's release review.

    py "Modding Files/source/iron_court_preview/release_sheet.py"
"""
import glob
import os
import re

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
SRC = os.path.join(ROOT, ".skilltree_cache", "ui_preview")
HERE = os.path.dirname(os.path.abspath(__file__))
W, H, COLS = 640, 360, 3

for race in ("chd", "dwf"):
    files = [p for p in sorted(glob.glob(os.path.join(SRC, "ic_*.png")))
             if not re.search(r"_(1600|2560)\.png$", p)
             and ("dwf" in os.path.basename(p)) == (race == "dwf")
             and not os.path.basename(p).startswith("ic_selftest")]
    rows = (len(files) + COLS - 1) // COLS
    sheet = Image.new("RGB", (COLS * W, rows * (H + 20)), (16, 16, 16))
    draw = ImageDraw.Draw(sheet)
    for i, p in enumerate(files):
        x, y = (i % COLS) * W, (i // COLS) * (H + 20)
        sheet.paste(Image.open(p).convert("RGB").resize((W, H), Image.LANCZOS), (x, y + 20))
        draw.text((x + 4, y + 4), os.path.basename(p), fill=(255, 248, 215))
    out = os.path.join(HERE, "release_sheet_%s.png" % race)
    sheet.save(out)
    print("wrote %s (%d views)" % (out, len(files)))
```

Run: `py "Modding Files\source\iron_court_preview\release_sheet.py"`
Expected: `wrote ...release_sheet_chd.png (V views)` and `wrote ...release_sheet_dwf.png (V views)`, the same V.

- [ ] **Step 3: Look first.** Open both sheets and every Dwarf picture at 1600 and 2560 with the Read tool. Fix anything a numeric check could not see (dead space, a bad wrap, a Chaos Dwarf word or picture on a Dwarf tab, art stretched rather than tiled) before showing; after a fix, Task 3 Step 4 and this task again.

- [ ] **Step 4: Show the author and wait.** Reply with the two sheet paths and the folder `.skilltree_cache\ui_preview\`, one line per view of what it shows, and ask: "Approve the Dwarf and Chaos Dwarf previews for release?" Do not build until the author approves. Each change asked for goes back through Task 3 Step 4 and this task.

---

### Task 5: Build, deploy and read the saved pack back

**Files:**
- Possibly modify: `tools/deploy_iron_court.py` (`SCRIPTS`, Step 1)
- Output: `Modding Files/Modpacks/derpy_iron_court.pack`, the game's `data/derpy_iron_court.pack`, a backup under `Modding Files/Backup/deployed_auto/`

**Interfaces:**
- Consumes: `check_ic_release.py --pack` (Task 3).
- Produces: `$BUILD` (the pack MD5's first eight characters), its full MD5 and byte size, the backup path; Tasks 6-9 quote them.

- [ ] **Step 1: The Dwarf file is in every list that ships or checks it.**

Run: `py -c "import sys; sys.path.insert(0, 'tools'); import import_iron_court as V, deploy_iron_court as D; n = 'zzz_derpy_iron_court_dwarf.lua'; print('import', any(n in s for s in V.SCRIPTS)); print('deploy', any(n in d for _s, d in D.SCRIPTS)); print('harness', n in open('tools/_iron_court_harness.lua', encoding='utf-8').read())"`
Expected: `import True`, `deploy True`, `harness True`. If `deploy False`, add after the model's tuple in `SCRIPTS`:

```python
    ("Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_dwarf.lua",
     "script/campaign/mod/zzz_derpy_iron_court_dwarf.lua"),
```
Any other False: STOP, phase 2 did not finish wiring the file; tell the author.

- [ ] **Step 2: RPFM and the game.**

Run: `Invoke-WebRequest http://127.0.0.1:45127/sessions -TimeoutSec 4 -UseBasicParsing | Select-Object StatusCode`
Expected: `200`. Connection refused: RPFM is closed; say so and stop.
Run: `[bool](Get-Process -Name Warhammer3 -ErrorAction SilentlyContinue)`
Expected: `False` (else Step 3 uses `--wait`).

- [ ] **Step 3: Build and deploy.**

Run (game shut): `py tools\deploy_iron_court.py`
Run (game up, with `run_in_background: true`): `py tools\deploy_iron_court.py --wait`
Expected: `gates green`, one line per table and file, `saved ...derpy_iron_court.pack (B bytes)`, `verified F file(s) in the saved pack`, `backed up the live pack to ...Modding Files\Backup\deployed_auto\derpy_iron_court.pack.bak_pre_auto_...`, `deployed ... byte-identical to the build`.

- [ ] **Step 4: Name the build.**

```powershell
$h = (Get-FileHash -Algorithm MD5 "Modding Files\Modpacks\derpy_iron_court.pack").Hash
$BUILD = $h.Substring(0, 8); $D = Get-Date -Format yyyyMMdd
"$BUILD $h $((Get-Item 'Modding Files\Modpacks\derpy_iron_court.pack').Length)"
(Get-FileHash -Algorithm MD5 "F:\SteamLibrary\steamapps\common\Total War WARHAMMER III\data\derpy_iron_court.pack").Hash -eq $h
```
Expected: the build line, then `True`. Record `$BUILD`, `$h`, the size, `$D`.

- [ ] **Step 5: What the pack holds is what was staged.**

Run: `py -c "import sys; sys.path.insert(0, 'tools'); import read_pack_index as P, deploy_iron_court as D; ps = P.paths(D.OUT); print(len(ps), 'paths;', [p for p in ps if p != p.lower()]); print('lua differs:', [d for s, d in D.SCRIPTS if [x for x in P.read(D.OUT, d) if x[0] == d][0][2] != open(s, 'rb').read()])"`
Expected: `F paths; []` (no upper case: the 6.1 rule) and `lua differs: []`.

- [ ] **Step 6: Every table read back, and the Chaos Dwarf rows unmoved.**

Run: `py tools\check_ic_release.py --pack`
Expected: the six fit and six contrast lines, `not stored in the binary, not compared:` followed by the eight `*_colour_hex` columns, `snapshot  ...Modding Files\Backup\...derpy_iron_court.pack.bak_pre_auto_...`, and `0 finding(s)`.
- `no F4C63911 snapshot`: STOP and ask the author; never reconstruct it.
- `<table>: changed or gone` or `loc <key>: ... became ...`: a Chaos Dwarf row moved. Find which phase changed it (`Select-String` the key in `tools\gen_iron_court.py` and the court Lua), put it back, rebuild from Step 3. An intended change needs the author's word, quoted in the handoff.
- `<table>: N rows saved, the generator writes M` or `row K differs`: the pack is stale against the generator; rebuild from Step 3, never edit the pack.

- [ ] **Step 7: Effects read back.**

Run: `py tools\check_effect_bundle_loc.py "G:\Modding for resources\Modding Files\Modpacks\derpy_iron_court.pack"`
Expected: 0 findings, and a bundle count above F4C63911's 73.
Run: `py tools\check_effect_signs.py "G:\Modding for resources\Modding Files\Modpacks\derpy_iron_court.pack" derpy_ic`
Expected: exit 0 (a review report). Read every `_dwf_` row it prints against the office, law or government text that grants it; the deliberate maluses (spec section 7, one per law option) are expected, any other is a sign fault to fix in `gen_iron_court.py` and rebuild.

---

### Task 6: The in-game checklist

**Files:**
- Create: `docs/sessions/HANDOFF_<$D>_IRON_COURT_DWARFS_RELEASE.md` (section 7 now; Task 8 writes the rest)

**Interfaces:**
- Consumes: `$BUILD`, `$D` (Task 5); the Dwarf start governments as shipped.
- Produces: the checklist the author ticks; its unticked items are the release's open list.

- [ ] **Step 1: Read the shipped start governments.**

Run: `Select-String -Path "Modding Files\pack\script\campaign\mod\zzz_derpy_iron_court_dwarf.lua" -Pattern 'wh_main_dwf_karak_kadrin|wh_main_dwf_karak_izor'`
Expected: `"legion"` for Karak Kadrin and `"chain"` for Clan Angrund (spec section 3). If phase 2 shipped others, write those governments' names in the list below.

- [ ] **Step 2: Write section 7 of the handoff** with exactly this content (the government names per Step 1):

```markdown
## 7. In-game checklist (build $BUILD) - tick each, note what you saw

Settings: MCT on, Default difficulty, UI scale 100%. Check the opener at 1600x900,
1920x1080 and 2560x1440 (Options > Graphics > resolution).

**A. Dwarfs, Karak Kadrin (Ungrim Ironfist), Immortal Empires**
- [ ] Turn 1: the court button sits on the Dwarf top bar beside the Book of Grudges bar, not over it, at all three resolutions.
- [ ] The panel opens in the Book of Grudges look: blue ribbon tabs, the open tab gold, red-ink knotwork card frames, the dimmed Dwarf backdrop. No Hell-Forge art anywhere.
- [ ] Title reads "The Council of Karak Kadrin". The throne plate reads "The Throne of Karak Kadrin" over Ungrim's name, and the words fit the plate.
- [ ] Offices tab: the Great Hall, two wings of seats facing the throne, no ziggurat; 2/4/4/4 seats; Fill Empty Seats under the doors.
- [ ] Court tab: the government is The War-King. Every party, office, law and move name is a Dwarf one; no Chaos Dwarf word on any tab, tooltip or message.
- [ ] Laws tab: Craft, Tribute, Ancestors, War, each starting on its first law.
- [ ] A grudge written: use Cast Out the Clan on a party. Its loyalty breakdown gains a line "Grudge: Cast Out, turn N" costing 1 a turn; the Record logs it written.
- [ ] Settled by weregild: Pay the Weregild on that party. Gold is spent, the grudge line leaves the breakdown, loyalty rises a little, the Record logs it settled.
- [ ] Kin of the Karak: every party's breakdown shows +1 a turn.
- [ ] Secession countdown: push one party to the bottom of its loyalty after turn 10. Its countdown shows 8 turns (a Chaos Dwarf party shows 5 on Default).
- [ ] The Book: once you have met a few factions, the Court tab shows "The Book names:" with three factions and their figures.
- [ ] A Book band firing: the turn a named faction's figure passes 500, its attitude toward you drops (diplomacy screen, its attitude breakdown, before and after). It does not drop again the next turn.
- [ ] Save, quit to menu, load: grudges, the Book list and the court are as they were; no band fires again on the first turn after the load.

**B. Dwarfs, Clan Angrund (Belegar Ironhammer)**
- [ ] The court opens with Clan Angrund's own title and throne caption; the government is The Iron Law.
- [ ] Swear on the Ancestors, Oath on the Anvil and Stand His Patron each cost a third less than in Karak Kadrin.

**C. Chaos Dwarfs (any Chaos Dwarf lord)**
- [ ] The court looks exactly as before this release: Hell-Forge tabs, the ziggurat, the court's own backdrop. No Dwarf word, picture or rule anywhere; no grudge lines; no "The Book names:".
- [ ] The MCT page has a "Dwarf courts" switch. Turn it off mid-campaign and end turn: nothing in your own court changes.

**D. The throne caption on a minor faction**
- [ ] With a mod that makes Dwarf minor factions playable, start as Barak Varr or Zhufbar: the throne plate reads "The Throne of" that faction over its leader's name and fits. Without such a mod, mark this "not checked".
```

---

### Task 7: Patch notes

**Files:**
- Create: `docs/sessions/PATCH_NOTES_<$D>_IRON_COURT_DWARFS.md`

**Interfaces:**
- Consumes: `$BUILD`, `$D`; the phase 2-5 handoffs' records of what was dropped.
- Produces: the Steam change note; Task 9's CHANGELOG reuses its lines.

- [ ] **Step 1: What was dropped.**

Run: `Select-String -Path docs\sessions\HANDOFF_202610*_IRON_COURT*.md -Pattern 'dropped|not built|out of scope|withdrawn' | Select-Object Filename, LineNumber, Line`
Expected: each feature a phase dropped (an unverified deed, a rebel faction, an effect). Remove its line from Step 2's block; add nothing a phase did not build.

- [ ] **Step 2: Write the file:**

````markdown
# Patch note draft - `derpy_iron_court` ($D)

Copy the fenced block below into the Steam change-note box. No emoji.

**Copy from the code block, not a rendered preview.** A Markdown preview reads the asterisks in
`[*]` as emphasis and drops them, and Steam then draws no bullets.

Covers build $BUILD against F4C63911, the last build pushed to GitHub before the Dwarf work
(phases 1-5 were each deployed to the author's install and never released). The Iron Court is
not on the Workshop yet; if this goes up as its first Workshop release, these lines belong in
the description instead. The detail is in `HANDOFF_$D_IRON_COURT_DWARFS_RELEASE.md`.

```text
[list]
[*]Dwarf factions now get an Iron Court
[*]Nine Dwarf parties, from the Throne-Sworn to the Hearth Clans
[*]Fourteen Dwarf offices in the Great Hall, in two wings facing the throne
[*]The throne shows your faction leader
[*]Six Dwarf governments, and each Dwarf faction starts under its own
[*]The Iron Law: oaths cost a third less, a broken oath costs more loyalty
[*]Dwarf laws: Craft, Tribute, Ancestors and War
[*]Dwarf intrigue moves, including Drive Him to the Slayer Oath
[*]Grudges: a wronged party holds a grudge, -1 loyalty a turn each, up to 4
[*]Pay the Weregild settles a party's oldest grudge
[*]Giving a party's man an office it claims settles one grudge
[*]Kin of the Karak: +1 loyalty a turn for every party, and parties take longer to leave
[*]The Court tab shows the three factions the Book of Grudges names most
[*]Relations with a faction worsen as its grudges pass 500, 1,000 and 2,000
[*]Peace, trade or alliance with a faction the Book names above 1,000 angers the Clan Warriors and the Ancestor Priesthood
[*]Settling a grudge from the Book pleases the Clan Warriors and the Ancestor Priesthood
[*]Dwarf courts wear the Book of Grudges look
[*]Dwarf rebels rise when a Dwarf party breaks away
[*]Other Dwarf factions run courts of their own
[*]New MCT setting: Dwarf courts, on or off at any time
[*]Chaos Dwarf courts unchanged
[/list]
```
````

(Replace `$D` and `$BUILD` with Task 5's values when writing.)

- [ ] **Step 3: Read it as a player.** No emoji, no "rung", no "standing", "cap", "AI", "accrue"; one phrase per line; one flat list. Run: `Select-String -Path "docs\sessions\PATCH_NOTES_$D_IRON_COURT_DWARFS.md" -Pattern '\bAI\b|standing|\bcap\b|accrue|rung' -CaseSensitive:$false`
Expected: no output.

---

### Task 8: Docs

**Files:**
- Modify: `docs/sessions/HANDOFF_<$D>_IRON_COURT_DWARFS_RELEASE.md` (sections 1-6 and 8), `docs/SESSION_INDEX.md` (one line at the end), `docs/MY_MODS.md` (the `derpy_iron_court.pack` row)

**Interfaces:**
- Consumes: every number recorded in Tasks 1-7.
- Produces: the current-handoff pointer for the Iron Court.

- [ ] **Step 1: The handoff, sections 1-6 and 8** (section 7 is Task 6's):
  1. **What shipped**: build `$BUILD`, MD5 `$h`, size, in data/ and Modpacks (same MD5), the backup path Task 5 Step 3 printed; "not pushed" until Task 9 says otherwise; no Workshop entry.
  2. **Gates**: harness `N0 + 3` checks (the two fifty-turn scenarios and the switch-off, by name); `check_lua_api`, literal-left, `gen_ic_ui --check`/`--selftest`, `gen_iron_court --check`, the deploy's own gates.
  3. **Mutation run**: M mutants, 0 unexplained; the seven "both races" mutants and what caught each; every survivor and its outcome (assertion added and seen catching, re-aimed, or deleted with the author's word); the hash comparison clean.
  4. **Fit and contrast**: the twelve matrix lines from `check_ic_release.py`, the worst cell per race per screen, any dim or cell change made, and the ribbon check phase 3 owns.
  5. **The saved pack**: per table, rows saved = rows generated (paste the counts); the snapshot path; "every F4C63911 row and loc line unchanged"; `check_effect_bundle_loc` and `check_effect_signs` results; 0 upper-case paths; the staged Lua byte-identical.
  6. **Previews**: the two sheet paths and the author's approving words, quoted.
  8. **Open**: the in-game checklist's unticked items; the Workshop upload (the author's separate decision; after a first publish the data/ copy moves to `Modding Files\Backup\` or the game sees two packs); custom Dwarf rebel crests and the Age of Reckoning score (spec section 12, out of scope); everything still open in the UI_POLISH handoff section 1 and section 6.

- [ ] **Step 2: One line at the end of `docs/SESSION_INDEX.md`:**

```markdown
`sessions/HANDOFF_$D_IRON_COURT_DWARFS_RELEASE.md` - **Iron Court for Dwarfs, phase 6 release pass: build `$BUILD` in data/ (Modpacks same MD5), harness N checks, M mutants 0 unexplained, both races fit and contrast at 1600/1920/2560, every F4C63911 Chaos Dwarf row byte-identical, previews approved, not pushed**: two fifty-turn both-races scenarios and the Dwarf-courts switch-off in the harness; `tools/check_ic_release.py` reads the saved pack back with RPFM shut; in-game checklist in section 7; patch notes `PATCH_NOTES_$D_IRON_COURT_DWARFS.md`; Workshop upload not done.
```
(Numbers and `$D`/`$BUILD` filled in; "not pushed" becomes "pushed as <hash>" in Task 9 Step 7.)

- [ ] **Step 3: `docs/MY_MODS.md`.** In the `derpy_iron_court.pack` row: the build and date become `$BUILD ($D)`; the size from Task 5; "A Rome 2-style court for Chaos Dwarf factions" becomes "A Rome 2-style court for Chaos Dwarf and Dwarf factions"; after the court's feature list add the sentence "Dwarf courts (2026-10, spec `superpowers/specs/2026-10-04-iron-court-dwarfs-design.md`): Dwarf parties, offices in the Great Hall (2/4/4/4 round a throne), governments, laws and moves, grudges inside the court settled by weregild, kinship, the Book of Grudges naming factions and souring relations at 500/1,000/2,000, the Book of Grudges skin, MCT switch \"Dwarf courts\"."; "Four campaign scripts" becomes "Five campaign scripts"; the table, bundle, trait and loc counts from Task 5 Step 6's read-back; "974 checks" and "1,097 mutants" become N and M; "Current handoff" becomes `sessions/HANDOFF_$D_IRON_COURT_DWARFS_RELEASE.md`.

---

### Task 9: The public repo (outward-facing: wait for the author)

**Files:**
- Modify: `tools/sync_iron_court_repo.py` (manifest), then inside `repos/derpy-iron-court/`: `CHANGELOG.md`, `README.md` (a "Dwarf courts" section), `docs/DEVELOPMENT.md` (counts), and the synced copies

**Interfaces:**
- Consumes: Task 5's build, Task 7's lines, Task 8's handoff.
- Produces: the commits; the push only on the author's word.

- [ ] **Step 1: The manifest.** In `tools/sync_iron_court_repo.py`:
  (a) add `import glob` to the imports;
  (b) in `manifest()`'s `same` list, after `_MOD + "zzz_derpy_iron_court.lua",`, add `_MOD + "zzz_derpy_iron_court_dwarf.lua",` unless phase 2 already did (`Select-String -Path tools\sync_iron_court_repo.py -Pattern 'iron_court_dwarf'`);
  (c) in the `tools/` tuple, after `"mutate_iron_court.py",`, add `"check_ic_release.py",`, and after `"read_vanilla_loc.py",` add `"read_vanilla_db.py",` (the release gate imports it);
  (d) directly after the `_DOCS = [...] + [...]` assignment, add:

```python
# THE DWARF WORK'S DOCS, found rather than typed (plan 2026-10-04 phase 6): six phase
# plans and their handoffs, named by whoever wrote each. Every October court handoff
# matches, the ones listed above too, so the list is de-duplicated in order.
def _dated(folder, pattern):
    return sorted(os.path.relpath(p, ROOT).replace(os.sep, "/")
                  for p in glob.glob(os.path.join(ROOT, folder, pattern)))


_DOCS += [("docs/superpowers/specs/2026-10-04-iron-court-dwarfs-design.md", "docs/design/")]
_DOCS += [(p, "docs/plans/") for p in _dated("docs/superpowers/plans",
                                              "2026-10-04-iron-court-dwarfs-*.md")]
_DOCS += [(p, "docs/history/") for p in _dated("docs/sessions", "HANDOFF_202610*_IRON_COURT*.md")]
_DOCS = list(dict.fromkeys(_DOCS))
```

- [ ] **Step 2: Selftest and sync.**

Run: `py tools\sync_iron_court_repo.py --selftest`
Expected: `selftest ok: N files, nothing of CA's` (N larger than before by the Dwarf Lua, two tools and the Dwarf docs).
Run: `py tools\sync_iron_court_repo.py; py tools\sync_iron_court_repo.py --check`
Expected: a list of copied files, `synced K file(s) into ...repos\derpy-iron-court`, then `0 file(s) drift`.

- [ ] **Step 3: The repo's own files.**
  - `CHANGELOG.md`, a new entry at the top, under the intro paragraph:

```markdown
## $D - build $BUILD

Deployed $D. MD5 `$h`, B bytes. Covers the Dwarf work's phase builds since F4C63911. The
detail is in `docs/history/HANDOFF_$D_IRON_COURT_DWARFS_RELEASE.md`; the design in
`docs/design/2026-10-04-iron-court-dwarfs-design.md`. Not yet seen in game.

- **Dwarf factions get an Iron Court** in the same pack: Dwarf parties, offices, governments,
  laws, moves, names and art. The Chaos Dwarf court is unchanged, row for row.
- **Grudges inside the court**, -1 loyalty a turn each, up to 4 a party; Pay the Weregild settles one.
- **Kin of the Karak**: +1 loyalty a turn for every party; secession countdowns 1.5 times as long.
- **The Book of Grudges**: the Court tab names the top three factions; relations sour once
  per band at 500, 1,000 and 2,000.
- **Seats in the Great Hall** round the faction leader's throne, in CA's Book of Grudges look.
- **MCT switch "Dwarf courts"**, live.
- Tests: two fifty-turn both-races scenarios and the switch-off in the harness;
  `tools/check_ic_release.py`, the release gate (both races at three screens, the saved pack
  read back with RPFM shut).
```
  - `README.md`: a "Dwarf courts" section after the last feature section, four sentences: which factions (every Dwarf faction, race taken from the subculture); what differs (names, effects, art, the Great Hall, kinship); grudges and weregild; the Book of Grudges bands; the MCT switch.
  - `docs/DEVELOPMENT.md`: harness and mutant counts to N and M; the Dwarf Lua in the file list; `check_ic_release.py` in the tool list with its three commands.

- [ ] **Step 4: Nothing of CA's is staged.**

Run: `git -C repos/derpy-iron-court add -A; git -C repos/derpy-iron-court diff --cached --name-only | Select-String '\.(png|dds|jpg|pack|bin|loc|wem)$|factions\.tsv'`
Expected: no output. Then `git -C repos/derpy-iron-court status --short` and read the list.

- [ ] **Step 5: Ask.** Tell the author: the staged file count, the CHANGELOG entry, the commit message below, and that the push goes to `origin main` as every build before it did; ask "Commit and push the Dwarf release to GitHub?" Stop until the author says yes. A no leaves the files staged and the handoff says "not pushed".

- [ ] **Step 6: On the author's yes, commit and push.**

```powershell
git -C repos/derpy-iron-court commit -m "Build $BUILD: Iron Court for Dwarfs (phases 1-6 since F4C63911)" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
git -C repos/derpy-iron-court push origin main
git -C repos/derpy-iron-court log -1 --format=%h
```
Expected: the commit line, the push to `main`, a short hash.

- [ ] **Step 7: Record the push** (the same pattern as 4440021): the handoff's section 1 and its SESSION_INDEX line say "pushed as <hash>"; then

```powershell
py tools\sync_iron_court_repo.py; git -C repos/derpy-iron-court add -A
git -C repos/derpy-iron-court commit -m "History: record the push of build $BUILD" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
git -C repos/derpy-iron-court push origin main
py tools\sync_iron_court_repo.py --check
```
Expected: the second commit pushed, `0 file(s) drift`. The author's yes in Step 5 covers both commits of this release; say so when asking.
