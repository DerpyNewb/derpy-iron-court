# Iron Court Military Doctrine Loyalty Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the vanilla Chaos Dwarf Military Doctrine commandment grant +2 loyalty per turn to
the party of each Iron Court governor actively administering a province under that commandment.

**Architecture:** A small model query reads the active governor's current region through CA's
documented edict API. The existing loyalty-term builder counts qualifying provinces and emits one
aggregated term, preserving the single arithmetic path shared by turn drift and the panel tooltip.
The feature is entirely derived and adds no save or DB state.

**Tech Stack:** Lua 5.1.5 campaign scripting, Python 3 verification/mutation tools, RPFM MCP pack
builder, Total War: WARHAMMER III.

**Spec:** `docs/superpowers/specs/2026-09-20-iron-court-edict-loyalty-design.md`

## Global Constraints

- The workspace root is not a Git repository. Do not create commits, branches or worktrees.
- Maintained model source is
  `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court.lua`; do not edit the `.pack`.
- Use exactly `wh3_dlc23_edict_chd_armaments`, whose vanilla display title is Military Doctrine.
- Do not accept every non-empty edict and do not grant political effects to the other three Chaos
  Dwarf commandments.
- The governor must pass the existing `IC.governor_active` rule. An assignment by itself is not
  sufficient for the edict bonus.
- The beneficiary is the governor's resolved party. Never default the bonus to the Crown.
- The value is +2 per qualifying province with no separate cap.
- `IC.loyalty_terms` remains the common source for both `IC.drift_loyalty` and the UI tooltip.
- No new save field, listener, effect bundle, trait, ancillary, skill, rite, loc row, TWUI component
  or generated art is permitted.
- Do not deploy over the enabled game copy until every offline gate and a `--no-copy` build pass.
- Before each review checkpoint, copy changed text files to
  `.superpowers/sdd/iron-court-edict-loyalty/taskNN/`; these snapshots replace commits.

## File Structure

| File | Responsibility |
|---|---|
| Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court.lua` | Edict key, tuning value, guarded governor-edict query and loyalty term. |
| Modify: `tools/_iron_court_harness.lua` | Region API stub and model/UI parity checks against shipped Lua. |
| Modify: `tools/mutate_iron_court.py` | Mutants for exact key, active gate, party routing, stacking and shared term ownership. |
| Generated: `Modding Files/Modpacks/derpy_iron_court.pack` | Verified build output; no DB shape change. |
| Modify after verification: `docs/IRON_COURT_VS_ROME2.md` | Mark section 2.11 built and remove the superseded DB-work assumption. |
| Create after verification: `docs/sessions/HANDOFF_20260920_IRON_COURT_EDICT_LOYALTY.md` | Decisions, evidence, live result and final parity status. |
| Modify after verification: `docs/SESSION_INDEX.md` | One concise handoff entry. |

---

### Task 1: Expose the documented edict API in the runtime harness

**Files:**
- Modify: `tools/_iron_court_harness.lua:71-180, 1827-1878, 2810-2960`

**Interfaces:**
- Consumes: the existing character fixture's `_edict` and `_edict_throws` test fields.
- Produces: a stubbed `REGION_SCRIPT_INTERFACE:get_active_edict_key()` matching CA's documented
  receiver and return type.

- [ ] **Step 1: Extend `make_character`'s region stub**

Add the method to the region returned by `character:region()`:

```lua
get_active_edict_key = function()
    assert(not c._edict_throws, "get_active_edict_key refused")
    return c._edict or ""
end,
```

Add `_edict = ""` and `_edict_throws = false` to the fixture fields. Do not put the method on the
character or province; the receiver must remain the region interface.

- [ ] **Step 2: Reconfirm the API contract and shipped precedent**

Run:

```powershell
py tools\check_lua_api.py --explain get_active_edict_key
rg -n "get_active_edict_key" "Modding Files\reference\ca_scripts_wh3" -g "*.lua"
```

Expected: the offline docs say it is a region method returning the active key or `""`, and the
shipped Vampire Coast loyalty script calls it on `character:region()`. Record both outputs in the
task checkpoint. Do not expand the importer's top-level character/faction stub parser for one
nested region method.

- [ ] **Step 3: Run the unchanged harness and importer**

Run:

```powershell
& "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua
py tools\import_iron_court.py
```

Expected: both remain green. This checkpoint changes only test capability, not shipped behavior.

- [ ] **Step 4: Save review checkpoint 1**

Copy the harness to `.superpowers/sdd/iron-court-edict-loyalty/task01/`.

---

### Task 2: Drive the governor-edict query from failing checks

**Files:**
- Modify: `tools/_iron_court_harness.lua:1827-1878, 2810-2960`
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court.lua:696-744, 2791-2803`

