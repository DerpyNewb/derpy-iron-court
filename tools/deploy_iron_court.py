"""Builds derpy_iron_court.pack and deploys it to the game's data folder.

    py tools/deploy_iron_court.py                 # build, verify, deploy
    py tools/deploy_iron_court.py --no-copy       # build into Modpacks only
    py tools/deploy_iron_court.py --wait          # build; if the game is up, wait
                                                  # for it to close, then deploy
    py tools/deploy_iron_court.py --deploy-only [--wait]   # ship the last build
    py tools/deploy_iron_court.py --selftest

THE AUTHOR'S RULE (2026-09-28): "always deploy it to data if the game is not
running", then "automate if the game is not running then deploy it" - a build
made while the game was up sat in Modpacks and the author played the old one.
--wait is that automation: run it in the background and it deploys the moment
Warhammer3 exits. Every deploy backs the live pack up first and byte-compares
the copy.

AN UNKNOWN FLAG IS REFUSED. It used to be ignored, and on 2026-09-28 a
--selftest passed to a copy of this file that had none built and deployed the
pack twice.

Needs RPFM OPEN - the MCP server only exists while it is. The registered MCP tools
are often absent (the server starts after Claude Code); import_house_ancillaries.call
talks raw HTTP to the same server either way.

CREATE, IMPORT AND SAVE MUST BE ONE RUN: pack state lives only as long as one MCP
session, so there is no resuming this half way through.
"""
import io
import json
import os
import shutil
import subprocess
import sys

sys.path.insert(0, "tools")
import gen_iron_court as G                  # noqa: E402
import import_iron_court as V               # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "Modding Files", "source", "iron_court")
OUT = os.path.join(ROOT, "Modding Files", "Modpacks", "%s.pack" % G.PACK_NAME)
GAME_DATA = r"F:\SteamLibrary\steamapps\common\Total War WARHAMMER III\data"

# (table name with its _tables suffix, schema version). Versions come from the
# generator so the TSV metadata line and the created file cannot disagree.
#
# DERIVED FROM THE GENERATOR, NEVER TYPED. This was a hand-written list of five
# until 2026-09-17, and the generator had been emitting nine for a month: the
# whole event-feed chain - the groups, their members, the criteria value the
# script passes as an index, and the message-event rows themselves - was written
# to Modding Files/source/iron_court/ on every run and packed by nothing.
#
# WHY IT COST SO MUCH TO FIND. An index with no event_feed_message_events row
# behind it draws NOTHING, and the engine logs show_message_event and whitelists
# the event type exactly as it does for one that works. So the log said the card
# had been raised, every time, and no card ever appeared. Two separate player
# reports - "no event when officers are removed from office" and "no event
# showing when doing the intrigue" - were this, and both were chased into the Lua.
#
# A SECOND LIST IS HOW IT HAPPENED, so there is no longer a second list. A table
# the generator writes is a table this ships, and adding one needs no edit here.
TABLES = [(G.TSV_META[t][0], G.TSV_META[t][1], t)
          for t in sorted(G.TSV_META) if t != "loc"]

SCRIPTS = [
    ("Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court.lua",
     "script/campaign/mod/zzz_derpy_iron_court.lua"),
    ("Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_ui.lua",
     "script/campaign/mod/zzz_derpy_iron_court_ui.lua"),
    ("Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_ui_map.lua",
     "script/campaign/mod/zzz_derpy_iron_court_ui_map.lua"),
    ("Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_parties.lua",
     "script/campaign/mod/zzz_derpy_iron_court_parties.lua"),
    # MCT loads every .lua under script/mct/settings/. Listed here, it is also in
    # the post-save check below, which asks the saved pack for every SCRIPTS path.
    ("Modding Files/pack/script/mct/settings/derpy_iron_court.lua",
     "script/mct/settings/derpy_iron_court.lua"),
]
UI = [("Modding Files/pack/ui/campaign ui/%s" % os.path.basename(p),
       "ui/campaign ui/%s" % os.path.basename(p)) for p in V.UI_FILES]

# THE DERPY HUD HUB's two files for this pack, from the sync tool's own list. Same
# (workspace-relative source, in-pack path) shape as SCRIPTS.
import sync_derpy_hub as _HUB              # noqa: E402
HUB = _HUB.pack_files("ic")

