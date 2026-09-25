"""Four rebel crests: our own devices on CA's own Chaos Dwarf rebel banner.

WHY THIS EXISTS. All four dormant factions a secession can become share ONE
flags_path in factions_tables:

    wh3_dlc23_chd_chaos_dwarfs_qb1  ->  ui\\flags\\wh3_dlc23_chd_chaos_dwarfs_rebels
    wh3_dlc23_chd_chaos_dwarfs_qb2  ->  the same
    wh3_dlc23_chd_chaos_dwarfs_qb3  ->  the same
    wh3_dlc25_chd_chaos_dwarfs_invasion -> the same

so two rebellions on one map are two identical green banners, which is what the
author photographed on 2026-09-17: "the faction logo should also be the party
faction logo".

AND A CREST CANNOT BE SET AT RUNTIME. flags_path is a factions_tables column and
nothing in CA's whole scripting reference writes one - searched, not assumed.
cm:change_custom_faction_name fixes the NAME and has no counterpart for the
picture. So the only lever is the DB, and the DB is read before the campaign
rolls which parties it seats: the crest can be distinct per FACTION and can never
be the specific party's own sigil. Four crests is the engine's ceiling. Ruthless
seats five rivals (2026-09-25), and a fifth party that leaves joins a rising
already under way instead of wanting a crest of its own - IC.rebel_faction.

RECOLOURED, NOT DRAWN. The frame, the rivets, the scratched plate and the torn
edge are CA's and stay CA's; only the sigil's hue moves. A hand-drawn crest beside
fifty of CA's reads as a mod's crest, and the point is a faction the player takes
as seriously as any other.

THE SIGIL IS SELECTED BY HUE, NOT BY A MASK. CA's rebel sigil sits at hue ~100
degrees (green) while the bronze frame is ~25 (orange) and the plate is almost
unsaturated. So: rotate the hue of every pixel that is both saturated enough to
be paint and inside the green band, and leave value and saturation alone - the
scratches, the bevel and the grain all survive because they are value, not hue.
Measured rather than guessed: report() prints the hue histogram of each file.

SIX FILES PER FOLDER, because that is what CA ships and a missing one is a blank
square with nothing in the log:

    mon_24.png      24x24    RGBA   the framed banner, diplomacy list
    mon_64.png      64x64    RGBA   the framed banner, larger
    mon_256.png     256x256  RGBA   the framed banner, full
    mon_icon.png    256x256  RGBA   the bare sigil on transparency
    mon_rotated.png 112x90   RGBA   the banner in perspective
    mon_banner.dds  256x256  BC3_UNORM, 9 mips - the BATTLE banner

THE DDS IS THE ONE THAT NEEDS A TOOL. Pillow silently downgrades the format, so
texconv does the encode: BC3_UNORM with a full mip chain, matching what texdiag
reports for CA's own file.

    py tools/make_ic_rebel_flags.py --check      re-measure what ships
    py tools/make_ic_rebel_flags.py --write      rebuild the four folders
    py tools/make_ic_rebel_flags.py --report     hue histogram of CA's art
    py tools/make_ic_rebel_flags.py --selftest
"""
import colorsys
import io
import os
import struct
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACK = os.path.join(ROOT, "Modding Files", "pack")
GAME_DATA = os.path.join("F:" + os.sep, "SteamLibrary", "steamapps", "common",
                         "Total War WARHAMMER III", "data")
TEXCONV = os.path.join(ROOT, "texconv", "texconv.exe")
CACHE = os.path.join(ROOT, ".skilltree_cache", "ic_rebel_flag_src")

# CA's own, the one every rebellion wears today.
DONOR = "ui/flags/wh3_dlc23_chd_chaos_dwarfs_rebels/"
FILES = [("mon_24.png", (24, 24)), ("mon_64.png", (64, 64)),
         ("mon_256.png", (256, 256)), ("mon_icon.png", (256, 256)),
         ("mon_rotated.png", (112, 90))]
DDS = "mon_banner.dds"

# WHICH FACTION WEARS WHICH, and the order is the order IC.rebel_faction walks
# IC.REBEL_POOL - so the first rebellion of a campaign is the first crest, the
# second is the second, and a player watching two of them can tell them apart.
#
# THE HUES ARE FOUR OF THE PANEL'S OWN PARTY COLOURS, read off gen_ic_ui rather
# than picked here, so a rebel crest and the standing bar are the same palette.
# Not the party's own colour - which party secedes is rolled per campaign and
# this is baked into the DB - but the same family, which is the whole of what
# the engine allows.
CREST = [
    ("wh3_dlc23_chd_chaos_dwarfs_qb1", "derpy_ic_rising_01", "crown",
     "rising_01.png"),
    ("wh3_dlc23_chd_chaos_dwarfs_qb2", "derpy_ic_rising_02", "legion",
     "rising_02.png"),
    ("wh3_dlc23_chd_chaos_dwarfs_qb3", "derpy_ic_rising_03", "tower",
     "rising_03.png"),
    ("wh3_dlc25_chd_chaos_dwarfs_invasion", "derpy_ic_rising_04", "hearth",
     "rising_04.png"),
]

