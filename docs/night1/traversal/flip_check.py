#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P3 round 11: flips vs FLIPS_SPEC.md (owner clip numbers). usage: flip_check.py <telemetry.csv> <label>
# Per trick (rows with flip_prog set): program, duration, rotations, and from the RENDERED body axis (hips->head from the bones;
# post-animation columns are same-row, legacy bone columns shift one row within each case): rate over 0.04 s windows,
# (peak / mean / slowest), holds (<= 150 deg/s), ease ratio,
# twist + body tilt, release->trick delay, catch continuity, leg lag at shape changes; camera roll / hero size / camera height.
import csv
import math
import sys


def f(r, k, d=0.0):
    try:
        return float(r[k])
    except (KeyError, ValueError, TypeError):
        return d


def same_case(a, b):
    """Legacy case-less CSVs are one run; named case resets are hard boundaries."""
    return a.get("case", "") == b.get("case", "")


def main(path, label):
    with open(path, newline="") as stream:
        R = list(csv.DictReader(stream))
    n = len(R)
    t = [f(r, "t") for r in R]
    # New post-animation columns describe the row actually rendered. Legacy
    # columns are one row late. Never borrow a new scripted case's spawn pose
    # to complete a legacy flip window.
    same_frame = bool(n) and all(f(row, "fw_body_pitch_deg", None) is not None and f(row, "fw_body_axis_deg", None) is not None for row in R)
    if same_frame:
        bp = [f(row, "fw_body_pitch_deg") for row in R]
        bax = [f(row, "fw_body_axis_deg") for row in R]
    else:
        bp = [f(R[i + 1], "body_pitch_deg") if i + 1 < n and same_case(R[i], R[i + 1]) else None for i in range(n)]
        bax = [f(R[i + 1], "body_axis_deg") if i + 1 < n and same_case(R[i], R[i + 1]) else None for i in range(n)]
    px_h = [(f(r, "px_bottom") - f(r, "px_top")) / 1080.0 if f(r, "px_bottom") > 0 else -1 for r in R]
    tricks = []
    i = 0
    while i < n:
        if R[i]["flip_prog"]:
            j = i
            while j + 1 < n and same_case(R[j], R[j + 1]) and R[j + 1]["flip_prog"] == R[i]["flip_prog"] and f(R[j + 1], "flip_t") >= f(R[j], "flip_t"):
                j += 1
            tricks.append((i, j))
            i = j + 1
        else:
            i += 1
    out = []
    P = out.append
    P("FLIP CHECK %s (%s): %d tricks" % (label, path.split("/")[-1], len(tricks)))
    P("rendered-axis phase: %s" % ("same-frame post-animation" if same_frame else "legacy case-bounded one-row shift"))
    allpass = True
    for k, (a, b) in enumerate(tricks):
        prog = R[a]["flip_prog"]
        dur = t[b] - t[a]
        prog_rot = abs(f(R[b], "flip_pitch_deg")) / 360.0
        twist = abs(f(R[b], "flip_twist_deg"))
        # Only the last rendered sample can be unavailable. All earlier 0.04 s
        # windows still count, including genuine high-rate primary tuck peaks.
        measured_end = b if bp[b] is not None else b - 1
        if measured_end < a or bp[a] is None:
            P("-- trick %d: %s  t %.2f-%.2f (%.2f s)" % (k + 1, prog, t[a], t[b], dur))
            P("   rendered axis n/m: no same-case shifted pose samples")
            allpass = False
            continue
        un = [bp[a]]
        for i in range(a + 1, measured_end + 1):
            d = bp[i] - bp[i - 1]
            d = (d + 180) % 360 - 180
            un.append(un[-1] + d)
        rend_rot = abs(un[-1] - un[0]) / 360.0
        # 0.04 s rates (every 2-3 frames at 60 fps)
        step = max(1, int(round(0.04 / max(1e-3, (t[b] - t[a]) / max(1, b - a)))))
        rates, rt = [], []
        for i in range(0, len(un) - step, 1):
            rates.append(abs(un[i + step] - un[i]) / (t[a + i + step] - t[a + i]))
            rt.append(t[a + i])
        peak = max(rates) if rates else 0
        # F2 over the program itself (a held final reach while waiting for the web is not rotation time)
        pe = max([i for i in range(a, measured_end + 1) if f(R[i], "flip_rate_dps") != 0.0] or [measured_end])
        mean = abs(un[pe - a] - un[0]) / max(1e-3, t[pe] - t[a])
        # holds: longest run with the rate <= 150 deg/s (rendered), and its shape
        best, bs, cur, cs = 0.0, "", 0.0, None
        for i in range(len(rates)):
            if rates[i] <= 150:
                if cs is None:
                    cs = i
                cur = rt[i] - rt[cs] + 0.04
                if cur > best:
                    best, bs = cur, R[a + cs + len(rates[:0])]["flip_shape"] + "@%.2f" % (rt[cs] - t[a])
            else:
                cs = None
        # ease ratio per 360 deg chunk: peak rate / slowest rate (slowest floored at 20 deg/s)
        eases = []
        start = 0
        for i in range(len(rates)):
            if abs(un[i] - un[start]) >= 330 or i == len(rates) - 1:
                ch = rates[start:i + 1]
                if len(ch) > 5:
                    eases.append(max(ch) / max(20.0, min(ch)))
                start = i
        # twist tilt: body axis from vertical while the twist is turning
        tilt = [bax[i] for i in range(a + 1, measured_end + 1) if bax[i] is not None and abs(f(R[i], "flip_twist_deg") - f(R[i - 1], "flip_twist_deg")) > 0.5]
        # release -> trick start
        rel = None
        for i in range(a, max(-1, a - 120), -1):
            if R[i]["mode"] == "swing" or R[i]["mode"] == "wall":
                rel = t[a] - t[i + 1] if i + 1 < n else None
                break
        # catch: next swing row after the trick
        catch_dt, catch_ax = None, None
        for i in range(b + 1, min(n, b + 90)):
            if not same_case(R[b], R[i]):
                break
            if R[i]["mode"] in ("swing",):
                catch_dt, catch_ax = t[i] - t[b], bax[i]
                break
            if R[i]["mode"] in ("land", "ground", "perch", "wall"):
                catch_dt, catch_ax = None, None
                break
        # leg lag at shape changes
        lags = []
        for i in range(a + 1, b + 1):
            if R[i]["flip_shape"] != R[i - 1]["flip_shape"]:
                for j in range(i, min(b + 1, i + 30)):
                    if R[j]["flip_shape_legs"] == R[i]["flip_shape"]:
                        lags.append(t[j] - t[i])
                        break
        # camera during the trick
        rolls = [abs(f(R[i], "pcm_roll")) for i in range(a, b + 1)]
        camdz = sorted(f(R[i], "cam_z") - f(R[i], "z_m") for i in range(a, b + 1))
        hs = sorted(px_h[i] for i in range(a, b + 1) if px_h[i] > 0)
        q = lambda L, p: L[min(len(L) - 1, int(p * (len(L) - 1)))] if L else float("nan")
        P("-- trick %d: %s  t %.2f-%.2f (%.2f s)" % (k + 1, prog, t[a], t[b], dur))
        if measured_end < b:
            P("   rendered axis limit: final %.4f s sample has no same-case next-row pose; rates measured through %.4f s" % (t[b] - t[measured_end], t[measured_end]))
        P("   F1 rotations: program %.2f, rendered %.2f; twist %.0f deg" % (prog_rot, rend_rot, twist))
        f2 = 300 <= mean <= 500 if prog_rot >= 1.5 else None
        f3 = 450 <= peak <= 800
        f4 = best >= 0.3
        f5 = bool(eases) and min(eases) >= 3
        P("   F2 mean %.0f deg/s %s | F3 peak %.0f deg/s %s | F4 longest hold %.2f s (%s) %s | F5 ease ratio %s %s" % (
            mean, "" if f2 is None else ("PASS" if f2 else "FAIL"), peak, "PASS" if f3 else "FAIL", best, bs, "PASS" if f4 else "FAIL",
            ",".join("%.1f" % e for e in eases), "PASS" if f5 else "FAIL"))
        if twist > 0:
            f7 = twist >= 180 and tilt and 60 <= q(sorted(tilt), 0.5) <= 110
            P("   F7 twist %.0f deg, body tilt while twisting med %.0f deg %s" % (twist, q(sorted(tilt), 0.5) if tilt else -1, "PASS" if f7 else "FAIL"))
        P("   F10 release->trick %s" % ("%.3f s %s" % (rel, "PASS" if rel is not None and rel <= 0.1 else "FAIL") if rel is not None else "n/a (no swing / wall before)"))
        if catch_dt is not None:
            f8 = catch_dt <= 0.25 and (catch_ax is not None and catch_ax <= 30)
            P("   F8 catch %.2f s after the trick, body %.0f deg from upright %s" % (catch_dt, catch_ax, "PASS" if f8 else "FAIL"))
        else:
            P("   F8 no web catch after this trick (landing / end of clip)")
        P("   F11 leg lag at shape changes: %s" % (("mean %.3f s (n=%d) %s" % (sum(lags) / len(lags), len(lags), "PASS" if 0.05 <= sum(lags) / len(lags) <= 0.12 else "FAIL")) if lags else "n/a"))
        f9r = max(rolls) <= 5 if rolls else True
        P("   F9 camera roll max %.1f deg %s | camera - hero height med %.2f m | hero px height p10/p50/p90 %s" % (
            max(rolls) if rolls else 0, "PASS" if f9r else "FAIL", q(camdz, 0.5),
            ("%.3f/%.3f/%.3f %s" % (q(hs, 0.1), q(hs, 0.5), q(hs, 0.9), "PASS" if 0.18 <= q(hs, 0.5) <= 0.36 else "FAIL")) if hs else "n/a (no pixels)"))
        for ok in (f3, f4, f5, f9r):
            allpass = allpass and bool(ok)
    P("SUMMARY %s: %s" % (label, "core lines PASS" if allpass and tricks else "see FAIL lines"))
    print("\n".join(out))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "")
