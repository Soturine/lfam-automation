# -*- coding: utf-8 -*-
# Probe: opens a COPY of the project, creates an LD POU, exports PLCopen XML to inspect the format.
import os
base = os.environ.get("LFAM_WORK")
log = open(os.path.join(base, "probe.log"), "w")
try:
    proj = projects.open(os.path.join(base, "LFAM_copy.project"))
    app = proj.active_application
    log.write("app=%s\n" % app)
    pou = app.create_pou("POC_LD", PouType.Program, "LD") if False else None
except Exception as e:
    log.write("ERR %r\n" % (e,))
log.close()