# THE SUPPLIED ART. Whole flags - white device on CA's plate, in CA's frame.
# Only the DEVICE is taken; see the module docstring for why not the frame.
CREST_SRC = os.path.join(ROOT, "Modding Files", "source", "ic_crests")

# A DEVICE PIXEL: bright, and barely coloured. The devices are white on near
# black stone, so value alone separates them and the saturation test keeps the
# bronze out of it.
DEVICE_VALUE = 0.62
DEVICE_SAT = 0.30

# A PART SMALLER THAN THIS FRACTION OF THE LARGEST IS A SPECK. Measured, not
# picked: the two frame ornaments that survive the plate test come out at 19px
# and 13px in every one of the four files, and the smallest part that is really
# device is the ziggurat's top block at 426px. Anything from 0.5% to 25% would
# separate them; 2% sits well inside that.
DEVICE_SPECK = 0.02

# THE SAME IDEA ON CA'S OWN MASK, AT A DIFFERENT SIZE. CA's device has four
# satellite marks that must be erased with it, and they run 1.5-2.3% of the
# device - so DEVICE_SPECK's 2% would delete half of them and leave CA's marks
# showing on the flag. The strays that do need dropping are at most 0.30%.
# Measured across all six layouts; see the docstring on restyle's erase step.
ERASE_SPECK = 0.008

# TINTED, OR LEFT AS DRAWN. The four hues are what makes two rebellions on one
# map tellable apart at a glance; white is what the artist drew. Flipping this
# to False ships the devices in their own colour.
CREST_TINT = True

# ---------------------------------------------------------------------------
# The supplied devices.
# ---------------------------------------------------------------------------
def plate_mask(im):
    """CA's stone field: everything inside the frame, holes filled.

    BUILT FROM "DARK AND BARELY SATURATED" AND THEN FILLED BY ROW. The raw test
    returns a ring with a device-shaped hole in the middle, because CA's own
    device is bright and green and fails it - and the hole is exactly where a
    device needs to go. The plate is a rectangle with one corner cut away, so
    for every row the span between its first and last stone pixel IS the plate:
    no flood fill, no convex hull, and the cut corner survives because it is
    still one span per row.

    Then a light erode, so the search stops short of the frame's inner bevel.
    """
    from PIL import Image, ImageDraw, ImageFilter
    im = im.convert("RGBA")
    px = im.load()
    w, h = im.size
    out = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(out)
    for y in range(h):
        lo, hi = None, None
        for x in range(w):
            r, g, b, a = px[x, y]
            if a < 200:
                continue
            _hh, ss, vv = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
            if vv < 0.32 and ss < 0.40:
                lo = x if lo is None else lo
                hi = x
        if lo is not None and hi - lo > 2:
            d.line([(lo, y), (hi, y)], fill=255)
    k = max(3, int(round(min(w, h) / 96.0)) * 2 + 1)
    return out.filter(ImageFilter.MinFilter(k))


def _extent(mask, thresh=128):
    """(bbox, centroid, count) of a mask, in one walk."""
    p = mask.load()
    w, h = mask.size
    xs = ys = 0
    n = 0
    x0, y0, x1, y1 = w, h, -1, -1
    for y in range(h):
        for x in range(w):
            if p[x, y] < thresh:
                continue
            n += 1
            xs += x
            ys += y
            x0 = min(x0, x)
            y0 = min(y0, y)
            x1 = max(x1, x)
            y1 = max(y1, y)
    if not n:
        return None, None, 0
    return (x0, y0, x1 + 1, y1 + 1), (xs / float(n), ys / float(n)), n


def _parts(mask):
    """Every connected part of a mask, as lists of points."""
    from collections import deque
    w, h = mask.size
    p = mask.load()
    seen = [[False] * w for _ in range(h)]
    parts = []
    for y in range(h):
        for x in range(w):
            if p[x, y] < 128 or seen[y][x]:
                continue
            q = deque([(x, y)])
            seen[y][x] = True
            pts = []
            while q:
                cx, cy = q.popleft()
                pts.append((cx, cy))
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1),
                               (1, 1), (1, -1), (-1, 1), (-1, -1)):
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < w and 0 <= ny < h and p[nx, ny] >= 128 \
                            and not seen[ny][nx]:
                        seen[ny][nx] = True
                        q.append((nx, ny))
            parts.append(pts)
    return parts


def _components(mask):
    """Part sizes, largest first. The measurement ERASE_SPECK is set from."""
    return sorted((len(p) for p in _parts(mask)), reverse=True) or [0]


