# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Editor-side job runner for THIS worktree's (P4 Look) Unreal Editor, started via -ExecCmds="py <this file>".
# Polls a private job directory; each job is a .py file executed on the game thread (slate post-tick); stdout/stderr and
# the exception (if any) go to <job>.out / <job>.done. File based -> only this editor ever sees these jobs.
# (Same mechanism as tools/export/ue/job_server.py of P1, with its own job directory.)
import unreal, os, sys, io, time, traceback, glob

JOBS = os.environ.get('SM2_LOOK_JOBS', os.path.join(os.environ.get('SM2_LOOK_SCRATCH', '/Users/midir/sm2-n1/_scratch/look'), 'uejobs'))
os.makedirs(JOBS, exist_ok=True)
_last = [0.0]

def _run(path):
    out = io.StringIO(); old = sys.stdout, sys.stderr; ok = True
    sys.stdout = sys.stderr = out
    try:
        src = open(path).read()
        g = {'__name__': '__main__', '__file__': path}
        exec(compile(src, path, 'exec'), g)
    except Exception:
        ok = False; traceback.print_exc()
    finally:
        sys.stdout, sys.stderr = old
    with open(path + '.out', 'w') as f: f.write(out.getvalue())
    with open(path + '.done', 'w') as f: f.write('ok' if ok else 'error')

def _tick(dt):
    now = time.time()
    if now - _last[0] < 0.25: return
    _last[0] = now
    for p in sorted(glob.glob(os.path.join(JOBS, '*.py'))):
        if os.path.exists(p + '.done') or os.path.exists(p + '.running'): continue
        open(p + '.running', 'w').close()
        _run(p)
        try: os.remove(p + '.running')
        except OSError: pass

unreal.register_slate_post_tick_callback(_tick)
unreal.log('[sm2-look] job server polling ' + JOBS)
