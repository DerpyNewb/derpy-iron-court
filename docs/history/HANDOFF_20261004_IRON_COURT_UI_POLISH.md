# Iron Court - status check, preview fixes, UI polish (2026-10-04)

Continues `HANDOFF_20261003_IRON_COURT_BAR_BORDER_AND_LIVE_CHECKS.md`. Starting point: build
`05C8F762`, in data/ and `Modpacks/` (same MD5), pushed as aa5723d, repo clean, harness 973.

## 1. Status found

- data/ == Modpacks == `05C8F762`; no Iron Court source newer than that pack; the public repo
  `repos/derpy-iron-court` level with origin/main (`sync_iron_court_repo.py --check`: 0 drift).
- Stale records: the `MY_MODS.md` entry still says `47E345D7` / 972 checks; the SESSION_INDEX line
  for the 10-03 handoff still lists the vote-bar border, button overrun and labels as open (fixed
  in its section 5, owed only in game).
- Everything still open across the IC handoffs was gathered into one reply: unbuilt (votes on
  seats/governors, laws sub-project 2), release (no Workshop entry; patch notes stop at
  `D3712F85`), unfixed (Black Kraken's wholesale party change between the turn-19 and turn-20 saves,
  rebel pool running out, the Hold/leader and one-turn-old-rules governments minors, deeds minors),
  three surviving mutants, and the long in-game owed list. Sources: GOVERNMENTS handoff sections
  5/8/9/10, KNOWN_BUG_PASS section 7, GOVERNORS_MAP section 6, AI_LIVE_CHECK "Still open".

## 2. Preview tool fixes (`tools/preview_iron_court.py`) - the panel was right

Four faults in the PICTURE, none in the game:
- `ic_gov` / `ic_gov_btn` drew on every tab. The Lua's tab switch hides them by name (they are not
  on `CONTROL_KEYS`); the preview now hides them off the court view and raises if the Lua stops
  doing `show(comp("ic_gov", panel), false)`.