# EVERY PNG THE GENERATOR OWNS, off its own list rather than a folder listing: a
# stray PNG in that folder must not ship, and a house whose plate was never
# written must not be quietly skipped.
#
# art_paths(), NOT build_plates(). build_plates is the plates - the rim, the
# walls, the sigils, the frames - and the 1,560 wedge pictures are not in it,
# because they are generated per party and listed separately. Deploying
# build_plates shipped a pack with a rim, walls and crests and no pie inside
# them: 96 pictures where the pack built by hand had 1,656, and nothing said so
# because every file it did name was present. art_paths() is the union and
# rasterises nothing to answer.
import gen_ic_ui as U                        # noqa: E402
import make_ic_rebel_flags as F              # noqa: E402

# AND THE FOUR REBEL CRESTS, which are NOT under ui/derpy_ic and so are not in
# art_paths(). They live at ui/flags/derpy_ic_rising_0N because that is where a
# faction's flags_path points and the column holds a folder, not a file. Left
# out of this list the factions_tables override would point at nothing and every
# rebellion would draw a blank square, with nothing in the log to say so.
ART = ([("Modding Files/pack/" + p, p) for p in sorted(U.art_paths())]
       + [("Modding Files/pack/" + p, p) for p in F.paths()])


def game_running():
    return bool(subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "if (Get-Process -Name Warhammer3 -ErrorAction SilentlyContinue)"
         " { exit 1 } else { exit 0 }"]).returncode)


def deploy(src, data_dir, wait=False, running=game_running, sleep=None,
           poll=15):
    """Back up the live pack, copy src over it, byte-compare. 0 on success.

    THE GAME HOLDS AN OPEN HANDLE ON EVERY PACK IT LOADED, so a copy under a
    running game fails with WinError 32 - or, where it did not, would swap a pack
    under a live session. Without wait that is a refusal; with it, a wait.
    """
    import time
    sleep = sleep or time.sleep
    if not os.path.isdir(data_dir):
        sys.stderr.write("game data folder not found: %s\n" % data_dir)
        return 1
    if running():
        if not wait:
            sys.stderr.write("REFUSING to deploy: Warhammer3 is running. The pack "
                             "is built at %s - close the game and re-run, or "
                             "pass --wait.\n" % src)
            return 1
        print("Warhammer3 is running; deploying when it closes")
        sys.stdout.flush()
        while running():
            sleep(poll)
        sleep(poll)     # its file handles go a moment after the process does
    dest = os.path.join(data_dir, os.path.basename(src))
    new = open(src, "rb").read()
    if os.path.exists(dest):
        if open(dest, "rb").read() == new:
            print("already deployed: %s" % dest)
            return 0
        bak = "%s.bak_pre_auto_%s" % (dest, time.strftime("%Y%m%d_%H%M%S"))
        shutil.copy2(dest, bak)
        print("backed up the live pack to %s" % bak)
    shutil.copy2(src, dest)
    if open(dest, "rb").read() != new:
        sys.stderr.write("the deployed copy differs from %s\n" % src)
        return 1
    print("deployed %s (%d bytes), byte-identical to the build"
          % (dest, len(new)))
    return 0


def _selftest():
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, "p.pack")
        data = os.path.join(tmp, "data")
        os.mkdir(data)
        open(src, "wb").write(b"new")
        live = os.path.join(data, "p.pack")
        open(live, "wb").write(b"old")
        # Running, no wait: refused, live copy untouched.
        assert deploy(src, data, running=lambda: True) == 1
        assert open(live, "rb").read() == b"old"
        # Running twice then closed, with wait: waits, backs up, deploys.
        states = [True, True, True, False]
        slept = []
        assert deploy(src, data, wait=True, running=lambda: states.pop(0),
                      sleep=slept.append) == 0
        assert len(slept) == 3, slept
        assert open(live, "rb").read() == b"new"
        baks = [f for f in os.listdir(data) if ".bak_pre_auto_" in f]
        assert len(baks) == 1
        assert open(os.path.join(data, baks[0]), "rb").read() == b"old"
        # Same bytes again: nothing copied, no second backup.
        assert deploy(src, data, running=lambda: False) == 0
        assert len([f for f in os.listdir(data) if ".bak_pre_auto_" in f]) == 1
    assert main(["--no-such-flag"]) == 2
    print("selftest: ok")
    return 0


FLAGS = {"--no-copy", "--wait", "--deploy-only", "--selftest"}


