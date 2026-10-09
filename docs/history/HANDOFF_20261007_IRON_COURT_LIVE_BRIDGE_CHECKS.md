# Iron Court - live checks through the wh3 bridge, party members, hero upkeep (2026-10-07)

Continues `HANDOFF_20261006_IRON_COURT_DWARFS_RELEASE.md`. **Built and deployed: starting
members, build `522125A3`** (section 9). Design A, the live-check runner, is still not approved.

## 1. State at the end of the session

- The game is running a **new Karaz-a-Karak campaign** (`wh_main_dwf_dwarfs`, Old World map,
  turn 1, script log `script_log_071026_0643.txt`).
- It carries test debris: a Thane on the map at Karaz-a-Karak (cqi 2695) wearing a runtime
  bundle, and a Thane put in the recruitment pool. **Do not save this game.**
- No Dwarf save exists in `save_games/`. Both of today's Karaz-a-Karak sessions were new
  campaigns, which is why the parties differ between them (06:24: ledger/crown/temple;
  06:43: road/crown/hearth). That is a new roll, not a court changing under a save.

## 2. The bridge, and the rule that keeps the game alive

- The `mcp__wh3__*` tools did not load (same G:/ vs g: registration as 2026-10-03). The file
  protocol works without them. The installed `wh3_mcp_server.pack` (Workshop 3786971022) is
  byte-identical to `wh3-mcp/pack/script/_lib/mod/wh3_mcp.lua`. Both it and
  `derpy_iron_court.pack` are ticked in `used_mods.txt`.
