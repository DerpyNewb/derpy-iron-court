# Iron Court UI Feedback and Effects Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give the Iron Court panel CA's own Chaos Dwarf effects - a lit rim and a claim starburst on held seats, attention markers, answer sentences, change numbers and a fail look - so every player action and waiting decision shows on screen.

**Architecture:** Effects live in the panel's `.twui.xml` as extra image layers that ship a transparent placeholder (`MASK_NONE`) and are swapped to CA's rim by `SetImagePath`, the pattern the party card's gold frame and the Great Guilds' rim already prove. Breathing is CA's `glow_pulse_t0` shader declared on the layer. The claim burst is its own tiny layout file, created into the card on a claim and destroyed after it plays, the way `ICUI.card_fire` creates the embers. The Lua only decides which look each card wears.

**Tech Stack:** Lua 5.1 (campaign script), Python 3 generators (`tools/gen_ic_ui.py`, `tools/gen_iron_court_emitter.py`), the Lua harness `tools/_iron_court_harness.lua`, the mutation runner `tools/mutate_iron_court.py`.

**Spec:** `docs/superpowers/specs/2026-09-28-iron-court-ui-feedback-design.md`. Evidence: `docs/sessions/CA_CHD_UI_FX_20260928.md`, `docs/sessions/IC_FEEDBACK_AUDIT_20260928.md`.

## Global Constraints

- The workspace is NOT git. There are no commits: every "checkpoint" step is the harness run green plus the gates named in it.
- No emojis anywhere. Never write the word "rung". Player text in plain words: no "standing", "cap", "rep", "AI", "HUD" in any string the player reads.
- The three Iron Court Lua files, the harness, `gen_iron_court.py` and `mutate_iron_court.py` are LF. Edit with the Edit tool or byte-safe Python; never `sed -i` (it strips CRLF elsewhere and mangles escapes in heredocs).
- Harness: `"/c/Program Files (x86)/Lua/5.1/lua.exe" tools/_iron_court_harness.lua` - stops at the first FAIL, ends `iron court harness: ok (N checks)`. New checks go ABOVE `check("no parties' turn failed anywhere in the run"`.
- Never edit any file while `tools/mutate_iron_court.py` runs.
- A loc call from a listener or turn handler is a turn-1 CTD. No new loc keys are added by this plan; every new string is a Lua literal.
- Runtime components ignore `.twui.xml` offsets and dockpoints: everything is positioned with `MoveTo`.
- A 9-slice margin larger than half a texture's size samples the texture atlas and draws streaks in game while the preview looks clean. `MASK_NONE` is 300x164 and CA's rim is 299x877, so margin 40 fits both.
- Never keep a Lua reference to a UI component inside a `cm:callback`: the panel may be closed before it fires. Re-find the component by name from the panel inside the callback.
- Build only with RPFM open (`http://127.0.0.1:45127/sessions` answers 200) and the game closed. Build with `py tools/deploy_iron_court.py --no-copy`. Deploy to data/ ONLY when the author asks, after `cp` of the data pack to `.bak_pre_<name>_<date>`.
- CA art paths used (verified in `ui.pack`/`ui3.pack` by the research pass):
  - rim `ui/skins/default/dlc23_tower_of_zharr/district_complete_glow_02.png`
  - marker `ui/skins/default/dlc23_chd_hell_forge/heat_glow.png`
  - burst frames `UI/sprite_anims/warband_upgrade_starburst/starburst_` 0..19
  - sound `UI_CLICK_Begin_Ritual`

## Rulings against the spec (made while planning, ledger them at execution)

