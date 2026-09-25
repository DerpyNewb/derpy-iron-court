# Iron Court Military Doctrine loyalty - design

Approved in conversation 2026-09-20. This is the second of the two remaining parity items in
`docs/IRON_COURT_VS_ROME2.md`: a provincial edict can improve a political party's loyalty.

Implementation plan: `docs/superpowers/plans/2026-09-20-iron-court-edict-loyalty.md`.

---

## 1. Outcome

The existing Chaos Dwarf commandment **Military Doctrine** becomes a political choice. When an
Iron Court governor is actively administering a province under that commandment, the governor's
party gains +2 loyalty per turn.

This uses a vanilla edict already present in every Chaos Dwarf campaign. It adds no ancillary,
skill tree, rite, DB row, pack dependency or new UI component.

## 2. Exact rule

The recognized key is:

```lua
wh3_dlc23_edict_chd_armaments -- display title: Military Doctrine
```

For each governed province:

1. The province must still be held and have an assigned governor in `court.govs`.
2. `IC.governor_active(faction_key, province_key)` must be true. Under the existing rule this
   means the assigned character is alive, still in the faction, and physically inside the
   assigned province.
3. The governor's current region must report the Military Doctrine key from
   `region:get_active_edict_key()`.
4. The governor's resolved party receives +2 loyalty in that turn's normal drift calculation.

Multiple qualifying provinces held by the same party stack: one gives +2, two give +4, and so on.
There is no separate cap. Every province requires an eligible governor, 150 standing for the
assignment, physical presence, and a commandment chosen instead of the other three vanilla
economic commandments.

Only Military Doctrine grants loyalty. Counting every Chaos Dwarf commandment would make the
bonus automatic rather than a choice. Giving all four different political effects is outside this
Rome II parity item.

## 3. Model interfaces

The implementation adds one query and one tuning value:

```lua
IC.MILITARY_DOCTRINE = "wh3_dlc23_edict_chd_armaments"
IC.TUNE.loyalty_military_doctrine = 2

IC.governor_edict(faction_key, province_key) -- edict key or nil
```

`IC.governor_edict` is pure campaign-state derivation. It does not save, apply bundles or modify
loyalty. It returns nil unless the existing `IC.governor_active` rule succeeds. It then resolves
the assigned character, reads `character:region()`, and calls the documented
`get_active_edict_key()` under `pcall`.

`IC.loyalty_terms` counts qualifying provinces while it performs its existing governor scan. If
the count is non-zero it appends exactly one term:

```lua
{
    label = count == 1 and "Military Doctrine" or
            string.format("Military Doctrine in %d provinces", count),
    n = count * IC.TUNE.loyalty_military_doctrine,
}
```

The existing `IC.loyalty_net` remains the sole sum used by both `IC.drift_loyalty` and the panel's
loyalty tooltip. No second arithmetic path is introduced.

## 4. API evidence and safety

`REGION_SCRIPT_INTERFACE:get_active_edict_key()` is documented and returns the active edict key,
or an empty string when no edict is active. CA's shipped
`wh2_dlc11_vampire_coast_loyalty.lua` uses the same character-region call shape for an edict-driven
loyalty rule.

The read is protected because region interfaces can be transient during character teardown. A
failed call, a null region, an empty key, or an unknown key means no bonus for that read; none can
abort the faction turn.

The harness's region stub must expose the documented method and allow each fixture to set its
edict key. The API validator must continue to compare stub methods with CA's interface index so a
test-only invented method cannot pass.

## 5. Persistence and AI

No state is saved. The term is derived from the map whenever the model or panel asks for the
loyalty breakdown. Changing the edict or moving the governor out of the province changes the next
read immediately.

The same rule runs for every Chaos Dwarf court. Human courts display it; AI courts receive the
same drift without UI-specific code.

## 6. Player-facing presentation

The existing loyalty tooltip gains the term automatically because it renders
`IC.loyalty_terms`. The label names Military Doctrine and, when stacked, the number of provinces.
No TWUI, generator, loc or binary DB work is required.

The vanilla commandment already carries its own name and effects. The Iron Court tooltip explains
only the political effect it is applying; it does not attempt to alter the vanilla commandment
tooltip.

## 7. Verification requirements

The shipped Lua harness must prove:

1. An active governor under Military Doctrine adds exactly +2.
2. A different Chaos Dwarf commandment adds zero.
3. An empty edict key adds zero.
4. An assigned governor outside the province adds zero and keeps the assignment.
5. A missing/dead governor adds zero without throwing.
6. Two qualifying provinces held by one party produce one named +4 term.
7. A qualifying province benefits the governor's resolved party, not the Crown or province owner
   by default.
8. A Military Doctrine province governed by another party does not benefit the party under test.
9. The net shown by the breakdown is exactly the delta applied by `IC.drift_loyalty`.
10. An engine error from `get_active_edict_key()` is isolated and produces zero.

Mutation tests must independently break the exact key check, active-governor gate, party routing,
per-province multiplication and inclusion of the term in the shared loyalty breakdown.

## 8. Non-goals

- The other three Chaos Dwarf commandments receive no political effect.
- No dignitary skill, follower, ancillary or hero action is added.
- No new commandment or alteration to vanilla commandment DB data is added.
- No loyalty is granted merely because a province has an edict but no active Iron Court governor.
- No bespoke event feed message is added for changing commandments.

