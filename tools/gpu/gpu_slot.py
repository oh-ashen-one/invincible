#!/usr/bin/env python3
# Homage fan game tooling. Not an official Marvel, Sony or Insomniac project; no affiliation.
"""gpu_slot: shared-GPU capture slots + exclusive perf lock for the Night-1 Unreal loop.

  gpu_slot.sh capture [opts] -- CMD...   hold one of N (default 2) shared capture slots while CMD runs
  gpu_slot.sh perf    [opts] -- CMD...   EXCLUSIVE: waits for no capture slot held, no other Unreal
                                         capture process, and GPU "Device Utilization %" < 15 for 10
                                         consecutive seconds; then runs CMD (max hold 15 min)
  gpu_slot.sh status [--json]            holders, waiters, GPU utilization, Unreal processes
  gpu_slot.sh util                       print the current GPU utilization (integer percent)
  gpu_slot.sh summary FILE.json          one-line "GPU-LOCK: ..." summary of a --json sidecar (paste next to perf numbers)

opts: --label NAME  --json FILE (result sidecar)  --timeout SECS (max wait to acquire)
Exit code = CMD's exit code.  Wrapper-only codes: 2 usage, 70 internal error, 75 wait timed out
(CMD NOT run), 124 max hold exceeded (CMD killed), 127 CMD not found, 128+N killed by signal N.

Locking = kernel flock(2) via python fcntl on files in the state dir (default
/Users/midir/sm2-n1/_scratch/gpu). flock is released by the kernel when the holder dies, so a
crashed / kill -9'd holder can never wedge the lock; stale holder/queue records (dead PID, or PID
reused: start time differs) are detected, logged as "stale-recovered" and removed by any waiter.
Fairness: strict FIFO ticket queue, only the head waiter may try to acquire.

Environment (all optional; tests shrink the timings):
  GPU_SLOT_DIR, GPU_SLOT_LOG, GPU_SLOT_POLL=1, GPU_SLOT_UTIL_MAX=15, GPU_SLOT_CALM_SECONDS=10,
  GPU_SLOT_CAPTURE_SLOTS=2, GPU_SLOT_PERF_MAX_HOLD=900, GPU_SLOT_CAPTURE_MAX_HOLD=2400,
  GPU_SLOT_PERF_WAIT_TIMEOUT=1800, GPU_SLOT_CAPTURE_WAIT_TIMEOUT=3600, GPU_SLOT_SAMPLE_INTERVAL=2,
  GPU_SLOT_LABEL, GPU_SLOT_QUIET=1,
  GPU_SLOT_MOCK_UTIL=<int> | GPU_SLOT_MOCK_UTIL_FILE=<file holding an int>   (replaces ioreg),
  GPU_SLOT_UNREAL_PATTERN=<regex on the command line> (replaces "executable is UnrealEditor"),
  GPU_SLOT_CAPTURE_PATTERN=<regex> (which Unreal instances count as capture processes).
"""
import errno
import fcntl
import json
import os
import re
import signal
import subprocess
import sys
import threading
import time
from datetime import datetime

DEFAULT_DIR = "/Users/midir/sm2-n1/_scratch/gpu"
DEFAULT_CAPTURE_PAT = r"(^|\s)-game(\s|$)|-WHShotDir=|-WHPerfFrom="
EX_TIMEOUT = 75
EX_MAXHOLD = 124


def _f(name, default):
    v = os.environ.get(name)
    if v is None or v == "":
        return default
    try:
        return float(v)
    except ValueError:
        sys.stderr.write("gpu_slot: bad %s=%r\n" % (name, v))
        sys.exit(2)


