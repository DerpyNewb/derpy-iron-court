# -*- coding: utf-8 -*-
"""The Iron Court's release gate: both races, three screens, and the saved pack read back.

WHY IT EXISTS (plan 2026-10-04, Iron Court for Dwarfs phase 6). gen_ic_ui.py --check and
make_ic_backdrop.py --check each prove what they were written for. A release needs the
matrix - Chaos Dwarf and Dwarf, at 1600x900, 1920x1080 and 2560x1440 - and a release that
promised "the Chaos Dwarf court does not change" needs that measured on the pack that
ships, not on the plan that built it.

    py tools/check_ic_release.py            # fit and contrast, both races, three screens
    py tools/check_ic_release.py --pack     # and the saved Modpacks pack: every table read
                                            # back against gen_iron_court.build(), and every
                                            # row and loc line of F4C63911 unchanged
    py tools/check_ic_release.py --selftest

Exit 1 on any finding. An unknown flag is refused.

THE PACK IS READ WITH RPFM SHUT (read_vanilla_db, read_vanilla_loc), so the read-back is
not RPFM's session vouching for its own save.
"""
import copy
import hashlib
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import deploy_iron_court as DEP       # noqa: E402
import gen_iron_court as G            # noqa: E402
import gen_ic_ui as U                 # noqa: E402
import make_ic_backdrop as B          # noqa: E402
import read_pack_index as RPI         # noqa: E402
import read_vanilla_db as RVD         # noqa: E402
import read_vanilla_loc as RVL        # noqa: E402

BOXES = (1600, 1920, 2560)
PACK_DIR = os.path.join(ROOT, "Modding Files", "pack")
LIVE = os.path.join(DEP.GAME_DATA, G.PACK_NAME + ".pack")
# F4C63911, the last build before phase 1 (HANDOFF_20261004_IRON_COURT_DWARFS_DESIGN.md s1).
SNAPSHOT_MD5 = "f4c6391183a7aa76309558640068318b"
SNAPSHOT_SIZE = 10914962


def fit_problems():
    """gen_ic_ui's whole check() - text fit (20k), crossings, the scale rules - once per
    race at each screen, so neither race is passed at a size only by inference."""
    out = []
    for race in sorted(G.RACES):
        for bw in BOXES:
            got = U.at_box(bw, race=race).check()
            print("fit       %s %4d: %d finding(s)" % (race, bw, len(got)))
            out += ["fit %s at %d: %s" % (race, bw, p) for p in got]
    return out


def grounds():
    """{race: [backdrop PNG on disk]}. The Chaos Dwarf one is PANEL_BG; the Dwarf one is
    every OTHER panel-sized picture gen_ic_ui ships - found, not named, so this does not
    depend on what phase 3 called it. Exactly one is the only right answer."""
    from PIL import Image
    found = {"chd": [os.path.join(PACK_DIR, *U.PANEL_BG.split("/"))], "dwf": []}
    for p in sorted(U.art_paths()):
        name = os.path.basename(p)
        if p == U.PANEL_BG or name.startswith("wedge_") or not name.endswith(".png"):
            continue
        full = os.path.join(PACK_DIR, *p.split("/"))
        if os.path.isfile(full):
            with Image.open(full) as im:
                if im.size == (U.PANEL_W, U.PANEL_H):
                    found["dwf"].append(full)
    return found


def contrast_problems(found=None, boxes=BOXES):
    """make_ic_backdrop's per-cell measure (Rec.709, p95, MIN_RATIO) for each race's
    ground at each screen. The picture is scaled to that screen's panel with LANCZOS, as
    make_ic_backdrop's own 1600 leg does; the 2560 leg is new here."""
    from PIL import Image
    found = grounds() if found is None else found
    out = []
    for race in sorted(found):
        if len(found[race]) != 1:
            out.append("contrast %s: %d panel-sized grounds in art_paths(), wanted 1: %s"
                       % (race, len(found[race]), found[race]))
            continue
        img = Image.open(found[race][0]).convert("RGB")
        for bw in boxes:
            m = U.at_box(bw, race=race)
            pic = img if img.size == (m.PANEL_W, m.PANEL_H) else img.resize(
                (m.PANEL_W, m.PANEL_H), Image.LANCZOS)
            rows = B.contrast(pic, m)
            if not rows:
                out.append("contrast %s at %d: no cell measured" % (race, bw))
                continue
            print("contrast  %s %4d: %d cells, worst %s %.2f:1"
                  % (race, bw, len(rows), rows[-1][0], rows[-1][3]))
            out += ["contrast %s at %dx%d: %s reads %.2f:1 (p95 %.0f), under %.1f:1"
                    % (race, m.PANEL_W, m.PANEL_H, n, r, p, B.MIN_RATIO)
                    for n, _mean, p, r in rows if r < B.MIN_RATIO]
    return out