**Interfaces:**
- Consumes: `IC.governor_active`, `court.govs`, `IC.character_by_cqi`, and
  `region:get_active_edict_key()`.
- Produces: `IC.MILITARY_DOCTRINE`, `IC.TUNE.loyalty_military_doctrine`, and
  `IC.governor_edict(faction_key, province_key) -> string or nil`.

- [ ] **Step 1: Add failing exact-query checks**

Add these checks beside the existing `governor_active` cases:

```lua
check("governor_edict reads Military Doctrine only from an active governor", function()
    IC.state = {}
    local gov = make_character(801, ANY_SEAT, "forge", "prov_a")
    gov._edict = "wh3_dlc23_edict_chd_armaments"
    make_faction(F, IC.CHD_SUBCULTURE, {gov}, {"prov_a"})
    IC.add_house(F, "forge")
    IC.court(F).govs.prov_a = 801
    assert(IC.governor_edict(F, "prov_a") == IC.MILITARY_DOCTRINE)
    gov._edict = "wh3_dlc23_edict_chd_architects"
    assert(IC.governor_edict(F, "prov_a") ==
           "wh3_dlc23_edict_chd_architects")
end)

check("governor_edict refuses absence and isolates an engine error", function()
    IC.state = {}
    local gov = make_character(802, ANY_SEAT, "forge", "prov_b")
    make_faction(F, IC.CHD_SUBCULTURE, {gov}, {"prov_a"})
    IC.add_house(F, "forge")
    IC.court(F).govs.prov_a = 802
    assert(IC.governor_edict(F, "prov_a") == nil)
    gov._edict_throws = true
    assert(IC.governor_edict(F, "prov_a") == nil)
end)
```

The first check deliberately proves the helper returns the actual key. The exact Military Doctrine
filter belongs to the loyalty rule, not to this general query.

- [ ] **Step 2: Run the harness and confirm the query is missing**

Run the Lua harness. Expected: failure naming `IC.governor_edict`; a parse or unrelated fixture
failure is not the expected red result.

- [ ] **Step 3: Add the key and tuning value**

Add:

```lua
IC.MILITARY_DOCTRINE = "wh3_dlc23_edict_chd_armaments"
IC.TUNE.loyalty_military_doctrine = 2
```

Keep the key near other verified vocabulary and the number beside the other loyalty tuning values.

- [ ] **Step 4: Implement the guarded query**

Place this immediately after `IC.governor_active`:

```lua
function IC.governor_edict(faction_key, province_key)
    if not IC.governor_active(faction_key, province_key) then return nil end
    local cqi = IC.court(faction_key).govs[province_key]
    local character = IC.character_by_cqi(faction_key, cqi)
    if not character then return nil end
    local ok, key = pcall(function()
        local region = character:region()
        if not region or region:is_null_interface() then return nil end
        return region:get_active_edict_key()
    end)
    if not ok or not key or key == "" then return nil end
    return key
end
```

Do not save, log or apply loyalty in this helper.

- [ ] **Step 5: Run syntax, harness and API checks**

Run:

```powershell
& "C:\Program Files (x86)\Lua\5.1\luac.exe" -p "Modding Files\pack\script\campaign\mod\zzz_derpy_iron_court.lua"
& "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua
py tools\import_iron_court.py
```

Expected: all exit 0, including the API checker recognizing the region method.

- [ ] **Step 6: Save review checkpoint 2**

Copy the model and harness to `.superpowers/sdd/iron-court-edict-loyalty/task02/`.

---

### Task 3: Add Military Doctrine to the shared loyalty breakdown