class Cfg:
    def __init__(self):
        e = os.environ
        self.dir = e.get("GPU_SLOT_DIR") or DEFAULT_DIR
        self.log = e.get("GPU_SLOT_LOG") or os.path.join(self.dir, "gpu_slot.log")
        self.poll = _f("GPU_SLOT_POLL", 1.0)
        self.util_max = _f("GPU_SLOT_UTIL_MAX", 15.0)
        self.calm = _f("GPU_SLOT_CALM_SECONDS", 10.0)
        self.slots = int(_f("GPU_SLOT_CAPTURE_SLOTS", 2))
        self.max_hold = {"perf": _f("GPU_SLOT_PERF_MAX_HOLD", 900.0),
                         "capture": _f("GPU_SLOT_CAPTURE_MAX_HOLD", 2400.0)}
        self.wait_timeout = {"perf": _f("GPU_SLOT_PERF_WAIT_TIMEOUT", 1800.0),
                             "capture": _f("GPU_SLOT_CAPTURE_WAIT_TIMEOUT", 3600.0)}
        self.sample = _f("GPU_SLOT_SAMPLE_INTERVAL", 2.0)
        self.wait_log_every = _f("GPU_SLOT_WAIT_LOG_EVERY", 30.0)
        self.quiet = e.get("GPU_SLOT_QUIET") == "1"
        self.unreal_pat = e.get("GPU_SLOT_UNREAL_PATTERN") or None
        self.capture_pat = re.compile(e.get("GPU_SLOT_CAPTURE_PATTERN") or DEFAULT_CAPTURE_PAT)
        self.mock_util = e.get("GPU_SLOT_MOCK_UTIL")
        self.mock_util_file = e.get("GPU_SLOT_MOCK_UTIL_FILE")
        self.holders = os.path.join(self.dir, "holders")
        self.queue = os.path.join(self.dir, "queue")
        self.locks = os.path.join(self.dir, "locks")
        self.perf_lock = os.path.join(self.locks, "perf.lock")

    def ensure_dirs(self):
        for d in (self.dir, self.holders, self.queue, self.locks, os.path.dirname(self.log)):
            os.makedirs(d, mode=0o777, exist_ok=True)


# ---------------------------------------------------------------- small helpers

def now_iso():
    return datetime.now().astimezone().isoformat(timespec="milliseconds")


def _run(argv, timeout=10):
    try:
        return subprocess.run(argv, capture_output=True, text=True, timeout=timeout).stdout
    except Exception:
        return ""


def read_util(cfg):
    """GPU 'Device Utilization %' (max over accelerators) as float, or None if unreadable."""
    if cfg.mock_util_file:
        try:
            with open(cfg.mock_util_file) as fh:
                return float(fh.read().strip())
        except Exception:
            return None
    if cfg.mock_util is not None:
        try:
            return float(cfg.mock_util)
        except ValueError:
            return None
    out = _run(["ioreg", "-r", "-d", "1", "-c", "IOAccelerator"])
    vals = [int(x) for x in re.findall(r'"Device Utilization %"\s*=\s*(\d+)', out)]
    return float(max(vals)) if vals else None


def fmt_util(u):
    return "?" if u is None else ("%d" % u if float(u).is_integer() else "%.1f" % u)


def proc_start(pid):
    """(state, lstart) for a pid, or ('', '') if it does not exist."""
    out = _run(["ps", "-o", "stat=,lstart=", "-p", str(pid)], 5).strip()
    if not out:
        return "", ""
    parts = out.split(None, 1)
    return parts[0], (parts[1].strip() if len(parts) > 1 else "")


