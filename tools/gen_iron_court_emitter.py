"""The Iron Court's XML emitter. A COPY of the Great Guilds' copy, deliberately.

WHY A COPY, again. Two mods that ship separately do not share a code path that
changes what they emit. The Guilds' own header records what happened when they did:
three fixes made for the Guilds silently restyled 20 cells of the already-published
Zharr Exchange. Copied from tools/gen_guilds_emitter.py on 2026-09-11, which is the
newer of the two and already carries the fontcat and leading fixes.

If a fix here is general, port it across deliberately rather than by sharing the
module.
"""

import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME = r"F:\SteamLibrary\steamapps\common\Total War WARHAMMER III"


class C(object):
    """One component. Children are nested in the hierarchy and flat in <components>."""

    def __init__(self, name, w, h, **kw):
        self.name, self.w, self.h, self.kw = name, w, h, kw
        self.kids = []
        self.gid = None
        self.sid = None

    def add(self, child):
        self.kids.append(child)
        return child

    def walk(self):
        yield self
        for k in self.kids:
            for d in k.walk():
                yield d


def assign(root, prefix):
    """Two GUIDs per component - the component and its standard state - from one counter."""
    n = [0]

    def guid():
        n[0] += 1
        return "%s%04X-D000-4000-B%015X" % (prefix, n[0], n[0])

    for c in root.walk():
        c.gid = guid()
        c.sid = guid()
        # A THIRD GUID PER COMPONENT, always minted even where no hover is authored. Handing
        # them out unconditionally keeps the counter - and therefore every GUID in the file -
        # independent of which components happen to carry a hover this build, so adding one
        # later does not renumber the rest.
        c.hid = guid()
    return root


def _esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def hierarchy(c, depth=2):
    tab = "\t" * depth
    if not c.kids:
        return '%s<%s this="%s"/>\n' % (tab, c.name, c.gid)
    out = '%s<%s this="%s">\n' % (tab, c.name, c.gid)
    for k in c.kids:
        out += hierarchy(k, depth + 1)
    out += "%s</%s>\n" % (tab, c.name)
    return out


def _spec(kw, key):
    """The image layer list for one state. `image` is shorthand for a single standard layer."""
    if kw.get(key):
        return list(kw[key])
    if key == "layers" and kw.get("image"):
        return [{"path": kw["image"], "offset": (0, 0), "dw": 0, "dh": 0,
                 "margin": kw.get("imagemargin", 0), "colour": kw.get("colour_img"),
                 "tile": kw.get("tile", False), "dock": None}]
    return []


# FONT CATEGORY IS A FIXED VOCABULARY, NOT A NUMBER. Counted across ui.pack,
# ui2.pack and ui3.pack: 32 distinct fontcat_name values, and the only BODY sizes in
# them are 10, 12 and 16. This emitter built the name as "body_%d" from the requested
# pixel size, so every size-14 label in the Exchange and the Guilds shipped
# fontcat_name="body_14" - a category the game does not have. An unknown value is not
# an error and not a blank; the engine falls back, so the label draws at a size nobody
# chose. That is why button captions and card text never matched their layout.
#
# Snap to the nearest real body category, or pass fontcat= to name one outright (the
# header_* family are the other real ones - see FONTCATS).
FONTCATS = set("""
body_10 body_12 body_16 body_12_bold body_12_italic body_alternative_12
header_12 header_14 header_16 header_18 header_20_bold header_24_bold
header_16_bold header_18_bold header_alternative_18
dev_text dev_text_on_white dev_text_grey dev_button_text dev_subheader
dev_header dev_item_header dev_text_grey_disable dev_text_dark_grey_on_white
grudges_subheader
""".split())

_BODY_SIZES = (10, 12, 16)


def fontcat(kw):
    """The font category for a text block: an explicit fontcat=, else nearest body."""
    named = kw.get("fontcat")
    if named:
        assert named in FONTCATS, "no such font category: %r" % (named,)
        return named
    size = kw.get("size", 12)
    return "body_%d" % min(_BODY_SIZES, key=lambda n: abs(n - size))


