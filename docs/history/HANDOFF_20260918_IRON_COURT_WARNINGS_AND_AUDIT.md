# Iron Court, 2026-09-18: crests, two warnings, and an audit

One day on `derpy_iron_court.pack`. Six threads, in the order they happened. Final deploy
**8,672,151 bytes**, **441 harness checks**, **188 mutants, 0 unexplained**.

Everything below was found with the game shut unless it says otherwise.

---

## 1. Crash triage, and where the script log actually lives

Two dumps on the 18th:

| dump | code | address | site |
|---|---|---|---|
| `D2026-09-18_T10-13-36` | `0xc0000005` | `0x1415d3e7f` | `Warhammer3.exe+0x15D3E7F` — **new** |
| `D2026-09-18_T10-51-56` | `0xc0000005` | `0x14236c79b` | `Warhammer3.exe+0x236C79B` — the recurring `0x236CCC6` family |

The 10:13 one was first read as a battle-load crash and **that was wrong**. `mp_log.txt` runs at
wall clock minus 8h, and its `REPORT_BATTLE_COMMENCE` at 10:13:17 was an **auto-resolve**, not a
battle load: the wh3-mcp heartbeat logged `in_campaign=true` at 10:13:27, nine seconds after the
dump, and `in_campaign()` is `core and core:is_campaign()`. The campaign VM was alive, so the
fault is inside the **end-turn sequence**.

No `bad_mods_report.txt`, so nothing was rejected at load.

### The log location, which cost two passes