def pid_alive(pid, start):
    try:
        os.kill(int(pid), 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        pass
    except Exception:
        return False
    stat, lstart = proc_start(pid)
    if not stat or stat.startswith("Z"):
        return False
    return (not start) or lstart == start


def proc_table(cfg):
    """All processes: {pid: dict(pid, ppid, etime, cmd, comm)}."""
    out1 = _run(["ps", "-axww", "-o", "pid=,ppid=,etime=,command="])
    out2 = _run(["ps", "-axww", "-o", "pid=,comm="])
    comm = {}
    for line in out2.splitlines():
        m = re.match(r"\s*(\d+)\s+(.*)$", line)
        if m:
            comm[int(m.group(1))] = m.group(2).strip()
    table = {}
    for line in out1.splitlines():
        m = re.match(r"\s*(\d+)\s+(\d+)\s+(\S+)\s+(.*)$", line)
        if not m:
            continue
        pid = int(m.group(1))
        table[pid] = {"pid": pid, "ppid": int(m.group(2)), "etime": m.group(3),
                      "cmd": m.group(4), "comm": comm.get(pid, "")}
    return table


def unreal_procs(cfg, table=None):
    """Unreal editor/game instances (not gpu_slot wrappers): list of dicts with kind capture|editor."""
    table = table if table is not None else proc_table(cfg)
    res = []
    for p in table.values():
        cmd = p["cmd"]
        if "gpu_slot.py" in cmd or "gpu_status" in cmd:
            continue
        if cfg.unreal_pat:
            is_ue = re.search(cfg.unreal_pat, cmd) is not None
        else:
            is_ue = p["comm"].endswith("/MacOS/UnrealEditor")
        if not is_ue:
            continue
        kind = "capture" if cfg.capture_pat.search(cmd) else "editor"
        m = re.search(r"(/\S+?)/unreal/WebHomage/WebHomage\.uproject", cmd) or \
            re.search(r"(/\S*?)/[^/ ]*\.uproject", cmd)
        proj = m.group(1) if m else ""
        q = dict(p)
        q["kind"] = kind
        q["project"] = os.path.basename(proj) if proj else ""
        res.append(q)
    return sorted(res, key=lambda x: x["pid"])


def descendants(table, root):
    kids = {}
    for p in table.values():
        kids.setdefault(p["ppid"], []).append(p["pid"])
    seen, stack = set(), [root]
    while stack:
        x = stack.pop()
        for k in kids.get(x, []):
            if k not in seen:
                seen.add(k)
                stack.append(k)
    return seen


def foreign_captures(cfg, root_pid=None):
    """Unreal capture processes not descended from root_pid (default: this process)."""
    table = proc_table(cfg)
    mine = descendants(table, root_pid or os.getpid())
    return [p for p in unreal_procs(cfg, table) if p["kind"] == "capture" and p["pid"] not in mine]


def piece_from_cwd():
    m = re.match(r"/Users/midir/sm2-n1/([^/]+)", os.getcwd())
    if m:
        return m.group(1)
    m = re.match(r"/Users/midir/(spider-man-2[^/]*)", os.getcwd())
    return m.group(1) if m else os.path.basename(os.getcwd())


# ---------------------------------------------------------------- logging

class Logger:
    def __init__(self, cfg, cls, label):
        self.cfg, self.cls, self.label = cfg, cls, label

    def __call__(self, event, util="auto", echo=False, **kv):
        cfg = self.cfg
        if util == "auto":
            util = read_util(cfg)
        parts = [now_iso(), "pid=%d" % os.getpid(), "class=%s" % self.cls,
                 "label=%s" % self.label, "event=%s" % event, "util=%s" % fmt_util(util)]
        for k, v in kv.items():
            s = str(v)
            if re.search(r"[\s\"]", s) or s == "":
                s = json.dumps(s)
            parts.append("%s=%s" % (k, s))
        line = " ".join(parts) + "\n"
        try:
            fd = os.open(cfg.log, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o666)
            try:
                os.write(fd, line.encode())
            finally:
                os.close(fd)
        except OSError:
            pass
        if echo and not cfg.quiet:
            sys.stderr.write("gpu_slot[%s/%s]: %s %s\n" % (self.cls, self.label, event,
                             " ".join("%s=%s" % (k, v) for k, v in kv.items())))
            sys.stderr.flush()


# ---------------------------------------------------------------- state records

def _atomic_write(path, obj):
    tmp = "%s.tmp%d" % (path, os.getpid())
    with open(tmp, "w") as fh:
        json.dump(obj, fh)
    os.replace(tmp, path)


def _read_json(path):
    try:
        with open(path) as fh:
            return json.load(fh)
    except Exception:
        return None


def list_records(d):
    recs = []
    try:
        names = sorted(os.listdir(d))
    except OSError:
        return recs
    for n in names:
        if not n.endswith(".json"):
            continue
        r = _read_json(os.path.join(d, n))
        if r is not None:
            r["_file"] = os.path.join(d, n)
            recs.append(r)
    return recs


def reap_stale(cfg, log):
    """Remove holder/queue records whose owner is dead. Returns number recovered."""
    n = 0
    for kind, d in (("holder", cfg.holders), ("waiter", cfg.queue)):
        for r in list_records(d):
            if not pid_alive(r.get("pid", -1), r.get("start", "")):
                try:
                    os.unlink(r["_file"])
                except OSError:
                    continue
                n += 1
                log("stale-recovered", kind=kind, dead_pid=r.get("pid"), dead_class=r.get("class"),
                    dead_label=r.get("label"), dead_slot=r.get("slot", ""),
                    orphan_child=r.get("child_pid", ""), echo=True)
    return n


def try_flock(path, mode):
    fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o666)
    try:
        fcntl.flock(fd, mode | fcntl.LOCK_NB)
        return fd
    except OSError as e:
        os.close(fd)
        if e.errno in (errno.EAGAIN, errno.EACCES, errno.EWOULDBLOCK):
            return None
        raise


