# Iron Court - pane bar border, live influence grant, government check (2026-10-03)

Continues `HANDOFF_20261002_IRON_COURT_GOVERNMENTS.md` (its section 11 records the border build).

## 1. Built and deployed

- **`65333E8C`** (MD5 first eight), deployed to data/ by `deploy_iron_court.py` (backup
  `.bak_pre_auto_20261003_153741` holds `47E345D7`). Not pushed.
- A bronze border on the LAWS PANE's projection bar (`ic_law_p_bar`, 14px): one new cell
  `ic_law_p_barrim` on the bar's box, art `ui/derpy_ic/plates/law_bar_rim.png` from
  `frame_pixels(LAW_PBAR_RIM_PX, LAW_PBAR_RIM_BAND)` (frame_pixels now takes px and band), drawn
  `LAW_PBAR_RIM_OUT` = 3px outside the bar. It sorts after `ic_law_p_barnay`, so it draws over both
  sides. **Seen working in game** (author's screenshot of the pane).
- The three new constants are in the NOT_GEOMETRY list (`_classify` refuses an unclassified one).

## 2. Verified, and how

- `check_law_bar` refuses the rim declared before a side - seen failing by patching `_panel_order`.
- Harness: the pane-bar check asserts the rim is visible and on the bar's layout box; the
  known-cells list names it. Seen failing by moving the rim's Lua offset 1px. Harness 972.
- gen_ic_ui run + `--selftest` (28 files, 1050 components, 3965 guids), preview drawn, deploy gates.

## 3. Live game, through the wh3 bridge (no pack change)

- The `mcp__wh3__*` tools did NOT load in this session: `.claude.json` registers the server
  under the project key `G:/Modding for resources`, and the session ran as `g:\...`.
  `wh3-mcp/tools/send-eval.mjs` hardcodes a C: install. What worked: write
  `{"command":"eval","params":{"code":...}}` to `F:\...\Total War WARHAMMER III\wh3_mcp_command.json`
  and poll `wh3_mcp_result.json` (a 15-line Python sender; the eval handler pcalls the chunk and
  `IC`/`ICUI` are reachable from it).
- The author plays **`wh3_dlc23_chd_minor_faction`**: "Overlords of Zharrduk" is the player's own
  CROWN party (a confederate party carries a house name too - check `house_of_character` before
  assuming which). Crown = one man, `derpy_zharrduk`, cqi 1730. Granted +1000 with
  `IC.add_standing` (saves) + `IC.stamp_standing` + `ICUI.refresh`.
- A first attempt built a local debug pack for this; the author wanted the in-game route, and it
  was deleted (never reached data/).
- **Change Doctrine worked:** gov `chain`, only `derpy_ic_doctrine_chain` on the faction, a
  `doctrine_force` Record entry, 400 spent (1000 -> 600), `gov_cool` 16 (turn 1 + 15).

## 4. Do not re-derive

- Two bars: the PANE bar (`ic_law_p_bar*`, board view) and the VOTE bar (`ic_lv_bar`, 34px, crests,
  `ICUI.draw_law_bar`). Both now wear the same rim art (section 5).
- In the vote bar every AYE party fills from the left (the Crown, then a supporting party in its
  own colour), nay from the right, abstain is the grey between.

## 5. The vote screen, after the author's look (2026-10-03)

Reported: no border on the vote bar; button text over the buttons' ends; "Abstaining" and "Nay"
not aligned to the bar.

- **Why 20k passed the overrun:** `ic_lv_st_*` / `ic_lv_lvl_*` wear the skull-capped TAB art
  (`law_light` uses its selected state, so it stays), and `usable_w` gave them LABEL_TX's 6px.
  The bar between the caps is `box - 2 * TAB_TEXT_INSET` (46). `usable_w` now says so for
  `LAW_TAB_BUTTONS`; on the old sizes it reports all nine labels (seen). `measure_text` matched
  the screenshot's text widths to within 6px, so the measure was never the fault.
- **Two rows in the same 96px hand**, each heading inline on its left: Your side (3 x 204) and
  Decide it now (2 x 220) on row 1 at y 914, Your support (3 x 372) on row 2 at y 958. One row
  needs ~2040px with the caps and has 1848. Sized for 1600x900, where the box shrinks by 5/6 and
  the 46px caps do not - 190/350 passed at 1920 and failed there.
- **Vote bar border:** `ic_lv_barrim`, the pane's rim art, tier 1 in `_panel_order` so it draws
  over the segments and crests (`check_law_bar` refuses otherwise).
- **Labels:** `ic_lv_nay` right-aligned, its box ending at the bar's end; `ic_lv_abs` centred
  and MoveTo'd by `ICUI.draw_law_bar` over the abstaining gap, clamped `ICUI.LV_LABEL_GAP` (24,
  NOT_SCALED) clear of the aye and nay text by `TextDimensionsForText` of the strings it just
  wrote. The three label writes moved from `draw_law_vote` into `draw_law_bar` for that.
  Harness check "the vote bar's abstaining label sits over its gap..." - both mutants (no move,
  no clamp) seen failing. Harness 973.

Built as **`05C8F762`**, deployed to data/ (backup `.bak_pre_auto_20261003_170130` holds
`65333E8C`). Pushed to GitHub as aa5723d with every build since 9A66C3C8. `preview_iron_court.py` now draws `ic_lv_abs` at its dumped runtime x and
both rims after the segments, as the panel declares them.

## 6. Open

- In game: the two-row hand, the vote bar's border, the labels over a real bar.
- Still owed: the government line and Faction Effects bundle reading Slave-Lords.
