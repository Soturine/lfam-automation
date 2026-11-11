# -*- coding: utf-8 -*-
# POC on a COPY of the project: import LD POU as PLC_PRG, build, login to Control Win (local virtual PLC), force input, read coil.
import os, time, traceback
base = os.environ["LFAM_WORK"]; xml = os.environ["LFAM_XML"]
log = open(os.path.join(base, "poc.log"), "w")
def w(s): log.write(s + "\n"); log.flush()
try:
    proj = projects.open(os.path.join(base, "LFAM_copy.project"))
    app = proj.active_application
    for o in list(app.get_children()):
        if o.get_name().startswith("PLC_PRG") and o.parent == app:
            w("remove " + o.get_name()); o.remove()
    app.import_xml(xml, ConflictResolve.Replace)
    w("children: " + ",".join(o.get_name() for o in app.get_children(True)))
    app.build()
    for m in system.get_message_objects():
        w("MSG %r | %r" % (m.severity, m.text))
    w("build done")
    onl = online.create_online_application(app)
    w("login...")
    onl.login(OnlineChangeOption.Never, True)
    w("logged in: %s" % onl.is_logged_in)
    onl.start(); time.sleep(2)
    w("state: %s" % onl.application_state)
    for bt, fl in (("FALSE","FALSE"),("TRUE","FALSE"),("TRUE","TRUE")):
        onl.set_prepared_value("PLC_PRG.BT_TESTE", bt)
        onl.set_prepared_value("PLC_PRG.FALHA_TESTE", fl)
        onl.write_prepared_values(); time.sleep(1.5)
        w("BT=%s FALHA=%s -> EST_TESTE=%s" % (bt, fl, onl.read_value("PLC_PRG.EST_TESTE")))
    onl.logout()
    proj.save(); proj.close()
except Exception:
    w("ERR " + traceback.format_exc())
log.close()
