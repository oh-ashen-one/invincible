#!/usr/bin/env python3
"""Build the PERF.md tables from docs/night1/baseline/perf/*.json (written by playtest.mjs MODE=perf).
   python3 docs/night1/baseline/tools/perf_table.py > /tmp/perf_tables.md"""
import json, glob, os, statistics
base = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
ORDER = ['swingChain', 'street', 'fight', 'water', 'crowd']
rows = []
for f in glob.glob(os.path.join(base, 'perf', '*.json')):
    d = json.load(open(f)); tag = os.path.basename(f)[:-5]
    raw = d['rawFrameTimes']; t = 0; hitch = []
    for x in raw:
        t += x
        if x > 50: hitch.append((round(t / 1000, 1), round(x)))
    rows.append(dict(tag=tag, rep=tag.split('_')[-1] if tag.split('_')[-1] in ('r2', 'r3') else '', d=d, ft=d['frameTimes'], hitch=hitch, raw=raw))
main = [r for r in rows if not r['rep']]
rep = [r for r in rows if r['rep']]
key = lambda r: (-r['d']['W'], r['d']['render']['devicePixelRatio'], ORDER.index(r['d']['name']) if r['d']['name'] in ORDER else 9)
main.sort(key=key)

def buf(r):
    er = r['d'].get('endRender') or {}; ri = r['d']['render']
    b = er.get('drawingBuffer', ri['drawingBuffer']); return f"{b[0]}x{b[1]} ({er.get('pixelRatio', ri['pixelRatio']):g})"

print('| scenario | viewport @DPR | drawing buffer (pixelRatio) | frames | rAF median ms | p95 | p99 | max | >33 ms | >50 ms | >100 ms | rAF fps | GPU ms median / p95 / p99 | external GPU util before launch / mean during | verdict |')
print('|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|')
for r in main:
    d, ft = r['d'], r['ft']; ri = d['render']; g = d['gpuUtil']; q = ft.get('gpuMs')
    gq = f"{q['median']} / {q['p95']} / {q['p99']}" if q else 'n/a'
    print(f"| {d['name']} | {ri['css'][0]}x{ri['css'][1]} @{ri['devicePixelRatio']:g} | {buf(r)} | {ft['frames']} | {ft['median']} | {ft['p95']} | {ft['p99']} | {ft['max']} | {ft['hitches33']} | {ft['hitches50']} | {sum(1 for x in r['raw'] if x > 100)} | {ft['fps']} | {gq} | {g['before']}% / {g['duringMean']}% | {'CONTAMINATED' if d['contaminated'] else 'quiet'} |")
print()
if rep:
    print('Repeat runs of the same scenario at 3840x2160 (run-to-run noise under the shared GPU):')
    print()
    print('| scenario | run | rAF median / p95 ms | GPU ms median / p95 | >33 ms | external GPU util before / mean during |')
    print('|---|---|---|---|---|---|')
    for name in ORDER:
        grp = [r for r in main if r['d']['name'] == name and r['d']['W'] == 3840] + sorted([r for r in rep if r['d']['name'] == name], key=lambda r: r['rep'])
        if len(grp) < 2: continue
        for i, r in enumerate(grp):
            ft, g = r['ft'], r['d']['gpuUtil']; q = ft.get('gpuMs')
            print(f"| {name} | {'r1' if i == 0 else r['rep']} | {ft['median']} / {ft['p95']} | {q['median']} / {q['p95']} | {ft['hitches33']} | {g['before']}% / {g['duringMean']}% |" if q else f"| {name} | {r['rep'] or 'r1'} | {ft['median']} / {ft['p95']} | n/a | {ft['hitches33']} | {g['before']}% / {g['duringMean']}% |")
        meds = [r['ft']['median'] for r in grp]; gm = [r['ft']['gpuMs']['median'] for r in grp if r['ft'].get('gpuMs')]
        print(f"| {name} | spread | rAF median {min(meds)}-{max(meds)} | GPU median {min(gm) if gm else 'n/a'}-{max(gm) if gm else 'n/a'} | | |")
    print()
print('Worst frame gaps (>50 ms) in each run, "seconds since the rAF logger started : ms" (the first one is the scenario start: teleport + streaming):')
for r in main:
    h = sorted(r['hitch'], key=lambda x: -x[1])[:5]; d = r['d']
    print(f"- {r['tag']}: " + (', '.join(f'{a}s:{b}ms' for a, b in h) if h else 'none') + f"  (last frame: {d['gpu']['calls']} draw calls, {d['gpu']['tris']:,} triangles)")