def _despeckle(mask, frac=DEVICE_SPECK):
    """Drop parts far smaller than the largest. See DEVICE_SPECK."""
    from PIL import Image
    w, h = mask.size
    parts = _parts(mask)
    if not parts:
        return mask
    big = max(len(x) for x in parts)
    out = Image.new("L", (w, h), 0)
    op = out.load()
    for pts in parts:
        if len(pts) >= frac * big:
            for x, y in pts:
                op[x, y] = 255
    return out


_DEVICE_CACHE = {}


def crest_device(src_name):
    """The supplied device, lifted off CA's 256 plate.

    Returns (cover, detail, ratio, offset):
      cover  - L mask, cropped to the device, its coverage
      detail - L, the artist's own luminance inside it, so the cracks survive
      ratio  - device's long side as a fraction of the plate's short side
      offset - device centre minus plate centroid, over the plate's short side
    The last two are what let a different layout - the perspective banner, the
    battle banner - be given the same device at the same relative size and
    position without inheriting CA's composition for its own device.
    """
    from PIL import Image
    if src_name in _DEVICE_CACHE:
        return _DEVICE_CACHE[src_name]
    ca = Image.open(os.path.join(fetch(), "mon_256.png")).convert("RGBA")
    plate = plate_mask(ca)
    pbox, pcent, _n = _extent(plate)
    short = min(pbox[2] - pbox[0], pbox[3] - pbox[1])

    art = Image.open(os.path.join(CREST_SRC, src_name)).convert("RGB")
    art = art.resize(ca.size, Image.LANCZOS)
    ap = art.load()
    pp = plate.load()
    w, h = ca.size
    cover = Image.new("L", (w, h), 0)
    detail = Image.new("L", (w, h), 0)
    cp, dp = cover.load(), detail.load()
    for y in range(h):
        for x in range(w):
            if pp[x, y] < 128:
                continue
            r, g, b = ap[x, y]
            _hh, ss, vv = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
            if vv > DEVICE_VALUE and ss < DEVICE_SAT:
                cp[x, y] = 255
                dp[x, y] = int(round(vv * 255))
    cover = _despeckle(cover)
    dbox, dcent, n = _extent(cover)
    if not n:
        raise RuntimeError("%s: no device found on the plate" % src_name)
    ratio = max(dbox[2] - dbox[0], dbox[3] - dbox[1]) / float(short)
    offset = ((dcent[0] - pcent[0]) / float(short),
              (dcent[1] - pcent[1]) / float(short))
    out = (cover.crop(dbox), detail.crop(dbox), ratio, offset)
    _DEVICE_CACHE[src_name] = out
    return out

# CA's sigil, measured by --report: the green paint clusters at hue 0.26-0.30 of
# a turn with saturation above 0.35. The bronze frame is 0.05-0.10 and the plate
# is under 0.20 saturation, so neither is touched.
SIGIL_HUE = (0.22, 0.38)
SIGIL_SAT = 0.30

# HOW FAR APART TWO CRESTS MUST MEASURE at 24 pixels, over the saturated pixels
# only. The current four measure 12.9 at their closest (indigo against purple),
# so this is a floor under what ships rather than a description of it.
CREST_GAP = 10


def flag_dir(folder):
    return "ui/flags/%s" % folder


def paths():
    """Every in-pack path these four folders own."""
    out = []
    for _key, folder, _slug, _shape in CREST:
        for name, _size in FILES:
            out.append("%s/%s" % (flag_dir(folder), name))
        out.append("%s/%s" % (flag_dir(folder), DDS))
    return sorted(out)


def target_hue(slug):
    """The hue of a party colour, as a fraction of a turn."""
    import gen_ic_ui as U
    hexcol = U.HOUSE_COLOUR[slug]
    r = int(hexcol[1:3], 16) / 255.0
    g = int(hexcol[3:5], 16) / 255.0
    b = int(hexcol[5:7], 16) / 255.0
    return colorsys.rgb_to_hsv(r, g, b)[0]


# ---------------------------------------------------------------------------
# CA's art, offline.
# ---------------------------------------------------------------------------
def _unwrap(raw):
    """ui/**/* in CA's packs is a u32 length then a zstd frame."""
    if len(raw) > 8 and raw[4:8] == b"\x28\xb5\x2f\xfd":
        want = struct.unpack("<I", raw[:4])[0]
        import zstandard
        return zstandard.ZstdDecompressor().decompress(
            raw[4:], max_output_size=max(want, 1 << 24))
    return raw


def fetch(force=False):
    """CA's six files into .skilltree_cache, with RPFM shut. Returns the dir."""
    os.makedirs(CACHE, exist_ok=True)
    want = [n for n, _s in FILES] + [DDS]
    if not force and all(os.path.isfile(os.path.join(CACHE, n)) for n in want):
        return CACHE
    import read_pack_index as R
    got = set()
    for pack in sorted(os.listdir(GAME_DATA)):
        if not pack.endswith(".pack") or got == set(want):
            continue
        try:
            hits = R.read(os.path.join(GAME_DATA, pack), DONOR)
        except Exception:                                  # noqa: BLE001
            continue
        for path, _comp, raw in hits:
            name = path.replace("\\", "/").rsplit("/", 1)[-1]
            if name in want:
                io.open(os.path.join(CACHE, name), "wb").write(_unwrap(raw))
                got.add(name)
    missing = [n for n in want if n not in got
               and not os.path.isfile(os.path.join(CACHE, n))]
    if missing:
        raise RuntimeError("CA's rebel flag is missing %s from %s"
                           % (", ".join(missing), GAME_DATA))
    return CACHE