def release_fd(fd):
    if fd is None:
        return
    try:
        fcntl.flock(fd, fcntl.LOCK_UN)
    except OSError:
        pass
    try:
        os.close(fd)
    except OSError:
        pass


class Aborted(Exception):
    def __init__(self, sig):
        super().__init__("signal %d" % sig)
        self.sig = sig


# ---------------------------------------------------------------- acquire / run

def run_wrapped(cls, label, json_path, wait_timeout, cmd):
    cfg = Cfg()
    cfg.ensure_dirs()
    log = Logger(cfg, cls, label)
    me = os.getpid()
    my_start = proc_start(me)[1]
    cmd_text = " ".join(cmd)

    # re-entrancy: never deadlock against a lock this process tree already holds
    held = os.environ.get("GPU_SLOT_HELD")
    if held:
        if cls == "perf" and held == "capture":
            sys.stderr.write("gpu_slot: refusing perf inside a capture slot (would deadlock)\n")
            log("refused-nested", nested_in=held, echo=True)
            return 2
        log("nested-passthrough", nested_in=held, cmd=cmd_text[:200], echo=True)
        try:
            return subprocess.call(cmd)
        except FileNotFoundError:
            sys.stderr.write("gpu_slot: command not found: %s\n" % cmd[0])
            return 127

    state = {"sig": None, "child": None, "run_phase": False}

    def on_signal(signum, _frame):
        if not state["run_phase"]:
            raise Aborted(signum)
        state["sig"] = signum
        c = state["child"]
        if c is not None:
            try:
                os.killpg(c.pid, signum)
            except OSError:
                pass

    for s in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
        signal.signal(s, on_signal)

    ticket = "%020d-%d" % (time.time_ns(), me)
    qfile = os.path.join(cfg.queue, ticket + ".json")
    hfile = os.path.join(cfg.holders, "%s-%d.json" % (cls, me))
    t_enq = time.time()
    m_enq = time.monotonic()
    _atomic_write(qfile, {"pid": me, "start": my_start, "class": cls, "label": label,
                          "since": now_iso(), "since_epoch": t_enq, "ticket": ticket,
                          "cmd": cmd_text[:300]})
    log("enqueue", cmd=cmd_text[:200], echo=False)

    fds = []      # held flock fds
    holder = {"pid": me, "start": my_start, "class": cls, "label": label, "cmd": cmd_text[:300],
              "state": "acquiring", "since": now_iso(), "since_epoch": t_enq, "slot": ""}
    child = None
    result = {"schema": "gpu_slot/1", "class": cls, "label": label, "pid": me, "cmd": cmd,
              "cwd": os.getcwd(), "queued_at": now_iso()}
    rc = 1
    try:
        # ---- phase 1: FIFO head + lock acquisition
        last_log = 0.0
        while True:
            reap_stale(cfg, log)
            queue = [r for r in list_records(cfg.queue)]
            head = queue[0] if queue else None
            if head is None or head.get("pid") == me:
                got = None
                if cls == "capture":
                    got = try_acquire_capture(cfg)
                else:
                    got = try_acquire_perf(cfg)
                if got is not None:
                    fds, slot = got
                    holder["slot"] = slot
                    break
            waited = time.monotonic() - m_enq
            if wait_timeout > 0 and waited > wait_timeout:
                log("wait-timeout", waited_s=round(waited, 1), echo=True)
                result.update(exit_code=EX_TIMEOUT, outcome="wait-timeout", wait_s=round(waited, 1),
                              exclusive=False, contaminated=True)
                write_result(cfg, json_path, result)
                return EX_TIMEOUT
            if waited - last_log >= cfg.wait_log_every or last_log == 0.0:
                ahead = [r for r in queue if r.get("pid") != me and r.get("ticket", "") < ticket]
                holders = list_records(cfg.holders)
                log("wait", phase="queue", waited_s=round(waited, 1), ahead=len(ahead),
                    holders=",".join("%s:%s" % (h.get("class"), h.get("pid")) for h in holders),
                    echo=(last_log == 0.0 or waited - last_log >= cfg.wait_log_every))
                last_log = waited
            time.sleep(cfg.poll)
        try:
            os.unlink(qfile)
        except OSError:
            pass
        holder["state"] = "settling" if cls == "perf" else "running"
        _atomic_write(hfile, holder)
        t_lock = time.time()
        m_lock = time.monotonic()
        log("acquire", slot=holder["slot"], waited_s=round(m_lock - m_enq, 1), phase="lock", echo=(cls == "capture"))

        # ---- phase 2 (perf only): drain + calm gate
        settle = {}
        if cls == "perf":
            streak0, streak_util, last_log = None, [], 0.0
            while True:
                u = read_util(cfg)
                fc = foreign_captures(cfg)
                ok = (u is not None and u < cfg.util_max and not fc)
                nowm = time.monotonic()
                if ok:
                    if streak0 is None:
                        streak0, streak_util = nowm, []
                    streak_util.append(u)
                    if nowm - streak0 >= cfg.calm:
                        break
                else:
                    streak0, streak_util = None, []
                waited = nowm - m_enq
                if wait_timeout > 0 and waited > wait_timeout:
                    log("wait-timeout", phase="settle", waited_s=round(waited, 1), util=u,
                        foreign_captures=len(fc), echo=True)
                    result.update(exit_code=EX_TIMEOUT, outcome="wait-timeout", wait_s=round(waited, 1),
                                  exclusive=False, contaminated=True)
                    write_result(cfg, json_path, result)
                    return EX_TIMEOUT
                if nowm - m_lock - last_log >= cfg.wait_log_every or last_log == 0.0:
                    log("wait", phase="settle", waited_s=round(waited, 1), util=u,
                        need_util_lt=cfg.util_max, calm_s=cfg.calm,
                        streak_s=0 if streak0 is None else round(nowm - streak0, 1),
                        foreign_captures=",".join(str(p["pid"]) for p in fc), echo=True)
                    last_log = nowm - m_lock
                time.sleep(cfg.poll)
            settle = {"calm_s": cfg.calm, "util_max": cfg.util_max, "samples": len(streak_util),
                      "min": min(streak_util), "max": max(streak_util)}

        # ---- phase 3: run
        wait_s = round(time.monotonic() - m_enq, 2)
        util_before = read_util(cfg)
        table = proc_table(cfg)
        ue_before = unreal_procs(cfg, table)
        exclusive = (cls == "perf")
        result.update(wait_s=wait_s, util_before=util_before, exclusive=exclusive,
                      slot=holder["slot"], settle=settle,
                      unreal_before={"instances": len(ue_before),
                                     "captures": sum(1 for p in ue_before if p["kind"] == "capture"),
                                     "editors": sum(1 for p in ue_before if p["kind"] == "editor")})
        env = dict(os.environ)
        env.update(GPU_SLOT_HELD=cls, GPU_SLOT_LABEL=label, GPU_SLOT_WAIT_S=str(wait_s),
                   GPU_SLOT_UTIL_BEFORE=fmt_util(util_before),
                   GPU_SLOT_INSTANCES_BEFORE=str(len(ue_before)),
                   GPU_SLOT_EXCLUSIVE="1" if exclusive else "0")
        if json_path:
            env["GPU_SLOT_JSON"] = json_path
        max_hold = cfg.max_hold[cls]
        mon = {"utils": [], "instances_max": len(ue_before), "foreign": {}, "stop": threading.Event()}

        def monitor():
            while not mon["stop"].wait(cfg.sample):
                u = read_util(cfg)
                if u is not None:
                    mon["utils"].append(u)
                tb = proc_table(cfg)
                ue = unreal_procs(cfg, tb)
                mine = descendants(tb, me)
                mon["instances_max"] = max(mon["instances_max"], len(ue))
                if cls == "perf":
                    for p in ue:
                        if p["kind"] == "capture" and p["pid"] not in mine:
                            mon["foreign"][p["pid"]] = p["cmd"][:200]

        mt = threading.Thread(target=monitor, daemon=True)
        state["run_phase"] = True
        t_start = time.time()
        m_start = time.monotonic()
        try:
            child = subprocess.Popen(cmd, env=env, start_new_session=True)
        except FileNotFoundError:
            sys.stderr.write("gpu_slot: command not found: %s\n" % cmd[0])
            result.update(exit_code=127, outcome="cmd-not-found")
            rc = 127
            child = None
        except PermissionError:
            sys.stderr.write("gpu_slot: command not executable: %s\n" % cmd[0])
            result.update(exit_code=126, outcome="cmd-not-executable")
            rc = 126
            child = None
        hold_killed = False
        if child is not None:
            state["child"] = child
            holder["child_pid"] = child.pid
            holder["state"] = "running"
            holder["run_since_epoch"] = t_start
            _atomic_write(hfile, holder)
            log("run", child_pid=child.pid, max_hold_s=max_hold, cmd=cmd_text[:200], echo=True)
            mt.start()
            while True:
                try:
                    rc = child.wait(timeout=0.5)
                    break
                except subprocess.TimeoutExpired:
                    pass
                if not hold_killed and max_hold > 0 and time.monotonic() - m_start > max_hold:
                    hold_killed = True
                    log("max-hold-exceeded", max_hold_s=max_hold, echo=True)
                    _killpg(child, signal.SIGTERM)
                    t_term = time.monotonic()
                    while child.poll() is None and time.monotonic() - t_term < 10:
                        time.sleep(0.2)
                    if child.poll() is None:
                        _killpg(child, signal.SIGKILL)
                    child.wait()
                    rc = EX_MAXHOLD
                    break
            mon["stop"].set()
            if rc is not None and rc < 0:
                rc = 128 + (-rc)
            _killpg(child, signal.SIGKILL, quiet=True)  # stragglers in the command's process group
        t_end = time.time()
        util_after = read_util(cfg)
        utils = mon["utils"]
        reasons = []
        if cls != "perf":
            reasons.append("no-exclusive-lock")
        else:
            if util_before is None or util_before >= cfg.util_max:
                reasons.append("util-before-not-idle")
            if mon["foreign"]:
                reasons.append("foreign-capture-process-during-run")
            if hold_killed:
                reasons.append("max-hold-exceeded")
        result.update(
            exit_code=rc, outcome="max-hold-killed" if hold_killed else result.get("outcome", "ran"),
            acquired_at=datetime.fromtimestamp(t_lock).astimezone().isoformat(timespec="milliseconds"),
            started_at=datetime.fromtimestamp(t_start).astimezone().isoformat(timespec="milliseconds"),
            released_at=datetime.fromtimestamp(t_end).astimezone().isoformat(timespec="milliseconds"),
            hold_s=round(t_end - t_lock, 2), run_s=round(t_end - t_start, 2),
            util_after=util_after,
            util_during={"n": len(utils), "min": min(utils) if utils else None,
                         "avg": round(sum(utils) / len(utils), 1) if utils else None,
                         "max": max(utils) if utils else None},
            instances_before=len(ue_before), instances_max_during=mon["instances_max"],
            foreign_capture_during=mon["foreign"],
            contaminated=bool(reasons), contaminated_reasons=reasons,
            perf_valid=(cls == "perf" and not reasons))
        write_result(cfg, json_path, result)
        log("release", exit=rc, hold_s=result["hold_s"], wait_s=wait_s, util_before=fmt_util(util_before),
            util_after=fmt_util(util_after), instances_before=len(ue_before),
            instances_max=mon["instances_max"], contaminated=str(bool(reasons)).lower(),
            reasons=",".join(reasons), echo=True)
        return rc if rc is not None else 1
    except Aborted as a:
        log("aborted", signal=a.sig, echo=True)
        return 128 + a.sig
    finally:
        state["run_phase"] = False
        if child is not None and child.poll() is None:
            _killpg(child, signal.SIGTERM, quiet=True)
            time.sleep(0.3)
            _killpg(child, signal.SIGKILL, quiet=True)
        for fd in fds:
            release_fd(fd)
        for f in (qfile, hfile):
            try:
                os.unlink(f)
            except OSError:
                pass


