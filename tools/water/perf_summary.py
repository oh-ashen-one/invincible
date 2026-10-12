#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.
"""Water GPU cost from tools/perf_ue/run_perf.py runs (-csvGpuStats): water map vs the same view with P1's flat water (_Base).
usage: perf_summary.py <perf dir (one sub-dir per map)> <config, e.g. native100> <out perf.json>
Reported BOTH ways (r03 reconciled rule c): frame delta = GPU frame avg (water) - GPU frame avg (flat base), and the SingleLayerWater pass
alone (absolute); plus SLW depth prepass and the LumenReflections / Basepass / Prepass deltas (water_passes_sum = their sum)."""
import csv, json, os, sys

PAIRS = (('Water_View_RiverLow', 'Water_Perf_RiverLow_Base'), ('Water_Perf_S4', 'Water_Perf_S4_Base'), ('Water_View_RiverSun', 'Water_Perf_RiverSun_Base'))


def stats(d):
    rows = list(csv.DictReader(open(os.path.join(d, 'csv.csv'))))
    def num(x):
        try: return float(x)
        except (TypeError, ValueError): return None
    rows = [r for r in rows if num(r.get('FrameTime')) is not None]   # the CSV profiler repeats the header / metadata at the end
    def m(k):
        v = [num(r.get(k)) for r in rows]; v = [x for x in v if x is not None]
        return sum(v) / len(v) if v else 0.0
    res = json.load(open(os.path.join(d, 'result.json')))
    wp = res.get('wh_perf', {})
    return dict(gpu_avg_ms=wp.get('gpu_avg_ms'), internal='%sx%s' % (wp.get('internal_w'), wp.get('internal_h')), contaminated=res.get('contaminated'),
                SLW=m('GPU/SingleLayerWater'), SLWd=m('GPU/SingleLayerWaterDepthPrepass'), LR=m('GPU/LumenReflections'), BP=m('GPU/Basepass'), PP=m('GPU/Prepass'))


def main():
    P, cfg, out = sys.argv[1:4]
    res = {'_note': 'config %s (3840x2160 output), static camera, exclusive gpu_slot perf lock; frame_delta = water - flat base GPU avg; '
                    'SingleLayerWater = that pass alone (absolute); water_passes_sum = SLW + SLW depth prepass + LumenReflections/Basepass/Prepass deltas' % cfg}
    for w, b in PAIRS:
        dw, db = os.path.join(P, w, cfg), os.path.join(P, b, cfg)
        if not (os.path.exists(os.path.join(dw, 'csv.csv')) and os.path.exists(os.path.join(db, 'csv.csv'))):
            res[w] = {'error': 'missing run'}; continue
        a, z = stats(dw), stats(db)
        r = dict(gpu_avg_ms_water=a['gpu_avg_ms'], gpu_avg_ms_base=z['gpu_avg_ms'], internal=a['internal'],
                 frame_delta=round(a['gpu_avg_ms'] - z['gpu_avg_ms'], 2) if a['gpu_avg_ms'] and z['gpu_avg_ms'] else None,
                 SingleLayerWater=round(a['SLW'], 3), SLW_depth_prepass=round(a['SLWd'], 3), LumenReflections_delta=round(a['LR'] - z['LR'], 3),
                 Basepass_delta=round(a['BP'] - z['BP'], 3), Prepass_delta=round(a['PP'] - z['PP'], 3), contaminated=bool(a['contaminated'] or z['contaminated']))
        r['water_passes_sum'] = round(r['SingleLayerWater'] + r['SLW_depth_prepass'] + r['LumenReflections_delta'] + r['Basepass_delta'] + r['Prepass_delta'], 2)
        res[w] = r
        print('%-22s frame %6.2f / %6.2f  delta %+5.2f  SLW %.2f  SLWd %.2f  LR %+5.2f  sum %.2f  internal %s  contaminated %s'
              % (w, r['gpu_avg_ms_water'], r['gpu_avg_ms_base'], r['frame_delta'], r['SingleLayerWater'], r['SLW_depth_prepass'], r['LumenReflections_delta'],
                 r['water_passes_sum'], r['internal'], r['contaminated']))
    json.dump(res, open(out, 'w'), indent=1)


if __name__ == '__main__':
    main()