def _state(c, name, sguid, entries, target):
    """One <state> block. `entries` are (componentimage guid, metrics guid, layer) tuples.

    `target` is the state GUID this one transitions to, or None for a component with only the
    one state.

    THE TRANSITION MAP IS WHAT MAKES HOVER WORK, and authoring the extra state without it is
    the silent failure here - the state exists, the engine has no edge to reach it by, and the
    button simply never lights. The index vocabulary is read out of CA's own
    ui/templates/round_small_button.twui.xml, whose active state carries an index-less
    transition to hover and whose hover state carries index="1" back to active:
        (omitted) = 0  mouse enters
        1              mouse leaves
        2              mouse down
    Only 0 and 1 are used here. A press state would need 2 and its own texture, and the button
    already has a click sound, so it buys nothing.
    """
    kw = c.kw
    st = ['this="%s"' % sguid, 'name="%s"' % name,
          'width="%d"' % c.w, 'height="%d"' % c.h]
    if kw.get("interactive"):
        st.append('interactive="true"')
    # NO dockpoint / dock_offset. MEASURED 2026-09-04: the engine ignores both on these
    # runtime-created components - every child rendered at its parent's origin, stacked, so only
    # the last-drawn one was visible. uicomponent:MoveTo works, so EX.layout() in
    # zzz_derpy_chd_exchange.lua positions every component explicitly. The same is true of
    # SetDockOffset at runtime.
    st.append('uniqueguid="%s"' % sguid)
    out = "\t\t\t\t<%s\n\t\t\t\t\t%s>\n" % (name, "\n\t\t\t\t\t".join(st))

    if entries:
        out += "\t\t\t\t\t<imagemetrics>\n"
        for cig, mg, lay in entries:
            ox, oy = lay.get("offset", (0, 0))
            dock = lay.get("dock", "Center")
            out += ('\t\t\t\t\t\t<image\n\t\t\t\t\t\t\tthis="%s"\n'
                    '\t\t\t\t\t\t\tuniqueguid="%s"\n\t\t\t\t\t\t\tcomponentimage="%s"\n'
                    '\t\t\t\t\t\t\toffset="%.2f,%.2f"\n\t\t\t\t\t\t\twidth="%d"\n'
                    '\t\t\t\t\t\t\theight="%d"\n'
                    % (mg, mg, cig, ox, oy,
                       c.w + lay.get("dw", 0), c.h + lay.get("dh", 0)))
            if lay.get("tile"):
                out += '\t\t\t\t\t\t\ttile="true"\n'
            # MIRRORS THE GLYPH HORIZONTALLY. x_flipped, NOT flipped - the shorter name
            # is not an attribute the engine knows, and an unknown attribute is ignored
            # in silence, so the first version of this shipped two arrows pointing the
            # same way with every check green (screenshotted 2026-09-07). The name is
            # copied out of CA's own ui/templates/cycle_button_arrow_next.twui.xml,
            # where it is the ONLY difference from the previous button.
            if lay.get("flip"):
                out += '\t\t\t\t\t\t\tx_flipped="true"\n'
            if dock:
                out += '\t\t\t\t\t\t\tdockpoint="%s"\n' % dock
            if lay.get("colour"):
                out += '\t\t\t\t\t\t\tcolour="%s"\n' % lay["colour"]
            m = float(lay.get("margin", 0))
            out += '\t\t\t\t\t\t\tmargin="%.2f,%.2f,%.2f,%.2f"/>\n' % (m, m, m, m)
        out += "\t\t\t\t\t</imagemetrics>\n"

    if target:
        # index is OMITTED on the enter edge and 1 on the leave edge - CA's own shape.
        idx = "" if name == "standard" else '\n\t\t\t\t\t\t\tindex="1"'
        out += ('\t\t\t\t\t<transitionmap>\n\t\t\t\t\t\t<transition%s\n'
                '\t\t\t\t\t\t\ttransition_m_target_state="%s"/>\n'
                '\t\t\t\t\t</transitionmap>\n' % (idx, target))

    if kw.get("text"):
        # EMITTED ON EVERY STATE, not just standard. A state with no component_text draws its
        # label in the engine's default font, so a hover state missing this block changes the
        # typeface the instant the mouse arrives.
        #
        # The STRING is a separate problem and it is solved in Lua: SetStateText writes to the
        # CURRENT state only, so a dynamic label ("Buy 10") set once would leave the hover state
        # blank. EX.set_state_text walks the states and writes each. See its comment.
        out += ('\t\t\t\t\t<component_text\n'
                # texthalign is HORIZONTAL, textvalign is VERTICAL - counted in ui3.pack:
                # textvalign is Center 8734 / Bottom 219, texthalign is Center 3981 /
                # Right 631. This generator had them the other way round, and passed British
                # "Centre", which is not a value the engine accepts - an unknown value is
                # ignored in silence, so every button label sat left and high.
                '\t\t\t\t\t\ttexthalign="%s"\n\t\t\t\t\t\ttextvalign="%s"\n'
                '\t\t\t\t\t\ttextxoffset="%s"\n\t\t\t\t\t\ttextyoffset="%s"\n'
                '\t\t\t\t\t\ttexthbehaviour="Never split"\n'
                '\t\t\t\t\t\tfont_m_size="%d"\n\t\t\t\t\t\tfont_m_colour="%s"\n'
                '\t\t\t\t\t\tfont_m_leading="%d"\n\t\t\t\t\t\tfontcat_name="%s"/>\n'
                # "Never split" IS THE ONLY ONE OF THE THREE THAT KEEPS A
                # LABEL ON ONE LINE, and it is written in rather than passed,
                # so no caller can ask for the other two by accident.
                #
                # CA ships three, counted across ui.pack, ui2, ui3 and ui_3 on
                # 2026-09-12: "Never split" 5365, "Resize" 4403, "Slip by
                # character" 115. "Resize" does NOT shrink text to fit - it
                # WRAPS it, one word per line, and draws outside the height the
                # component declares. This was measured on screen: a cell
                # declaring width="304" wrapped a 27-character name down across
                # the three cells below it. A cell too small for its string is
                # a layout to fix, which is what check 20c measures; clipping
                # makes that visible and "Resize" hides it behind a wall of
                # single words.
                % (kw.get("align", "Left"), kw.get("valign", "Center"),
                   kw.get("tx", "4.00,0.00"),
                   kw.get("ty", "8.00,0.00"),
                   kw.get("size", 12),
                   kw.get("colour", "#FFF8D7FF"), kw.get("leading", 3),
                   fontcat(kw)))

    out += "\t\t\t\t</%s>\n" % name
    return out




