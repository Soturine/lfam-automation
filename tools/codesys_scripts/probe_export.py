# -*- coding: utf-8 -*-
# Probe (read-only on a COPY): export PLC_PRG as PLCopen XML to learn the language/format.
import os
base = os.environ["LFAM_WORK"]
log = open(os.path.join(base, "probe.log"), "w")
try:
    proj = projects.open(os.path.join(base, "LFAM_copy.project"))
    app = proj.active_application
    log.write("app=%s\n" % app)
    for o in app.get_children(True):
        log.write("child %s\n" % o.get_name())
    prg = [o for o in app.get_children() if o.get_name() == "PLC_PRG"][0]
    proj.export_xml((prg,), path=os.path.join(base, "plc_prg_after.xml"))
    log.write("exported\n")
    proj.close()
except Exception as e:
    import traceback
    log.write("ERR %s\n" % traceback.format_exc())
log.close()
