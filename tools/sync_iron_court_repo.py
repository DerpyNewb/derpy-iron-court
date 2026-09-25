"""Mirror The Iron Court's files into repos/derpy-iron-court, the public GitHub repo.

The workspace is the source of truth; the repo is a copy with the same layout, so every
tool's relative paths ("Modding Files/pack/...", "tools/...") work from either root.
README.md, CHANGELOG.md, docs/DEVELOPMENT.md, LICENSE, .gitignore and .gitattributes are
written in the repo itself and never touched here. The copying is sync_guilds_repo's.

    py tools/sync_iron_court_repo.py            # copy every changed file into the repo
    py tools/sync_iron_court_repo.py --check    # list drift, copy nothing; exit 1 on drift
    py tools/sync_iron_court_repo.py --selftest

Then commit and push from inside the repo folder.

NOTHING OF CA'S OR GW'S IS PUBLISHED (the author's rule for every public repo from this
workspace). No images - the backdrop, plates and rebel flags are all derived from CA art -
and no DB rows copied out of CA's db.pack. `refused()` checks the manifest for both before
anything is copied, and the sync will not run while it reports anything.
"""
import os
import sys

import sync_guilds_repo as SG

ROOT = SG.ROOT
REPO = os.path.join(ROOT, "repos", "derpy-iron-court")

_MOD = SG._MOD
_UI = SG._UI
_SRC = "Modding Files/source/iron_court/"

# CA'S OWN ROWS. The four dormant Chaos Dwarf rebel factions, exported verbatim out of
# db.pack (_donor_) and re-emitted with one column changed (factions.tsv). Game data, so
# they ship in the pack only - the same line the Guilds repo draws at CA's art.
CA_ROWS = ("_donor_factions.tsv", "factions.tsv")

# Anything that is art, a built pack, or a binary game format never goes public.
REFUSED_EXT = (".png", ".dds", ".jpg", ".jpeg", ".webp", ".tga", ".pack", ".bin",
               ".loc", ".anim", ".rigid_model_v2", ".wem")


def _tsvs(root=ROOT):
    """Every generated TSV but CA's rows, read off the folder so a new table is not missed."""
    d = os.path.join(root, _SRC)
    if not os.path.isdir(d):
        return []
    return [_SRC + n for n in sorted(os.listdir(d))
            if n.endswith(".tsv") and n not in CA_ROWS]


_DOCS = [
    ("docs/superpowers/specs/2026-09-11-iron-court-design.md", "docs/design/"),
    ("docs/superpowers/specs/2026-09-20-iron-court-ambition-design.md", "docs/design/"),
    ("docs/superpowers/specs/2026-09-20-iron-court-edict-loyalty-design.md", "docs/design/"),
    ("docs/superpowers/specs/2026-09-23-iron-court-rival-party-ai-design.md", "docs/design/"),
    ("docs/superpowers/specs/2026-09-24-iron-court-ui-scale-design.md", "docs/design/"),
    ("docs/IRON_COURT_VS_ROME2.md", "docs/design/"),
    ("docs/superpowers/plans/2026-09-20-iron-court-ambition.md", "docs/plans/"),
    ("docs/superpowers/plans/2026-09-20-iron-court-edict-loyalty.md", "docs/plans/"),
    ("docs/superpowers/plans/2026-09-23-iron-court-rival-party-ai-build1.md", "docs/plans/"),
    ("docs/superpowers/plans/2026-09-23-iron-court-rival-party-ai-build2.md", "docs/plans/"),
    ("docs/superpowers/plans/2026-09-24-iron-court-ui-scale.md", "docs/plans/"),
] + [("docs/sessions/" + n, "docs/history/") for n in [
    "HANDOFF_20260911_IRON_COURT_DESIGN.md",
    "HANDOFF_20260914_IRON_COURT_SAVE_BUG_AND_FONT_PASS.md",
    "HANDOFF_20260916_IRON_COURT_SIX_LIVE_BUGS.md",
    "HANDOFF_20260917_IRON_COURT_SECESSION_CRASH.md",
    "HANDOFF_20260918_IRON_COURT_WARNINGS_AND_AUDIT.md",
    "HANDOFF_20260921_IRON_COURT_HUMANIZE_PARTIAL.md",
    "HANDOFF_20260921_PANEL_LISTENER_CHAIN_BREAK.md",
    "HANDOFF_20260922_IRON_COURT_GOVERNOR_BAR_AND_AI_LOYALTY.md",
    "HANDOFF_20260922_LISTENER_CHAIN_FIX_AND_DIRECTOR_REBELLIONS.md",
    "HANDOFF_20260923_IRON_COURT_AI_LIVE_CHECK.md",
    "HANDOFF_20260924_IRON_COURT_PARTY_BAR.md",
    "HANDOFF_20260924_IRON_COURT_UI_SCALE.md",
]]