def component(c):
    kw = c.kw
    attrs = ['this="%s"' % c.gid, 'id="%s"' % c.name, 'tooltipslocalised="true"']
    if kw.get("tooltip"):
        # literal, not {{tr:}} - see the TIP_* block for the measurement behind that
        attrs.append('componentleveltooltip="%s"' % _esc(kw["tooltip"]))
    if kw.get("priority"):
        attrs.append('priority="%d"' % kw["priority"])
    # UI sound. This is a component ATTRIBUTE (it sits beside priority in CA's own templates),
    # not a script call - common.trigger_soundevent takes a sound EVENT, and CA's UI clicks are
    # driven by these CATEGORIES instead. Names harvested from ui3.pack; an invented one is
    # silent with no error, so only use categories that actually appear there.
    if kw.get("sound"):
        attrs.append('soundcategory="%s"' % kw["sound"])
    attrs += ['uniqueguid="%s"' % c.gid,
              'currentstate="%s"' % c.sid, 'defaultstate="%s"' % c.sid]
    out = "\t\t<%s\n\t\t\t%s>\n" % (c.name, "\n\t\t\t".join(attrs))

    # A CONTEXT COLOUR BINDING - the one and only way a COLOUR can vary at runtime.
    #
    # Script can set an image path and an opacity; there is no colour or tint setter on a
    # uicomponent anywhere in CA's reference. What there is, is this: a callback declared on
    # the component that reads a Colour off a context object and applies it to chosen image
    # layers. uicomponent:SetContextObject(cco(...)) then decides WHICH object, per component,
    # at runtime - so the colour follows whatever cco the Lua hands this cell.
    #
    # Shape copied from ui/battle ui/reinforcement_icon.twui.xml, which colours two of its
    # layers this way. The property NAME is an enumerator - colour_index0 is "the first layer
    # to colour" - and its VALUE is the image index, which is why CA's file pairs
    # colour_index1 with value 2.
    #
    # A LAYER COLOUR MULTIPLIES. CA's masks are pure white where they mark (measured: one
    # distinct opaque colour, 255/255/255), so white times the faction colour is the faction
    # colour, and the mask's transparent 82% stays untouched.
    cc = kw.get("colour_from")
    if cc:
        out += ('\t\t\t<callbackwithcontextlist>\n'
                '\t\t\t\t<callback_with_context\n'
                '\t\t\t\t\tcallback_id="ContextColourSetter"\n'
                '\t\t\t\t\tcontext_object_id="%s"\n'
                '\t\t\t\t\tcontext_function_id="%s">\n'
                '\t\t\t\t\t<child_m_user_properties>\n'
                '\t\t\t\t\t\t<property\n'
                '\t\t\t\t\t\t\tname="colour_index0"\n'
                '\t\t\t\t\t\t\tvalue="%d"/>\n'
                '\t\t\t\t\t</child_m_user_properties>\n'
                '\t\t\t\t</callback_with_context>\n'
                '\t\t\t</callbackwithcontextlist>\n'
                % (_esc(cc["object"]), _esc(cc["function"]), cc["index"]))

    # ONE component_image PER LAYER OF EVERY STATE, concatenated. <componentimages> is a
    # COMPONENT-level list and each state's <imagemetrics> picks the entries it draws by GUID -
    # CA's round_small_button carries seven images and each of its eleven states references a
    # different handful. A texture used by both states therefore appears twice here, which is
    # harmless and keeps the index arithmetic below trivial.
    std_spec = _spec(kw, "layers")
    hov_spec = _spec(kw, "hover")
    layers = []
    for i, lay in enumerate(std_spec + hov_spec):
        # Two fresh guid slots per layer, well inside the -D0xx- space at these layer counts.
        layers.append((c.gid.replace("-D000-", "-D%03d-" % (i * 2 + 1)),
                       c.gid.replace("-D000-", "-D%03d-" % (i * 2 + 2)), lay))
    if layers:
        out += "\t\t\t<componentimages>\n"
        for cig, _mg, lay in layers:
            out += ('\t\t\t\t<component_image\n\t\t\t\t\tthis="%s"\n'
                    '\t\t\t\t\tuniqueguid="%s"\n\t\t\t\t\timagepath="%s"/>\n'
                    % (cig, cig, _esc(lay["path"])))
        out += "\t\t\t</componentimages>\n"

    # THE STATE LIST. One state where no hover is authored - which is every text cell, the
    # sparkline bars and the panel itself - and two where one is, wired to each other by the
    # transition map inside _state().
    out += "\t\t\t<states>\n"
    if hov_spec:
        out += _state(c, "standard", c.sid, layers[:len(std_spec)], c.hid)
        out += _state(c, "hover", c.hid, layers[len(std_spec):], c.sid)
    else:
        out += _state(c, "standard", c.sid, layers, None)
    out += "\t\t\t</states>\n\t\t</%s>\n" % c.name
    return out


def layout(root, comment):
    out = '<?xml version="1.0"?>\n<layout\n\tversion="142"\n\tcomment="%s"\n' % _esc(comment)
    out += '\tprecache_condition="">\n\t<hierarchy>\n'
    out += hierarchy(root)
    out += "\t</hierarchy>\n\t<components>\n"
    for c in root.walk():
        out += component(c)
    out += "\t</components>\n</layout>\n"
    return out

def _game_assets():
    """Every file path in the game's ui packs, cached. Used to prove a texture exists."""
    import json
    cache = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         ".skilltree_cache", "ui_asset_paths.json")
    if os.path.isfile(cache):
        return set(json.load(open(cache, encoding="utf-8")))
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import read_pack_index as rpi
    data = os.path.join(GAME, "data")
    out = set()
    for name in sorted(os.listdir(data)):
        if not name.endswith(".pack") or not name.startswith("ui"):
            continue
        try:
            out.update(rpi.paths(os.path.join(data, name)))
        except Exception:
            pass
    assert out, "no ui pack read from %s" % data
    json.dump(sorted(out), open(cache, "w", encoding="utf-8"))
    return out

