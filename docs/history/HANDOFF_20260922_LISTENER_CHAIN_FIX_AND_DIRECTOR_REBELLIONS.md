# HANDOFF 2026-09-22 - the panel-listener chain break, fixed and shipped; and why every player conquest spawns a rebel army

Two unrelated pieces of work, **both fixed, packed and verified**. Part A is the Iron Court
listener chain. Parts B and C are the rebel armies: B is the diagnosis, C is what was then
changed - and C exists only because the author pushed back twice after the first answer, which
had stopped at "it is your own mod, by design".

---

## PART A - the listener chain break (FIXED AND SHIPPED)

Closes `HANDOFF_20260921_PANEL_LISTENER_CHAIN_BREAK.md`, whose section 6 is now rewritten in
place with the resolution. Read that file for the diagnosis; this is only what was done.

### A1. The fix

`data/derpy_iron_court.pack`, `script/campaign/mod/zzz_derpy_iron_court_ui.lua`, lines 4877
and 4882:

```lua
if context.string and context:string() ~= ICUI.STANDING_PANEL then return end   -- was
if context.string ~= ICUI.STANDING_PANEL then return end                        -- now
```

`context.string` is a plain field. Calling it threw on every panel open and close, and because
CA's `event_protected_callback` xpcalls the callback but **not** the failure handler after it,
`script_error` escaped the dispatch loop and abandoned all 31 `PanelOpenedCampaign` and 9
`PanelClosedCampaign` listeners queued behind it - across every mod loaded.

### A2. How it was pushed - one file, not a rebuild

`deploy_iron_court.py` rebuilds the whole pack from the generators and would have pushed a
stale staging tree at every DB table. The surgical route was used instead - the same pattern
`import_victory_routes.py` uses: `open_packfiles` -> `add_packed_files` -> `save_packfile`,
one Lua file, one MCP session.

### A3. What was verified, and how

| Check | Result |
|---|---|
| shipped file re-read out of the saved pack | byte-identical to staging (md5 `39954f0b`) |
| pack file list before vs after | **all 1705 paths identical** |
| pack size delta | exactly **-42 bytes** = 2 x the 21 chars of ` and context:string()` |
| all 10 DB fragments re-decoded, **fresh MCP session** | 10/10 ok, 0 failed |
| the idiom across **all 268 enabled packs** | 0 |
| `import_iron_court.verify()` | **0 findings** |
| `tools/mutate_iron_court.py` | **13 stale anchors -> 7** |
| `check_lua_api.py --selftest` / full scan | ok / 107 files, 0 field-call findings |

### A4. The staging tree was an ANCESTOR, not a later edit

This is the part that cost the most and the part most likely to be got wrong again. The staged
copy was **3021 lines** against the pack's **4892**, and its mtime was NEWER (Sep 21 17:09 vs
the pack's 07:12), which reads as "staging is ahead". It was not. Its strings are the EARLIER
wording - "Court record, newest first" against the shipped "The court's record, newest first" -
so it is an older lineage carrying a newer timestamp.

The corrected file already existed on disk and had never been packed:

```
.superpowers/sdd/2026-09-20-iron-court-ambition/task-04/after-fix1/   == the live pack, byte for byte
.superpowers/sdd/2026-09-21-iron-court-humanize/baseline/             == that file + this exact 2-line fix, nothing else
```

The humanize baseline differs from the shipped file by **4 diff lines** - the two guards and
nothing more.

### A5. The harness had to move with it

Installing the shipped file made `import_iron_court.verify()` fail on
`the mood ladder reads the clock before the loyalty`. That was **not a behaviour bug**:
`ICUI.mood`'s logic is identical in both copies and only the strings were reworded
(`LEAVES IN %d` -> `SECEDES %d`, `BREAKING APART` -> `SPLINTERING`).
`tools/_iron_court_harness.lua` was stale in the same way staging was, and the humanize
baseline carries the matching harness. Both were installed. All 58 diff lines between the two
harnesses are wording, and both carry **459** `check(` assertions, so no check was traded away.

**A stale harness is worse than a failing one**: it was validating a file that had not shipped
for two days and reporting green.

### A6. The new gate

`tools/check_lua_api.py` gained a `field-call` rule (`FIELD_CALL`) that flags any `:string()`.
Evidence it can never be a false positive: across the **831** Lua files in
`reference/ca_scripts_wh3` there are **690 `context.string` FIELD reads and zero `:string()`
calls of any kind**. The `--selftest` case was watched to fail (`AssertionError: []`) with the
rule neutered, then pass with it restored.

---

## PART B - every player conquest spawns a rebel army (DIAGNOSED, THEN FIXED - see PART C)

The report was "every time I capture a settlement, a rebel army will spawn". It is **our own
mod**, by design, and the player hits it 100% of the time while the AI hits it about 6%.
**Part C is what was then changed and shipped.**

