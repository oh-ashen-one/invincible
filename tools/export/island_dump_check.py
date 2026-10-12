#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.
"""Island piece (A), round 02: check a traversal primitive dump (game run with -WHTravDumpPrims=<csv>, WebTravWorld.cpp round 20) against the
island collision contract ("collision = what is drawn"):

  * every VISIBLE SM_facade__ / SM_roofs__ / SM_detail__ / SM_fireescape__ tile (and SM_facadeLod__, landmarks) is role 'solid', its mesh's body
    setup is CTF_UseComplexAsSimple (ctf 3) and the component is QueryOnly (coll_after 1)
  * no 'far-off' row (far skyline / giant component de-collided by the traversal) inside the M1 region
  * WHBox cubes: role 'box-index', collision off after init (index only)
  * sheds / shed tops / subway entrances (instanced): role 'solid'; signs / streetkit / props: excluded

    python3 tools/export/island_dump_check.py <export_dir> <dump.csv> [--out report.json]

Dump columns: actor,comp,mesh,class,visible,coll_before,coll_after,objtype,ctf,minx..maxz (UE metres),role.
coll: 0 NoCollision, 1 QueryOnly, 2 PhysicsOnly, 3 QueryAndPhysics. ctf: 0 default, 1 simple+complex, 2 simple-as-complex, 3 complex-as-simple."""
import csv, json, os, sys, collections

SOLID_PREFIX = ('SM_facade__', 'SM_roofs__', 'SM_detail__', 'SM_fireescape__')


def main():
    a = sys.argv[1:]
    out = None
    if '--out' in a: i = a.index('--out'); out = a[i + 1]; del a[i:i + 2]
    E, dump = a
    reg = json.load(open(os.path.join(E, 'manifest.json')))['region']   # browser metres: x east, z south -> UE x, y (metres)
    X0, X1, Y0, Y1 = reg['x0'], reg['x1'], reg['z0'], reg['z1']
    rows = list(csv.DictReader(open(dump)))
    roles = collections.Counter(r['role'] for r in rows)
    tiles = collections.Counter(); bad = []
    for r in rows:
        m = r['mesh']
        if not m.startswith(SOLID_PREFIX) or r['visible'] != '1': continue
        kind = m.split('__')[0][3:]
        ok = r['role'] == 'solid' and r['ctf'] == '3' and r['coll_after'] == '1'
        tiles[(kind, ok)] += 1
        if not ok: bad.append({k: r[k] for k in ('actor', 'mesh', 'role', 'ctf', 'coll_before', 'coll_after')})
    def inside(r):
        cx = (float(r['minx']) + float(r['maxx'])) / 2; cy = (float(r['miny']) + float(r['maxy'])) / 2
        return X0 <= cx <= X1 and Y0 <= cy <= Y1
    def overlaps(r):
        return float(r['minx']) < X1 and float(r['maxx']) > X0 and float(r['miny']) < Y1 and float(r['maxy']) > Y0
    far = [r for r in rows if r['role'] == 'far-off']
    far_in = [r for r in far if inside(r)]
    far_ov = [r for r in far if overlaps(r)]
    cubes = [r for r in rows if r['role'] == 'box-index']
    cubes_on = sum(1 for r in cubes if r['coll_after'] != '0')
    sheds = collections.Counter((r['mesh'], r['role'], r['coll_after'], r['ctf']) for r in rows if r['mesh'] in ('SM_shed', 'SM_shedtop', 'SM_subway'))
    solid_ctf = collections.Counter((r['ctf'], r['coll_after']) for r in rows if r['role'] == 'solid')
    solid_no_tris = [r['mesh'] for r in rows if r['role'] == 'solid' and r['ctf'] not in ('3',)]
    excl = collections.Counter(r['mesh'].split('__')[0] for r in rows if r['role'] in ('excluded', 'excluded-ism'))
    rep = {'dump': dump, 'rows': len(rows), 'roles': dict(roles),
           'visible_solid_tiles': {'%s_%s' % (k, 'ok' if ok else 'BAD'): n for (k, ok), n in sorted(tiles.items())}, 'bad_tiles': bad[:50],
           'far_off_rows': len(far), 'far_off_centre_inside_M1': len(far_in), 'far_off_overlapping_M1': len(far_ov),
           'far_off_overlapping_M1_meshes': sorted(set(r['mesh'] for r in far_ov))[:40],
           'whbox_cubes': len(cubes), 'whbox_cubes_with_collision_after_init': cubes_on,
           'sheds_subway': {' / '.join(k): n for k, n in sheds.items()},
           'solid_rows_by_ctf_coll': {'ctf%s_coll%s' % k: n for k, n in solid_ctf.items()},
           'solid_rows_without_complex_ctf': collections.Counter(m.split('__')[0] for m in solid_no_tris).most_common(25),
           'excluded_by_mesh_prefix': excl.most_common(30)}
    rep['pass'] = (not bad and sum(n for (k, ok), n in tiles.items() if ok) > 0 and len(far_in) == 0 and cubes_on == 0)
    if out: json.dump(rep, open(out, 'w'), indent=1)
    print(json.dumps({k: v for k, v in rep.items() if k not in ('bad_tiles',)}, indent=1))


if __name__ == '__main__':
    main()
