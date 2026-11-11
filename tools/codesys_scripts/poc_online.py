# -*- coding: utf-8 -*-
# Online test of the LD POC on the LOCAL Control Win.
# RUN INSIDE THE CODESYS IDE (Tools > Scripting > Execute Script File) with work/LFAM_POC.project open,
# already logged in to the device with YOUR device administrator. The script never creates users,
# never touches authentication and never deletes applications on the controller.
# Result is written to %TEMP%\lfam_poc_online.log (no credentials are logged).
import os, time, tempfile, traceback
log = open(os.path.join(tempfile.gettempdir(), "lfam_poc_online.log"), "w")
def w(s):
    log.write(str(s) + "\n"); log.flush()
try:
    app = projects.primary.active_application
    onl = online.create_online_application(app)
    if not onl.is_logged_in:
        w("not logged in: log in manually first (Online > Login)"); raise SystemExit
    w("logged_in=%s state=%s" % (onl.is_logged_in, onl.application_state))
    results = []
    for bt, fl in (("FALSE", "FALSE"), ("TRUE", "FALSE"), ("TRUE", "TRUE")):
        onl.set_prepared_value("PLC_PRG.BT_TESTE", bt)
        onl.set_prepared_value("PLC_PRG.FALHA_TESTE", fl)
        onl.write_prepared_values()
        time.sleep(1.5)
        est = onl.read_value("PLC_PRG.EST_TESTE")
        results.append((bt, fl, est))
        w("BT_TESTE=%s FALHA_TESTE=%s -> EST_TESTE=%s" % (bt, fl, est))
    # release: leave inputs FALSE
    onl.set_prepared_value("PLC_PRG.BT_TESTE", "FALSE"); onl.set_prepared_value("PLC_PRG.FALHA_TESTE", "FALSE")
    onl.write_prepared_values()
    expected = ["FALSE", "TRUE", "FALSE"]
    ok = all(str(r[2]).upper() == e for r, e in zip(results, expected))
    w("PASS=%s (esperado EST_TESTE = F, T, F)" % ok)
except SystemExit:
    pass
except Exception:
    w("ERR " + traceback.format_exc())
log.close()