def main(argv):
    unknown = [a for a in argv if a not in FLAGS]
    if unknown:
        sys.stderr.write("REFUSING: unknown argument(s) %s; known: %s\n"
                         % (" ".join(unknown), " ".join(sorted(FLAGS))))
        return 2
    if "--selftest" in argv:
        return _selftest()
    if "--deploy-only" in argv:
        return deploy(OUT, GAME_DATA, wait="--wait" in argv)
    # 1. Every offline gate first. Nothing is created until they all pass.
    problems = V.verify()
    for problem in problems:
        sys.stderr.write("REFUSING: %s\n" % problem)
    if problems:
        return 1
    print("gates green")

    from import_house_ancillaries import call, check_keys

    # A schema binding is per MCP SESSION even though the game key is global, so
    # this is not optional. rebuild_dependencies=False skips the 105MB rebuild.
    call("set_game_selected", {"game_name": "warhammer_3", "rebuild_dependencies": False})

    plan = []
    for table_name, version, stem in TABLES:
        plan.append(("db/%s/%s" % (table_name, G.PACK_NAME),
                     {"DB": [G.PACK_NAME, table_name, version]},
                     os.path.join(SRC, stem + ".tsv")))
    plan.append(("text/db/%s.loc" % G.PACK_NAME,
                 {"Loc": G.PACK_NAME},
                 os.path.join(SRC, "loc.tsv")))

    # Duplicated combined keys, before anything is written. The game says nothing
    # at all about a duplicate - the second row is simply not there - and only
    # RPFM's own check ever catches it, on the next manual open.
    check_keys([(path, spec, os.path.basename(tsv), os.path.dirname(tsv))
                for path, spec, tsv in plan])

    for _path, _spec, tsv in plan:
        if not os.path.isfile(tsv):
            sys.stderr.write("REFUSING: missing %s\n" % tsv)
            return 1

    key = call("new_pack", {})["String"]

    for path, spec, tsv in plan:
        # import_tsv CANNOT create a table: the file must already exist, and
        # new_packed_file's `path` is the full file path, not the folder.
        call("new_packed_file", {"pack_key": key, "path": path,
                                 "new_file": json.dumps(spec)})
        call("import_tsv", {"pack_key": key, "table_path": path, "tsv_path": tsv})
        print("  %s" % path)

    for src, dest in SCRIPTS + UI + ART + HUB:
        full = os.path.join(ROOT, *src.split("/"))
        if not os.path.isfile(full):
            sys.stderr.write("REFUSING: missing %s\n" % full)
            return 1
        call("add_packed_files", {"pack_key": key, "source_paths": [full],
                                  "destination_paths": json.dumps([{"File": dest}])})
        print("  %s" % dest)

    outdir = os.path.dirname(OUT)
    if not os.path.isdir(outdir):
        os.makedirs(outdir)
    call("save_pack_as", {"pack_key": key, "path": OUT})
    print("saved %s (%d bytes)" % (OUT, os.path.getsize(OUT)))

    # WHAT WAS SAVED, READ BACK. Every art path above was added one call at a
    # time and each said it succeeded, which is exactly what a pack missing
    # 1,560 pictures also said - the list was short, not the adding. So the
    # saved file is opened offline and asked for the generator's whole list.
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import read_pack_index as RPI            # noqa: E402
    saved = set(RPI.paths(OUT))
    # THE DB AND THE LOC ARE IN THIS COUNT NOW. It asked only about the files
    # added by hand, so a table missing from the list above was a table nobody
    # ever asked the saved pack about.
    #
    # ASKED OF THE GENERATOR, NOT OF THE PLAN. The first version of this read the
    # plan, which is built from the same list it was meant to police - drop a
    # table and the check simply stopped asking about it, and it passed. Every
    # name here comes from G.TSV_META, which is the generator's own account of
    # what it writes, so nothing this deploy script does can quiet it.
    want = [p for _src, p in SCRIPTS + UI + ART + HUB]
    want += ["db/%s/%s" % (G.TSV_META[t][0], G.PACK_NAME)
             for t in G.TSV_META if t != "loc"]
    want += ["text/db/%s.loc" % G.PACK_NAME]
    short = sorted(p for p in want if p not in saved)
    if short:
        sys.stderr.write("REFUSING: %d file(s) did not reach the pack, "
                         "first is %s\n" % (len(short), short[0]))
        return 1
    print("verified %d file(s) in the saved pack" % len(saved))

    if "--no-copy" in argv:
        return 0
    rc = deploy(OUT, GAME_DATA, wait="--wait" in argv)
    if rc:
        return rc
    # A pack is NOT byte-reproducible - every DB table carries a per-save GUID -
    # so two BUILDS never match by md5; deploy() compares the copy to its build.
    print("NOTE: a new pack in data/ is listed but UNTICKED. Enable it in the "
          "launcher or mod manager before it does anything.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