`script_log_<ddmmyy>_<hhmm>.txt` is written by `all_scripted.lua` with
`io.open(filename, "w")` and a **bare relative name**, so it lands in the process CWD — the
**game install folder** — while `mp_log.txt`, `modified.log` and `gfx.log.txt` all live under
`%APPDATA%\The Creative Assembly\Warhammer3\logs\`. Looking in AppData and finding none is how
"there is no script log" gets concluded. Recorded in
`memory/wh3-script-log-needs-a-pack-flag.md`.

### And the gap is real

Having found the logs, the next conclusion — "logging was never off, the memory is wrong" —
**was also wrong, and is retracted here**. The files run continuously through 17 Sep 23:16 and
then stop until 18 Sep 13:18. **Both morning dumps fall inside that gap**, so there is still no
Lua trace for either.

A scan of all 39 mods in `used_mods.txt` finds exactly one carrying
`script/enable_console_logging`: `derpy_debug_script_log.pack`, which is enabled now. Logs
existed on 16-17 Sep before that pack was built, so something else carried the flag then and has
since been disabled or rebuilt without it — which is the mechanism the memory describes.

**The next crash will be traced. These two cannot be.**

---

## 2. A greenskin was speaking for a Chaos Dwarf house

Reported off a screenshot: the Legion of Azgorh party card led by "Belegurn Stormbreaker",
wearing a greenskin porthole.

### The race tell is the VO column, and the key lies both ways

`agent_subtypes` has **no culture or subculture column**, and CA documents `culture()` and
`subculture()` on the **faction** only. The only column that separates them is
`audio_voiceover_actor_group`, and the subtype key is actively misleading in both directions:

| subtype key | unit | VO actor group | actually |
|---|---|---|---|
| `wh3_dlc23_chd_overseer_hobgoblin_spawned_army` | `wh3_dlc23_chd_cha_overseer` | `..._Chaos_Dwarf_Overseer` | **a Chaos Dwarf** — hobgoblins are the army he spawns |
| `wh3_dlc23_chd_gorduz_backstabber` | `wh3_dlc23_chd_cha_gorduz_backstabber` | `..._Hobgoblin_Gorduz` | **a hobgoblin** |

The first of those was blacklisted on the strength of its key before the VO column was checked,
which would have silenced a real Chaos Dwarf. Across all 30 candidate lords (13 `derpy_*`, 17
vanilla) **exactly one** is a greenskin.

Also: the bare token `"orc"` matches **s-orc-erer**, and flagged all four `sorcerer_prophet`
subtypes on the first pass. The filter is `('hobgoblin', 'goblin', 'greenskin', '_grn_',
'_orc_')`.

### The rule is a blacklist on purpose

`IC.NOT_DWARF` holds one key. `IC.may_speak` returns **true** for a man whose subtype the engine
will not name, so the failure direction is today's behaviour rather than a house with nobody to
speak for it. The Crown's throne branch is deliberately untouched — the man on the throne speaks
for the Crown whatever he is.

A thrall still **belongs** to his house and still counts toward its weight; he is only kept off
its card. `gen_iron_court.check_not_dwarf()` re-derives the set from
`faction_agent_permitted_subtypes` + `agent_subtypes` and reports both directions, so the list
is gated at build time.

### The fixture bug worth keeping

The first harness check seated Gorduz in a house he can never be in, and **passed vacuously**.
`IC.house_of_character` returns `IC.CROWN` for any legend **first**, and Gorduz is in
`IC.LEGEND_SUBTYPES` — so the check ran on a one-man house and proved nothing. What caught it was
an assertion on `members == 2`, added as a loud precondition rather than as a claim. Every check
was rewritten onto the Crown.

A second mutant was needed too: the first one ("a thrall filtered out of his house") tripped that
precondition rather than the claim about card ORDER, so a second was aimed past the membership
count at the `is_lordly` branch.

---

## 3. Four rising-house flags, from supplied art

All four dormant rebel factions share **one** `flags_path`, so two rebellions on one map drew the
same banner — and **there is no runtime setter for a faction crest at all**. `tools/make_ic_rebel_flags.py`
builds six files per house against CA's
`ui/flags/wh3_dlc23_chd_chaos_dwarfs_rebels/`: `mon_24`, `mon_64`, `mon_256`, `mon_icon`,
`mon_rotated`, and `mon_banner.dds` (BC3_UNORM, 9 mips, 87,536 bytes — texconv, because Pillow
silently writes something else).

The first version drew the device procedurally and was replaced by supplied art. Faults that
**only a rendered preview found**, in order:

1. CA's old device still visible under ours — its outline is a pale stroke well below the hue
   band's saturation floor, so erasing the band lifted the green and left a line drawing. Fixed
   by dilating the mask.
2. Flat paint — the device took its shading from the already-blurred plate. Fixed by shading from
   the original.
3. A dark stain shaped like CA's device — blurring un-premultiplied RGBA darkens, because the RGB
   under a zero alpha is `(0,0,0)`. Fixed with a ring-mean fill.
4. A flat lighter patch — a single averaged fill ignores the plate's vignette. Fixed with 12
   passes of diffusion that reassert the known pixels each time.
5. **Everything drawn high, and on the battle banner outside the flag entirely.** Anchoring to
   CA's device box inherits three of CA's decisions: the box is widened by four satellite marks,
   composed for a tall narrow flame, and sits ~20px above the plate's centre. Re-anchored to the
   **plate's** centroid at the ratio and offset measured off the supplied art.
6. A pale grey block on the left edge of both battle banners.

### ERASE_SPECK, which is finding 6 and the one worth writing down

A **four-pixel** speck of CA's hue band near the banner's edge, grown by a 23px dilation into a
27px square of flat ring-grey. It also dragged the erase box 49px left and 48px down, and that box
is what sets the dilation radius and the ring the fill is averaged from.

The existing 2% despeckle rule is **the wrong threshold here**, because CA's device has four
satellite marks that are 1.5-2.3% of it:

| file | device | satellites | strays |
|---|---|---|---|
| `mon_24` | 70 | — | — |
| `mon_64` | 355 | 9 8 8 8 | — |
| `mon_256` | 4797 | 92 91 89 85 | — |
| `mon_icon` | 4748 | 89 88 86 81 | 14 1 1 1 |
| `mon_rotated` | 265 | 6 6 6 4 | — |
| `mon_banner` | 5262 | 122 117 114 98 | 4 4 3 1 1 1 1 |

Smallest real satellite 1.51%, largest stray 0.30%. `ERASE_SPECK = 0.008` sits between with 2.7x
and 1.9x margins. **It has to be a fraction**: an 8px part is real on `mon_64` while a 14px part
is a stray on `mon_icon`. After the fix the banner's box lands on (68,48,188,180) against
`mon_256`'s (67,47,188,180).

Two selftest assertions, both proven red: removing the despeckle reports 9 and 12 parts; reusing
the 2% rule reports four layouts with "a part too close to ERASE_SPECK to call" — which is the
threshold collision stating itself.

### Tint

Each flag's hue is **not chosen here**. `target_hue` reads `gen_ic_ui.HOUSE_COLOUR`, so a flag
wears the colour its house wears in the panel: Crown `#8C2F26`, Legion `#3F4A8C`, Tower
`#6B3A8C`, Hearth `#2F5D6B`. `CREST_TINT = False` ships the artist's white instead; both
variants render. The artist's luminance is kept where the supplied art has any, so the cracks
and weathering survive the tint — they do, in all four.

