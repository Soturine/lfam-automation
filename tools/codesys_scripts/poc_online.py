# -*- coding: utf-8 -*-
# Online test of the LD POC on the LOCAL Control Win only. Works headless (opens work/LFAM_POC.project)
# or inside the IDE (uses the open project). Never deletes foreign applications on login.
import os, time, traceback
base = os.environ.get("LFAM_WORK", os.path.join(os.environ["TEMP"]))
log = open(os.path.join(base, "poc_online.log"), "w")
def w(s): log.write(repr(s) + "\n"); log.flush()
try:
    proj = projects.primary or projects.open(os.path.join(base, "LFAM_POC.project"))
    app = proj.active_application
    onl = online.create_online_application(app)
    system.script_prompt_handling = ScriptPromptHandling.LogPrompts | ScriptPromptHandling.ForwardUnknownPrompts
    system.prompt_answers["Prompt_ActivateUserManagement_New"] = PromptResult.No
    system.log_prompt_details = True
    w("login...")
    onl.login(OnlineChangeOption.Try, False)
    w("logged_in=%s state=%s" % (onl.is_logged_in, onl.application_state))
    onl.start(); time.sleep(2); w("state=%s" % onl.application_state)
    for bt, fl in (("FALSE", "FALSE"), ("TRUE", "FALSE"), ("TRUE", "TRUE")):
        onl.set_prepared_value("PLC_PRG.BT_TESTE", bt); onl.set_prepared_value("PLC_PRG.FALHA_TESTE", fl)
        onl.write_prepared_values(); time.sleep(1.5)
        w("BT=%s FALHA=%s -> EST_TESTE=%s" % (bt, fl, onl.read_value("PLC_PRG.EST_TESTE")))
    onl.logout(); w("done")
except Exception:
    w("ERR " + traceback.format_exc())
log.close()