def sigil_box(im):
    """Which pixels are CA's device, and the box they sit in.

    Returns (mask, box) with mask an L-mode image the size of `im`. The hue band
    is the same one the recolour used, so "what to repaint" and "what used to be
    painted" cannot drift apart.
    """
    from PIL import Image
    im = im.convert("RGBA")
    px = im.load()
    w, h = im.size
    mask = Image.new("L", (w, h), 0)
    mp = mask.load()
    xs, ys = [], []
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            hh, ss, _v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
            if ss >= SIGIL_SAT and SIGIL_HUE[0] <= hh <= SIGIL_HUE[1]:
                mp[x, y] = 255
                xs.append(x)
                ys.append(y)
    if not xs:
        return mask, None
    return mask, (min(xs), min(ys), max(xs) + 1, max(ys) + 1)


def restyle(im, src_name, hue):
    """CA's banner with our device on it. Returns (image, pixels painted)."""
    from PIL import Image, ImageFilter
    im = im.convert("RGBA")
    mask, box = sigil_box(im)
    if box is None:
        return im, 0
    w, h = im.size

    # STRAYS FIRST, OR THE DILATION TURNS THEM INTO BLOCKS. A four-pixel speck
    # of CA's hue band near the banner's edge grew into a 27px square of flat
    # ring-grey on both battle banners. It also widened the box, which is what
    # sets the dilation radius and the ring the fill is averaged from, so the
    # box is taken again from the cleaned mask. See ERASE_SPECK for the numbers
    # and for why the supplied art's threshold is the wrong one here.
    mask = _despeckle(mask, ERASE_SPECK)
    box, _cent, n = _extent(mask)
    if not n:
        return im, 0

    # ---- 2. erase -------------------------------------------------------
    # THE MASK IS GROWN FIRST, and that is not a refinement - without it the old
    # device is still on the banner. The hue band selects CA's PAINT; the device
    # is also drawn with a pale outline sitting far below SIGIL_SAT, so erasing
    # the band alone lifts the green and leaves a white line drawing of the old
    # sigil showing through the new one. Measured off the preview, not guessed.
    # The radius is odd and proportional so one rule covers 256px and 24px.
    grow = max(3, int(round((box[2] - box[0]) / 16.0)) * 2 + 1)
    mask = mask.filter(ImageFilter.MaxFilter(grow))
    # THE FILL COMES FROM THE RING AROUND THE HOLE, not from a blur of it.
    # Punching the hole transparent and blurring darkens everything nearby -
    # PIL blurs each channel and the RGB under a zero alpha is (0,0,0) - which
    # painted a soot-coloured blob, shaped like CA's old sigil, behind every
    # device. Measured off the preview.
    mp = mask.load()
    ip = im.load()
    ring, rs = [], [0, 0, 0, 0]
    for y in range(max(0, box[1] - 6), min(h, box[3] + 6)):
        for x in range(max(0, box[0] - 6), min(w, box[2] + 6)):
            if mp[x, y] == 0:
                ring.append(ip[x, y])
    if ring:
        for p in ring:
            for i in range(4):
                rs[i] += p[i]
        fill = tuple(int(round(c / float(len(ring)))) for c in rs)
    else:
        fill = (0, 0, 0, 0)
    base = Image.composite(Image.new("RGBA", (w, h), fill), im, mask)
    # DIFFUSED FROM THE EDGE INWARD. Blur the whole frame, then put every known
    # pixel back exactly as it was, and repeat: the boundary is reasserted each
    # pass so the hole converges to a smooth interpolation of what surrounds it.
    # That follows the plate's vignette without this file knowing the plate is
    # lit at all - a single averaged fill left a patch shaped like the device it
    # was hiding, which is what the preview showed.
    radius = max(1.0, (box[2] - box[0]) / 12.0)
    for _ in range(12):
        base = Image.composite(
            base.filter(ImageFilter.GaussianBlur(radius)), im, mask)

    # ---- 3. paint -------------------------------------------------------
    # PLACED AGAINST THE PLATE, NOT AGAINST CA'S DEVICE BOX. See the docstring
    # on crest_device: `box` above is CA's composition and is only used to
    # decide what to ERASE. Where OUR device goes is the plate's own centroid,
    # at the size and offset the supplied art chose, both as fractions of the
    # plate - so the perspective banner and the battle banner, whose layouts CA
    # drew differently, still get the device the artist drew.
    cover, detail, ratio, offset = crest_device(src_name)
    pmask = plate_mask(im)
    pbox, pcent, pn = _extent(pmask)
    if not pn:
        # NO PLATE HERE. mon_icon.png is the bare device on transparency - the
        # same layout as mon_256 with the frame and the stone taken away - so
        # mon_256's plate is the anchor, scaled to this file. Read off CA's own
        # art rather than written down, so a patch that moves the plate moves
        # this with it.
        ref = Image.open(os.path.join(fetch(), "mon_256.png")).convert("RGBA")
        rbox, rcent, rn = _extent(plate_mask(ref))
        if not rn:
            return im, 0
        sx, sy = w / float(ref.size[0]), h / float(ref.size[1])
        pbox = (rbox[0] * sx, rbox[1] * sy, rbox[2] * sx, rbox[3] * sy)
        pcent = (rcent[0] * sx, rcent[1] * sy)
    short = min(pbox[2] - pbox[0], pbox[3] - pbox[1])
    long_side = max(1, int(round(ratio * short)))
    cw, ch = cover.size
    scale = long_side / float(max(cw, ch))
    tw, th = max(1, int(round(cw * scale))), max(1, int(round(ch * scale)))
    cover = cover.resize((tw, th), Image.LANCZOS)
    detail = detail.resize((tw, th), Image.LANCZOS)
    cx = pcent[0] + offset[0] * short
    cy = pcent[1] + offset[1] * short
    ox, oy = int(round(cx - tw / 2.0)), int(round(cy - th / 2.0))
    full = Image.new("L", (w, h), 0)
    full.paste(cover, (ox, oy))
    det = Image.new("L", (w, h), 0)
    det.paste(detail, (ox, oy))
    box = (max(0, ox), max(0, oy), min(w, ox + tw), min(h, oy + th))

    # SHADED, NOT FILLED. Each painted pixel keeps CA's own luminance under it,
    # pulled toward the device's value - so the weave, the bevel and the
    # scratches still read through and the device sits IN the cloth.
    px = base.load()
    fp = full.load()
    # SHADED FROM THE ORIGINAL FRAME AND NOT THE ERASED ONE. The erase is a
    # heavy blur, so every pixel beneath the device has nearly the same value
    # and shading from it produced one flat colour. CA's untouched frame still
    # has the weave, the bevel and the scratches in it.
    op = im.load()
    dtp = det.load()
    painted = 0
    for y in range(box[1], box[3]):
        for x in range(box[0], box[2]):
            cov = fp[x, y]
            if cov == 0:
                continue
            r, g, b, a = px[x, y]
            # THE ARTIST'S OWN LUMINANCE, which is what carries the cracks and
            # the weathering. CA's cloth underneath is the fallback for the
            # feathered edge, where the supplied art has no opinion.
            dv = dtp[x, y]
            if dv > 0:
                vv = dv / 255.0
            else:
                orr, og, ob, _oa = op[x, y]
                _hh, _ss, vv = colorsys.rgb_to_hsv(orr / 255.0, og / 255.0,
                                                   ob / 255.0)
            # A floor under the value, or the device disappears into the darkest
            # corners of the plate it is painted on.
            vv = 0.34 + 0.66 * min(vv, 1.0)
            sat = 0.62 if CREST_TINT else 0.0
            nr, ng, nb = colorsys.hsv_to_rgb(hue, sat, vv)
            k = cov / 255.0
            px[x, y] = (int(round((nr * 255) * k + r * (1 - k))),
                        int(round((ng * 255) * k + g * (1 - k))),
                        int(round((nb * 255) * k + b * (1 - k))),
                        max(a, cov))
            painted += 1
    return base, painted


