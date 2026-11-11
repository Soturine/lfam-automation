# -*- coding: utf-8 -*-
# Read-only probe on a COPY: export every POU named PLC_PRG* of a project to PLCopen XML (round-trip check).
# Env: LFAM_WORK (dir), LFAM_PROJECT (file name in LFAM_WORK), LFAM_EXPORT (output file name).
import os, traceback
base = os.environ["LFAM_WORK"]
log = open(os.path.join(base, "probe.log"), "w")
try:
    proj = projects.open(os.path.join(base, os.environ.get("LFAM_PROJECT", "LFAM_copy.project")))
    app = proj.active_application
    prg = [o for o in app.get_children() if o.get_name().startswith("PLC_PRG") and o.parent == app]
    log.write("pous=%r\n" % [o.get_name() for o in prg])
    proj.export_xml(tuple(prg), path=os.path.join(base, os.environ.get("LFAM_EXPORT", "export.xml")))
    log.write("exported\n")
    proj.close()
except Exception:
    log.write("ERR %s\n" % traceback.format_exc())
log.close()