**Files:**
- Modify: `tools/_iron_court_harness.lua:2810-2960`
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court.lua:3046-3150`

**Interfaces:**
- Consumes: `IC.governor_edict`, `IC.MILITARY_DOCTRINE`,
  `IC.TUNE.loyalty_military_doctrine` and `IC.house_of_cqi`.
- Produces: one aggregated Military Doctrine term in `IC.loyalty_terms`.

- [ ] **Step 1: Add a failing single-province term check**

Build an active Forge governor in `prov_a`, set `_edict` to Military Doctrine, and find the term by
label rather than list position:

```lua
local doctrine = nil
for _, term in ipairs(IC.loyalty_terms(F, "forge")) do
    if term.label == "Military Doctrine" then doctrine = term end
end
assert(doctrine and doctrine.n == 2,
       "Military Doctrine did not add exactly +2 to its governor's party")
```

Then set `_edict` to each of `architects`, `higher_quotas`, `smoke_stacks`, and `""`; assert the
term is absent in every case.

- [ ] **Step 2: Add failing activity and party-routing checks**

Use one assigned Forge governor standing outside `prov_a` and assert no Doctrine term. Move him
inside without changing the assignment and assert it appears. Add a Legion governor with Military
Doctrine and assert the Forge breakdown does not receive his +2 while Legion does.

- [ ] **Step 3: Add a failing stacking and drift-parity check**

Give the same party active governors in `prov_a` and `prov_b`, both under Military Doctrine. Assert
there is exactly one term, its label is `Military Doctrine in 2 provinces`, and `n == 4`.

Compute the net by manually summing every term, call `IC.drift_loyalty`, and assert the party's
loyalty changed by that exact net. Do not use `IC.loyalty_net` on both sides of the assertion.

- [ ] **Step 4: Run the harness and confirm the term is absent**

Run the Lua harness. Expected: the first new term check fails while all earlier checks pass.

- [ ] **Step 5: Extend the existing governor scan once**

In `IC.loyalty_terms`, retain the current `govs` count and add `doctrine = 0`. During the same
`court.govs` loop, after confirming the governor belongs to `slug`, increment `doctrine` only when:

```lua
IC.governor_edict(faction_key, province_key) == IC.MILITARY_DOCTRINE
```

After the existing governed-province term, append:

```lua
if doctrine > 0 then
    terms[#terms + 1] = {
        label = doctrine == 1 and "Military Doctrine"
                or string.format("Military Doctrine in %d provinces", doctrine),
        n = doctrine * IC.TUNE.loyalty_military_doctrine,
    }