- `ic_fill` drew as an empty red bar on Offices: its label is now read from `ICUI.FILL_LABEL`.
- Intrigue printed two footer lines over each other: in game `ic_alert` holds ONE string (`warn` is
  draw_intrigue's sentence on that tab), so the sufferance line is blanked there when
  `intrigue_lines` has anything.
- The header said "0 of 14 seats filled" over a ziggurat with seven holders: now
  `len(DEMO_OFFICES)`.

## 3. Polish, in `tools/gen_ic_ui.py` and the panel Lua's mirrored tables

- **Government chooser centred down the page**: `gov_card_cells` gains `dy = 84` on the cards and
  on `ic_gc_now` / `ic_gc_nowrule` (block ran 134..850 with 230px of bare backdrop under it).
- **Law card text inset 10 -> 14**: `ic_law_fx1..3` (14, y, 290, 18), `ic_law_foot` (14, 114, 238, 20).
- The Lua's `ICUI.PANEL_XY` / `ICUI.LAW_CHILD_XY` were synced by a scratch script that rewrites only
  differing literal entries (86 lines: 82 chooser + 4 law). `import_iron_court.py` compares them.

## 4. Do not re-derive

- **The law effect cells cannot narrow below 290.** 20k measures at 1600x900 too: 'Raw Materials
  used -15%' is 234px there, and a cell of 288 gives 234 usable, which FAILS (needs strictly less).
  282 and 288 were both tried and refused. Inset can only come from x, so the cell ends 2px inside
  the card.
- **The government line's `->` was left alone.** `ic_gov` is 622px and the preview's own calibration
  says PIL understates the game font by a third or more, so the line is already near full; adding
  words risks a clip nothing measures (20k covers the laws tab, not `ic_gov`).
- **The office card's cut holder names ("Dazminus...") are by design** - the 364x184 card is fixed
  by the ziggurat and the author declined reshaping it (CARD_LAYOUT comment, 2026-09-14).
- `check_lua_undeclared.py` on the UI file alone lists IC.* names; the untouched file does too. It
  must be run the way the importer runs it, over the set.
- `gen_ic_ui.py` imports `gen_guilds_ui` and `preview_iron_court.py` imports `preview_guilds_panel`;
  a parallel session (modding-for-resources-08) was editing both Guilds tools on 2026-10-04.

## 5. Build and deploy

Built as **`E64B290E`** (MD5) by `deploy_iron_court.py`, 1818 files verified in the saved pack,
deployed to data/ byte-identical (backup `Modding Files/Backup/deployed_auto/...bak_pre_auto_20261004_100624`
holds `05C8F762` - backups no longer go beside the pack in data/). Same byte size as `05C8F762`:
every changed number kept its digit count. Not pushed to GitHub (`sync_iron_court_repo.py`, then
commit inside `repos/derpy-iron-court`).

Gates: `gen_ic_ui.py` write + `--check` + `--selftest` (28 files, 1052 components, 3973 guids),
luac, harness 973, `check_lua_api` 0, literal-left 0, `preview_iron_court.py` + `--selftest`, the
importer's own drift checks inside the deploy. The mutation run was not re-run: no anchor names a
changed number (the one `ic_gc_` hit is draw code).

## 5b. Shader effects on the doctrine and on selection (2026-10-04, later)

Author: "add possible visual effect shader to action, such as active doctrine or selecting it ...
CA uses a lot of shader ui effects so base it on that".

**Survey of CA's own use** (ui3.pack, by state; scratch scripts `ca_shaders.py` /
`ca_shader_states.py` in the session scratchpad): brighten_t0 7263, set_greyscale_t0 2194,
drop_shadow_t0 1194, glow_pulse_t0 876, overlay_t0 177, multiply 123, distortion 68,
red_pulse_t0 34. Conventions: HOVER = `brighten_t0`, commonest value 1.0 (0.3 and 0.5 the gentler
ones); SELECTED = brighten 1.0, also 1.0 on selected_hover (2.0 is a minority). CORRECTED from "hover
0.5, selected_hover 2.0" against `docs/UI_SHADERS.md`'s per-state census - this pass's 80KB-window
state lookup misattributed states. What is ACTIVE or SELECTED breathes with `glow_pulse_t0` on a separate glow image
(Skull Throne ritual plate on `selected` at 0.85,0.10,1.35; Hell-Forge `skull_torch_light` on
`selected`; Hell-Forge `heat_glow` on an active category block at 0.80,1.50,0.80). The Tiger Court
(CA's court panel) uses `overlay_t0` 3.0 on hover and `multiply` 3.0 on down for its flags.
In the twui, a state is an element NAMED for the state (`<standard name="standard">`), not `<state>`.

**Built:**
- `ic_gov_glow`, a new panel cell (39, 864, 48x48) wearing MARK_LAYERS (the Hell-Forge heat glow
  at CA's active-block values), centred on the government's inline icon, draw tier -0.5 (over the
  Crown's plate, under `ic_gov`). Shown and hidden with `ic_gov` by `ICUI.draw_gov` and the tab
  switch. Not in CROWN_CELLS (20b2 forbids crossings); `check_gov_glow()` holds its centre on the
  icon and its order under the line.
- A government chosen (`ICUI.ANSWERS.doctrine`, success, on the Court tab): refresh, then the
  doctrine sound and `ICUI.burst("ic_gov_glow")` (CA's seat-claim starburst). A refusal does neither.
  **No `pulse_uicomponent` on the glow** (removed in `F4C63911`): CA's `lib_campaign_ui.lua:2310`
  says the standard highlight "inadvertently clears active shaders" and caches the STATE technique
  to restore it. Whether it also clears an IMAGE-level shader like the glow's is UNKNOWN, and a
  cleared glow would stay dead for the session. The harness asserts no pulse on `ic_gov_glow`; the
  mutant that puts it back is caught.
- The chosen party card's gold frame (PARTY_SEL_INDEX) and the chosen law card's red glow
  (LAW_GLOW_INDEX) breathe: `SELECTED_PULSE`, glow_pulse_t0 at the seat rim's ToZ furnace values.
  The law IN FORCE (LAW_SEL_INDEX) stays still on purpose: four are always in force.
- Harness 974 (new check: the burst on a chosen government and no pulse on its glow, neither on a
  refusal; the glow in the known-cells list and in the Crown's-box visibility check). Four new
  mutants (`gov fx: ...`), all caught.
- **Same risk, older code, left alone:** `ICUI.confirm(<office card>, false, ...)` (panel Lua
  ~8516, a refused seat action) pulses a card that carries the breathing seat rim. A refused seat in
  game answers whether an image-level shader survives `StopPulseHighlight`.

**Not done, and why:** a hover look on law/party/gov cards. A hover STATE carries its own copy of
every layer, and the Lua repaints the glow and frame layers by index on the standard state only,
so hovering a chosen card would drop its glow. `ShaderTechniqueSet` at runtime was rejected by the
2026-09-28 spec (it replaces the component's technique). Needs an in-game probe first.

Built as **`6DE3D85C`** (MD5), deployed to data/ byte-identical (backup `Modding Files/Backup/deployed_auto/...bak_pre_auto_20261004_104723` holds `E64B290E`), not pushed. Gates: gen_ic_ui write + selftest (28 files, 1054 components, 3981 guids), harness 974, the four `gov fx` / government-row mutants caught, luac, API, literal-left, undeclared unchanged, deploy's own gates. Preview draws the glow under the icon (shaders themselves are invisible to it).

Then **`F4C63911`** (2026-10-04 11:09): the pulse removed after `docs/UI_SHADERS.md`'s trap was
read against CA's source. Deployed byte-identical (backup `...bak_pre_auto_20261004_110941` holds
`6DE3D85C`), pushed to GitHub as c97f25b. Harness 974, the four `gov fx` mutants caught, luac, API.

## 6. Open

- In game: the chooser at its new height at 1600 and 2560; law-card text at the new inset;
  the government glow breathing ON the icon (its centre assumes an 18px icon after 6px of inset);
  the burst after Change Doctrine; the chosen law and party cards breathing; a refused seat's
  card still breathing its rim after the red pulse ends.
- Everything in section 1's open list.