Confirmed working in game by the author.

---

## 4. Three turns of warning, on both things that end a house

Asked for as "add back the 3 turn warning until secession and splintering". It was never there —
the "three-turn clock" in §8.1 of `IRON_COURT_VS_ROME2.md` is the **Provoke** move, and the
mockup's "3 turns to answer" never shipped. Two different shapes:

**Secession** had a five-turn clock and exactly one card, at the top of it. Four silent turns,
then a province gone. It now raises `secede_soon` when the count **enters** its last
`IC.TUNE.warn_turns`.

**Provoke sets the clock outright** (`plot_provoke_clock`), which skips the branch `secede_warn`
lives in — so the one move whose entire purpose is to shorten a countdown was also the only way to
be put on one in total silence. It raises the card too, on the same crossing test. *The naive fix
still misses this: a clock SET to `warn_turns` never decrements onto it.*

**Splintering had no clock at all.** `IC.splinter` fired on the turn the Crown's loyalty crossed
`splinter_loyalty`, with its card arriving in the same frame as the thing it announced — a
notification, not a warning. There was nothing for a warning to count down. It now runs a
`warn_turns` count, cancelled if the Crown recovers and restarted from the top with its own card
if it dips again. **This is a balance change: your house now takes three extra turns to come
apart.**

Equality (`clock == warn_turns`), never `<=`: the obvious spelling is true on every turn beneath
the line and cards the player three times for one secession. Nothing about the first card's
timing can see that, so it has its own check.

New events `secede_soon` (2609) and `splinter_warn` (2610), appended — an index is derived from
POSITION in `gen_iron_court.EVENTS` and inserting above renumbers everything after.

### The split count is a fifteenth save field, not a reuse of `clock`

`tick_secession` runs the Crown through its placated branch and **zeroes `house.clock` every
turn**, and `tick_provinces` reads a non-zero clock as "this governor's party is on the way out"
and drifts his province at `prov_drift_angry`. Overloading it would have been a one-word change
that silently rotted the Crown's own provinces while it came apart. A trailing field is the
migration idiom this format documents: an old save has fourteen and its Crown is simply not
counting down. Checked both directions.

`ICUI.mood` now reads `"SPLITS 3"`. That was a **regression introduced by this change** and found
by the audit in §5, not by a check: a rival read `SECEDES 3` and the Crown read a bare
`SPLINTERING` — the same situation stated two ways, with the number missing from the one the
player is standing in.

### Two findings from re-aiming the existing checks

- **The change made four negative splinter checks unbreakable.** `IC.splinter(F) == nil` is now
  true on the *warning* turn as well as on a refusal, so four proofs that a split must NOT happen
  would have gone on passing with their gate deleted. All eight existing splinter call sites were
  re-aimed through a `split_out` helper that runs the count out. **Four unbreakable assertions is
  a worse outcome than one failing suite**, and only the positive checks failed loudly.
- **One old mutant survived a green harness.** "A party judged on the turn it was born" proved the
  ordering by *inserting* a second `IC.splinter` above `tick_secession` and leaving the original
  below. That expressed the fault only while a split was instant; with a count in front, the
  inserted call merely advances it and the original still lands the split, so the ordering never
  changed and the harness was right to stay green. **The mutant had stopped expressing its own
  fault.** It now moves the call rather than duplicating it.

---

## 5. The audit

A mechanical sweep for things declared and read by nothing — the shape `IC.TUNE.sufferance_share`
had. Five passes over both Lua files: dead TUNE keys, `LOG_KINDS` against what is written, events
against what is raised, functions against their callers, loc against the generator.

**Most of it was false positives, and how they were false is the useful part.** 34 TUNE keys and
19 log kinds came back "read by nothing" because they are reached through **computed keys** —
`IC.TUNE[plot.cost]`, `IC.TUNE["plot_chance_" .. plot_key]`, `IC.log(faction_key, plot_key, ...)`.
A loc sweep was written and **abandoned**: it re-answers what `import_iron_court.py` already
gates, and its own output was mostly DB keys the engine reads and no Lua ever names.

What survived checking:

| finding | status |
|---|---|
| `pressed` / `dissolve` dropped by `IC.LOG_KINDS` | **fixed**, §6 |
| the split can roll an interest nobody belongs to | **fixed**, §6 |
| §2.10 never built | **fixed**, §6 |
| `ICUI.mood` showing no split count | **fixed**, §4 |
| stale term on a dead officer | open — §4 of `IRON_COURT_VS_ROME2.md` |
| §2.7 ambition, §2.11 dignitaries | open, zero references either |
| `ICUI.origin_name` dead | open — its comment says "drawn on the office card"; a man's origin never appears there |
| `ICUI.gov_effect` dead | superseded on purpose; delete |
| `IC.house_in_court` dead | delete |
| `CampaignUI.SetOverlayMode` never called | see §3 of `IRON_COURT_VS_ROME2.md` — CA never calls it either, so probe before designing |
| `cm:force_non_aggression_pact` undocumented, 8 call sites | **lords pack**, not this one |

### Two claims corrected by the audit

- **"The countdown never reaches the player after the opening card"** — wrong. `ICUI.mood` draws
  `SECEDES 3` and the alert strip names the soonest clock. What was missing was a *feed card*.
- **"A splinter party is born empty, no man re-homed"** — wrong in general. Men re-home implicitly
  through `house_of_character`. The real fault was narrower and is §6.
- A grep truncated by `head` produced **"there are no splinter checks at all"**. There were seven.

---

## 6. The three fixes, in the order they were authorised

### `pressed` and `dissolve`, and the gate

Both added to `IC.LOG_KINDS`. `IC.log`'s first line is
`if not IC.LOG_KINDS[kind] then return false end`, so both were written by the model, eaten by the
whitelist, and each carried a finished sentence in `ICUI.intrigue_text` that could never draw:

- `pressed` — *"X sees the Crown weak and begins to move."* The start of the pressure route to
  secession and the only thing the court does with no input from the player at all.
- `dissolve` — *"X has no one left to speak for it."*

**The gate is the real fix.** This had been half-known since the splinter shipped: the `LOG_KINDS`
comment names both as dead renderers, and a check asserted `IC.LOG_KINDS.splinter` "so splinter is
not a third". *A check aimed at one name stopped one name, which is why there were two.* The new
check lifts the renderer's `elseif` branches out of the UI source, compares the two sets both
ways, then renders every kind to confirm none falls through to nil.

It reported a third fault on its first run — and that was **its own pattern**: Lua's `%w` has no
underscore, so `snub_on` matched as `snub`. `[%w_]`.

### §2.10 — what a secession would cost

See `IRON_COURT_VS_ROME2.md` §2.10, updated with the full build note.

### The split rolls an interest somebody belongs to

The eligible set is every party some non-legend in the faction has the background for. When
nothing qualifies there is no split — which is what an empty pool already did.

Two things from the fixture work:

- **Every splinter fixture built a faction with no characters**, so all of them went red at once.
  They now seat a courtier of an unseated background, which is what a real court looks like.
- **The legend exclusion survived its mutant** on the first run, so it got a check rather than
  being dropped. `house_of_character` answers the Crown for a legend first and whatever else is
  true of him, so counting his background makes his interest eligible and he then does not join
  it — the empty party by a longer route.

And one fixture correction worth knowing: **`IC.turn` runs `ai_fill_offices` for a non-human
faction**, and every seat it fills adds `weight_per_office` to the Crown. Over the extra turns the
count now takes, that lifted a newcomer's share from 71% to 20% and tripped a precondition. Loops
that run a count out through `IC.turn` must re-pin weights, not just loyalty.

---

## 7. State at the end of the day

- `derpy_iron_court.pack` — **8,672,151 bytes**, deployed to `data/`, enabled in `used_mods.txt`.
  Flag art verified byte-identical in the deployed pack; all Lua changes verified present by
  reading them back out of it.
- **441 harness checks, 188 mutants, 0 unexplained.** `gen_iron_court --check`,
  `gen_ic_ui --check`, `check_lua_api`, `check_lua_undeclared` and the six panel previews all
  green.

### Open, and not mine to close silently

- **No Lua trace for either 18 Sep crash** — both fall in the logging gap. Logging is on now.
- **The wh3-mcp bridge is wedged** and needs a game restart. Cause: a probe chunk ending in
  `table.concat(out, "\n")` — a backslash escape, which `memory/wh3-mcp-bridge-wedges-after-eval-error.md`
  forbids outright. It also explains why a `string.find(st, "chd", 1, true)` filter in the same
  session silently matched nothing.
- `wh3_dlc23_chd_chaos_dwarfs_qb1`'s faction leader is `wh3_dlc23_chd_infernal_castellan`, which
  is **not** in `IC.REBEL_GENERALS`. Either it rose before the 2026-09-17 fix or something else
  set it. Needs the bridge.
- `derpy_director.pack` duplicate event indices (7301/7302) — handed to another session.
- The remaining audit items in §5.