def manifest(root=ROOT):
    """(workspace path, repo path) for every published file."""
    same = [
        _MOD + "zzz_derpy_iron_court.lua",
        _MOD + "zzz_derpy_iron_court_parties.lua",
        _MOD + "zzz_derpy_iron_court_ui.lua",
    ] + [_UI + "derpy_ic_%s%s.twui.xml" % (n, c)
         for n in ("panel", "card", "row", "party", "plot") for c in ("", "_compact")] + [
        _UI + "derpy_ic_opener.twui.xml",
        _UI + "derpy_ic_standing.twui.xml",
    ] + _tsvs(root) + ["tools/" + n for n in (
        "_iron_court_harness.lua",
        "gen_iron_court.py",
        "gen_iron_court_emitter.py",
        "gen_ic_ui.py",
        "import_iron_court.py",
        "deploy_iron_court.py",
        "preview_iron_court.py",
        "mutate_iron_court.py",
        "make_ic_backdrop.py",
        "make_ic_rebel_flags.py",
        "probe_ic_string_break.lua",
        "probe_ic_draw_actions_steps.lua",
        "probe_ic_live_state.lua",
        "sync_iron_court_repo.py",
        # SHARED HELPERS the above import. sync_guilds_repo is this file's own copier.
        "sync_guilds_repo.py",
        "preview_guilds_panel.py",
        "read_pack_index.py",
        "read_vanilla_cache.py",
        "read_vanilla_loc.py",
        "import_house_ancillaries.py",
        "check_lua_undeclared.py",
        "check_lua_literal_left.py",
        "check_lua_api.py",
        # THE VANILLA-TABLE CACHE the checks read is CA's data and is not published, so
        # the fetcher that builds it from your own install is (check_skill_trees holds
        # its RPFM calls; importing it runs nothing).
        "fetch_vanilla_tables.py",
        "check_skill_trees.py",
    )]
    return [(p, p) for p in same] + [(src, dst + os.path.basename(src)) for src, dst in _DOCS]


def refused(entries):
    """Why each entry may not be published: CA's rows, art, packs and binaries."""
    out = []
    for src, dst in entries:
        for p in (src, dst):
            name = os.path.basename(p)
            if name in CA_ROWS:
                out.append("%s is CA's own DB rows" % p)
            elif os.path.splitext(name)[1].lower() in REFUSED_EXT:
                out.append("%s is art or a binary game file" % p)
    return out


def _selftest():
    m = manifest()
    assert refused(m) == [], refused(m)
    # The guard has to be able to say no, or a clean report means nothing.
    assert refused(m + [(_SRC + "_donor_factions.tsv",) * 2]), "CA's rows were not refused"
    assert refused(m + [("Modding Files/pack/ui/derpy_ic/bg.png",) * 2]), "art was not refused"
    assert refused([("a.md", "docs/x.PACK")]), "a pack under an upper-case name slipped by"
    # CA's rows are really in the workspace folder, so leaving them out is the filter's doing.
    here = set(os.listdir(os.path.join(ROOT, _SRC)))
    assert set(CA_ROWS) <= here, "the CA rows moved; re-check what the folder holds"
    assert not any(os.path.basename(s) in CA_ROWS for s, _d in m)
    missing = [s for s, _d in m if not os.path.isfile(os.path.join(ROOT, s))]
    assert not missing, "manifest names files the workspace does not have: %r" % missing
    dsts = [d for _s, d in m]
    assert len(dsts) == len(set(dsts)), "two sources map to one repo path"
    print("selftest ok: %d files, nothing of CA's" % len(m))


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        _selftest()
        sys.exit(0)
    flags = [a for a in sys.argv[1:] if a.startswith("-") and a != "--check"]
    if flags:
        sys.exit("unknown flag %r; usage: sync_iron_court_repo.py [--check | --selftest]"
                 % flags[0])
    m = manifest()
    bad = refused(m)
    if bad:
        sys.exit("REFUSING: " + "; ".join(bad))
    if "--check" in sys.argv:
        found = SG.drift(ROOT, REPO, m)
        for s, _d, why in found:
            print("%-22s %s" % (why, os.path.relpath(s, ROOT)))
        print("%d file(s) drift" % len(found))
        sys.exit(1 if found else 0)
    found = SG.sync(ROOT, REPO, m)
    for s, _d, why in found:
        print("%-22s %s" % (why, os.path.relpath(s, ROOT)))
    print("synced %d file(s) into %s" % (len(found), REPO))