def _dds_to_png(src, dst_dir):
    """texconv decodes BC3 to a straight RGBA png."""
    os.makedirs(dst_dir, exist_ok=True)
    subprocess.run([TEXCONV, "-nologo", "-y", "-ft", "png", "-f",
                    "R8G8B8A8_UNORM", "-o", dst_dir, src],
                   check=True, capture_output=True)
    return os.path.join(dst_dir, os.path.splitext(os.path.basename(src))[0]
                        + ".PNG")


def _png_to_dds(src, dst_dir):
    """Back to BC3_UNORM with a full mip chain, which is what CA's file is."""
    os.makedirs(dst_dir, exist_ok=True)
    subprocess.run([TEXCONV, "-nologo", "-y", "-ft", "dds", "-f", "BC3_UNORM",
                    "-m", "0", "-o", dst_dir, src],
                   check=True, capture_output=True)
    return os.path.join(dst_dir, os.path.splitext(os.path.basename(src))[0]
                        + ".DDS")


def build(out_root=None, verbose=True):
    """Write the four folders. Returns {in-pack path: bytes written}."""
    from PIL import Image
    src = fetch()
    out_root = out_root or PACK
    written = {}
    tmp = os.path.join(CACHE, "_tmp")
    os.makedirs(tmp, exist_ok=True)
    for _key, folder, slug, crest_src in CREST:
        hue = target_hue(slug)
        here = os.path.join(out_root, flag_dir(folder).replace("/", os.sep))
        os.makedirs(here, exist_ok=True)
        for name, size in FILES:
            im = Image.open(os.path.join(src, name))
            if im.size != size:
                raise RuntimeError("%s is %s, expected %s"
                                   % (name, im.size, size))
            out, moved = restyle(im, crest_src, hue)
            if moved == 0:
                raise RuntimeError("%s: no device was painted, so this crest "
                                   "is CA's unchanged" % name)
            dst = os.path.join(here, name)
            out.save(dst)
            written["%s/%s" % (flag_dir(folder), name)] = moved
            if verbose:
                print("  %-28s %s  %d px painted" % (folder + "/" + name,
                                                        size, moved))
        # THE BATTLE BANNER, THROUGH texconv BOTH WAYS. Pillow will open a BC3
        # dds and will silently write something that is not one.
        png = _dds_to_png(os.path.join(src, DDS), tmp)
        im = Image.open(png)
        out, moved = restyle(im, crest_src, hue)
        if moved == 0:
            raise RuntimeError("%s: no device was painted" % DDS)
        mid = os.path.join(tmp, "%s_%s.png" % (folder, "banner"))
        out.save(mid)
        made = _png_to_dds(mid, tmp)
        data = io.open(made, "rb").read()
        io.open(os.path.join(here, DDS), "wb").write(data)
        written["%s/%s" % (flag_dir(folder), DDS)] = moved
        if verbose:
            print("  %-28s %d bytes  %d px painted"
                  % (folder + "/" + DDS, len(data), moved))
    return written