### B1. The cause

`derpy_director.pack` -> `script/campaign/mod/derpy_director.lua`. Staging and the packed copy
are **byte-identical** (854 lines), so staging is safe to edit.

```
RegionFactionChangeEvent  ->  situation kind = "conquest"
  -> line 802  if outrage >= OUTRAGE_FLOOR (0.5)
  -> line 805  elseif sit.kind == "conquest" and self:afford(PRICE.unrest)   -- 30
  -> line 450  beat_unrest -> cm:force_rebellion_in_region(region, REBEL_UNITS, x, y, false)
```

`REBEL_UNITS = 4`, `OUTRAGE_FLOOR = 0.5`, `PRICE.unrest = 30`, budget starts and caps at 180
and refills 60 a turn.

### B2. Why the player gets it every single time

**Outrage is a constant for him, not a roll.** It is read from the baked culture-hatred matrix
in `derpy_director_lore.lua`, so Chaos Dwarf against `cr_ksl_slaves_of_zharr` lands in the
middle band of `OUTRAGE_STEPS` every time. Across **all 1377 script logs**:

```
10  outrage=0.60 old_enmity        <- every player conquest ever logged
```

0.60 clears the 0.50 floor, always.

**And he never loses the budget race.** The budget refills at turn start and his conquest
happens in his own turn with it full; the AI's conquests arrive afterwards in a burst and
starve each other.

| today's log `script_log_220926_1244.txt` | |
|---|---|
| conquest situations | 160 |
| cleared the 0.50 floor | 101 |
| rebellions actually fired | **6** |
| `budget N cannot afford 30, beat skipped` | **70** |
| **player conquests / player rebellions** | **4 / 4** |

Across all logs: 116 `unrest 4 units in ...` lines in 33 separate logs.

### B3. The two findings the author raised afterwards - BOTH REAL

**B3a. There is no warning, and the mod is only half the reason.** `derpy_director:news()`
writes to a saved-value ring buffer and **shows nothing**; the only event feed the Director
raises is `beat_tell` on the *grudge* branch, which is a different branch from the unrest one.
So the mod itself never announces a rebellion.

The engine should, though - `force_rebellion_in_region`'s **fifth parameter is "Suppress the
event message related to the rebellion"** and the Director passes `false`, meaning do NOT
suppress. The reason it is still not seen is **timing**, read off the log:

```
<1476.6s> [director] unrest 4 units in cr_oldworld_region_plains_of_zharr_3_3
<1476.8s> **** BattleCompleted event received, the attacker won
<1476.8s> **** Battle involving human faction [cr_chd_house_of_azeros] ... won a settlement battle as the attacker
```

The rebellion is spawned **0.2s BEFORE the battle-completion sequence**, i.e. inside the
post-battle/occupation flow, so its message is raised into a stack the player is clicking
through. `RegionFactionChangeEvent` fires the instant the region changes hands, and the
Director acts on it in the same tick.

**B3b. The rebels are not the previous owner** - and not through this call. The log names the
spawned army outright:

```
<1482.3s> Character selected, cqi: 5355 || faction:  (key rebels)
          || subtype: wh_dlc07_chs_sorcerer_lord_shadow || name: Grooxutaphsos
```

The faction key is the generic **`rebels`**, and the leader rolled a **Warriors of Chaos
sorcerer lord** - neither the dispossessed `cr_ksl_slaves_of_zharr` (Kislev) nor the player's
Chaos Dwarfs. `force_rebellion_in_region` takes a region key, a unit count and coordinates and
**has no faction parameter at all**, so there is no way to aim it at the previous owner from
this call. The sibling call `cm:force_rebellion_with_faction` does take one - see C1, which is
the fix.

### B4. The knobs, if this is to change

All in `derpy_director.lua`: `OUTRAGE_FLOOR` (line 70), `REBEL_UNITS` (89), `PRICE.unrest`
(81), and the `sit.kind == "conquest"` branch (805). Raising the floor above 0.60 stops the
player's conquests but also most AI ones, because 0.60 is a whole band, not his personal value.

---

## PART C - what was changed and shipped (Director)

Two changes, both chosen by the author after the diagnosis. Built with
`py tools/build_director.py` and copied to `data/`; backup
`derpy_director.pack.bak_pre_rebelfix_20260922`.

### C1. The rebels are now the dispossessed owner's own

`cm:force_rebellion_in_region` -> **`cm:force_rebellion_with_faction`**. The old call has no
faction argument at all and drops the army into the generic `rebels`. The new one takes one.
`REBEL_FACTIONS` maps subculture -> rebel faction for all **24** subcultures that have one,
read out of `db.pack`'s `factions_tables` where `is_rebel` is true - not typed by hand.
`rebel_faction()` keys it on **`sit.victim`**, the faction that lost the region.

