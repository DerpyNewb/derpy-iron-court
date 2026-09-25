# Iron Court Ambition Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give every Iron Court character a persistent ambition band and make personal standing
contribute a scaled, ambition-modified amount to the character's party influence.

**Architecture:** Ambition is model state keyed by character CQI and mirrored by a visible marker
trait. Party member weight is derived live from living faction characters; it is never folded into
saved house weight. Existing share consumers are moved to faction-aware weight functions so
control, secession, the dial and tooltips all use the same arithmetic.

**Tech Stack:** Lua 5.1.5 campaign scripting, Python 3 generators/checkers, RPFM MCP pack builder,
Total War: WARHAMMER III.

**Spec:** `docs/superpowers/specs/2026-09-20-iron-court-ambition-design.md`

## Global Constraints

- The workspace root is not a Git repository. Do not create commits, branches or worktrees.
- Maintained Lua is `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court.lua` and
  `zzz_derpy_iron_court_ui.lua`; the `.pack` is generated output.
- DB fragments and `.loc` files are binary. Change `tools/gen_iron_court.py`, regenerate TSVs,
  and let `tools/deploy_iron_court.py` import them through RPFM.
- Lua is 5.1.5. Do not use later-language syntax or `math.random`.
- `cm:random_number(max, min)` takes maximum first and is the multiplayer-safe RNG.
- Add the ambition save data as pipe field 8. Do not alter the seven existing field positions or
  the fifteen fields inside each house record.
- Missing ambition is neutral at 100% until stamped; it must never make a member worth zero.
- `house.weight` remains saved office/plot weight. Member weight is derived and never accumulated.
- Do not add a TWUI component, image asset, gameplay effect row, new dependency or ambition reroll.
- Do not deploy over the enabled game copy until every offline gate and a `--no-copy` build pass.
- Before each review checkpoint, copy changed text files to
  `.superpowers/sdd/iron-court-ambition/taskNN/`; these snapshots replace commits in this workspace.

## File Structure

| File | Responsibility |
|---|---|
| Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court.lua` | Ambition state, rolling, stamping, persistence, pruning and member-weight arithmetic. |
| Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_ui.lua` | Faction-aware share calls and standing-plate tooltip. |
| Modify: `tools/gen_iron_court.py` | Three marker traits and their localisation; generator checks. |
| Modify: `tools/import_iron_court.py` | Generator/model ambition-key parity and authoritative pack gates. |
| Modify: `tools/_iron_court_harness.lua` | Runtime model, migration, arithmetic and UI checks against shipped Lua. |
| Modify: `tools/mutate_iron_court.py` | Mutants proving the new checks detect plausible regressions. |
| Generated: `Modding Files/source/iron_court/{character_traits,character_trait_levels,trait_info,loc}.tsv` | Generator-owned DB and localisation inputs. |
| Generated: `Modding Files/Modpacks/derpy_iron_court.pack` | Verified build output. |
| Modify after verification: `docs/IRON_COURT_VS_ROME2.md` | Mark section 2.7 built and record the implemented formula. |
| Create after verification: `docs/sessions/HANDOFF_20260920_IRON_COURT_AMBITION.md` | Decisions, changed files, evidence and remaining edict work. |
| Modify after verification: `docs/SESSION_INDEX.md` | One concise handoff entry. |

---

### Task 1: Persistent ambition and trait reconciliation