end
```

Do not add a second scan, a saved counter or a special case in `IC.drift_loyalty`.

- [ ] **Step 6: Add the engine-error term case**

Set `_edict_throws = true` for an otherwise active governor and assert `IC.loyalty_terms` returns
normally without the Doctrine term. This makes the `pcall` observable at the actual turn-start
consumer, not only in the helper check.

- [ ] **Step 7: Run the full offline verifier**

Run:

```powershell
& "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua
py tools\gen_iron_court.py --check
py tools\import_iron_court.py
```

Expected: all exit 0. `gen_iron_court.py --check` must report the same DB/loc counts as before this
feature because the edict feature owns no generated data.

- [ ] **Step 8: Save review checkpoint 3**

Copy the model and harness to `.superpowers/sdd/iron-court-edict-loyalty/task03/`.

---

### Task 4: Prove the tests can catch broken edict behavior

**Files:**
- Modify: `tools/mutate_iron_court.py:49 onward`

**Interfaces:**
- Consumes: Task 2's query and Task 3's shared loyalty term.
- Produces: mutation coverage for every political rule introduced by this feature.

- [ ] **Step 1: Add five unique mutants**

Add `(old, new)` mutations for these mistakes:

1. Replace the exact-key comparison with `IC.governor_edict(...) ~= nil`, allowing every edict.
2. Remove the `IC.governor_active` guard from `IC.governor_edict`.
3. Count every governor in the Doctrine total without checking `IC.house_of_cqi == slug`.
4. Set the term to one fixed +2 instead of `doctrine * loyalty_military_doctrine`.
5. Add Doctrine directly inside `IC.drift_loyalty` instead of returning it from
   `IC.loyalty_terms`, making model and tooltip disagree.

Name each mutant with the word `edict` so the filtered command selects the complete feature set.

- [ ] **Step 2: Run the mutation runner's own selftest**

Run:

```powershell
py tools\mutate_iron_court.py --selftest
```

Expected: all anchors match exactly once, the harmless survivor is reported internally, the stale
anchor is recognized, and the shipped model is restored byte for byte.

- [ ] **Step 3: Run the filtered edict mutants**

Run:

```powershell
py tools\mutate_iron_court.py edict
```

Expected: every edict mutant is caught and the summary reports `0 unexplained`.

- [ ] **Step 4: Run the complete regression suite**

Run:

```powershell
py tools\gen_iron_court.py --selftest
py tools\gen_iron_court.py --check
py tools\import_iron_court.py
py tools\mutate_iron_court.py
```

Expected: all commands exit 0 and the complete mutation suite has no survivor or stale anchor.

- [ ] **Step 5: Save review checkpoint 4**

Copy `tools/mutate_iron_court.py`, the model and the harness to
`.superpowers/sdd/iron-court-edict-loyalty/task04/`.

---

### Task 5: Build, verify in game and close the parity document

**Files:**
- Generated: `Modding Files/Modpacks/derpy_iron_court.pack`
- Modify after successful verification: `docs/IRON_COURT_VS_ROME2.md:174-182`
- Create after successful verification: `docs/sessions/HANDOFF_20260920_IRON_COURT_EDICT_LOYALTY.md`
- Modify after successful verification: `docs/SESSION_INDEX.md`

**Interfaces:**
- Consumes: the verified model and tests from Tasks 1-4.
- Produces: an undeployed verified pack first, then live evidence and current-truth docs.

- [ ] **Step 1: Build without deploying**

Inspect `tools/deploy_iron_court.py` before running it. With RPFM open and WARHAMMER III closed,
run:

```powershell
py tools\deploy_iron_court.py --no-copy
```

Expected: `gates green`, a saved pack under `Modding Files/Modpacks`, and successful read-back of
the pack index. Confirm the game-data copy's timestamp and size did not change.

- [ ] **Step 2: Deploy through the normal guarded path**

After recording the pre-deploy game pack size and SHA-256, run:

```powershell
py tools\deploy_iron_court.py
```

Expected: the script refuses if the game is running; otherwise it copies the built pack into the
game data directory. Verify built and deployed copies have the same byte size and SHA-256.

- [ ] **Step 3: Verify the exact rule in an existing campaign**

Use provinces with active Iron Court governors and inspect the loyalty breakdown:

1. Military Doctrine with the governor inside the province shows `Military Doctrine +2`.
2. A second qualifying province for the same party produces one `...in 2 provinces +4` term.
3. Masterful Architects, Higher Quotas and Billowing Smoke Stacks produce no political term.
4. Moving the governor outside the assigned province removes the Doctrine term but preserves the
   governorship.
5. Moving the governor back restores the term.
6. Ending the turn changes loyalty by exactly the displayed net.
7. Saving and reloading does not create a stale or doubled term.

- [ ] **Step 4: Inspect runtime evidence**

Read the newest `script_log_*.txt`, `modified.log`, `bad_mods_report.txt` and crash-dump timestamps.
Require no Iron Court error, no DB rejection and no crash newer than the verified launch.

- [ ] **Step 5: Update the parity and handoff documents**

Replace section 2.11's proposed routes with a `BUILT 2026-09-20` note naming Military Doctrine,
the +2-per-active-governor rule, the documented API, the shared loyalty breakdown and the absence
of new DB data. In section 5, state that both implementable parity items are now built; retain the
political-affiliation overlay limitation.

Write `docs/sessions/HANDOFF_20260920_IRON_COURT_EDICT_LOYALTY.md` with goal, decisions, changed
files, command output, pack size/hash, screenshots or observed values, logs, and any remaining live
risk. Add exactly one concise link line to `docs/SESSION_INDEX.md`.

- [ ] **Step 6: Save the final review checkpoint**

Copy every changed text file and documentation update to
`.superpowers/sdd/iron-court-edict-loyalty/final/`. Record the built and deployed pack paths
separately in the handoff.
