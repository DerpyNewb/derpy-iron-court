# Iron Court Ambition - design

Approved in conversation 2026-09-20. This is the first of the two remaining parity items in
`docs/IRON_COURT_VS_ROME2.md`: character ambition changes how strongly personal standing
contributes to a party's influence.

Implementation plan: `docs/superpowers/plans/2026-09-20-iron-court-ambition.md`.

---

## 1. Outcome

Every living Chaos Dwarf courtier has a permanent, visible ambition band. Personal standing
continues to gate offices and governorships exactly as it does now, but it also contributes a
small derived amount to the influence share of the courtier's party. Ambition multiplies that
derived contribution.

The player can therefore raise an ambitious ally, suppress an ambitious rival, or prefer a
steady candidate even when two characters have similar standing. Existing office, plot and
governor weights remain meaningful.

## 2. Bands and distribution

| Slug | Character trait | Factor | Roll weight |
|---|---|---:|---:|
| `cautious` | `derpy_ic_ambition_cautious` | 75% | 25 |
| `steady` | `derpy_ic_ambition_steady` | 100% | 50 |
| `ambitious` | `derpy_ic_ambition_ambitious` | 125% | 25 |

The expected factor is exactly 100%, so adding ambition does not bias a large random court up or
down. Extremes are uncommon enough to stay distinctive. The roll uses
`cm:random_number(100, 1)`, whose argument order is maximum first.

The stored value is the slug, not the factor. The table above owns the factor, roll weight,
display name and trait key. No caller duplicates those mappings.

## 3. Influence arithmetic

The current party weight has two parts:

```
saved house weight + derived governor weight
```

Ambition adds a third, derived part:

```
member weight = sum(character standing * ambition factor / 100 / 100)
party weight  = saved house weight + governor weight + member weight
```

The second division is the scale: **100 personal standing equals 1 party weight at Steady**.
Examples:

| Standing | Cautious | Steady | Ambitious |
|---:|---:|---:|---:|
| 100 | 0.75 | 1.00 | 1.25 |
| 400 | 3.00 | 4.00 | 5.00 |

An ordinary office is currently worth 6 party weight and a governorship 3, so a 400-standing
courtier matters without replacing the existing political levers. Fractional derived weight is
kept until the existing share display rounds the final percentage. Rounding each character
individually would erase the early-game contribution of several low-standing courtiers.

All living faction characters contribute, including heroes. This matches the existing rule that
all living characters hold and earn standing. A character whose background currently resolves to
the Crown contributes to the Crown. A dead, transferred or seceded character contributes nothing.

`house.weight` remains the saved, mutable office/plot component. Ambition never writes into it,
so repeated refreshes cannot inflate the court and old saves do not need their existing weights
rewritten.

## 4. Model interfaces

The implementation adds these model-owned interfaces:

```lua
IC.AMBITION = {
    cautious  = {factor = 75,  roll = 25, trait = "derpy_ic_ambition_cautious"},
    steady    = {factor = 100, roll = 50, trait = "derpy_ic_ambition_steady"},
    ambitious = {factor = 125, roll = 25, trait = "derpy_ic_ambition_ambitious"},
}

IC.ambition_slug(faction_key, cqi)       -- string or nil
IC.ambition_factor(faction_key, cqi)     -- integer percentage; 100 if unstamped
IC.stamp_ambition(faction_key, character)-- true only when state or trait changed
IC.member_weight(faction_key, slug)      -- non-negative derived number
IC.house_weight(faction_key, slug)       -- complete weight
IC.total_weight(faction_key)             -- complete court weight
IC.share(faction_key, slug)              -- percentage
```

Changing the weight functions to accept `faction_key` and `slug` is intentional. The current
`IC.house_weight(house)` cannot discover which living characters belong to that house. Caching a
third transient field would become stale after battle rewards, plots, recruitment and deaths;
the live derivation has one owner and the court contains only a small character list.