- **A probe calling `string.format` and `s:find` wedged the bridge AND broke the game's
  scripts.** 3,600 `find_single_uicomponent ... is not a ui component` errors followed within a
  minute (Resource Overhaul's stores timer, the hub). The first error came 1s after the probe,
  with zero before it. The chunk's own `pcall` caught the probe's error and did not help. The
  game had to be restarted without saving.
- **After the restart, eight probes with no string-library calls all ran clean**: zero script
  errors, ping healthy after each. They used only `..`, `tostring`, `pairs`/`ipairs`, `#`, IC/ICUI
  calls, `cm:` calls and a 4-item `character_list` loop. Calling the mod's own functions is
  fine, even though those functions use the string library internally.
- **The rule:** a chunk sent to `eval` calls no `string.*` and no `s:method()`. It returns raw
  tables, and every text match is done in Python. After each probe, count `SCRIPT ERROR` in the
  newest `script_log_*.txt`. A rise means quit without saving. Recorded in the memory
  `wh3-mcp-bridge-wedges-on-interface-walks` (fifth trigger).

The sender used, worth keeping verbatim (Python, writes ASCII with no BOM):

```python
import json, os, sys, time
G = r"F:\SteamLibrary\steamapps\common\Total War WARHAMMER III"
CMD, RES = os.path.join(G, "wh3_mcp_command.json"), os.path.join(G, "wh3_mcp_result.json")
cmd = sys.argv[1]; arg = sys.argv[2] if len(sys.argv) > 2 else "{}"
if arg.startswith("@"):
    code = open(arg[1:], encoding="utf-8").read()
    params = {"code": "local ok, r = pcall(function()\n" + code + "\nend)\nif ok then return r end\nreturn 'PCALL ERROR: ' .. tostring(r)"}
else:
    params = json.loads(arg)
if os.path.exists(RES): os.remove(RES)
with open(CMD, "w", encoding="ascii", newline="") as f: f.write(json.dumps({"command": cmd, "params": params}))
deadline = time.time() + 30
while time.time() < deadline:
    if os.path.exists(RES):
        time.sleep(0.2); out = open(RES, encoding="utf-8", errors="replace").read(); os.remove(RES)
        print(out); sys.exit(0)
    time.sleep(0.25)
print('{"status":"timeout"}'); sys.exit(1)
```

## 3. Section 7 checks read live (06:24 session, Karaz-a-Karak, turn 1)

Read through string-free probes. All passed:

- **Title:** "The Council of %s" with "Karaz-a-Karak".
- **Government:** `priest`, "The Ancestors' Writ".
- **Seats per tier:** 2/4/4/4.
- **Laws:** all four on their first law (`measure`, `tithe`, `rites`, `levy`), laws on.
- **Secession countdown:** `IC.tune(fk,"secede_turns")` = 8.
- **Kin of the Karak:** +1 on all three parties.
- **Grudges:** a turn-1 grudge "A demand refused" on the temple party, logged in the Record as demand, then grudge, then demand_refused.
- **The Book:** Bloody Spearz 1461, Ferrik 815, Grutnik 480.
- **Book bands crossed:** Spearz 2, Ferrik 1, Grutnik none.
- **Move costs:** oath 90, patron 130, pledge 150, the base prices.

## 4. Party leaders and members - the code does what was ruled

- **Members:** a member is any character whose background maps to the party (`IC.house_of_character`).
- **Dealing:** men are dealt to the party with the fewest members (2026-09-25), so Karaz-a-Karak's three starting characters give one member per party.
- **Turn 1:** a leaderless party gets a lord **in the recruitment pool**, not on the map. This is the author's 2026-09-30 ruling, at `zzz_derpy_iron_court.lua:2862`. Measured: "ledger ... has no leader - a wh_main_dwf_lord waits in the lord pool".
- **Consequence the author may not want:** on turn 1 that pool lord is the party's one gift. `house.fielded` is set on turn 1 (`:2913`), so the party never gets a lord put on the map later, even if the pool lord is never hired.
- **Temple's leader:** in the 06:24 game it was a garrison commander (cqi 891, `wh_main_dwf_lord` with `colonel=true`), the last-resort leader.

## 5. Measured: hero upkeep, removing it by script, heroes in the pool

| Test (06:43 session) | Result |
|---|---|
| `faction:upkeep()` before | 1919 |
| `cm:spawn_agent_at_settlement(f, capital, "champion", "wh_main_dwf_thane")` | upkeep **2169**: a hero standing alone pays 250 |
| Runtime bundle on that Thane | upkeep back to **1919**: his 250 removed, and only his |
| `cm:spawn_character_to_pool(fk,"","","","",30,true,"champion","wh_main_dwf_thane",false,"")` | call succeeded, but **the Recruit Hero panel lists hero TYPES** (Dragon Slayer, Thane, Runesmith, Master Engineer), not men; a pooled hero has nowhere to show (author's screenshot) |

How the bundle was built:
1. `cm:create_new_custom_effect_bundle(IC.gov_bundle_base(fk))`.
2. `remove_effect_by_key(IC.GOV_ORDER_EFFECT)`.
3. `add_effect("wh2_dlc14_effect_upkeep_reduction_heroes", "character_to_character_own", -100)`, which returned true.
4. `cm:apply_custom_effect_bundle_to_character(b, man)`.

Vanilla never ships that effect on that scope, but the game honours it. After step 2 the bundle still held **one other base effect**, so the real build needs a dedicated empty bundle row, which `gen_iron_court.py` would add.

- **Upkeep facts:** `main_units` gives 250 upkeep for the Dwarf and Chaos Dwarf generic heroes and lords. CA ships effects that reduce upkeep only for *unembedded* agents, which agrees with the measurement.
- **Hero caps:** the screenshot shows a red badge on all four hero types. Its meaning is not read yet; it may be the hero cap.

## 5b. Measured: the pool route (a third new campaign, script log `script_log_071026_0656.txt`)

The 2026-09-23 finding still holds: a lord sent BACK to the pool stays in `character_list`. It was
never built as a feature, for either race. Chaos Dwarf courts only look fuller because their
factions start with more characters (Ghorth's Conclave has 7; Karaz-a-Karak has 3).

| Step | Measured |
|---|---|
| `create_force_with_general(fk, "", capital, x, y, "general", "wh_main_dwf_lord", ...)` | cqi 2695, dealt by `ic_born` to `chain`, the leaderless party; rank 1; upkeep 1919 -> 2257 (+338) |
| `cm:wound_character(lookup, 1)` | his army is gone, and he comes back as a **new cqi, 2696**, wounded, no region, still in `character_list`, still `chain`; upkeep 1984 |
| `cm:stop_character_convalescing(2696)` | no longer wounded, no army, still `chain`; upkeep stays 1984 (+65 over the start, a projection only) |
| The author hires him from Recruit Lord | **`CharacterRecruited` fires** for 2696, the same man, still `chain`, rank 1; `IC.recruit_rank` at Karaz-a-Karak is 0, so nothing to top up |

For design B, now revised to the pool route:
- record each seeded lord's cqi AFTER the wound, because it changes;
- `raise_hired` must accept the seeded list as well as `house.stored`;
- the seeding replaces the turn-1 pool-lord gift. In this test `chain` held both: the gift was `stored = true`.

Still open: the 65 a turn while pooled, to be measured against the treasury at end of turn.

## 6. Two designs, neither approved

**A. `tools/live_check_iron_court.py`** (the author wants both modes):
- Stdlib only, speaking the two-file protocol, with string-free probes.
- After every probe it checks for new script errors and stops at the first one.
- `checklist` mode runs section 7 by race, with an opt-in `--mutate` for Insult and Weregild, the switch-off, and save/reload comparisons through `IC.pack`.
- `soak` mode uses the bridge's `soak_turns` and records per turn:
  - each court's party set, flagging a party gone with no secession or dissolve line in the Record (the Black Kraken bug);
  - the rebel pools, 4 Chaos Dwarf and 3 Dwarf factions, alive or dead;
  - leaderless-party durations.
- Output is a JSON log under `Modding Files/source/iron_court_live/`, exit 1 on a FAIL, plus a `--selftest`.
- Next stage: the author approves the design, then the spec, then the plan.

**B. At least three members per party at the start** (author: "Mix: 1 lord + heroes", "Player courts only"):
- **When:** once, on turn 1, after the `ensure_leaders` call at `:7996`, guarded by a saved value `derpy_ic_seeded_<fk>`.
- **The lord:** a party with no lord, a garrison commander counting as none, gets one pool lord. This is the existing code, moved into a shared function.
- **The heroes:**
  - Heroes from `R.REBEL_HEROES` are spawned at the capital to bring each party, the Crown included, to 3 members.
  - `spawn_agent_at_settlement` returns nil, so `ic_born` would stamp the next new hero from a per-faction queue of party slugs.
  - Each hero carries the free-upkeep bundle.
- **Open questions:**
  - whether the starting heroes stay free for life;
  - whether a pool lord counts toward the 3;
  - whether the turn-1 "fielded" rule in section 4 should change;
  - the hero caps.

## 7. Do not re-derive

- `faction:upkeep()` and `faction:expenditure()` update at once after a spawn or a bundle, so no end turn is needed to measure.
- `IC.party_lords(fk, slug)` returns `lords, members, heroes`, and its heroes list holds only men for whom `IC.can_defect_hero` is true. The spawned Thane was not in it.
- `IC.REBEL_HEROES`: Dwarfs `wh_main_dwf_thane` = champion, `wh_main_dwf_master_engineer` = engineer, `wh_main_dwf_runesmith` = runesmith. The Chaos Dwarf list is at core:7002.
- Dwarf store lords: `wh_main_dwf_lord`, `wh_dlc06_dwf_runelord`.

## 8. Open

- The two designs in section 6.
- The section 7 in-game checklist of the release handoff; this session ticked only its read-only half, on Karaz-a-Karak rather than Karak Kadrin.
- The red badges on the Recruit Hero panel.
- The Workshop upload, unchanged from the release handoff.

## 9. Built: starting members, build `522125A3` (2026-10-07)

The author approved design B as revised: "implement both dwarf and chaos dwarf", and C for the
numbers (MCT fewest and most, each party rolling between them).

- **Where:** in `data/`, byte-identical to `Modding Files/Modpacks/`.
  - Backup of `F4CF5CA4`: `Backup/deployed_auto/derpy_iron_court.pack.bak_pre_auto_20261007_072343`.
  - Not pushed; not on the Workshop.
- **Settings:** `seed_min` 3 and `seed_max` 6.
  - `IC.TUNE`, appended after `dwarf_courts`, so `TUNE_ORDER` positions 31 and 32.
  - `IC.TUNE_START`, which no difficulty sets and which is read off the page on every difficulty.
  - Swapped when reversed.
- **MCT:** a "Starting court" section with two sliders, 0-8. Open from the main menu, locked in a campaign. 0 and 0 gives nobody.
- **`IC.seed_members`,** called last in `IC.first_tick` for each player court on turn 1, guarded by the saved value `derpy_ic_seeded_<fk>`. Its steps:
  1. **The plan:** each party, the Crown included, rolls between the two numbers, less the members it already has. A party with nobody to speak for it gets one lord anyway.
  2. **Each lord,** one at a time, is made with `create_force_with_general` at `IC.hire_region` using a store lord. Then:
     - he is stamped with the party's background, replacing what `ic_born` dealt him;
     - he is wounded for 1 turn;
     - he is found again by background under his NEW cqi (`IC.seed_wounded`), returned with `stop_character_convalescing`, and recorded in `derpy_ic_seedlords_<fk>`.
  3. **Safeguards:**
     - the feed is shut for `IC.QUIET_FEED` and opened 2s after the end;
     - a 5s watchdog per spawn, and a token so a late landing is ignored;
     - the new-cqi lookup retries 6 times, 0.5s apart.
- **`IC.ensure_leaders`:** the turn-1 pool gift waits while `IC.seeding(fk)` is true.
- **`IC.raise_hired`:** also raises a lord on the seeded list, once, and strikes him off.
- **Gates:**
  - **Harness:** 1079 checks (1070 + 9 "starting members:"). `fielding` now runs the old leader checks with `seed_max = 0`, and the `dwarf_courts` check asserts position 30 instead of last.
  - **Mutation:** 18 new mutants, all caught. One survived the first pass, "the turn-1 pool gift made beside the seeding": the fixture's idle Crown lord moved over before any gift. The fixture now uses a legend.
  - **Static checks:** `check_lua_api` 0; literal-left 0; undeclared names are the pre-existing UI ones only.
  - **Read-back:** `check_ic_release --pack` 0 findings; the pack's 7 Lua files are byte-identical to the staged ones.
- **Patch notes:** three lines added to `PATCH_NOTES_20261006_IRON_COURT_DWARFS.md`; "Chaos Dwarf courts unchanged" became "otherwise unchanged".
- **Full mutation run:** 1197 mutants, **0 unexplained**, done after the build. Guarded in `Modding Files/Backup/mutation_guard_20261007/` (the shipped Lua, `before.json` with MD5s of 9430 files under `Modding Files/pack`, and `run.log`). After the run:
  - all six shipped Lua files and the harness are byte-identical to the guards;
  - all 9430 staged files match their hashes.

  The first pass reported 4 STALE ANCHORS, which were never run. They were re-aimed at the changed lines and all 4 are caught:
  - "field: the feed left shut" matched twice, because the seeding has its own re-open. It is now anchored on `field_leader`'s `end, 1)`.
  - "a lord made in store every turn".
  - "mct: the sliders read under every difficulty".
  - "every hire raised, not just a stored party's".

**Owed in game** (a new campaign, Karaz-a-Karak, and one Chaos Dwarf start):
- every party of yours has 3-6 members on turn 1;
- the lords are in Recruit Lord with their party's background;
- no wounded-lord panel or feed message. The first live test showed the panel; the suppressed second test was not yet confirmed by the author;
- hiring one at a place with recruit rank raises him;
- the projected pool upkeep, +65 per pooled lord, against the real treasury at end of turn.

## 10. The first live start of 522125A3, and build `60E2E401`

**Seen by the author (Karaz-a-Karak, new campaign):** a Wounded! entry for every starting lord, and Trait Gained and Trait Removed cards ("Household Warrior").

**Read live** (script log `script_log_071026_0851.txt`, and the bridge):
- the seeding ran from 107 to 123s and logged "11 of 12 starting lords sent to the pool";
- at 112.7s the turn's own pass ran `ensure_leaders`, which moved starting lord 2484 (then a Crown man) to forge with `force_remove_trait`. That is the Trait Removed card, and it lost his return ("starting lord 2483 was not found in the pool");
- the parties ended Crown 3, forge 7, temple 5, with 11 seeded lords in the pool, none wounded;
- 0 script errors.

**Fixed in `60E2E401`:**
- `ensure_leaders` returns at once while `IC._seeding[fk]`.
- `ic_born` stamps a starting lord with the background in `IC._seed_bg[fk]`, set just before each spawn, and his origin, both QUIET, then returns. No deal, no swap, no card. The swap in `seed_land` remains only for a court of the Crown alone, which `IC.court_rolled` reads as unrolled.
- `IC.seed_quiet` shuts and opens `IC.QUIET_FEED` and also the events `character_wounded` (subcategory `character_deaths`), `character_trait_gained` and `character_trait_lost` (subcategory `character_traits`), read from `event_feed_events`. It shuts again before every lord.

**Gates:**
- **Harness:** 1081 checks, including 11 "starting members". New: no card on any starting lord; every wound made with `character_wounded` shut, and the events opened again at the end; the leader pass moves nobody mid-seeding; a court of the Crown alone. The seeding fixture's court is now `rolled`, so `ic_born`'s stamping path runs.
- **Mutation:** 5 new mutants; all 25 seeding mutants are caught.
- **Build:** Modpacks MD5 `60E2E401...`, Lua byte-identical to the staged files. It waits for the game to close (`--deploy-only --wait`).
- **Full mutation run:** running, guarded in `Modding Files/Backup/mutation_guard_20261007b/`.

**Not known:** whether event-level suppression holds where category suppression did not. It needs the author's eyes on a new start.

## 11. The second live start of 60E2E401: Chaos Dwarf pictures, an unhurt lord

**Seen by the author:** a Dwarf court's "A Demand Refused" card showed Chaos Dwarf art. Seeded lords cost nothing to recruit.

**Read live:** Crown 3, hearth 6, tower 3. 8 of 9 starting lords were recorded. 0 script errors. No Wounded! entries were seen.

**Why the pictures were wrong:** the picture belongs to the `event_feed_message_events` record that the index names. There was only one run of records, all `chd/`, so every Dwarf card drew the Chaos Dwarf picture.

**Fixed (Lua, generator, importer):**
- `gen_iron_court.py` now writes a second run of records, `RACE_EVENT_OFFSET = {"chd": 0, "dwf": 200}`:
  - each record is keyed `derpy_ic_event_<slug>_dwf`, with its own group, member and criteria;
  - each points at the `dwf/` twin of its picture;
  - indices are 2800-2835. 2800-2899 is free across all 354 installed packs;
  - the Chaos Dwarf rows are unchanged, and no new loc was added;
  - check 16b confirms every `dwf/` image is a value vanilla uses.
- The model raises cards through `IC.event_index(slug, faction_key)`, which is `ev[1] + R.EVENT_OFFSET`. `DWF.EVENT_OFFSET = 200`. The located card is numbered by the court the news is about (`about`), so it matches the race whose words the text uses.
- `import_iron_court.py` refuses to build when `DWF.EVENT_OFFSET` differs from the generator's value.
- **The missing lord** (8 of 9): the first lord of a party came back from the wound with `is_wounded` false, and the lookup required it. `IC.seed_wounded` now takes the newest armyless lord of that background, newer than the one just made. `stop_character_convalescing` is called only if he is wounded.

**Not changed: recruiting is free.** That is how the engine treats a pool lord made by script. Whether to charge the normal price when one is hired is the author's call.

**Gates:**
- **Harness:** 1083 checks, OK. New checks:
  - a Dwarf card raises the Dwarf record and a Chaos Dwarf card raises the base record, for both the plain and the located call;
  - an unhurt lord is still found and recorded, and is not sent home.
  - The seeding stub now deals cqis from 8000, so lords made by the seeding are newer than the 71xx fixtures, as the game deals them.
- **Mutation:** 5 new mutants, and the 2 stale ones re-aimed. All 27 in the starting members and Dwarf records groups are caught.
- **Full run:** guarded in `mutation_guard_20261007c/`.
- **Process note:** the 20261007b run was started before the Lua edits. Its in-memory restore overwrote them, and stopping it left `_parties.lua` mid-mutant. That file was restored from the guard and the edits were re-applied. **Never edit the Lua while a mutation run is going.**

## 12. Starting lords cost the normal price, shown on their card (build `EFE99176`)

**Author:** "leave them with normal recruit price once", then "write the price in the panel".

**Read live** (a new Karaz-a-Karak start on 60E2E401, through the bridge, with the Recruit Lord panel open):
- the cards sit at `character_panel > general_selection_panel > character_list_parent > character_list > listview > list_clip > list_box > general_candidate_N_`;
- a minted candidate's card: CCO `character_details_NNNN`, cost "900" (Dwarf Lord) or "850" (Runelord), which is exactly `agent_subtypes.cost`, and the cost holder is shown;
- a starting lord's card: CCO is his cqi ("2712"), cost "0", and **`recruitment_cost_holder` is hidden**;
- writing the cost and showing the holder drew exactly like CA's card (author's screenshot: 900 and upkeep 263), and it held through a click on the card and after 3s;
- **closing and reopening the panel resets it.** The cards are rebuilt at every open.

**Built:**
- `IC.SEED_PRICE`: every `STORE_LORDS` subtype at `agent_subtypes.cost` (Chaos Dwarf 1500 each, Dwarf Lord 900, Runelord 850). `gen_iron_court.check_seed_price()` holds it to CA's DB, both ways.
- `IC.raise_hired`: a seeded lord is struck off the list at hire and charged `cm:treasury_mod(fk, -price)`, once. That now happens before the house test, so it does not depend on his party.
- `ICUI.price_pool_cards`:
  - for every card whose CCO is a cqi on the seeded list, it writes `SetText(price, "")` on `recruitment_cost` and shows the holder;
  - it runs on `PanelOpenedCampaign` "character_panel" and after any click while that panel is up (a tab rebuilds the list), at `STANDING_DELAYS`.
  - `SetText`, not `SetStateText`: the importer refuses the latter.

**Known limits:**
- the price is CA's base price, so a lord-recruitment discount does not lower it;
- the engine still lets you hire him with too little gold, which can push the treasury below zero;
- lord 2484 on the test save was the one the old lookup missed; he shows free there. New starts on this build record every lord.

**Gates:**
- harness 1084 checks, OK; new: charged once at his type's price, and the card check (his card painted, a minted candidate, an unseeded man and a card with no context left alone, only the Recruit Lord panel's opening, after a click, not after his hire);
- 6 new mutants, all caught; 31 of 31 in the starting members group;
- `gen_iron_court --check`, `check_lua_api`, literal-left: clean;
- built `EFE99176`; `check_ic_release --pack`: 0 findings, including the 72 event rows;
- deploy to data/ is waiting for the game to close. The full mutation run is guarded in `mutation_guard_20261007d/`.

**Untouched:** `derpy_more_resources_stores.lua` changed at 09:38 today, outside this work, probably in another session.

**Owed in game:** a Dwarf court's card shows a Dwarf picture; a starting lord's card shows 900 or 850 at every open; hiring one takes that from the treasury once; and a Chaos Dwarf start (1500).

## 13. The Record, read at a glance (build `C0A47D98`, deployed)

**Author** (a Chaos Dwarf Record on turn 1, playing the Overlords of Zharrduk): "whats renown and what parties are being mentioned here?", then "yes do that, or not mention that at all, there are no Icons for the player to be guided visually in the log as well".

**What confused:**
- the Crown was named by the faction ("Overlords of Zharrduk is given Howling District"), so it read as one more house;
- a party with no seat ("The Legion grew on your victories: +3 renown") read like one of the court;
- no line had a picture.

**Built (all in `zzz_derpy_iron_court_ui.lua`):**
- `ICUI.logged_name` names the Crown by its party name, `IC.key("party_name", "crown", player)` ("The Crown", or "The Throne-Sworn" for Dwarfs). This applies in the Record only; the cards and the Court tab keep the faction's name.
- A deed line whose `e.sw` is nil and whose party is not the Crown reads "The Legion, not yet at court, grew on ...". `IC.who_was` logs nothing for a party with no seat, so the mark is correct for the time the deed was done, not just at draw time.
- `ICUI.draw_log` gives every line the party's crest (`ICUI.crest`) on its plate colour, the way Petitions draws. News from another court wears that court's flag (`IC.house_icon(IC.CROWN, faction)`).
- `ICUI.set_row_icon` moves a crest to `ic_row_crest`'s y, the row's middle. The cell's y=2 belongs to the porthole, which fills the row, and it had left every crest 11px above its line on Petitions too. A portrait keeps y=2.

**Gates:**
- harness 1088, OK; 4 new checks: the Crown for both races, the unseated deed, the crest, plate and flag per line, and the crest centred while a face still fills the row. The bribe check now asserts "The Crown";
- 6 new mutants, all caught;
- preview `ic_log_dwf.png` / `ic_petitions_dwf.png` re-rendered and looked at: crests level with their text;
- built `C0A47D98`, `check_ic_release --pack` 0 findings, deployed to data/ byte-identical;
- the full mutation run is guarded in `mutation_guard_20261007f/`.

**Not changed:** the 560px gap between the Turn and Event columns. It is the shared row layout's, and the Event column's width is measured against it.

**Full mutation run on C0A47D98** (`mutation_guard_20261007f/`): 1218 mutants. 1217 were caught. 1 was a STALE ANCHOR: "the Record's figures left bare", which was aimed at the `draw_log` line this section rewrote. It was re-aimed to `ICUI.units(a.text)` and is caught. Every Lua file, the MCT file and the harness are byte-identical to the guards afterwards.

**Live, C0A47D98** (a new Overlords of Zharrduk start, `script_log_071026_1136.txt`, 0 script errors):
- Crown 4, Ledger 5, Chain 5;
- 7 starting lords recorded, including 2484, the one the old lookup missed;
- every starting lord's card read "1500" with its cost shown, the same format as CA's own candidates;
- Aldrash the Dominator (2401, a wounded lord of the faction's own) was left at CA's free re-hire;
- hiring Kastabull Fyrskyr (2704): the author saw the treasury drop, and no trait card was shown.

Not read: the rank raise, because detailed_log is off; and the saved list after the hire, because the game closed first.

**Open:** a garrison captain made at a capture (a colonel, 2709 at Plains of Zharr) is stamped with house and background showing messages, so every capture shows two Trait Gained entries. Colonels are court members by design; whether to stamp them quietly is the author's call.
