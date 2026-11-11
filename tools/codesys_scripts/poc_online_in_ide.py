# -*- coding: utf-8 -*-
# Run INSIDE the CODESYS IDE (Tools > Scripting > Execute Script File) with work/LFAM_POC.project open.
# Logs in to the local Control Win, starts it, toggles inputs and prints the coil. Result also in %TEMP%\lfam_poc_online.log
import os, time, tempfile
out = open(os.path.join(tempfile.gettempdir(), "lfam_poc_online.log"), "w")
def w(s): print(s); out.write(s + "\n"); out.flush()
app = projects.primary.active_application
onl = online.create_online_application(app)
onl.login(OnlineChangeOption.Try, True)
onl.start(); time.sleep(2)
w("state=%s" % onl.application_state)
for bt, fl in (("FALSE","FALSE"),("TRUE","FALSE"),("TRUE","TRUE")):
    onl.set_prepared_value("PLC_PRG.BT_TESTE", bt); onl.set_prepared_value("PLC_PRG.FALHA_TESTE", fl)
    onl.write_prepared_values(); time.sleep(1.5)
    w("BT=%s FALHA=%s -> EST_TESTE=%s" % (bt, fl, onl.read_value("PLC_PRG.EST_TESTE")))
onl.logout(); out.close()