# ---------------------------------------------------------------------------
# Checks.
# ---------------------------------------------------------------------------
def check():
    """Every way these crests can be wrong and say nothing about it."""
    from PIL import Image
    out = []

    # 1. Four distinct factions, four distinct folders, four distinct hues. Two
    #    identical crests is the bug this whole file is about.
    keys = [c[0] for c in CREST]
    folders = [c[1] for c in CREST]
    if len(set(keys)) != len(keys):
        out.append("a faction is listed twice in CREST")
    if len(set(folders)) != len(folders):
        out.append("a flag folder is listed twice in CREST")
    hues = {}
    try:
        for _key, folder, slug, crest_src in CREST:
            hues[folder] = round(target_hue(slug), 4)
        if len(set(hues.values())) != len(hues):
            out.append("two crests share a hue: %s" % hues)
    except Exception as exc:                               # noqa: BLE001
        out.append("cannot read the party colours: %s" % exc)

    # 2. The pool it covers must be the pool the model actually walks. A fifth
    #    dormant faction added to IC.REBEL_POOL and not here is a rebellion
    #    wearing CA's shared banner again, with nothing to say so.
    try:
        import gen_iron_court as G
        pool = set(G.REBEL_POOL)
        if pool != set(keys):
            out.append("CREST covers %s and IC.REBEL_POOL is %s"
                       % (sorted(keys), sorted(pool)))
    except Exception as exc:                               # noqa: BLE001
        out.append("cannot read REBEL_POOL: %s" % exc)

    # 3. Every file present, at the size CA's is. A missing or wrong-sized one
    #    draws a blank square and logs nothing.
    for _key, folder, _slug, _shape in CREST:
        here = os.path.join(PACK, flag_dir(folder).replace("/", os.sep))
        for name, size in FILES:
            fp = os.path.join(here, name)
            if not os.path.isfile(fp):
                out.append("missing %s/%s" % (flag_dir(folder), name))
                continue
            im = Image.open(fp)
            if im.size != size:
                out.append("%s/%s is %s, expected %s"
                           % (flag_dir(folder), name, im.size, size))
            if im.mode != "RGBA":
                out.append("%s/%s is %s, expected RGBA"
                           % (flag_dir(folder), name, im.mode))
        fp = os.path.join(here, DDS)
        if not os.path.isfile(fp):
            out.append("missing %s/%s" % (flag_dir(folder), DDS))
        else:
            head = io.open(fp, "rb").read(128)
            if head[:4] != b"DDS ":
                out.append("%s/%s is not a dds" % (flag_dir(folder), DDS))
            elif b"DXT5" not in head:
                # BC3_UNORM writes the DXT5 fourcc in the legacy header.
                out.append("%s/%s is not BC3/DXT5" % (flag_dir(folder), DDS))

    # 4. AND THEY MUST BE TELLABLE APART AT TWENTY-FOUR PIXELS, which is the
    #    size the diplomacy list draws and therefore the size the whole
    #    complaint was about. Two hues that are obviously different at 256 can
    #    be one smudge at 24.
    #
    #    THE SATURATED PIXELS ONLY. The bronze frame and the dark plate are
    #    identical across all four and would swamp an average that included
    #    them - every crest would measure the same and this check would pass
    #    for a set that is genuinely four copies of one picture.
    try:
        casts = {}
        for _key, folder, _slug, _shape in CREST:
            fp = os.path.join(PACK, flag_dir(folder).replace("/", os.sep),
                              "mon_24.png")
            if not os.path.isfile(fp):
                continue
            rr = gg = bb = n = 0
            for pr, pg, pb, pa in Image.open(fp).convert("RGBA").getdata():
                if pa < 8:
                    continue
                if colorsys.rgb_to_hsv(pr / 255.0, pg / 255.0,
                                       pb / 255.0)[1] < SIGIL_SAT:
                    continue
                rr += pr
                gg += pg
                bb += pb
                n += 1
            if n:
                casts[folder] = (rr / n, gg / n, bb / n)
        names = sorted(casts)
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                a, b = casts[names[i]], casts[names[j]]
                gap = sum((a[k] - b[k]) ** 2 for k in range(3)) ** 0.5
                if gap < CREST_GAP:
                    out.append("%s and %s are %.1f apart at 24px, under the "
                               "floor of %d - two rebellions on one map would "
                               "read as one banner"
                               % (names[i], names[j], gap, CREST_GAP))
    except Exception as exc:                               # noqa: BLE001
        out.append("cannot measure the crests apart: %s" % exc)

    # 5. And they must actually differ from CA's, which is the one thing a
    #    correct-looking set of six files can silently fail at: a hue band that
    #    selects nothing writes CA's picture back out under a new name.
    try:
        src = fetch()
        base = Image.open(os.path.join(src, "mon_icon.png")).convert("RGBA")
        for _key, folder, _slug, _shape in CREST:
            fp = os.path.join(PACK, flag_dir(folder).replace("/", os.sep),
                              "mon_icon.png")
            if not os.path.isfile(fp):
                continue
            if Image.open(fp).convert("RGBA").tobytes() == base.tobytes():
                out.append("%s/mon_icon.png is CA's picture unchanged"
                           % flag_dir(folder))
    except Exception as exc:                               # noqa: BLE001
        out.append("cannot compare against CA's art: %s" % exc)
    return out