def pack_tables(pack):
    """{table: (version, rows, {field: type})} and {"loc": {key: text}} out of a saved pack."""
    out = {}
    for path in RPI.paths(pack):
        parts = path.split("/")
        if len(parts) == 3 and parts[0] == "db" and parts[2] == G.PACK_NAME:
            (_p, ver, rows), = RVD.load(pack, parts[1])
            out[parts[1]] = (ver, rows, dict(RVD.defs(parts[1])[ver]))
    (_p, _c, data), = RPI.read(pack, "text/db/%s.loc" % G.PACK_NAME)
    out["loc"] = RVL.parse(data)
    return out


def find_snapshot():
    """F4C63911 wherever a deploy backed it up under Modding Files/Backup, by MD5."""
    for top, _dirs, files in os.walk(os.path.join(ROOT, "Modding Files", "Backup")):
        for n in files:
            p = os.path.join(top, n)
            if n.startswith(G.PACK_NAME + ".pack") and os.path.getsize(p) == SNAPSHOT_SIZE:
                if hashlib.md5(open(p, "rb").read()).hexdigest() == SNAPSHOT_MD5:
                    return p
    return None


def chd_unchanged(old, new):
    """Every row and loc line of the snapshot is in the new pack, unchanged. New rows are
    allowed - they are the Dwarf ones; nothing the Chaos Dwarf court shipped may move."""
    out = []
    for t in sorted(k for k in old if k != "loc"):
        ver, rows = old[t][0], old[t][1]
        if t not in new:
            out.append("%s: the whole table is gone" % t)
            continue
        if new[t][0] != ver:
            out.append("%s: version %d became %d" % (t, ver, new[t][0]))
            continue
        have = set(tuple(r.items()) for r in new[t][1])
        lost = [r for r in rows if tuple(r.items()) not in have]
        out += ["%s: changed or gone: %s" % (t, list(r.values())[:3]) for r in lost[:5]]
        if len(lost) > 5:
            out.append("%s: and %d more" % (t, len(lost) - 5))
    moved = [k for k in sorted(old["loc"]) if new["loc"].get(k) != old["loc"][k]]
    out += ["loc %s: %r became %r" % (k, old["loc"][k], new["loc"].get(k)) for k in moved[:20]]
    if len(moved) > 20:
        out.append("loc: and %d more" % (len(moved) - 20))
    return out


def _same(packed, text, ftype):
    if ftype == "ColourRGB":
        return packed == int(text, 16)
    if isinstance(packed, bool):
        return text.lower() == ("true" if packed else "false")
    if isinstance(packed, float):
        return abs(packed - float(text or 0)) < 1e-4
    if isinstance(packed, int):
        return packed == int(float(text or 0))
    return packed == text


def matches_generator(new, built=None, meta=None):
    """The saved pack holds what gen_iron_court.build() writes: the same tables, the same
    row counts, every cell equal, the loc whole. RPFM's derived *_colour_hex columns are
    not in the binary; they are printed, not compared, and no table is exempt."""
    built = G.build() if built is None else built
    meta = G.TSV_META if meta is None else meta
    out, skipped = [], set()
    for t, rows in sorted(built.items()):
        if t == "loc":
            want = dict((r["key"], r["text"]) for r in rows)
            if len(rows) != len(new["loc"]) or want != new["loc"]:
                out.append("loc: %d lines saved, the generator writes %d, %d differ"
                           % (len(new["loc"]), len(rows),
                              sum(1 for k in want if new["loc"].get(k) != want[k])))
            continue
        name = meta[t][0]
        if not rows and name not in new:
            continue
        if name not in new:
            out.append("%s: not in the saved pack" % name)
            continue
        _ver, got, types = new[name]
        if len(got) != len(rows):
            out.append("%s: %d rows saved, the generator writes %d" % (name, len(got), len(rows)))
            continue
        for i, (g, b) in enumerate(zip(got, rows)):
            skipped.update(c for c in b if c not in g)
            bad = [c for c in b if c in g and not _same(g[c], b[c], types.get(c))]
            if bad:
                out.append("%s row %d differs in %s" % (name, i + 1, ", ".join(bad)))
                break
    names = set(meta[t][0] for t in built if t != "loc")
    out += ["%s: in the saved pack, not in the generator" % t
            for t in sorted(set(new) - names - {"loc"})]
    if skipped:
        print("not stored in the binary, not compared: %s" % ", ".join(sorted(skipped)))
    return out


