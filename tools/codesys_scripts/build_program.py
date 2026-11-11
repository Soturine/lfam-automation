# -*- coding: utf-8 -*-
# Headless, on a COPY: import the generated LD program as PLC_PRG, add the Util library, set MainTask to cyclic 100 ms, build,
# and save under a new name. The ORIGINAL project is never opened here.
# Env: LFAM_WORK (dir), LFAM_SRC (source project file name in LFAM_WORK), LFAM_XML (PLCopen xml path),
#      LFAM_OUT (output project file name), LFAM_LOG (log file name).
import os, traceback
base = os.environ["LFAM_WORK"]
xml = os.environ["LFAM_XML"]
src = os.environ.get("LFAM_SRC", "LFAM_copy.project")
out_name = os.environ.get("LFAM_OUT", "LFAM_NET.project")
log = open(os.path.join(base, os.environ.get("LFAM_LOG", "build_program.log")), "w")


def w(s):
    log.write(repr(s) + "\n")
    log.flush()


try:
    proj = projects.open(os.path.join(base, src))
    app = proj.active_application
    for o in list(app.get_children()):
        if o.get_name().startswith("PLC_PRG") and o.parent == app:
            o.remove()
    libman = [o for o in app.get_children() if o.get_name() == "Library Manager"][0]
    have = [str(l) for l in libman.get_libraries()] if hasattr(libman, "get_libraries") else []
    w("libs before: %r" % have)
    if not any("Util" == h.split(",")[0].strip() or h.startswith("Util") for h in have):
        cands = [m for m in librarymanager.get_all_libraries() if str(m.displayname).startswith("Util") and "Utility" not in str(m.displayname)]
        w("Util candidates: %r" % [str(m.displayname) for m in cands])
        lib = cands[0] if cands else None
        w("find_library: %r" % (lib,))
        libman.add_library(lib if lib is not None else "Util")
    w("libs after: %r" % [str(l) for l in libman.get_libraries()])
    app.import_xml(xml, ConflictResolve.Replace)
    for o in app.get_children(True):
        if o.get_name() == "MainTask":
            o.interval = "100"
            o.interval_unit = "ms"
            w("MainTask interval=%s %s" % (o.interval, o.interval_unit))
    app.build()
    try:
        for cat in system.get_message_categories(True):
            for m in system.get_message_objects(cat):
                if "Error" in str(m.severity):
                    w("ERRMSG %r" % (m.text,))
                    for a in dir(m):
                        if a.startswith("_") or a in ("text", "severity"):
                            continue
                        try:
                            w("   %s=%r" % (a, getattr(m, a)))
                        except Exception:
                            pass
                    raise StopIteration
    except StopIteration:
        pass
    proj.save_as(os.path.join(base, out_name))
    w("saved " + out_name)
    proj.close()
except Exception:
    w("ERR " + traceback.format_exc())
log.close()