def _killpg(child, sig, quiet=False):
    try:
        os.killpg(child.pid, sig)
    except OSError:
        pass


def try_acquire_capture(cfg):
    """Shared: SH on perf.lock (fails while a perf run holds/settles) + one free capture slot."""
    sh = try_flock(cfg.perf_lock, fcntl.LOCK_SH)
    if sh is None:
        return None
    for i in range(cfg.slots):
        fd = try_flock(os.path.join(cfg.locks, "capture.%d.lock" % i), fcntl.LOCK_EX)
        if fd is not None:
            return [sh, fd], str(i)
    release_fd(sh)
    return None


def try_acquire_perf(cfg):
    """Exclusive: EX on perf.lock (fails while any capture holds SH or another perf holds EX)."""
    fd = try_flock(cfg.perf_lock, fcntl.LOCK_EX)
    if fd is None:
        return None
    return [fd], "perf"


def write_result(cfg, json_path, result):
    if json_path:
        try:
            os.makedirs(os.path.dirname(os.path.abspath(json_path)), exist_ok=True)
            _atomic_write(json_path, result)
        except OSError as e:
            sys.stderr.write("gpu_slot: cannot write %s: %s\n" % (json_path, e))
    try:
        with open(os.path.join(cfg.dir, "runs.jsonl"), "a") as fh:
            fh.write(json.dumps(result) + "\n")
    except OSError:
        pass