1. **Dim and red rims are extra layers with a fixed colour, not generated art.** The spec asked for `rim_dim.png` / `rim_red.png` derived from CA's rim. A layer's `colour` multiplies its image, so a second and third layer that hold the same CA rim under a different colour give the same look with no derived file, no PNG decoding of CA art, and nothing to prune. Cost if wrong: a colour that reads badly in game is a one-value change.
2. **The burst is created and destroyed per claim, not shown and hidden.** This removes the "does a sprite replay" unknown instead of probing it. Cost if wrong: none known; the creation route is the one the embers already use.
3. **The HUD button's attention glow is CA's `pulse_uicomponent`**, the call CA uses to make HUD buttons ask for attention and the one `ICUI.confirm` already uses, instead of a new glow child on the opener (the opener has a hover state, and a new layer's index differs between states). Task 1's in-game probe checks that the pulse is visible; if it is not, Task 4 falls back to a hidden marker component beside the opener.

4. **The preview does not draw the rim.** The spec's testing section lists it, but the rim is written by the Lua at runtime into a layer that ships transparent, and its breathing is a shader the preview cannot render - a static picture of it would review nothing the in-game check does not. The preview must still pass `--check` with the new layers. Cost if wrong: one extra drawing pass in `preview_iron_court.py` later.

## Review Focus

1. A card recycled from a held seat to a vacant one must lose its rim - the pool redraws every card every refresh, and a rim left on is a seat that looks held.
2. The governor list shares its row pool with four other views - a rim written on a Governors row must be cleared when the same row draws Log or Petitions lines.
3. The burst's destroy callback must not touch a component the player closed - panel shut within 1.3 s of a claim.
4. Attention markers and the button's tooltip must agree - a lit Offices marker with a tooltip reading "Empty seats: 0" is a contradiction the player sees.
5. A change number on the first draw after a load has no baseline - it must draw no suffix, not "+34".

---

### Task 1: Phase 0 - the office rim and the claim burst (in-game probe)

**Files:**
- Modify: `tools/gen_iron_court_emitter.py` (the `<image>` writer in `_state`)
- Modify: `tools/gen_ic_ui.py` (`CARD_LAYERS` neighbourhood ~line 1125, `_card()` ~line 3104, `GUID_PREFIXES` ~line 84, `ui_file_names()` ~line 3608, `build_xml()` ~line 3831, `check()` ~line 4040, selftest ~line 6128, `NOT_GEOMETRY` ~line 3352)
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_ui.lua` (constants near `ICUI.PARTY_SEL_INDEX` ~line 651, `ICUI.draw_offices` ~line 3699, `picked()` ~line 5884, `ICUI.NOT_SCALED` ~line 6192)
- Modify: `tools/_iron_court_harness.lua` (fake component `Destroy` ~line 5031; new checks)
- Modify: `tools/sync_iron_court_repo.py` (manifest, beside `derpy_ic_fire.twui.xml`)

**Interfaces:**
- Produces (Lua): `ICUI.RIM_ART` (string), `ICUI.RIMS` (table kind -> {look -> layer index}), `ICUI.set_rim(c, kind, look)` (look is `"lit"`, `"dim"`, `"red"` or nil for off), `ICUI.BURST`, `ICUI.PATH_BURST`, `ICUI.BURST_SECONDS`, `ICUI.burst(host_name)` (host_name is the card or row component NAME, re-found under the panel), `ICUI.SOUND_SEAT`.
- Produces (Python): layer keys `"shader"` and `"shader_vars"` understood by the emitter; `RIM_ART`, `RIM_MARGIN`, `rim_layers(looks)`, `OFFICE_CARD_LAYERS`, `CARD_RIM`, `BURST_FILE`, `burst_xml()`, `check_burst()`, `check_rim_slots()`.

- [ ] **Step 1: Write the failing harness checks**

First make the fake component's `Destroy` real, so a destroyed burst can be created again. Replace, in `fake_component`:

```lua
    function c:Destroy() end
```

with

```lua
    -- REMOVED FROM ITS PARENT, so a component destroyed and then created again
    -- is a new one - the claim burst depends on exactly that.
    function c:Destroy()
        self.destroyed = true
        local p = self.parent
        if p and p.children and p.children[self.name] == self then
            p.children[self.name] = nil
            for i = #p.order, 1, -1 do
                if p.order[i] == self then table.remove(p.order, i) end
            end
        end
    end
```

Then add these checks above the final check:

```lua
check("a held seat wears the lit rim and an empty one none, on a recycled card", function()
    IC.state = {}
    turn = 1
    local man = make_character(1, ANY_SEAT, "forge")
    make_faction(F, IC.CHD_SUBCULTURE, {man}, {})
    IC.add_house(F, IC.CROWN)
    IC.add_house(F, "forge")
    ICUI.sel, ICUI.pick = nil, nil
    local seat = IC.OFFICES[1].slug
    IC.court(F).offices[seat] = 1
    with_fake_panel(function(panel)
        ICUI.view = "offices"
        ICUI.refresh()
        local held = panel.children[ICUI.CARD .. "_1"]
        local empty = panel.children[ICUI.CARD .. "_2"]
        local lit = ICUI.RIMS.card.lit
        assert(held.images[lit] == ICUI.RIM_ART,
            "the held seat's rim layer holds " .. tostring(held.images[lit]))
        assert(empty.images[lit] == ICUI.MASK_NONE,
            "an empty seat's rim layer holds " .. tostring(empty.images[lit]))
        -- THE SAME CARD, EMPTIED: the pool redraws it, and a rim left on is a
        -- seat that looks held.
        IC.court(F).offices[seat] = nil
        ICUI.refresh()
        assert(held.images[lit] == ICUI.MASK_NONE,
            "the card kept its rim after its seat emptied")
    end)
end)

check("filling a seat plays the burst over its card, and the burst goes away", function()
    IC.state = {}
    turn = 1
    local man = make_character(1, ANY_SEAT, "forge")
    make_faction(F, IC.CHD_SUBCULTURE, {man}, {})
    IC.add_house(F, IC.CROWN)
    IC.add_house(F, "forge")
    local seat = IC.OFFICES[1].slug
    sounds, pulses = {}, {}
    local later = {}
    local saved_cb = cm.callback
    cm.callback = function(_self, fn, delay) later[#later + 1] = {fn = fn, delay = delay} end
    local ok, err = pcall(with_fake_panel, function(panel)
        ICUI.view = "offices"
        ICUI.refresh()
        ICUI.ANSWERS.appoint(seat .. "|1", true)
        local card = panel.children[ICUI.CARD .. "_1"]
        local burst = card.children[ICUI.BURST]
        assert(burst, "no burst was created in the filled seat's card")
        assert(burst.visible ~= false, "the burst was created and left hidden")
        assert(sounds[1] == ICUI.SOUND_SEAT,
            "a filled seat played " .. tostring(sounds[1]))
        local stop = nil
        for _, cb in ipairs(later) do
            if cb.delay == ICUI.BURST_SECONDS then stop = cb end
        end
        assert(stop, "nothing was scheduled to take the burst away")
        stop.fn()
        assert(not card.children[ICUI.BURST], "the burst outlived its callback")
        -- A SECOND CLAIM MAKES A NEW ONE: a burst that is only ever shown
        -- once is a seat that stops answering.
        ICUI.ANSWERS.appoint(seat .. "|1", true)
        assert(card.children[ICUI.BURST], "the second claim drew no burst")
    end)
    cm.callback = saved_cb
    assert(ok, err)
end)

check("a burst whose panel was closed is not touched when its time is up", function()
    local later = {}
    local saved_cb = cm.callback
    cm.callback = function(_self, fn, delay) later[#later + 1] = fn end
    local ok, err = pcall(with_fake_panel, function(panel)
        ICUI.burst(ICUI.CARD .. "_1")
        -- THE PANEL GOES: find_uicomponent now answers nothing for it.
        local saved_find = find_uicomponent
        find_uicomponent = function() return false end
        for _, fn in ipairs(later) do fn() end
        find_uicomponent = saved_find
    end)
    cm.callback = saved_cb
    assert(ok, "the burst's callback failed on a closed panel: " .. tostring(err))
end)
```

- [ ] **Step 2: Run the harness, verify it fails**

Run: `"/c/Program Files (x86)/Lua/5.1/lua.exe" tools/_iron_court_harness.lua`
Expected: FAIL on "a held seat wears the lit rim..." with `attempt to index field 'RIMS' (a nil value)`. If an EARLIER check fails, the `Destroy` change broke it: read that check, and restore the old no-op only if a check depends on a destroyed component staying reachable (then report it as a ruling).

- [ ] **Step 3: Emitter - shader on a layer**

In `tools/gen_iron_court_emitter.py`, `_state`, inside the `for cig, mg, lay in entries:` loop, immediately before the `m = lay.get("margin", 0)` line, add:

```python
            # CA'S PULSE, ON THE IMAGE. glow_pulse_t0 is how every torch and rune
            # in the Chaos Dwarf panels breathes (876 uses in ui3.pack), declared
            # per image and running on its own while the image is visible - no
            # trigger. Values: lowest, highest, interval, time offset (CA's
            # uicomponent.html "Shader Techniques" table).
            if lay.get("shader"):
                out += '\t\t\t\t\t\t\tshader_name="%s"\n' % lay["shader"]
                out += ('\t\t\t\t\t\t\tshadertechnique_vars="%s"\n'
                        % lay.get("shader_vars", "0.00,0.00,0.00,0.00"))
```

- [ ] **Step 4: Generator - the rim layers and the burst file**

In `tools/gen_ic_ui.py`, after `CARD_LAYERS = [...]` closes:

```python
# THE SEAT'S RIM (spec 2026-09-28 section 4.1). CA's completed-district glow off
# the Tower of Zharr, 9-sliced at 40 - the Great Guilds' measured value, and it
# fits MASK_NONE (300x164) as well as the rim (299x877), so no layer can sample
# outside its texture whichever of the two it holds.
#
# ONE LAYER PER LOOK, each shipping MASK_NONE. ICUI.set_rim writes the rim into
# the look's layer and MASK_NONE into the others. A layer's colour multiplies
# its image, so the dim and red looks are the same CA art under another colour
# rather than derived files (ruling 1 of the 2026-09-28 plan).
RIM_ART = "ui/skins/default/dlc23_tower_of_zharr/district_complete_glow_02.png"
RIM_MARGIN = 40
RIM_LOOKS = {
    # CA's ToZ furnace glow_01 values.
    "lit": {"shader": "glow_pulse_t0", "shader_vars": "1.00,1.30,0.80,0.00"},
    "dim": {"colour": "#FFFFFF66"},
    # A fast flicker in red: a failure is short and sharp, not a slow breath.
    "red": {"colour": "#FF3A2AFF", "shader": "glow_pulse_t0",
            "shader_vars": "0.60,1.60,0.25,0.00"},
}


def rim_layers(looks):
    out = []
    for look in looks:
        lay = {"path": MASK_NONE, "offset": (0, 0), "dw": 0, "dh": 0,
               "margin": RIM_MARGIN, "dock": None}
        lay.update(RIM_LOOKS[look])
        out.append(lay)
    return out


OFFICE_CARD_LAYERS = CARD_LAYERS + rim_layers(["lit", "dim"])
# Which layer holds each look, per component kind. Must match ICUI.RIMS;
# check_rim_slots() holds the two together.
CARD_RIM = {"lit": len(CARD_LAYERS), "dim": len(CARD_LAYERS) + 1}
```

`MASK_NONE` is defined later in the file (line ~1881); if Python raises `NameError`, move this block to just after `MASK_NONE = ...` instead. In `_card()`, change `layers=CARD_LAYERS` on `derpy_ic_card` to `layers=OFFICE_CARD_LAYERS`.

Add `"RIM_ART", "RIM_MARGIN", "RIM_LOOKS", "OFFICE_CARD_LAYERS", "CARD_RIM"` to `NOT_GEOMETRY`.

The burst file, after `check_fire`:

```python
# THE CLAIM BURST (spec 2026-09-28 section 4.1). CA's own seat-claimed starburst,
# in the SHAPE of the Hell-Forge's unlock burst (hellforge_panel_unit_caps_tab,
# sprite_progression_celebration): SpriteAnimation with no `paused`, one blank
# image slot, hidden in the file. ICUI.burst creates it into the card, shows it,
# and destroys it after ICUI.BURST_SECONDS - a new one per claim, so whether a
# finished sprite replays when shown again never arises (ruling 2).
BURST_FILE = "derpy_ic_burst.twui.xml"
BURST_FRAMES = "UI/sprite_anims/warband_upgrade_starburst/starburst_"
BURST_LAST = 19
BURST_MS = 60
BURST_SIZE = 200            # CA's frames are 200x200

_BURST_TEMPLATE = """<?xml version="1.0"?>
<layout
	version="142"
	comment="derpy: CA's seat-claimed starburst for the Iron Court. Created at runtime into a card or row by ICUI.burst; generated by tools/gen_ic_ui.py - do not edit by hand."
	precache_condition="">
	<hierarchy>
		<root this="@0">
			<derpy_ic_burst this="@1"/>
		</root>
	</hierarchy>
	<components>
		<root
			this="@0"
			id="root"
			tooltipslocalised="true"
			uniqueguid="@0"
			currentstate="@2"
			defaultstate="@2">
			<states>
				<standard
					this="@2"
					name="standard"
					width="@S"
					height="@S"
					uniqueguid="@2"/>
			</states>
		</root>
		<derpy_ic_burst
			this="@1"
			id="derpy_ic_burst"
			visible="false"
			priority="60"
			tooltipslocalised="true"
			uniqueguid="@1"
			currentstate="@3"
			defaultstate="@3">
			<callbackwithcontextlist>
				<callback_with_context callback_id="SpriteAnimation">
					<child_m_user_properties>
						<property
							name="frame_name"
							value="@FRAMES"/>
						<property
							name="last_frame"
							value="@LAST"/>
						<property
							name="loops"
							value="0"/>
						<property
							name="time_per_frame"
							value="@MS"/>
					</child_m_user_properties>
				</callback_with_context>
			</callbackwithcontextlist>
			<componentimages>
				<component_image
					this="@4"
					uniqueguid="@4"/>
			</componentimages>
			<states>
				<default
					this="@3"
					name="default"
					width="@S"
					height="@S"
					uniqueguid="@3">
					<imagemetrics>
						<image
							this="@5"
							uniqueguid="@5"
							componentimage="@4"
							width="@S"
							height="@S"/>
					</imagemetrics>
				</default>
			</states>
		</derpy_ic_burst>
	</components>
</layout>
"""


def burst_xml():
    g = GUID_PREFIXES[BURST_FILE]
    text = _BURST_TEMPLATE
    for key, value in (("@FRAMES", BURST_FRAMES), ("@LAST", BURST_LAST),
                       ("@MS", BURST_MS), ("@S", BURST_SIZE)):
        text = text.replace(key, str(value))
    for n in range(5, -1, -1):
        text = text.replace("@%d" % n, "%s%04X-D000-4000-B%015X" % (g, n, n))
    return text


def check_burst(text, assets=None):
    """The burst's frames must exist: a wrong frame name draws nothing, silently."""
    out = []
    if 'callback_id="SpriteAnimation"' not in text:
        out.append("%s: no SpriteAnimation callback" % BURST_FILE)
    if 'name="paused"' in text:
        out.append("%s: paused - nothing in Lua can start a paused sprite" % BURST_FILE)
    if assets is not None:
        for n in range(BURST_LAST + 1):
            p = (BURST_FRAMES + "%d.png" % n).lower()
            if p not in assets:
                out.append("%s: frame %s is in no pack" % (BURST_FILE, p))
    return out
```

Register it: `GUID_PREFIXES["derpy_ic_burst.twui.xml"] = "IC38"` (add the entry beside `IC37`); `ui_file_names()` returns `... + [FIRE_FILE, BURST_FILE] + ...`; `build_xml()` adds `out[BURST_FILE] = burst_xml()` beside the fire line; `check()` adds, beside check 1b, `out.extend(check_burst(all_files.get(BURST_FILE, ""), set(p.lower() for p in _assets())))`; add `BURST_FILE`, `BURST_FRAMES`, `BURST_LAST`, `BURST_MS`, `BURST_SIZE` to `NOT_GEOMETRY`. `_assets()` may return mixed case; if frames are reported missing, print `[a for a in _assets() if "starburst" in a.lower()][:3]` and match its case rule.

The rim-slot parity check, beside the other checks:

```python
def check_rim_slots():
    """ICUI.RIMS in the panel Lua must name the layers this file emits."""
    ui = os.path.join(ROOT, "Modding Files", "pack", "script", "campaign", "mod",
                      "zzz_derpy_iron_court_ui.lua")
    text = io.open(ui, encoding="utf-8").read()
    want = {"card": CARD_RIM}
    for kind in ("row", "party"):
        if ("%s_RIM" % kind.upper()) in globals():
            want[kind] = globals()["%s_RIM" % kind.upper()]
    out = []
    for kind, looks in want.items():
        m = re.search(r"\b%s\s*=\s*\{([^}]*)\}" % kind,
                      text[text.find("ICUI.RIMS"):text.find("ICUI.RIMS") + 600])
        if not m:
            out.append("ICUI.RIMS has no %s entry" % kind)
            continue
        got = dict((k, int(v)) for k, v in re.findall(r"(\w+)\s*=\s*(\d+)", m.group(1)))
        if got != looks:
            out.append("ICUI.RIMS.%s is %r and the file emits %r" % (kind, got, looks))
    return out
```

Call it from `check()`: `out.extend(check_rim_slots())`. Selftest, beside the fire selftest: `assert not check_burst(burst_xml()), check_burst(burst_xml())` and `assert check_burst(burst_xml().replace('name="loops"', 'name="paused" value="1"/><property name="loops"')), "check_burst passed a paused sprite"`.

- [ ] **Step 5: Lua - the rim, the burst, the seat sound**

In `zzz_derpy_iron_court_ui.lua`, after `ICUI.PARTY_SELECTED = ...`:

```lua
-- THE SEAT'S RIM (spec 2026-09-28 section 4.1): CA's completed-district glow off
-- the Tower of Zharr. Each kind of component carries one layer per look, all
-- shipping MASK_NONE; set_rim writes the rim into one and clears the rest.
-- Must match RIM_ART and CARD_RIM / ROW_RIM / PARTY_RIM in tools/gen_ic_ui.py
-- (check_rim_slots).
ICUI.RIM_ART = "ui/skins/default/dlc23_tower_of_zharr/district_complete_glow_02.png"
ICUI.RIMS = {
    card = {lit = 2, dim = 3},
}

function ICUI.set_rim(c, kind, look)
    if not c then return end
    for name, index in pairs(ICUI.RIMS[kind]) do
        local path = (name == look) and ICUI.RIM_ART or ICUI.MASK_NONE
        pcall(function() c:SetImagePath(path, index) end)
    end
end

-- THE CLAIM BURST: CA's seat-claimed starburst, created into the card and
-- destroyed after it plays (tools/gen_ic_ui.py BURST_FILE). HOST BY NAME: the
-- callback re-finds everything under the panel, because the panel may be shut
-- before it fires and a component kept from before is then a dead address.
ICUI.BURST = "derpy_ic_burst"
ICUI.PATH_BURST = "ui/campaign ui/derpy_ic_burst.twui.xml"
ICUI.BURST_SECONDS = 1.3    -- 20 frames at 60 ms, and a little over
ICUI.SOUND_SEAT = "UI_CLICK_Begin_Ritual"

function ICUI.burst(host_name)
    local ok, err = pcall(function()
        local host = comp(host_name, comp(ICUI.PANEL))
        if not host then return end
        local old = find_uicomponent(host, ICUI.BURST)
        if old then old:Destroy() end
        host:CreateComponent(ICUI.BURST, ICUI.PATH_BURST)
        local b = find_uicomponent(host, ICUI.BURST)
        if not b or not is_uicomponent(b) then return end
        local x, y = host:Position()
        local w, h = host:Dimensions()
        local bw, bh = b:Dimensions()
        b:MoveTo(x + math.floor((w - bw) / 2), y + math.floor((h - bh) / 2))
        b:SetVisible(true)
    end)
    if not ok then IC.warn("IRON COURT: the claim burst failed: " .. tostring(err)) end
    cm:callback(function()
        pcall(function()
            local panel = comp(ICUI.PANEL)
            local host = panel and comp(host_name, panel)
            local b = host and find_uicomponent(host, ICUI.BURST)
            if b then b:Destroy() end
        end)
    end, ICUI.BURST_SECONDS)
end
```

Check how `comp(name, parent)` treats a nil parent before relying on `comp(host_name, comp(ICUI.PANEL))`; if a nil parent means "search the registry", guard with `local panel = comp(ICUI.PANEL); if not panel then return end` first.

In `ICUI.draw_offices`, beside `ICUI.card_fire(card, cqi ~= nil)`:

```lua
            ICUI.set_rim(card, "card", cqi and "lit" or nil)
```

In `picked()`, replace the success branch's `ICUI.confirm(filled and ICUI.office_card(filled) or nil, true)` with:

```lua
            -- THE CARD THAT JUST CHANGED, when a seat is what changed: CA's
            -- claim burst and the ritual sound, instead of the generic chime.
            local card = filled and ICUI.office_card(filled) or nil
            if card then
                pcall(function() common.trigger_soundevent(ICUI.SOUND_SEAT) end)
                ICUI.burst(card:Id())
            else
                ICUI.confirm(nil, true)
            end
```

Add `"BURST_SECONDS"` to `ICUI.NOT_SCALED`. Add `_UI + "derpy_ic_burst.twui.xml",` to the manifest in `tools/sync_iron_court_repo.py` beside `derpy_ic_fire.twui.xml`.

The existing check "a click the player made is answered, and the answer stops" drives `ICUI.confirm` directly and is unaffected. If any other check asserted `SOUND_OK` for an appoint, update it to `SOUND_SEAT` and say so in the ledger.

- [ ] **Step 6: Run the harness and the generator**

Run: `"/c/Program Files (x86)/Lua/5.1/lua.exe" tools/_iron_court_harness.lua`
Expected: `iron court harness: ok (700 checks)` (697 + 3).
Run: `py tools/gen_ic_ui.py` then `py tools/gen_ic_ui.py --check` then `py tools/gen_ic_ui.py --selftest`
Expected: files written including `derpy_ic_burst.twui.xml`; `ok: 14 files, ...`; `selftest: ok (...)`. Any complaint that a new global is not classified goes into `NOT_GEOMETRY`; any complaint about the office card's layer count is the 21b pairing and is fixed at its cause, not silenced.

- [ ] **Step 7: Gates and build**

Run the Iron Court gates: `luac -p` on the three Lua files; `py tools/check_lua_api.py` (1 known suspect in `ai_test_tower_of_zharr.lua`); `py tools/check_lua_literal_left.py`; `py tools/check_lua_undeclared.py` on the three files together (only `BUTTON, BUTTON_GAP, BUTTON_SIZE, GGUI`); `py tools/gen_iron_court.py --check`; `py tools/make_ic_backdrop.py --check`; `py -c "import sys; sys.path.insert(0,'tools'); import import_iron_court as i; print(i.verify())"` -> `[]`; `py tools/preview_iron_court.py --check`.
Then, with RPFM open and the game closed: `py tools/deploy_iron_court.py --no-copy`. Expected: `verified 1724 file(s)` (one more than 1723) and the pack in `Modding Files/Modpacks/`.

- [ ] **Step 8: STOP - the author's in-game check**

Report to the author and ask them to deploy (with the usual backup) and check, with the Offices tab open:
1. A held seat's card has a red-orange rim that slowly breathes.
2. Filling a seat plays a starburst over the card with a ritual sound; dismissing it and filling it again plays the burst again.
3. The card pulses brighter for about a second and a half after filling (the existing `pulse_uicomponent` - this is what ruling 3 rests on).

Ledger the answers. If 1 draws but does not breathe: remove the `shader` keys from `RIM_LOOKS` (static rim) and carry on. If 1 draws nothing: stop the plan and report. If 2 draws nothing: stop and report. If 3 is invisible: Task 4 uses its fallback. Tasks 2-6 start only after this answer.

---

### Task 2: Stalled seats, governors and the release answer

**Files:**
- Modify: `tools/gen_ic_ui.py` (`_row()` ~line 3048, beside the rim block)
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_ui.lua` (`ICUI.RIMS`, `ICUI.draw_offices` stall lines ~3761, `ICUI.draw_govs`, `ICUI.fill_rows`, `ICUI.ANSWERS`, `picked()`)
- Test: `tools/_iron_court_harness.lua`

**Interfaces:**
- Consumes: `ICUI.set_rim`, `ICUI.RIMS`, `ICUI.burst`, `ICUI.SOUND_SEAT` (Task 1); `IC.governor_active(faction, province_key)`; `IC.stalled_for(faction, office_slug)`.
- Produces: `ICUI.RIMS.row = {lit = 1, dim = 2}`; line field `rim` (`"lit"`, `"dim"` or nil) honoured by `ICUI.fill_rows`; `ICUI.ANSWERS.ungov`; `ICUI.gov_row(province_key)` returning the row component name or nil.

- [ ] **Step 1: Write the failing checks**

```lua
check("a stalled seat's rim is dimmed, not lit", function()
    IC.state = {}
    turn = 1
    local man = make_character(1, ANY_SEAT, "forge")
    make_faction(F, IC.CHD_SUBCULTURE, {man}, {})
    IC.add_house(F, IC.CROWN)
    IC.add_house(F, "forge")
    local seat = IC.OFFICES[1].slug
    IC.court(F).offices[seat] = 1
    IC.stall_office(F, seat, 3, "chain", "sabotage")
    with_fake_panel(function(panel)
        ICUI.view = "offices"
        ICUI.refresh()
        local card = panel.children[ICUI.CARD .. "_1"]
        assert(card.images[ICUI.RIMS.card.dim] == ICUI.RIM_ART,
            "a stalled seat's dim layer holds " .. tostring(card.images[ICUI.RIMS.card.dim]))
        assert(card.images[ICUI.RIMS.card.lit] == ICUI.MASK_NONE,
            "a stalled seat still wears the lit rim")
    end)
end)

check("a governed province's row is lit, an away one dim, and other views clear it", function()
    IC.state = {}
    turn = 1
    local man = make_character(1, 20, "forge", "prov_a")
    make_faction(F, IC.CHD_SUBCULTURE, {man}, {"prov_a", "prov_b"})
    IC.add_house(F, IC.CROWN)
    IC.add_house(F, "forge")
    IC.court(F).govs["prov_a"] = 1
    local keep = IC.governor_active
    local ok, err = pcall(with_fake_panel, function(panel)
        IC.governor_active = function() return true end
        ICUI.view = "govs"
        ICUI.refresh()
        local row = panel.children[ICUI.gov_row("prov_a")]
        assert(row.images[ICUI.RIMS.row.lit] == ICUI.RIM_ART, "a present governor's row is not lit")
        local bare = panel.children[ICUI.gov_row("prov_b")]
        assert(bare.images[ICUI.RIMS.row.lit] == ICUI.MASK_NONE, "an ungoverned province is lit")
        IC.governor_active = function() return false end
        ICUI.refresh()
        assert(row.images[ICUI.RIMS.row.dim] == ICUI.RIM_ART, "an away governor's row is not dimmed")
        -- THE POOL IS SHARED: the same row drawing the Log must drop the rim.
        ICUI.view = "log"
        ICUI.refresh()
        for i = 1, ICUI.MAX_ROWS do
            local r = panel.children[ICUI.ROW .. "_" .. i]
            if r then
                for _, index in pairs(ICUI.RIMS.row) do
                    assert(r.images[index] ~= ICUI.RIM_ART,
                        "row " .. i .. " kept a governor's rim on the log")
                end
            end
        end
    end)
    IC.governor_active = keep
    assert(ok, err)
end)

check("releasing a governor is answered, and assigning one bursts his row", function()
    IC.state = {}
    turn = 1
    local man = make_character(1, 20, "forge", "prov_a")
    make_faction(F, IC.CHD_SUBCULTURE, {man}, {"prov_a"})
    IC.add_house(F, IC.CROWN)
    IC.add_house(F, "forge")
    assert(ICUI.ANSWERS.ungov, "releasing a governor has no answer at all")
    sounds = {}
    ICUI.ANSWERS.ungov("prov_a", true)
    assert(sounds[1] == ICUI.SOUND_BAD, "a release played " .. tostring(sounds[1]))
    ICUI.notice = nil
    ICUI.ANSWERS.ungov("prov_a", false, "no governor")
    assert(ICUI.notice and ICUI.notice ~= "", "a refused release said nothing")
    IC.court(F).govs["prov_a"] = 1
    local saved_cb = cm.callback
    cm.callback = function() end
    local ok, err = pcall(with_fake_panel, function(panel)
        ICUI.view = "govs"
        ICUI.refresh()
        sounds = {}
        ICUI.ANSWERS.gov("prov_a|1", true)
        local row = panel.children[ICUI.gov_row("prov_a")]
        assert(row.children[ICUI.BURST], "assigning a governor drew no burst on his row")
        assert(sounds[1] == ICUI.SOUND_SEAT, "assigning a governor played " .. tostring(sounds[1]))
    end)
    cm.callback = saved_cb
    assert(ok, err)
end)
```

`make_character`'s fourth argument is the province; `IC.stall_office(faction, office, turns, by_slug, cause)` is the model's own stall call (see the parties file line ~301). If `ICUI.ANSWERS.gov` refreshes the panel and the refresh re-sorts rows, look the row up again after the call, as written.

- [ ] **Step 2: Run the harness, verify it fails**

Expected: FAIL on "a stalled seat's rim is dimmed" (`dim layer holds nil`, since draw_offices writes only lit/off).

- [ ] **Step 3: Implement**

Generator: after the rim block, `ROW_RIM = {"lit": len(ROW_LAYERS), "dim": len(ROW_LAYERS) + 1}` and in `_row()` use `layers=ROW_LAYERS + rim_layers(["lit", "dim"])` on `derpy_ic_row`; add `"ROW_RIM"` to `NOT_GEOMETRY`. If `make_ic_backdrop.py --check` then reports a changed contrast measurement, read how it reads row layers - the new layers are transparent by default and must not count as a plate.

Lua: `ICUI.RIMS.row = {lit = 1, dim = 2}` inside the `ICUI.RIMS` table. In `ICUI.draw_offices`, replace the Task 1 line with:

```lua
            local stalled = cqi and (court.stalled or {})[office.slug] ~= nil
            ICUI.set_rim(card, "card", cqi and (stalled and "dim" or "lit") or nil)
```

(If `stall` is computed later in the same loop body, move that computation up and reuse it rather than reading `court.stalled` twice.)

In `ICUI.draw_govs`, add to each line table: `rim = cqi and (IC.governor_active(faction, province_key) and "lit" or "dim") or nil,`. In `ICUI.fill_rows`, for every row in the pool - drawn or hidden - call `ICUI.set_rim(row, "row", line and line.rim or nil)`, so a row that draws another view, or nothing, is cleared.

`ICUI.gov_row(province_key)`: the row component name drawing that province, from `ICUI.gov_keys`, the scroll offset `fill_rows` applied (`ICUI.clamp_scroll`/`ICUI.scroll.govs`) and `ICUI.first_row("govs")`:

```lua
function ICUI.gov_row(province_key)
    local first = ICUI.first_row("govs")
    local at = (ICUI.scroll and ICUI.scroll.govs) or 0
    for i, key in ipairs(ICUI.gov_keys or {}) do
        if key == province_key then
            local slot = i - at + first - 1
            if slot >= first and slot <= ICUI.MAX_ROWS then return ICUI.ROW .. "_" .. slot end
            return nil
        end
    end
    return nil
end
```

Check the arithmetic against `fill_rows` (`lines[(i - first + 1) + at]` draws line `i - first + 1 + at` in row `i`, so line `n` sits in row `n - at + first - 1`), and against where `clamp_scroll` stores the offset; adjust the field name to the real one.

`ICUI.ANSWERS.ungov = confirmed(false, false)` beside the others. In `picked()`, also set `filled` for `gov`: `if op == "gov" then filled_row = ICUI.gov_row(string.match(arg or "", "^([^|]*)")) end`, and in the success branch, when `filled_row` is set, play `ICUI.SOUND_SEAT` and `ICUI.burst(filled_row)`.

- [ ] **Step 4: Run the harness and generator, verify they pass**

Expected: `iron court harness: ok (703 checks)`; `gen_ic_ui.py --check` ok; `--selftest` ok.

- [ ] **Step 5: Checkpoint**

`luac -p` the UI file; harness green.

---

### Task 3: Petition answers, the party rim flash and the fail look

**Files:**
- Modify: `tools/gen_ic_ui.py` (`PARTY_LAYERS` ~line 3144)
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_ui.lua` (`ICUI.RIMS`, `confirmed()`, `picked()`, the grant/refuse sender ~line 4867)
- Test: `tools/_iron_court_harness.lua`

**Interfaces:**
- Consumes: `ICUI.set_rim` (Task 1); `ICUI.house_name(slug, faction)`; `ICUI.court_keys`; tuning `T.party_demand_met` (parties file) - read through the model, never retyped.
- Produces: `ICUI.RIMS.party = {lit = 3, red = 4}`; `ICUI.party_card(slug)` -> component or nil; `ICUI.flash(slug, look)`; `ICUI.FLASH_SECONDS`; `ICUI.answer_text(op, arg, faction)` -> string or nil.

- [ ] **Step 1: Write the failing checks**

```lua
check("a granted demand, an accepted offer and a settled feud each say so", function()
    IC.state = {}
    turn = 1
    make_faction(F, IC.CHD_SUBCULTURE, {make_character(1, ANY_SEAT, "forge")}, {})
    IC.add_house(F, IC.CROWN)
    IC.add_house(F, "forge")
    IC.add_house(F, "chain")
    local saved_cb = cm.callback
    cm.callback = function() end
    local ok, err = pcall(function()
        for _, case in ipairs({{"grant", "forge"}, {"accept", "forge"},
                               {"arbit", "forge|back"}, {"arbit", "forge|peace"},
                               {"favour", "gift|forge"}}) do
            ICUI.notice = nil
            ICUI.ANSWERS[case[1]](case[2], true)
            assert(ICUI.notice and ICUI.notice ~= "",
                case[1] .. " " .. case[2] .. " was answered with a chime and no words")
            assert(string.find(ICUI.notice, ICUI.house_name("forge", F), 1, true),
                case[1] .. " does not name the party: " .. ICUI.notice)
        end
    end)
    cm.callback = saved_cb
    assert(ok, err)
end)

check("a failed plot flashes its target red, and the flash goes out", function()
    IC.state = {}
    turn = 1
    make_faction(F, IC.CHD_SUBCULTURE, {make_character(1, ANY_SEAT, "forge")}, {})
    IC.add_house(F, IC.CROWN)
    IC.add_house(F, "forge")
    local later = {}
    local saved_cb = cm.callback
    cm.callback = function(_self, fn, delay) later[#later + 1] = {fn = fn, delay = delay} end
    local ok, err = pcall(with_fake_panel, function(panel)
        ICUI.view = "court"
        ICUI.refresh()
        local card = ICUI.party_card("forge")
        assert(card, "the forge party has no card on the court view")
        ICUI.ANSWERS.plot("rumour|1|forge", true, "failed")
        assert(card.images[ICUI.RIMS.party.red] == ICUI.RIM_ART,
            "a failed plot left its target's card " .. tostring(card.images[ICUI.RIMS.party.red]))
        for _, cb in ipairs(later) do
            if cb.delay == ICUI.FLASH_SECONDS then cb.fn() end
        end
        assert(card.images[ICUI.RIMS.party.red] == ICUI.MASK_NONE,
            "the red flash never went out")
    end)
    cm.callback = saved_cb
    assert(ok, err)
end)
```

The favour arg is `favour|party` per `IC.MP_OPS.favour`; use a real favour key from `IC.FAVOURS` (or the table the Court tab's gift button reads) in place of `"gift"` - read it off the model before running. `ICUI.ANSWERS.plot` is `picked("plot")`; the plot key `rumour` must be one `IC.PLOTS` knows - check.

- [ ] **Step 2: Run the harness, verify it fails**

Expected: FAIL on "a granted demand..." with `grant forge was answered with a chime and no words`.

- [ ] **Step 3: Implement**

Generator: `PARTY_RIM = {"lit": len(PARTY_LAYERS), "red": len(PARTY_LAYERS) + 1}` and `PARTY_LAYERS` gains `+ rim_layers(["lit", "red"])` at its definition (keep `PARTY_SEL_INDEX` at 2); add `"PARTY_RIM"` to `NOT_GEOMETRY`.

Lua: `party = {lit = 3, red = 4}` in `ICUI.RIMS`. Then:

```lua
-- THE PARTY'S CARD ON SCREEN, or nil when the court view is not drawing it.
function ICUI.party_card(slug)
    local panel = comp(ICUI.PANEL)
    if not panel or ICUI.view ~= "court" then return nil end
    local at = (ICUI.scroll and ICUI.scroll.court) or 0
    for i, s in ipairs(ICUI.court_keys or {}) do
        if s == slug then
            local slot = i - at
            if slot >= 1 and slot <= ICUI.PARTY_SLOTS then
                return comp(ICUI.PARTY .. "_" .. slot, panel)
            end
        end
    end
    return nil
end

-- A SHORT RIM ON A PARTY'S CARD: lit for a party an answer pleased, red for the
-- target of a plot that failed. Off again after FLASH_SECONDS, re-found by slug.
ICUI.FLASH_SECONDS = 1.5
function ICUI.flash(slug, look)
    local card = ICUI.party_card(slug)
    if not card then return end
    ICUI.set_rim(card, "party", look)
    cm:callback(function()
        pcall(function() ICUI.set_rim(ICUI.party_card(slug), "party", nil) end)
    end, ICUI.FLASH_SECONDS)
end
```

`fill_party` must also call `ICUI.set_rim(card, "party", nil)` every draw, so a recycled card never carries a flash to another party.

`ICUI.answer_text(op, arg, faction)`, for the four yes answers, with names from `ICUI.house_name` and amounts read from the model's own tuning (find where `T.party_demand_met` and the favour's loyalty gain live and read them through `IC`, exposing them on `IC.PARTY_TUNE` or similar if they are file-local - never retype the number):

| op | arg | text |
|---|---|---|
| grant | party | `"Granted. %s is pleased (+%d loyalty)."` |
| accept | party | `"Accepted. %s keeps its word."` |
| arbit | party\|back | `"You backed %s. The feud is over."` |
| arbit | party\|peace | `"Settled. %s and its rival stand down."` |
| favour | favour\|party | `"Sent. %s is pleased (+%d loyalty)."` |

`confirmed(yes, demand)` becomes `confirmed(yes, demand, op)`; on `done` it sets `ICUI.notice = yes and ICUI.answer_text(op, _arg, ICUI.player()) or nil`, calls `ICUI.confirm(nil, yes)`, and when `yes`, `ICUI.flash(<party from arg>, "lit")`. Every `ICUI.ANSWERS.x = confirmed(...)` line passes its op name.

The grant sender (~line 4867) sends the demand's party as the arg instead of `""` (the model's `IC.MP_OPS.grant` ignores its arg, so the wire is unchanged in meaning): read the slug off `IC.agenda(faction).demand` before sending.

In `picked()`'s failed branch, after the notice: `if op == "plot" then local target = string.match(arg or "", "^[^|]*|[^|]*|(.*)$"); if target and target ~= "" then ICUI.flash(target, "red") end end`.

- [ ] **Step 4: Run the harness and generator, verify they pass**

Expected: `iron court harness: ok (705 checks)`; `gen_ic_ui.py --check` ok (check 20c may now also measure nothing new - the notice line's own fit check covers the new sentences if one exists; if the notice cell has a fit list, add the five sentences at their longest party name).

- [ ] **Step 5: Checkpoint**

`luac -p`; harness green.

---

### Task 4: Attention markers and the button's pulse

**Files:**
- Modify: `tools/gen_ic_ui.py` (`PANEL_LAYOUT` tab block ~line 195, panel builder)
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_ui.lua` (the Lua layout mirror ~line 223, `ICUI.opener_tip` ~line 1106, `ICUI.update_opener_tip`, `ICUI.refresh`)
- Test: `tools/_iron_court_harness.lua`

**Interfaces:**
- Consumes: `IC.agenda(faction)` fields `demand`, `offers`, `feuds`; `IC.terms_ending(faction)`; `IC.present_houses(faction)`; `IC.seats(faction)`; `court.govs`.
- Produces: `ICUI.court_state(faction)` -> `{empty = n, back = {...}, ending = {...}, leaving = {{slug, clock}, ...}}`; `ICUI.attention(faction)` -> `{court = bool, offices = bool, govs = bool, petitions = bool, any = bool}`; `ICUI.MARKS` (tab view -> marker component name); `ICUI.draw_marks(panel, faction)`.

- [ ] **Step 1: Write the failing checks**

```lua
check("a tab with something waiting is marked, and the button pulses while any is", function()
    IC.state = {}
    turn = 1
    make_faction(F, IC.CHD_SUBCULTURE, {make_character(1, ANY_SEAT, "forge")}, {"prov_a"})
    IC.add_house(F, IC.CROWN)
    IC.add_house(F, "forge")
    for i = 1, #IC.OFFICES do IC.court(F).offices[IC.OFFICES[i].slug] = nil end
    local a = ICUI.attention(F)
    assert(a.offices, "empty seats did not mark the Offices tab")
    assert(a.govs, "an ungoverned province did not mark the Governors tab")
    assert(not a.petitions, "the Petitions tab is marked with nothing waiting")
    assert(not a.court, "the Court tab is marked with nobody leaving")
    assert(a.any, "something is waiting and the button would not pulse")
    IC.agenda(F).demand = {slug = "forge", kind = "office", cqi = 1,
                           key = IC.OFFICES[1].slug, was = 0, ends = 6}
    assert(ICUI.attention(F).petitions, "an open demand did not mark Petitions")
    IC.agenda(F).demand = nil
    IC.court(F).houses["forge"].clock = 3
    assert(ICUI.attention(F).court, "a party leaving did not mark the Court tab")
end)

check("the markers and the button's summary never disagree", function()
    IC.state = {}
    turn = 1
    make_faction(F, IC.CHD_SUBCULTURE, {make_character(1, ANY_SEAT, "forge")}, {})
    IC.add_house(F, IC.CROWN)
    IC.add_house(F, "forge")
    for i = 1, #IC.OFFICES do IC.court(F).offices[IC.OFFICES[i].slug] = 1 end
    local tip = ICUI.opener_tip(F)
    local a = ICUI.attention(F)
    assert(string.find(tip, "Empty seats: 0 of", 1, true), tip)
    assert(not a.offices or #IC.terms_ending(F) > 0,
        "Offices is marked while the summary says every seat is full and no term ends")
    IC.court(F).offices[IC.OFFICES[1].slug] = nil
    assert(ICUI.attention(F).offices
           and not string.find(ICUI.opener_tip(F), "Empty seats: 0 of", 1, true),
        "the marker and the summary disagree about an empty seat")
end)

check("the markers are drawn on their tabs and the button pulses", function()
    IC.state = {}
    turn = 1
    make_faction(F, IC.CHD_SUBCULTURE, {make_character(1, ANY_SEAT, "forge")}, {})
    IC.add_house(F, IC.CROWN)
    IC.add_house(F, "forge")
    for i = 1, #IC.OFFICES do IC.court(F).offices[IC.OFFICES[i].slug] = nil end
    with_fake_panel(function(panel)
        ICUI.view = "court"
        ICUI.refresh()
        assert(panel.children[ICUI.MARKS.offices].visible ~= false,
            "the Offices marker is hidden with empty seats")
        assert(panel.children[ICUI.MARKS.petitions].visible == false,
            "the Petitions marker shows with nothing waiting")
    end)
    pulses = {}
    ICUI.pulse_opener(true)
    assert(pulses[1] and pulses[1].on, "the button was not pulsed")
    ICUI.pulse_opener(false)
    assert(pulses[2] and not pulses[2].on, "the button's pulse was not stopped")
end)
```

`ICUI.pulse_opener` finds the opener with `comp(ICUI.BTN)`; in the harness the check calls it directly, so make it take an optional component for testing only if `comp(ICUI.BTN)` returns nothing in the harness - read how the existing opener tooltip checks (harness line ~22057) reach the button and copy that.

- [ ] **Step 2: Run the harness, verify it fails**

Expected: FAIL with `attempt to call field 'attention' (a nil value)`.

- [ ] **Step 3: Implement**

Refactor `ICUI.opener_tip` into two: `ICUI.court_state(faction)` computes `empty`, `back`, `ending` and `leaving` exactly as the tip does now, and `ICUI.opener_tip` formats the same lines from it (no change to any sentence). Then:

```lua
-- WHAT IS WAITING, per tab. Shares court_state with the button's summary, so a
-- marker and a sentence can never disagree about the same fact.
function ICUI.attention(faction)
    local s = ICUI.court_state(faction)
    local court = IC.court(faction)
    local a = IC.agenda(faction)
    local out = {
        offices = s.empty > 0 or #s.ending > 0,
        court = #s.leaving > 0,
        petitions = a.demand ~= nil or next(a.offers or {}) ~= nil
                    or next(a.feuds or {}) ~= nil,
        govs = false,
    }
    -- NOT a governor away: a lord in the field is away most turns, and a marker
    -- that is nearly always lit tells the player nothing (spec 4.4).
    for _, province in ipairs(IC.seats(faction)) do
        if not court.govs[province] then out.govs = true end
    end
    out.any = out.offices or out.court or out.petitions or out.govs
    return out
end
```

Generator: four marker components in `PANEL_LAYOUT`, each 28x28 at its tab's right end, vertically centred (`x + 240 - 32, 62 + 2`):

```python
    "ic_mark_court": (18 + 240 - 32, 64, 28, 28),
    "ic_mark_offices": (262 + 240 - 32, 64, 28, 28),
    "ic_mark_govs": (506 + 240 - 32, 64, 28, 28),
    "ic_mark_petitions": (994 + 240 - 32, 64, 28, 28),
```

built in the panel builder with one layer `{"path": "ui/skins/default/dlc23_chd_hell_forge/heat_glow.png", "offset": (0, 0), "dw": 0, "dh": 0, "margin": 0, "dock": None, "colour": "#FFFFFFD0", "shader": "glow_pulse_t0", "shader_vars": "0.80,1.50,0.80,0.00"}` (CA's Hell-Forge category block values). They must draw above the tabs: read `_panel_order`'s docstring for how draw order is decided and place them in the tier after the tabs. Mirror the four entries in the Lua layout table (the one holding `ic_tab_court = {18, 62, 240, 32}`), and add `ICUI.MARKS = {court = "ic_mark_court", offices = "ic_mark_offices", govs = "ic_mark_govs", petitions = "ic_mark_petitions"}`.

```lua
function ICUI.draw_marks(panel, faction)
    local ok, a = pcall(ICUI.attention, faction)
    if not ok then a = {} end
    for view, name in pairs(ICUI.MARKS) do
        local m = comp(name, panel)
        if m then m:SetVisible(a[view] == true) end
    end
end

-- CA'S OWN "LOOK AT ME" on a HUD button, the same call ICUI.confirm uses
-- (plan ruling 3). Started and stopped explicitly: a pulse nothing stops runs
-- until the button is destroyed.
function ICUI.pulse_opener(on)
    local button = comp(ICUI.BTN)
    if not button then return end
    pcall(function() pulse_uicomponent(button, on, ICUI.PULSE_STRENGTH, false) end)
end
```

Call `ICUI.draw_marks(panel, faction)` in `ICUI.refresh` wherever the tabs are lit (`ICUI.light_tabs`). In `ICUI.update_opener_tip`, after the tooltip is set: `local ok2, a = pcall(ICUI.attention, ICUI.player()); ICUI.pulse_opener(ok2 and a.any == true)`. `update_opener_tip` already runs one tick after the player's turn start and after panel actions, so no new listener is needed.

If the Task 1 probe found `pulse_uicomponent` invisible: replace `ICUI.pulse_opener` with a fifth marker, `ic_mark_opener`, created on the UI root beside the opener from a one-component layout generated like the burst file, `MoveTo`'d to the opener's top-right corner in `ICUI.place_opener`, and shown/hidden where the pulse would start/stop. Ledger the fallback.

- [ ] **Step 4: Run the harness and generator, verify they pass**

Expected: `iron court harness: ok (708 checks)`; `gen_ic_ui.py --check` ok; `make_ic_backdrop.py --check` ok (the markers are not text cells); `preview_iron_court.py --check` ok.

- [ ] **Step 5: Checkpoint**

`luac -p`; harness green.

---

### Task 5: Change numbers since the start of the turn

**Files:**
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_ui.lua` (`ICUI.fill_party` ~line 3093, a turn-start listener beside `ic_opener_tip` ~line 6048)
- Modify: `tools/gen_ic_ui.py` (20c sample for `ic_party_nums` ~line 5223)
- Test: `tools/_iron_court_harness.lua`

**Interfaces:**
- Produces: `ICUI.baseline` (faction key -> slug -> `{share = n, loyalty = n}`), `ICUI.take_baseline(faction)`, `ICUI.delta(n)` -> `""` or a coloured suffix.

- [ ] **Step 1: Write the failing checks**

```lua
check("a party's numbers show what moved since the turn began, and nothing before a baseline", function()
    IC.state = {}
    turn = 1
    make_faction(F, IC.CHD_SUBCULTURE, {make_character(1, ANY_SEAT, "forge")}, {})
    IC.add_house(F, IC.CROWN)
    IC.add_house(F, "forge")
    ICUI.baseline = {}
    with_fake_panel(function(panel)
        ICUI.view = "court"
        ICUI.refresh()
        local card = ICUI.party_card("forge")
        local before = card.children.ic_party_nums.text
        assert(not string.find(before, "[[col:", 1, true),
            "with no baseline the numbers carry a change: " .. before)
        ICUI.take_baseline(F)
        IC.move_loyalty(F, "forge", -10)
        ICUI.refresh()
        local after = card.children.ic_party_nums.text
        assert(string.find(after, "[[col:red]]-10[[/col]]", 1, true),
            "a loss of 10 loyalty reads " .. after)
    end)
    assert(ICUI.delta(0) == "", "no change still drew a suffix")
    assert(string.find(ICUI.delta(5), "[[col:green]]+5", 1, true), ICUI.delta(5))
end)
```

(`IC.move_loyalty` may clamp or scale; if the loss lands as another number, assert against `IC.court(F).houses.forge.loyalty - baseline` computed in the check rather than the literal 10.)

- [ ] **Step 2: Run the harness, verify it fails**

Expected: FAIL with `attempt to call field 'take_baseline' (a nil value)`.

- [ ] **Step 3: Implement**

```lua
-- WHAT MOVED THIS TURN (spec 2026-09-28 section 4.5). A snapshot of every
-- party's share and loyalty taken as the player's turn begins - BEFORE the
-- model's own turn-start work, since this file's listeners register first - so
-- the numbers show the turn's changes and the player's own. Kept on screen
-- only: after a load there is no snapshot, and no suffix, until the next turn.
ICUI.baseline = {}

function ICUI.take_baseline(faction)
    local court = IC.court(faction)
    local snap = {}
    for slug, house in pairs(court.houses) do
        snap[slug] = {share = math.floor(IC.share(faction, slug) + 0.5),
                      loyalty = house.loyalty or 0}
    end
    ICUI.baseline[faction] = snap
end

function ICUI.delta(n)
    if not n or n == 0 then return "" end
    if n > 0 then return string.format(" [[col:green]]+%d[[/col]]", n) end
    return string.format(" [[col:red]]%d[[/col]]", n)
end
```

In `ICUI.fill_party`, replace the `ic_party_nums` text with:

```lua
    local share = math.floor(IC.share(faction, slug) + 0.5)
    local loyalty = house.loyalty or 0
    local base = (ICUI.baseline[faction] or {})[slug]
    set_text(nums, string.format("%d%%%s of the court - %d%s loyalty",
        share, base and ICUI.delta(share - base.share) or "",
        loyalty, base and ICUI.delta(loyalty - base.loyalty) or ""))
```

Listener, beside `ic_opener_tip`:

```lua
core:add_listener("ic_baseline", "FactionTurnStart", true, function(context)
    local faction = context:faction()
    if not faction or faction:is_null_interface() then return end
    if faction:name() ~= ICUI.player() then return end
    pcall(ICUI.take_baseline, faction:name())
end, true)
```

Only for the local player, and it never touches the model or the save, so it is multiplayer-safe. Generator: change the 20c sample for `ic_party_nums` to the longest real string, `"100% [[col:green]]+99[[/col]] of the court - 100 [[col:red]]-99[[/col]] loyalty"`. If 20c then reports it does not fit, shorten the format to `"%d%%%s - %d loyalty%s"` (both in the Lua and the sample) rather than shrinking the font.

- [ ] **Step 4: Run the harness and generator, verify they pass**

Expected: `iron court harness: ok (709 checks)`; `gen_ic_ui.py --check` ok.

- [ ] **Step 5: Checkpoint**

`luac -p`; harness green.

---

### Task 6: Mutants, gates, build and docs

**Files:**
- Modify: `tools/mutate_iron_court.py` (append to `MUTANTS`)
- Modify: `docs/sessions/PATCH_NOTES_20260925_IRON_COURT.md`, `docs/sessions/HANDOFF_20260925_IRON_COURT_MCT_MULTIPLAYER.md`, `docs/SESSION_INDEX.md`
- Modify: `docs/CUSTOM_UI.md` (a short section: the swapped rim layer, `glow_pulse_t0` on a layer, the per-claim burst file, with what the probe proved)

- [ ] **Step 1: Add one mutant per behaviour**

Append to `MUTANTS` (each anchor must match exactly once; `U` is the UI file):

```python
    # ---- UI feedback, 2026-09-28 ---------------------------------------------
    ("a held seat's rim never lit", U,
     """ICUI.set_rim(card, "card", cqi and (stalled and "dim" or "lit") or nil)""",
     """ICUI.set_rim(card, "card", nil)"""),
    ("a stalled seat lit like a working one", U,
     """cqi and (stalled and "dim" or "lit") or nil""",
     """cqi and "lit" or nil"""),
    ("a recycled row keeps the last view's rim", U,
     """ICUI.set_rim(row, "row", line and line.rim or nil)""",
     """if line and line.rim then ICUI.set_rim(row, "row", line.rim) end"""),
    ("the burst never taken away", U,
     """            if b then b:Destroy() end""",
     """            if false then b:Destroy() end"""),
    ("a second claim finds the old burst and draws nothing", U,
     """        if old then old:Destroy() end""",
     """        if old then return end"""),
    ("releasing a governor answered with silence again", U,
     """ICUI.ANSWERS.ungov = confirmed(false, false""",
     """ICUI.ANSWERS.ungov_unused = confirmed(false, false"""),
    ("a yes answered with a chime and no words", U,
     """ICUI.notice = yes and ICUI.answer_text(""",
     """ICUI.notice = nil and ICUI.answer_text("""),
    ("a failed plot's red flash never goes out", U,
     """        pcall(function() ICUI.set_rim(ICUI.party_card(slug), "party", nil) end)""",
     """        pcall(function() end)"""),
    ("the Offices tab not marked for an empty seat", U,
     """        offices = s.empty > 0 or #s.ending > 0,""",
     """        offices = #s.ending > 0,"""),
    ("a governor away marks the Governors tab every turn", U,
     """        if not court.govs[province] then out.govs = true end""",
     """        out.govs = true"""),
    ("the button's pulse never stops", U,
     """    ICUI.pulse_opener(ok2 and a.any == true)""",
     """    ICUI.pulse_opener(true)"""),
    ("a change drawn before any baseline", U,
     """        share, base and ICUI.delta(share - base.share) or "",""",
     """        share, ICUI.delta(share - (base and base.share or 0)),"""),
```

Adjust each anchor to the code as written in Tasks 1-5 (the anchors above quote the plan's code; if an implementation step changed a line, aim the mutant at the line that now does the job - a stale anchor is a finding).

- [ ] **Step 2: Selftest and run the new mutants**

Run: `py tools/mutate_iron_court.py --selftest` -> `selftest ok: N mutants all anchored...`
Run (in the background, touching nothing meanwhile): `py tools/mutate_iron_court.py "rim" "burst" "claim" "silence again" "chime and no words" "red flash" "Offices tab" "Governors tab" "pulse never" "before any baseline"`
Expected: `12 mutants, 0 unexplained`. A survivor means its check is inert: strengthen the check, never delete the mutant.

- [ ] **Step 3: All gates**

`luac -p` the three files; `py tools/gen_iron_court.py` then `--check`; `py tools/check_lua_api.py`; `py tools/check_lua_literal_left.py`; `py tools/check_lua_undeclared.py` on the three files together; `py tools/gen_ic_ui.py --check` and `--selftest`; `py tools/make_ic_backdrop.py --check`; `import_iron_court.verify()` -> `[]`; `py tools/preview_iron_court.py --check`; `py tools/sync_iron_court_repo.py --check`.

- [ ] **Step 4: Build**

RPFM open, game closed: `py tools/deploy_iron_court.py --no-copy`. Byte-verify the three Lua files and `derpy_ic_burst.twui.xml` in the saved pack with `read_pack_index.read(path, "zzz_derpy_iron_court")` / `read(path, "derpy_ic_burst")` against the workspace files. Record MD5, size and file count.

- [ ] **Step 5: Docs**

- Patch notes, New section: one plain-words line each for the rim, the burst, tab markers and the button glow, answer sentences, change numbers, the failed-plot flash; Fixes: releasing a governor now answers.
- Handoff addendum: what shipped, the three plan rulings, the probe's results, harness count, build MD5.
- `docs/CUSTOM_UI.md`: a short section "Effects on a runtime panel" - the swapped rim layer with a transparent placeholder, `glow_pulse_t0` declared on a layer, a SpriteAnimation burst created and destroyed per use, re-finding components inside `cm:callback`, and which of these the probe proved in game.
- `docs/SESSION_INDEX.md`: extend the 2026-09-28 spec line with "built (build <MD5>), not deployed".

- [ ] **Step 6: Report**

Tell the author what shipped, the build's location, and the in-game checklist for everything after Phase 0: stalled/away dim rims, governor burst, answer sentences, the four tab markers, the button's pulse, change numbers, and the red flash on a failed plot.
