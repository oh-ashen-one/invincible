#!/usr/bin/env python3
"""Conservative manual preview admission using the verified M5 shared locks.
Only invoked after owner authorization. Never clears pauses or stops foreign work.
"""
import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time


def main():
    base = Path(os.environ.get('GPU_SLOT_DIR', str(Path.home()/'.cache/gpu-slot')))
    if base.resolve() != (Path.home()/'.cache/gpu-slot').resolve():
        raise SystemExit('M5 preview requires its verified shared coordinator root.')
    if not all((base/n).is_dir() for n in ('locks','holders','queue')):
        raise SystemExit('Shared coordinator is unavailable; do not create a parallel namespace.')
    coexist=os.environ.get('SM2_COEXIST_HOLDER','').strip()
    if coexist and not (coexist.isdigit() and (base/'holders'/f'{coexist}.json').exists()):
        raise SystemExit(f'SM2_COEXIST_HOLDER={coexist} is not a current holder.')
    def guard():
        if (base/'PAUSED').exists():
            raise SystemExit('Shared GPU PAUSED; owner-approved recovery required.')
        if any((base/'queue').iterdir()):
            raise SystemExit('Existing GPU waiters have priority.')
        others=[h for h in (base/'holders').glob('*.json') if h.stem!=str(os.getpid()) and h.stem!=coexist]
        if others:
            raise SystemExit('Existing GPU holders require coordination.')
        table=subprocess.check_output(['ps','-axo','pid=,comm='],text=True)
        names={'unrealeditor','unrealeditor-cmd','blender','unity','unityshadercompiler'}
        engines=[line for line in table.splitlines() if line.strip().split(None,1)[-1].rsplit('/',1)[-1].lower() in names and '/Unity Hub.app/' not in line]
        if engines:
            raise SystemExit('Other renderer processes exist; review ownership before preview:\n'+'\n'.join(engines))
        owner=subprocess.check_output(['stat','-f','%Su','/dev/console'],text=True).strip()
        if owner in ('','root','loginwindow'):
            raise SystemExit('No live desktop session.')
    if len(sys.argv)<3 or sys.argv[1]!='--':
        raise SystemExit('Usage: guarded_preview.py -- executable args...')
    guard()
    handles=[]
    holder=base/'holders'/f'{os.getpid()}.json'
    child=None
    try:
        if coexist:
            # Owner-approved coexistence with ONE named holder (SM2_COEXIST_HOLDER=<pid>): shared perf lock + one free
            # capture slot taken exclusively. Never more than one slot; perf numbers from such a run are contaminated.
            fd=(base/'locks'/'perf.lock').open('a+'); handles.append(fd)
            try: fcntl.flock(fd,fcntl.LOCK_SH|fcntl.LOCK_NB)
            except BlockingIOError: raise SystemExit('Shared GPU capacity is occupied.')
            slot=None
            for s in (0,1):
                fd=(base/'locks'/f'capture.{s}.lock').open('a+')
                try: fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB); handles.append(fd); slot=s; break
                except BlockingIOError: fd.close()
            if slot is None: raise SystemExit('Shared GPU capacity is occupied.')
            meta={'class':'capture','slot':str(slot),'reserved_slots':[slot],'contaminated':True,'coexist_with':int(coexist)}
            print(f'COEXIST with holder {coexist}: capture slot {slot}, perf lock shared; perf numbers are contaminated', file=sys.stderr)
        else:
            # Exclusive perf admission also excludes inference/residency holding SH.
            # Reserve both capture locks conservatively; never raise the global cap.
            for name in ('perf.lock','capture.0.lock','capture.1.lock'):
                fd=(base/'locks'/name).open('a+'); handles.append(fd)
                try: fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
                except BlockingIOError: raise SystemExit('Shared GPU capacity is occupied.')
            meta={'class':'perf','slot':'0','reserved_slots':[0,1]}
        guard()
        holder.write_text(json.dumps({'pid':os.getpid(),'start':subprocess.check_output(['ps','-o','lstart=','-p',str(os.getpid())],text=True).strip(),**meta,'label':'spiderman-owner-preview','cmd':'tools/m5/guarded_preview.py'})+'\n')
        stop_requested=[False]
        def stop(signum, frame):
            stop_requested[0]=True
            if child is not None and child.poll() is None: child.terminate()
        signal.signal(signal.SIGTERM,stop)
        signal.signal(signal.SIGINT,stop)
        child=subprocess.Popen(sys.argv[2:])
        deadline=None
        while child.poll() is None:
            if (base/'PAUSED').exists() or stop_requested[0]:
                if deadline is None:
                    child.terminate(); deadline=time.monotonic()+60
                elif time.monotonic()>=deadline:
                    child.kill()  # only our child, after 60 seconds of graceful stop
            time.sleep(0.25)
        return child.returncode
    finally:
        if child is not None and child.poll() is None:
            child.terminate()
            try: child.wait(timeout=60)
            except subprocess.TimeoutExpired: child.kill(); child.wait()
        holder.unlink(missing_ok=True)
        for fd in reversed(handles): fd.close()

if __name__=='__main__':
    raise SystemExit(main())