**The two calls disagree on convention.** The old took a region KEY and map coordinates; the
new takes a region INTERFACE and none. Its 4th argument is full-strength and its **5th is
"suppress PUBLIC ORDER penalty", NOT the suppress-MESSAGE flag the old call carried in that
same position.**

A subculture with no rebel faction (21 of 45) logs and does nothing, rather than falling back
to the generic call - falling back would reintroduce the anonymous uprising this replaced.

### C2. A second, higher floor - and it could not be the existing one

`UNREST_FLOOR = 1.0`, on the conquest branch only. **`OUTRAGE_FLOOR` could not be raised**:
it also gates the grudge branch twenty lines above, so moving it would have silenced the feuds
the mod exists to tell. Plague-on-raze keeps the old floor. 1.0 admits kin-slaying (1.5) and
unprovoked (1.0) and nothing on the natural-enmity scale, whose top band is 0.85.

### C3. How it was verified

`build_director.py`'s stub now matches the real signature, and **the old call was made a hard
`error()` rather than deleted** - left as a recording stub, a regression back to it would have
passed every assertion in the suite.

Two new assertions, each watched to fail before being kept:

| Assertion | Broken by | Caught |
|---|---|---|
| a 0.60 conquest raises no rebels but still earns its grudge | `UNREST_FLOOR = 0.5` | `AssertionError` naming `wh3_main_ksl_kislev_rebels` |
| the **dispossessed** owner rises, not the conqueror | `rebel_faction(sit.instigator)` | `AssertionError` naming `wh3_main_cth_cathay_rebels` |

The second needed a real pairing with **different subcultures above 1.0**, which only the
unprovoked band gives: **Cathay against Kislev reads +10** in the shipped lore matrix and falls
off the end of `OUTRAGE_STEPS` to 1.0. It took three tries - **the cast is built from how much
a candidate hates the INSTIGATOR, not from who likes the victim**, so Kislev kin as neighbours
read +10 toward Cathay, nobody turned up, and an empty cast drops the situation before any
consequence is priced. Daemon neighbours (-100 toward Cathay) made it real.

Final state: `luac -p` ok, `check_lua_api` 0 suspect calls, `check_lua_undeclared` 0 findings,
`build_director.py --selftest` all groups ok, **46 mutants / 0 survived / 0 stale anchors**,
and the deployed pack's Lua is byte-identical to staging with **0** old call sites, **1** new
one and **24** rebel-faction entries.

### C4. What was NOT done - the missing warning

The author also reported no warning. **Not fixed.** `derpy_director:news()` is a save buffer
and shows nothing, and the only feed the Director raises is `beat_tell` on the *grudge*
branch. Adding an `unrest` card is generator-and-DB work, not a Lua edit: `FEED_BASE` needs a
new index block, plus per-culture `event_feed_strings` rows, loc and art, all regenerated and
repacked. Separately, the spawn lands **0.2s before `BattleCompleted`**, inside the post-battle
stack - and `force_rebellion_with_faction` has no suppress-message argument at all, so whether
the engine draws anything for it is now **unknown and untested**.

---

## Do not re-derive

- **The Iron Court's shipped Lua is 4892 lines and staging now matches it.** The 3021-line
  ancestor is at `...zzz_derpy_iron_court_ui.lua.bak_pre_listenerfix_20260922`. Do not
  "restore" it.
- **A newer mtime does not mean a newer file.** Compare CONTENT - the reworded strings are the
  tell. This wasted most of the resolution pass.
- **`.superpowers/sdd/<date>-<topic>/baseline/` is a real source of truth** in this workspace.
  Two files that had never been packed were sitting there, and the fix was among them.
- `context.string` is a field; 690 CA field reads, 0 `:string()` calls. Now gated.
- `cm:force_rebellion_in_region` spawns into faction key `rebels` with an engine-rolled leader,
  and takes **no faction argument**. Confirmed from a live log, not inferred.
- Its 5th argument is *suppress message*, and the Director already passes `false`.
- The Director's `news()` shows nothing - it is a save buffer, not a feed call.
- Backups from this session all carry the suffix `.bak_pre_listenerfix_20260922`.

## What is still open

- **The warning is still missing** - see C4. Whether `force_rebellion_with_faction` draws any
  event at all is untested; it has no suppress-message argument, so the old call's `false` no
  longer applies. Needs either a feed card (DB work) or a live check.
- **C1 and C2 have not been seen in a live campaign.** Everything above is the stubbed harness
  and a static read of the shipped pack. The next run should show `unrest N units in R as
  <culture>_rebels` in the log, and far fewer of them.
- `!starting_units`' roster has still never been checked - the button has not been clicked.
  Carried over from the 2026-09-21 handoff, section 6d.
- `tools/mutate_iron_court.py` still reports **7 stale anchors**, pre-existing and listed in
  its own run. They were 13 before this session.
