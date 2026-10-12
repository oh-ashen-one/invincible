# Set MPC_City scalar defaults from JOB_ARGS (run through uejob.py):  python3 tools/export/ue/uejob.py tools/export/ue/set_mpc.py DayEmisK=0.22 DebugMode=0
import unreal
p = '/Game/City/Materials/MPC_City'
m = unreal.EditorAssetLibrary.load_asset(p)
sp = list(m.get_editor_property('scalar_parameters'))
for q in sp:
    n = str(q.get_editor_property('parameter_name'))
    if n in JOB_ARGS:
        q.set_editor_property('default_value', float(JOB_ARGS[n]))
m.set_editor_property('scalar_parameters', sp)
unreal.EditorAssetLibrary.save_asset(p)
print({str(q.get_editor_property('parameter_name')): q.get_editor_property('default_value') for q in sp})