# ---------------------------------------------------------------- status

def cmd_status(as_json=False):
    cfg = Cfg()
    cfg.ensure_dirs()
    util = read_util(cfg)
    holders = list_records(cfg.holders)
    queue = list_records(cfg.queue)
    ue = unreal_procs(cfg)
    for r in holders + queue:
        r["alive"] = pid_alive(r.get("pid", -1), r.get("start", ""))
    if as_json:
        print(json.dumps({"util": util, "util_max": cfg.util_max, "perf_ready_now": util is not None and util < cfg.util_max,
                          "holders": holders, "waiters": queue, "unreal": ue, "slots": cfg.slots}, indent=1))
        return 0
    nowe = time.time()
    print("GPU Device Utilization now: %s %%   (perf gate: < %g %% for %g consecutive s)   %s"
          % (fmt_util(util), cfg.util_max, cfg.calm,
             "-> below threshold" if util is not None and util < cfg.util_max else "-> NOT idle"))
    live_h = [h for h in holders if h["alive"]]
    perf_h = [h for h in live_h if h.get("class") == "perf"]
    cap_h = [h for h in live_h if h.get("class") == "capture"]
    print("Perf lock:     %s" % ("HELD by pid %s label=%s state=%s for %ds" % (
        perf_h[0]["pid"], perf_h[0].get("label"), perf_h[0].get("state"), nowe - perf_h[0].get("since_epoch", nowe))
        if perf_h else "free"))
    print("Capture slots: %d/%d in use" % (len(cap_h), cfg.slots))
    print("Holders (%d):" % len(holders))
    for h in holders:
        print("  %-7s slot=%-4s pid=%-6s label=%-12s state=%-9s for %5ds%s  cmd=%s" % (
            h.get("class"), h.get("slot", ""), h.get("pid"), h.get("label"), h.get("state"),
            nowe - h.get("since_epoch", nowe), "" if h["alive"] else "  STALE(pid dead)", h.get("cmd", "")[:90]))
    print("Waiters, FIFO (%d):" % len(queue))
    for i, w in enumerate(queue, 1):
        print("  %d. %-7s pid=%-6s label=%-12s waiting %5ds%s  cmd=%s" % (
            i, w.get("class"), w.get("pid"), w.get("label"), nowe - w.get("since_epoch", nowe),
            "" if w["alive"] else "  STALE(pid dead)", w.get("cmd", "")[:90]))
    ncap = sum(1 for p in ue if p["kind"] == "capture")
    print("Unreal processes: %d (%d capture/-game, %d editor)   [hard cap 3]" % (len(ue), ncap, len(ue) - ncap))
    for p in ue:
        print("  pid=%-6s %-7s project=%-12s etime=%s" % (p["pid"], p["kind"], p["project"] or "?", p["etime"]))
    tbl = proc_table(cfg)
    under = set()
    for h in live_h:
        under |= descendants(tbl, h["pid"])
    unwrapped = [p for p in ue if p["kind"] == "capture" and p["pid"] not in under]
    if unwrapped:
        print("NOTE: %d capture process(es) not under a gpu_slot holder (unwrapped -> perf runs will wait / be contaminated): %s"
              % (len(unwrapped), ",".join(str(p["pid"]) for p in unwrapped)))
    return 0


