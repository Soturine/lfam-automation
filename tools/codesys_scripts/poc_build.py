# -*- coding: utf-8 -*-
# Headless, on a COPY: import LD POU as PLC_PRG via PLCopen XML, build, save as work/LFAM_POC.project.
import os, traceback
base = os.environ["LFAM_WORK"]; xml = os.environ["LFAM_XML"]
log = open(os.path.join(base, "poc_build.log"), "w")
def w(s): log.write(repr(s) + "\n"); log.flush()
try:
    proj = projects.open(os.path.join(base, "LFAM_copy.project"))
    app = proj.active_application
    for o in list(app.get_children()):
        if o.get_name().startswith("PLC_PRG") and o.parent == app:
            o.remove()
    app.import_xml(xml, ConflictResolve.Replace)
    app.build()
    n = 0
    for m in system.get_message_objects():
        w("MSG %r | %r" % (m.severity, m.text)); n += 1
    w("messages=%d" % n)
    proj.save_as(os.path.join(base, "LFAM_POC.project")); w("saved POC"); proj.close()
except Exception:
    w("ERR " + traceback.format_exc())
log.close()