def selftest():
    import tempfile
    from PIL import Image
    assert sorted(G.RACES) == ["chd", "dwf"], sorted(G.RACES)
    # 1. EVERY TABLE THE PACK SHIPS DECODES - on the copy in data/, so a field type the
    #    decoder does not know fails here and not half way through a release.
    t = pack_tables(LIVE)
    assert len(t) >= 14 and t["loc"] and all(t[k][1] for k in t if k != "loc"), sorted(t)
    # 2. THE SNAPSHOT DIFF CAN SAY NO, and does not object to a row being added.
    name = sorted(k for k in t if k != "loc")[0]
    ver, rows, types = t[name]
    first = dict(rows[0])
    k0 = next(k for k, v in first.items() if isinstance(v, str))
    first[k0] += "_x"
    assert chd_unchanged(t, t) == []
    grown = copy.deepcopy(t)
    grown[name] = (ver, rows + [first], types)
    assert chd_unchanged(t, grown) == [], "an added row was reported"
    moved = copy.deepcopy(t)
    moved[name] = (ver, rows[1:] + [first], types)
    assert chd_unchanged(t, moved), "a changed row was not reported"
    lost = copy.deepcopy(t)
    lost["loc"].pop(sorted(lost["loc"])[0])
    assert chd_unchanged(t, lost), "a lost loc line was not reported"
    # 3. THE GENERATOR COMPARE CAN SAY NO.
    meta = {"x": ("x_tables", 0)}
    built = {"x": [{"key": "a", "n": "2", "c": "555555", "c_hex": "555555"}],
             "loc": [{"key": "k", "text": "v", "tooltip": "false"}]}
    ok = {"x_tables": (0, [{"key": "a", "n": 2, "c": 5592405}], {"c": "ColourRGB"}),
          "loc": {"k": "v"}}
    assert matches_generator(ok, built, meta) == []
    wrong = copy.deepcopy(ok)
    wrong["x_tables"][1][0]["n"] = 3
    assert matches_generator(wrong, built, meta), "a changed cell was not reported"
    short = copy.deepcopy(ok)
    short["x_tables"] = (0, [], {})
    assert matches_generator(short, built, meta), "a short table was not reported"
    extra = copy.deepcopy(ok)
    extra["y_tables"] = (0, [{}], {})
    assert matches_generator(extra, built, meta), "a table nobody generates was not reported"
    # 4. THE CONTRAST LEG CAN SAY NO: a white ground fails, a race with no ground fails.
    with tempfile.TemporaryDirectory() as tmp:
        white = os.path.join(tmp, "white.png")
        Image.new("RGB", (U.PANEL_W, U.PANEL_H), (255, 255, 255)).save(white)
        assert contrast_problems({"chd": [white]}, boxes=(1920,)), "a white ground passed"
    assert contrast_problems({"dwf": []}, boxes=(1920,)), "a race with no ground passed"
    print("selftest ok: %d tables decode; the snapshot diff, the generator compare and "
          "the contrast leg each report a planted fault" % (len(t) - 1))


def main(argv):
    unknown = set(argv) - {"--pack", "--selftest"}
    if unknown:
        sys.stderr.write("REFUSING: unknown argument(s) %s\n" % " ".join(sorted(unknown)))
        return 2
    if "--selftest" in argv:
        selftest()
        return 0
    problems = fit_problems() + contrast_problems()
    if "--pack" in argv:
        new = pack_tables(DEP.OUT)
        problems += matches_generator(new)
        snap = find_snapshot()
        if snap:
            print("snapshot  %s" % snap)
            problems += chd_unchanged(pack_tables(snap), new)
        else:
            problems.append("no F4C63911 snapshot (MD5 %s) under Modding Files/Backup"
                            % SNAPSHOT_MD5)
    for p in problems:
        sys.stderr.write("FAIL %s\n" % p)
    print("%d finding(s)" % len(problems))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