# ---------------------------------------------------------------- main

def usage(code=2):
    sys.stderr.write(__doc__.split("Locking =")[0])
    sys.exit(code)


def main(argv):
    if len(argv) < 2 or argv[1] in ("-h", "--help", "help"):
        usage(0 if len(argv) >= 2 else 2)
    sub = argv[1]
    if sub == "status":
        return cmd_status("--json" in argv[2:])
    if sub == "util":
        u = read_util(Cfg())
        print(fmt_util(u))
        return 0 if u is not None else 1
    if sub == "summary":
        if len(argv) < 3:
            usage()
        r = _read_json(argv[2])
        if r is None:
            sys.stderr.write("gpu_slot: cannot read %s\n" % argv[2])
            return 1
        ud = r.get("util_during") or {}
        print("GPU-LOCK: class=%s exclusive=%s util_before=%s%% util_after=%s%% util_during_avg=%s%% wait_s=%s "
              "instances_before=%s instances_max=%s contaminated=%s%s" % (
                  r.get("class"), "yes" if r.get("exclusive") else "no", fmt_util(r.get("util_before")),
                  fmt_util(r.get("util_after")), ud.get("avg"), r.get("wait_s"), r.get("instances_before"),
                  r.get("instances_max_during"), str(bool(r.get("contaminated"))).lower(),
                  " (%s)" % ",".join(r.get("contaminated_reasons") or []) if r.get("contaminated") else ""))
        return 0
    if sub not in ("capture", "perf"):
        sys.stderr.write("gpu_slot: unknown subcommand %r\n" % sub)
        usage()
    args = argv[2:]
    label = os.environ.get("GPU_SLOT_LABEL") or piece_from_cwd()
    json_path, timeout = os.environ.get("GPU_SLOT_JSON") or None, None
    i = 0
    while i < len(args) and args[i] != "--":
        a = args[i]
        if a == "--label" and i + 1 < len(args):
            label = args[i + 1]; i += 2
        elif a == "--json" and i + 1 < len(args):
            json_path = args[i + 1]; i += 2
        elif a == "--timeout" and i + 1 < len(args):
            timeout = float(args[i + 1]); i += 2
        else:
            sys.stderr.write("gpu_slot: unknown option %r\n" % a)
            usage()
    cmd = args[i + 1:]
    if i >= len(args) or not cmd:
        sys.stderr.write("gpu_slot: missing '-- <command...>'\n")
        usage()
    cfg = Cfg()
    return run_wrapped(sub, label, json_path, timeout if timeout is not None else cfg.wait_timeout[sub], cmd)


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except KeyboardInterrupt:
        sys.exit(130)
