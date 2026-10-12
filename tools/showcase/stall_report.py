#!/usr/bin/env python3
"""one-line streaming-stall summary of a perf run dir: window stats (frames, p50/p95/p99/max, >33.3 / >50 ms), 'Waiting for static meshes' and distance-field build log counts
usage: stall_report.py <run dir> [--name route]"""
import csv, json, re, sys
from pathlib import Path
import numpy as np
d = Path(sys.argv[1]); name = sys.argv[sys.argv.index('--name') + 1] if '--name' in sys.argv else 'route'
rows = list(csv.DictReader((d / f'{name}_frames.csv').open())); ms = np.array([float(r['frame_ms']) for r in rows]); gpu = np.array([float(r['gpu_ms']) for r in rows])
log = (d / f'{name}.log').read_text(errors='replace')
tel = list(csv.DictReader((d / f'{name}_telemetry.csv').open())) if (d / f'{name}_telemetry.csv').exists() else []
print(json.dumps({'run': d.name, 'frames': int(ms.size), 'p50': round(float(np.percentile(ms, 50)), 1), 'p95': round(float(np.percentile(ms, 95)), 1), 'p99': round(float(np.percentile(ms, 99)), 1), 'max': round(float(ms.max()), 1),
                  'gpu_avg': round(float(gpu.mean()), 1), 'gpu_p95': round(float(np.percentile(gpu, 95)), 1), 'over33': int((ms > 33.3).sum()), 'over50': int((ms > 50).sum()), 'over500': int((ms > 500).sum()),
                  'waiting_for_static_meshes_lines': len(re.findall(r'Waiting for static meshes to be ready', log)), 'waiting_on_static_mesh_lines': len(re.findall(r'Waiting on static mesh', log)),
                  'distance_field_builds': len(re.findall(r'Finished distance field build', log)), 'stream_plus_level': len(re.findall(r'WH_TRAV stream \+level', log)),
                  'sim_t_end': float(tel[-1]['t']) if tel else None, 'y_end_m': float(tel[-1]['y_m']) if tel else None}))
