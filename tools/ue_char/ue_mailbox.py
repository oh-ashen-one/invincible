"""Editor-side mailbox for the P2 Characters UE instance (fan homage project; not official Marvel/Sony/Insomniac).

Launch the editor with  -ExecCmds="py <abs path to this file>"  (NOT -ExecutePythonScript: that quits after the script)
Then drop .py files into $BOX/in/ (tools/ue_char/uebox.py does it); each runs once on the game thread
(slate post-tick) and its stdout/traceback lands in $BOX/out/<name>.txt. Local-file only: no network
listener, so it can never reach another agent's editor.
"""
import unreal, os, glob, traceback, io, contextlib, time

# same root as tools/ue_char/p2paths.py (P2_SCRATCH, default <repo>/unreal/WebHomage/Saved/P2Build); the editor's project dir locates the repo
BOX = os.path.join(os.environ.get('P2_SCRATCH') or os.path.join(os.path.abspath(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())), 'Saved', 'P2Build'), 'uebox')
os.makedirs(BOX + '/in', exist_ok=True)
os.makedirs(BOX + '/out', exist_ok=True)
_state = {'t': 0.0, 'g': {}}


def _tick(dt):
    now = time.time()
    if now - _state['t'] < 0.2:
        return
    _state['t'] = now
    for f in sorted(glob.glob(BOX + '/in/*.py')):
        name = os.path.basename(f)
        try:
            code = open(f).read()
        finally:
            os.remove(f)
        buf = io.StringIO()
        ok = True
        g = _state['g']
        g.update({'__name__': '__mailbox__', 'unreal': unreal})
        try:
            with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
                exec(compile(code, f, 'exec'), g)
        except Exception:
            ok = False
            buf.write(traceback.format_exc())
        tmp = BOX + '/out/' + name + '.tmp'
        open(tmp, 'w').write(('OK\n' if ok else 'ERR\n') + buf.getvalue())
        os.replace(tmp, BOX + '/out/' + name + '.txt')


unreal.register_slate_post_tick_callback(_tick)
unreal.log('[ue_char mailbox] watching ' + BOX)