def report():
    """The hue histogram of CA's sigil, so the band is measured not guessed."""
    from PIL import Image
    src = fetch()
    for name, _size in FILES:
        im = Image.open(os.path.join(src, name)).convert("RGBA")
        bands = {}
        for r, g, b, a in im.getdata():
            if a < 8:
                continue
            hh, ss, _vv = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
            if ss < SIGIL_SAT:
                bands["unsaturated"] = bands.get("unsaturated", 0) + 1
            else:
                key = round(hh * 20) / 20.0
                bands[key] = bands.get(key, 0) + 1
        top = sorted(bands.items(), key=lambda kv: -kv[1])[:6]
        print("%-18s %s" % (name, ["%s:%d" % (k, v) for k, v in top]))


def selftest():
    from PIL import Image
    bad = 0

    # THE ERASE MASK IS THE DEVICE AND NOTHING ELSE, in every layout. Checking
    # only mon_256 cannot see this: it has no strays, and the four-pixel speck
    # that grew into a grey block lives on the battle banner. See ERASE_SPECK.
    tmpd = os.path.join(CACHE, "_tmp", "selftest")
    for fname, _sz in FILES + [(DDS, None)]:
        fp = os.path.join(fetch(), fname)
        if fname == DDS:
            fp = _dds_to_png(fp, tmpd)
        m, mbox = sigil_box(Image.open(fp))
        if mbox is None:
            print("SELFTEST: %s has no device to erase" % fname)
            bad += 1
            continue
        parts = _components(m)
        kept = [p for p in parts if p >= ERASE_SPECK * parts[0]]
        if len(kept) > 5:
            print("SELFTEST: %s erase mask keeps %d parts, CA's device is one "
                  "blob and four marks - the extras dilate into grey blocks"
                  % (fname, len(kept)))
            bad += 1
        near = [p for p in parts
                if ERASE_SPECK / 1.5 <= p / float(parts[0]) <= ERASE_SPECK * 1.5]
        if near:
            print("SELFTEST: %s has a part at %.4f of the device, too close to "
                  "ERASE_SPECK (%.4f) to call" % (fname, near[0] / float(parts[0]),
                                                  ERASE_SPECK))
            bad += 1

    # CA'S DEVICE IS GONE AND OURS IS THERE. This is the pair that would have
    # caught the first two builds: erasing only the hue band left the old
    # sigil's pale outline on the banner, under ours.
    src = fetch()
    plate = Image.open(os.path.join(src, "mon_256.png"))
    before, box0 = sigil_box(plate)
    if box0 is None:
        print("SELFTEST: CA's own plate has no device to replace")
        bad += 1
    out, painted = restyle(plate, "rising_02.png", 0.75)
    if painted < 500:
        print("SELFTEST: restyle painted %d pixels, expected a device"
              % painted)
        bad += 1
    # WHAT THE LEFTOVER UNAVOIDABLY IS: bright, in a region that should be
    # plate. Counting saturated green cannot see it - CA's device is outlined in
    # a pale stroke, and its low saturation is the exact reason the hue band
    # misses it, so that count was blind to the one bug it existed for.
    #
    # The region is the sigil box minus our own device; the statistic is its p99
    # luminance. Measured on both builds rather than chosen:
    #     dilated      max 0.365  p99 0.294  mean 0.214
    #     NOT dilated  max 0.933  p99 0.639  mean 0.227
    # The MEAN barely moves, which is why an average would have been decoration
    # too: the leftover is a thin line over a large area.
    # THE REGION IS CA'S OLD DEVICE BOX and the exclusion is OUR PAINT, told
    # apart by saturation: our device is tinted hard and CA's leftover is a
    # pale, near-grey outline. Reconstructing the placement here instead would
    # make this a second owner of geometry restyle already owns, and the two
    # would agree until the day they did not.
    op = out.convert("RGBA").load()
    vals = []
    for y in range(box0[1], box0[3]):
        for x in range(box0[0], box0[2]):
            pr, pg, pb, pa = op[x, y]
            if pa == 0:
                continue
            _hh, ss, vv = colorsys.rgb_to_hsv(pr / 255.0, pg / 255.0,
                                              pb / 255.0)
            if ss >= 0.30:
                continue                      # our own paint
            vals.append(vv)
    vals.sort()
    p99 = vals[int(len(vals) * 0.99)] if vals else 0.0
    if p99 > 0.45:
        print("SELFTEST: CA's own device survived the erase (p99 luminance "
              "%.3f behind ours, clean is ~0.29)" % p99)
        bad += 1
    # AND OURS IS ON IT, asked in OUR hue and not in CA's. sigil_box() searches
    # the green band, so after a successful restyle it finds nothing - that is
    # the erase working, not the paint failing, and asserting it the other way
    # round failed this selftest on its first run.
    mine = 0
    for pr, pg, pb, pa in out.convert("RGBA").getdata():
        if pa == 0:
            continue
        hh, ss, _vv = colorsys.rgb_to_hsv(pr / 255.0, pg / 255.0, pb / 255.0)
        if ss >= SIGIL_SAT and abs(hh - 0.75) < 0.04:
            mine += 1
    if mine < 500:
        print("SELFTEST: only %d pixels carry the device's own hue" % mine)
        bad += 1

    # THE FOUR SUPPLIED DEVICES ARE ACTUALLY DIFFERENT. Two crests given the
    # same source file would still pass check(), which compares finished art and
    # would see them differ by tint alone - four identical banners in four
    # colours, which is most of the bug this whole folder exists to fix.
    shapes = {}
    for _k, _f, _s, src_name in CREST:
        cover, _detail, _ratio, _off = crest_device(src_name)
        if _extent(cover)[2] < 500:
            print("SELFTEST: %s yielded almost no device" % src_name)
            bad += 1
        shapes[src_name] = list(cover.resize((64, 64), Image.LANCZOS).getdata())
    names = sorted(shapes)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = shapes[names[i]], shapes[names[j]]
            diff = sum(1 for k in range(len(a)) if abs(a[k] - b[k]) > 96)
            if diff < 200:
                print("SELFTEST: %s and %s are the same device (%d px apart)"
                      % (names[i], names[j], diff))
                bad += 1

    # check() reports two crests that would read as one banner. The floor is
    # raised past the measured worst pair rather than the art being broken, so
    # this watches the comparison itself rather than a fixture.
    global CREST_GAP
    was = CREST_GAP
    try:
        CREST_GAP = 400
        found = check()
        if not any("apart at 24px" in f for f in found):
            print("SELFTEST: check() said nothing about crests that match")
            bad += 1
    finally:
        CREST_GAP = was

    # check() reports a folder that is not there.
    saved = list(CREST)
    try:
        CREST.append(("wh3_nonexistent_faction", "derpy_ic_rising_99",
                      "road", "anvil"))
        found = check()
        if not any("derpy_ic_rising_99" in f for f in found):
            print("SELFTEST: check() said nothing about a missing folder")
            bad += 1
        if not any("REBEL_POOL" in f for f in found):
            print("SELFTEST: check() said nothing about the pool mismatch")
            bad += 1
    finally:
        del CREST[:]
        CREST.extend(saved)

    print("selftest: %s" % ("FAILED" if bad else "ok"))
    return bad


def main(argv):
    if "--selftest" in argv:
        return 1 if selftest() else 0
    if "--report" in argv:
        report()
        return 0
    if "--write" in argv:
        build()
        problems = check()
        for p in problems:
            sys.stderr.write("PROBLEM: %s\n" % p)
        if problems:
            return 1
        print("ok: %d file(s) across %d crest(s)" % (len(paths()), len(CREST)))
        return 0
    problems = check()
    for p in problems:
        sys.stderr.write("PROBLEM: %s\n" % p)
    if problems:
        return 1
    print("ok: %d file(s) across %d crest(s)" % (len(paths()), len(CREST)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
