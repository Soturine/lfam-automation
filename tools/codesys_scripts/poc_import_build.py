# -*- coding: utf-8 -*-
# POC on a COPY: replace PLC_PRG by a real LD network via PLCopen XML import, then build.
import os, traceback
base = os.environ["LFAM_WORK"]; xml = os.environ["LFAM_XML"]
log = open(os.path.join(base, "poc.log"), "w")
try:
    proj = projects.open(os.path.join(base, "LFAM_copy.project"))
    app = proj.active_application
    app.import_xml(xml, ConflictResolve.Replace)
    log.write("imported\n")
    app.build()
    for m in system.get_message_objects():
        log.write("MSG %s | %s\n" % (m.severity, m.text))
    proj.save(); log.write("saved\n"); proj.close()
except Exception:
    log.write("ERR %s\n" % traceback.format_exc())
log.close()