**Files:**
- Modify: `tools/_iron_court_harness.lua:71-180, 1387-1427`
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court.lua:640-744, 1046-1072, 1439-1660, 2079-2140, 2396-2430, 2894-2915`

**Interfaces:**
- Consumes: `cm:random_number(max, min)`, character CQI/traits, existing packed fields 1-7.
- Produces: `IC.AMBITION_ORDER`, `IC.AMBITION`, `IC.roll_ambition()`,
  `IC.ambition_slug(faction_key, cqi)`, `IC.ambition_factor(faction_key, cqi)`, and
  `IC.stamp_ambition(faction_key, character)`.

- [ ] **Step 1: Extend the harness fixtures without changing model behavior**

Keep `make_character`'s `_traits` table as the source read by `has_trait`. Use the existing
`rng({...})` sequence helper and trait add/remove stubs. Add this small helper beside `endow`:

```lua
local function ambition_traits(character)
    local out = {}
    for _, slug in ipairs(IC.AMBITION_ORDER or {}) do
        local key = "derpy_ic_ambition_" .. slug
        if character:has_trait(key) then out[#out + 1] = key end
    end
    return out
end
```

- [ ] **Step 2: Add failing roll, one-time stamp and reconciliation checks**

Place the checks after the existing court-stamping checks:

```lua
check("ambition uses the 25 50 25 roll bands", function()
    IC.state = {}
    local a = make_character(701, ANY_SEAT, "forge")
    local b = make_character(702, ANY_SEAT, "forge")
    local c = make_character(703, ANY_SEAT, "forge")
    make_faction(F, IC.CHD_SUBCULTURE, {a, b, c}, {})
    IC.add_house(F, "forge")
    rng({25, 26, 76})
    IC.stamp_court(F)
    assert(IC.ambition_slug(F, 701) == "cautious")
    assert(IC.ambition_slug(F, 702) == "steady")
    assert(IC.ambition_slug(F, 703) == "ambitious")
end)

check("saved ambition never rerolls and repairs its marker trait", function()
    IC.state = {}
    local a = make_character(704, ANY_SEAT, "forge")
    make_faction(F, IC.CHD_SUBCULTURE, {a}, {})
    IC.add_house(F, "forge")
    IC.court(F).ambition[704] = "ambitious"
    a._traits["derpy_ic_ambition_cautious"] = true
    rng({1})
    IC.stamp_court(F)
    assert(IC.ambition_slug(F, 704) == "ambitious")
    local worn = ambition_traits(a)
    assert(#worn == 1 and worn[1] == "derpy_ic_ambition_ambitious")
end)
```

- [ ] **Step 3: Add failing persistence and migration checks**

Extend the populated round-trip fixture with two ambition entries and assert both return. Add a
separate old-save check:

```lua
check("a seven-field court loads with neutral unstamped ambition", function()
    IC.state = {}
    local old = "forge,10,55,0,0,0,0,0,0,0,0,0,0,0,0||||||"
    IC.unpack(F, old)
    assert(next(IC.court(F).ambition) == nil)
    assert(IC.ambition_factor(F, 77) == 100)
end)
```

Also unpack `"...|||||||77,nosuchband"` and assert the unknown slug is discarded.

- [ ] **Step 4: Run the harness and confirm the new checks fail**

Run:

```powershell
& "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua
```

Expected: non-zero with the first new failure naming a missing ambition table or function. A parse
failure is not the expected failure.

- [ ] **Step 5: Add the ambition constants and accessors**

Add beside `IC.TUNE` and the court helpers:

```lua
IC.AMBITION_ORDER = {"cautious", "steady", "ambitious"}
IC.AMBITION = {
    cautious  = {factor = 75,  roll = 25,
                 trait = "derpy_ic_ambition_cautious"},
    steady    = {factor = 100, roll = 50,
                 trait = "derpy_ic_ambition_steady"},
    ambitious = {factor = 125, roll = 25,
                 trait = "derpy_ic_ambition_ambitious"},
}

function IC.ambition_slug(faction_key, cqi)
    if not cqi then return nil end
    local slug = (IC.court(faction_key).ambition or {})[cqi]
    return IC.AMBITION[slug or ""] and slug or nil
end

function IC.ambition_factor(faction_key, cqi)
    local row = IC.AMBITION[IC.ambition_slug(faction_key, cqi) or ""]
    return row and row.factor or 100
end
```

Implement `IC.roll_ambition` as a cumulative walk over `IC.AMBITION_ORDER`. Add a harness check
that sums the three roll weights to 100, requires every factor to be positive, and requires every
declared trait key to equal `derpy_ic_ambition_` plus its slug.

- [ ] **Step 6: Add ambition to court creation, save field 8 and unpack migration**

Add `ambition = {}` to `new_court`. In `IC.pack`, build validated `cqi,slug` entries and append
`join(ambition, ";")` after the province field. In `IC.unpack`, parse `fields[8] or ""`:

```lua
for _, entry in ipairs(split(fields[8] or "", ";")) do
    local bits = split(entry, ",")
    local cqi, slug = tonumber(bits[1]), bits[2]
    if cqi and IC.AMBITION[slug or ""] then court.ambition[cqi] = slug end
end
```

Do not change fields 1-7 or any house record format.

- [ ] **Step 7: Implement one-time stamping and wire every creation path**

Implement `IC.stamp_ambition` exactly from saved state first: roll only when no valid saved slug
exists, remove wrong ambition traits, then silently add the one correct trait. Call it from
`IC.stamp_court` after background stamping and from `IC.hired` after origin/background stamping.
The function returns true if it changed state or traits.

- [ ] **Step 8: Prune ambition with standing**

In `IC.income`, extend the existing living-CQI prune:

```lua
for cqi in pairs(court.ambition or {}) do
    if not alive[cqi] then court.ambition[cqi] = nil end
end
```

Add a harness assertion beside "income prunes the dead out of the save string" that CQI 999 is
removed from both tables while the living CQI remains in both.

- [ ] **Step 9: Run the focused runtime and syntax gates**

Run:

```powershell
& "C:\Program Files (x86)\Lua\5.1\luac.exe" -p "Modding Files\pack\script\campaign\mod\zzz_derpy_iron_court.lua"
& "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua
```

Expected: syntax exit 0 and the full harness summary with zero failures.

- [ ] **Step 10: Save review checkpoint 1**

Create `.superpowers/sdd/iron-court-ambition/task01/` and copy the model and harness there with
`Copy-Item -LiteralPath`. Do not copy or alter the live `.pack`.

---

### Task 2: Generate the three marker traits

**Files:**
- Modify: `tools/gen_iron_court.py:580-590, 1091-1133, 1847-1870, 2300-2306`
- Modify: `tools/import_iron_court.py:461 onward`
- Generated: `Modding Files/source/iron_court/character_traits.tsv`
- Generated: `Modding Files/source/iron_court/character_trait_levels.tsv`
- Generated: `Modding Files/source/iron_court/trait_info.tsv`
- Generated: `Modding Files/source/iron_court/loc.tsv`

**Interfaces:**
- Consumes: the model's three `derpy_ic_ambition_*` keys.
- Produces: one visible, one-level, effectless trait and four loc rows per ambition band.

- [ ] **Step 1: Add failing generator assertions**

In `selftest`, derive `ambition_keys` from a new generator constant and assert every key appears
once in `character_traits`, `character_trait_levels` and `trait_info`, has four loc rows, and has
no entry in a trait-to-effect junction table. Extend the expected trait count by
`len(AMBITION_BANDS)`.

- [ ] **Step 2: Run the generator selftest and confirm failure**

Run:

```powershell
py tools\gen_iron_court.py --selftest
```

Expected: assertion failure because the three ambition traits are not emitted. Do not accept a
cache or schema failure as the expected red result.

- [ ] **Step 3: Define and emit the bands through `emit_trait`**

Add:

```python
AMBITION_BANDS = {
    "cautious": ("Cautious", "His standing carries less weight in the Iron Court.",
                 "His standing contributes 25% less to his party's influence."),
    "steady": ("Steady", "His standing carries its usual weight in the Iron Court.",
               "His standing contributes normally to his party's influence."),
    "ambitious": ("Ambitious", "Every honour becomes another claim on the Iron Court.",
                  "His standing contributes 25% more to his party's influence."),
}
```

After standing-band emission, iterate the literal order `("cautious", "steady", "ambitious")`
and call `emit_trait("derpy_ic_ambition_" + slug, ...)`. Use the explanation as the colour text
and the exact contribution sentence as explanation text; use
`"His ambition does not change."` as removal text.

- [ ] **Step 4: Add generator/model key parity to the importer**

In `tools/import_iron_court.py`, extend the Lua-table cross-check to extract the three trait values
from `IC.AMBITION` and compare them with the generator's `AMBITION_BANDS` keys. A renamed trait in
only one owner must make `py tools/import_iron_court.py` refuse.

- [ ] **Step 5: Regenerate TSVs and run generator gates**

Run:

```powershell
py tools\gen_iron_court.py --selftest
py tools\gen_iron_court.py
py tools\gen_iron_court.py --check
```

Expected: all commands exit 0; the normal generation reports exactly three more traits and twelve
more loc rows than the pre-feature baseline.

- [ ] **Step 6: Run the authoritative import verifier**

Run:

```powershell
py tools\import_iron_court.py
```

Expected: `verify ok`, including Lua syntax, API, undeclared-global, generated-file and full harness
checks.

- [ ] **Step 7: Save review checkpoint 2**

Copy `tools/gen_iron_court.py`, `tools/import_iron_court.py` and the four changed TSVs to
`.superpowers/sdd/iron-court-ambition/task02/`.

---

### Task 3: Add derived member weight and refactor every share consumer

**Files:**
- Modify: `tools/_iron_court_harness.lua:1365-1405, 3297-3340`
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court.lua:640-744, 1308-1331, 3208-3357, 4338-4344`
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_ui.lua:1220-1281, 2343-2398, 2700-2710, 2840-2860`

**Interfaces:**
- Consumes: ambition state and `IC.house_of_character`.
- Produces: `IC.TUNE.ambition_standing_per_weight = 100`,
  `IC.member_weight(faction_key, slug)`, and faction-aware `house_weight`, `total_weight`, `share`.

- [ ] **Step 1: Add failing arithmetic checks**

Add fixtures with three same-party characters at standing 400 and stored factors 75/100/125.
Assert contributions 3, 4 and 5 when measured separately. Add a two-character fractional fixture
at standing 50 that totals 1.0 for two Steady characters rather than rounding each to zero.

Add a court with Crown and Forge and assert:

```lua
local total = IC.share(F, "crown") + IC.share(F, "forge")
assert(math.abs(total - 100) < 0.001)
assert(IC.house_weight(F, "forge") ==
       IC.court(F).houses.forge.weight +
       (IC.court(F).houses.forge.gov_weight or 0) +
       IC.member_weight(F, "forge"))
```

- [ ] **Step 2: Run the harness and confirm signature/arithmetic failure**

Run the Lua harness. Expected: a new check fails because `IC.member_weight` does not exist or the
old `IC.share(court, slug)` signature cannot satisfy the faction-aware assertion.

- [ ] **Step 3: Implement live member weight**

Add `ambition_standing_per_weight = 100` to `IC.TUNE`, then implement:

```lua
function IC.member_weight(faction_key, slug)
    local faction = real_faction(faction_key)
    if not faction or not slug then return 0 end
    local ok_list, list = pcall(function() return faction:character_list() end)
    if not ok_list or not list then return 0 end
    local ok_count, count = pcall(function() return list:num_items() end)
    if not ok_count or not count then return 0 end
    local total = 0
    for i = 0, count - 1 do
        local ok_man, man = pcall(function() return list:item_at(i) end)
        if not ok_man then man = nil end
        local ok_weight, weight = pcall(function()
            if not man or man:is_null_interface()
                    or IC.house_of_character(man, faction_key) ~= slug then
                return 0
            end
            local cqi = man:command_queue_index()
            return IC.standing(faction_key, cqi)
                * IC.ambition_factor(faction_key, cqi) / 100
                / IC.TUNE.ambition_standing_per_weight
        end)
        if ok_weight then total = total + weight end
    end
    return total
end
```

Keep the whole faction-list read safe in the same way neighboring character scans are guarded; a
failed interface read returns zero rather than aborting a turn.

- [ ] **Step 4: Replace the weight/share interfaces atomically**

Implement:

```lua
function IC.house_weight(faction_key, slug)
    local house = IC.court(faction_key).houses[slug or ""]
    if not house then return 0 end
    return house.weight + (house.gov_weight or 0)
        + IC.member_weight(faction_key, slug)
end
```

Make `IC.total_weight(faction_key)` iterate the keyed houses and call the new function. Make
`IC.share(faction_key, slug)` use those two functions. Update every model call, including
`IC.control`, `IC.sufferance`, `IC.defecting_provinces`, `IC.tick_secession` and
`IC.strongest_rival`.

- [ ] **Step 5: Update every UI call site in the same edit**

Change `ICUI.bar_widths` to accept `faction_key`, and pass it from `ICUI.dial_slots`. Add the
faction key to `ICUI.label_crest` and `ICUI.label_share`, then pass the existing local `faction`
from the court draw. Update party cards and secession tooltips to call `IC.share(faction, slug)`.

Run this search and require no old signatures:

```powershell
rg -n "IC\.(share|house_weight|total_weight)\(" "Modding Files\pack\script\campaign\mod" tools\_iron_court_harness.lua -g "zzz_derpy_iron_court*.lua" -g "_iron_court_harness.lua"
```

- [ ] **Step 6: Prove downstream control and secession use ambition**

Add one harness fixture where only a rival's ambition changes, then assert its share rises, Crown
control falls, and `IC.defecting_provinces` never returns fewer provinces after the rise. Do not
duplicate the share formula in the assertion; compare the two model states.

- [ ] **Step 7: Run syntax, harness and importer gates**

Run:

```powershell
& "C:\Program Files (x86)\Lua\5.1\luac.exe" -p "Modding Files\pack\script\campaign\mod\zzz_derpy_iron_court.lua"
& "C:\Program Files (x86)\Lua\5.1\luac.exe" -p "Modding Files\pack\script\campaign\mod\zzz_derpy_iron_court_ui.lua"
& "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua
py tools\import_iron_court.py
```

Expected: all exit 0.

- [ ] **Step 8: Save review checkpoint 3**

Copy the model, UI and harness to `.superpowers/sdd/iron-court-ambition/task03/`.

---

### Task 4: Explain ambition on the existing character standing plate

**Files:**
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_ui.lua:911-985`
- Modify: `tools/_iron_court_harness.lua:2968 onward`

**Interfaces:**
- Consumes: `IC.ambition_slug`, `IC.ambition_factor`, `IC.member_weight` arithmetic scale and the
  generated trait-name loc key.
- Produces: `ICUI.ambition_tip(faction_key, cqi) -> string`.

- [ ] **Step 1: Add a failing tooltip check**

Create a 400-standing Ambitious character, call `ICUI.ambition_tip`, and assert the returned text
contains `Ambitious`, `400`, `1.25` and `5`. Seed localisation so the display name differs from
the slug; this proves the UI resolves the generated name rather than title-casing internal data.

- [ ] **Step 2: Run the harness and confirm the helper is missing**

Run the Lua harness. Expected: failure naming `ICUI.ambition_tip`.

- [ ] **Step 3: Implement the tooltip from model values**

Implement `ICUI.ambition_tip` by reading the saved slug, factor and standing, resolving
`character_trait_levels_onscreen_name_derpy_ic_ambition_<slug>`, and calculating the displayed
contribution with `IC.TUNE.ambition_standing_per_weight`. Format the factor with two decimal places
and the contribution with at most two decimals. Return an empty string when the character is not
in the court or is not yet stamped.

- [ ] **Step 4: Attach it without adding UI components**

In `ICUI.show_standing`, after writing the existing plate text, call
`plate:SetTooltipText(ICUI.ambition_tip(faction, cqi), "", true)` and make the plate interactive
only when the tooltip is non-empty. Preserve the existing visibility and screen-bound guards.

- [ ] **Step 5: Run all offline checks**

Run the harness and `py tools/import_iron_court.py`. Expected: both exit 0 and no generated TWUI
file changes.

- [ ] **Step 6: Save review checkpoint 4**

Copy the UI and harness to `.superpowers/sdd/iron-court-ambition/task04/`.

---

### Task 5: Mutation coverage, pack build and live verification

**Files:**
- Modify: `tools/mutate_iron_court.py:49 onward`
- Modify after successful verification: `docs/IRON_COURT_VS_ROME2.md:139-149`
- Create after successful verification: `docs/sessions/HANDOFF_20260920_IRON_COURT_AMBITION.md`
- Modify after successful verification: `docs/SESSION_INDEX.md`

**Interfaces:**
- Consumes: all ambition model, generator and UI behavior from Tasks 1-4.
- Produces: mutation evidence, an undeployed verified pack, and durable handoff documentation.

- [ ] **Step 1: Add ambition mutants with unique anchors**

Add mutants that make these exact mistakes:

1. Change the Ambitious factor from 125 to 100.
2. Change `ambition_standing_per_weight` from 100 to 1.
3. Roll whenever `stamp_ambition` runs instead of only when state is missing.
4. Omit field 8 from `IC.pack`.
5. Remove the ambition prune from `IC.income`.
6. Stop removing a wrong marker trait before adding the saved marker.
7. Remove `IC.member_weight` from `IC.house_weight`.
8. Reintroduce one old `IC.share(court, slug)` UI call.
9. Recompute the tooltip factor from its text instead of calling the model.

Each `(old, new)` anchor must match exactly once; `py tools/mutate_iron_court.py --selftest` enforces
that property.

- [ ] **Step 2: Run filtered ambition mutation tests**

Run:

```powershell
py tools\mutate_iron_court.py ambition
```

Expected: every ambition mutant is caught and the summary reports `0 unexplained`.

- [ ] **Step 3: Run the complete regression suite**

Run:

```powershell
py tools\gen_iron_court.py --selftest
py tools\gen_iron_court.py --check
py tools\import_iron_court.py
py tools\mutate_iron_court.py --selftest
py tools\mutate_iron_court.py
```

Expected: all commands exit 0; the full mutation run reports zero unexplained survivors or stale
anchors.

- [ ] **Step 4: Build without deploying**

With RPFM open and WARHAMMER III closed, run:

```powershell
py tools\deploy_iron_court.py --no-copy
```

Expected: `gates green`, a saved `Modding Files/Modpacks/derpy_iron_court.pack`, and the saved-pack
index verification succeeding. The game-data copy must remain unchanged.

- [ ] **Step 5: Perform the old-save and new-campaign live checks**

After explicitly copying/deploying the verified pack through the normal deploy command:

1. Load the established Iron Court save and confirm every living courtier gains exactly one
   ambition trait without losing standing, offices, governorships, log entries or province mood.
2. Save, reload and confirm ambition bands do not change.
3. Compare equal-standing characters from different bands and confirm their parties' displayed
   influence moves in the expected direction.
4. Recruit and hire a new character and confirm each receives one band.
5. Kill or lose a disposable character, advance a turn, save and confirm no stale CQI behavior.
6. Read `script_log_*.txt` and `modified.log`; require no Iron Court error and no new crash dump.

- [ ] **Step 6: Update current-truth documentation**

Mark section 2.7 of `docs/IRON_COURT_VS_ROME2.md` built with the exact 75/100/125 factors,
100-standing scale, save field and live evidence. Do not mark section 2.11 built.

Write `docs/sessions/HANDOFF_20260920_IRON_COURT_AMBITION.md` with goal, decisions, changed files,
all command outputs, pack size/hash, live evidence and the remaining Military Doctrine feature.
Add exactly one concise link line to `docs/SESSION_INDEX.md`.

- [ ] **Step 7: Save final review checkpoint**

Copy every changed text source and the two documentation updates to
`.superpowers/sdd/iron-court-ambition/final/`. Record the built pack's byte size and SHA-256 in the
handoff; do not treat pack hashes as reproducible across independent RPFM builds.