Every model and UI call site moves to the new signatures in the same change. There is no
compatibility promise for these internal Lua functions outside this standalone pack.

## 5. Persistence and migration

`new_court()` gains:

```lua
ambition = {}, -- [character cqi] = ambition slug
```

`IC.pack` appends an eighth pipe-delimited section containing `cqi,slug` entries. `IC.unpack`
accepts a missing field, validates the slug through `IC.AMBITION`, and ignores malformed entries.
The first seven fields and all fifteen house fields remain byte-shape compatible.

An old save therefore loads with an empty ambition table. The next `IC.stamp_court` rolls each
living character once, writes the marker trait, and the normal turn-end save persists the result.
Before that stamp, `IC.ambition_factor` returns 100 so an early UI read remains safe and neutral.

The living-character prune that removes stale standing also removes stale ambition. This prevents
a recycled CQI inheriting a dead character's band.

## 6. Stamping and reconciliation

`IC.stamp_court` calls `IC.stamp_ambition` beside origin and background stamping. The hired-officer
path calls it immediately before appointment, so a newly bought officer affects the refreshed
court without waiting for the next turn. Confederated characters are covered by the existing
poll and the subsequent court stamp.

Saved state is authoritative. If a character has no ambition trait, or has a different ambition
trait from the saved slug, stamping removes every wrong ambition marker and applies the saved one.
If state is missing, stamping rolls once and then applies it. It never infers state from a trait,
because a stale trait must not silently rewrite the save.

Trait application is silent. Recruiting several characters must not produce several event cards.

## 7. Player-facing presentation

The generator emits three ordinary one-level traits through the existing `emit_trait` path:

- Cautious: "His standing contributes 25% less to his party's influence."
- Steady: "His standing contributes normally to his party's influence."
- Ambitious: "His standing contributes 25% more to his party's influence."

No gameplay effect rows are attached; Lua owns the political arithmetic. The traits appear in
CA's character trait panel and use the existing Chaos Dwarf trait category.

The existing character standing plate keeps its component and gains a tooltip line with the
band, multiplier and effective party-weight contribution, for example:

```
Ambitious: 400 standing x 1.25 = 5 party influence
```

No TWUI XML or generated art changes are required.

## 8. Failure handling

- A missing faction or character list returns zero member weight rather than throwing.
- A character-interface call that can fail during teardown is isolated with the established
  `pcall` pattern; that one character contributes zero for the read.
- An unknown saved slug is ignored on unpack and receives a valid roll at the next stamp.
- A missing ambition value is neutral, never zero. A migration frame must not erase a party's
  member contribution.

## 9. Verification requirements

The shipped Lua harness must prove:

1. Roll boundaries produce 25/50/25 bands and use max-first RNG.
2. A saved character never rerolls across stamps or reloads.
3. Wrong and missing marker traits reconcile to saved state.
4. Old seven-field saves load and are neutral before stamping.
5. The eighth field round-trips multiple CQIs and rejects unknown slugs.
6. Hired and later-recruited characters receive ambition immediately or on the next stamp.
7. Dead/transferred CQIs are pruned from both standing and ambition.
8. At equal standing, Cautious < Steady < Ambitious contribution.
9. Member contributions preserve the 100-standing-to-1-weight scale and fractional sums.
10. Shares still total 100 and existing control/secession readers use the augmented share.
11. The standing-plate tooltip uses the model's factor and contribution rather than recomputing
    either from trait text.

Mutation tests must independently break the factor, scale, one-time roll, saved field, prune,
trait reconciliation and new `IC.share` call signatures.

## 10. Non-goals

- Ambition does not change how quickly standing is earned or spent.
- Ambition does not change appointment bars, plot odds, leader selection or loyalty directly.
- No player choice, reroll action or ambition-training system is added.
- No rebalancing of office, governor, plot or secession constants is bundled with the feature.
- No new panel component or art asset is added.

