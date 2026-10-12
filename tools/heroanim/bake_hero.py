"""Bake Blender Actions onto the original glTF node frames without changing the mesh or bind skeleton."""
import json, math, struct
from pathlib import Path
import bpy
from mathutils import Matrix, Vector, Quaternion

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "public/assets/spiderman.glb"
C = Matrix.Rotation(math.pi / 2, 4, 'X')  # glTF Y-up to Blender Z-up
CI = C.inverted()

def glb():
    raw = SOURCE.read_bytes()
    size = struct.unpack_from('<I', raw, 12)[0]
    doc = json.loads(raw[20:20+size])
    offset = 20 + size
    length = struct.unpack_from('<I', raw, offset)[0]
    return doc, raw[offset+8:offset+8+length]

def trs(node):
    if 'matrix' in node:
        v = node['matrix']
        return Matrix([v[r::4] for r in range(4)])
    x,y,z,w = node.get('rotation', [0,0,0,1])
    return Matrix.LocRotScale(Vector(node.get('translation', [0,0,0])), Quaternion((w,x,y,z)), Vector(node.get('scale', [1,1,1])))

def source_data():
    doc, binary = glb()
    nodes = doc['nodes']
    parents = {c:i for i,n in enumerate(nodes) for c in n.get('children',[])}
    rest = {}
    def world(i):
        if i not in rest:
            rest[i] = (world(parents[i]) if i in parents else Matrix.Identity(4)) @ trs(nodes[i])
        return rest[i]
    for i in range(len(nodes)): world(i)
    return doc,binary,parents,rest

def action(rig, name):
    for track in rig.animation_data.nla_tracks: track.mute = True
    a = bpy.data.actions[name]
    rig.animation_data.action = a
    if len(a.slots): rig.animation_data.action_slot = a.slots[0]
    return a

def frame(t):
    f = t * bpy.context.scene.render.fps / bpy.context.scene.render.fps_base
    bpy.context.scene.frame_set(math.floor(f), subframe=f % 1)
    bpy.context.view_layer.update()

def posed_globals(rig,doc,rest):
    result={}
    for i,node in enumerate(doc['nodes']):
        pb=rig.pose.bones.get(node.get('name',''))
        if pb:
            bind=rig.matrix_world @ pb.bone.matrix_local
            delta=(rig.matrix_world @ pb.matrix) @ bind.inverted()
            result[i]=CI @ delta @ C @ rest[i]
        else: result[i]=rest[i].copy()
    return result

def bake(rig,names,out,fps=60):
    doc,_,parents,rest=source_data()
    joints=doc['skins'][0]['joints']
    clips=[]
    for name in names:
        a=action(rig,name)
        start,end=a.frame_range
        duration=(end-start)/bpy.context.scene.render.fps
        samples=max(1,math.ceil(duration*fps))
        times=[duration*k/samples for k in range(samples+1)]
        tracks=[]
        arrays={i:{'position':[],'quaternion':[],'scale':[]} for i in joints}
        previous={}
        for t in times:
            frame(t+start/bpy.context.scene.render.fps)
            world=posed_globals(rig,doc,rest)
            for i in joints:
                local=(world[parents[i]].inverted() @ world[i]) if i in parents else world[i]
                p,q,s=local.decompose()
                if i in previous and q.dot(previous[i])<0: q.negate()
                previous[i]=q.copy()
                arrays[i]['position'].extend(p)
                arrays[i]['quaternion'].extend((q.x,q.y,q.z,q.w))
                arrays[i]['scale'].extend(s)
        for i in joints:
            # Match THREE.PropertyBinding.sanitizeNodeName, also used by GLTFLoader.
            node=doc['nodes'][i]['name']
            for char in '[] .:/': node=node.replace(char, '_' if char==' ' else '')
            for prop,values in arrays[i].items():
                tracks.append({'name':node+'.'+prop,'type':'quaternion' if prop=='quaternion' else 'vector','times':times,'values':values})
        clips.append({'name':name,'duration':duration,'tracks':tracks,'blendMode':2500})
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps({'source':'Blender hand-authored Actions','fps':fps,'clips':clips},separators=(',',':')))
    return clips

def read_accessor(doc,binary,i):
    a=doc['accessors'][i];v=doc['bufferViews'][a['bufferView']]
    components={'SCALAR':1,'VEC3':3,'VEC4':4}[a['type']]
    assert a['componentType']==5126
    offset=v.get('byteOffset',0)+a.get('byteOffset',0)
    stride=v.get('byteStride',components*4)
    return [struct.unpack_from('<'+'f'*components,binary,offset+k*stride) for k in range(a['count'])]

def reference_world(doc,binary,anim,t,parents):
    nodes=[dict(n) for n in doc['nodes']]
    for channel in anim['channels']:
        sampler=anim['samplers'][channel['sampler']]
        ts=[v[0] for v in read_accessor(doc,binary,sampler['input'])]
        values=read_accessor(doc,binary,sampler['output'])
        assert sampler.get('interpolation','LINEAR') in ('LINEAR','STEP')
        k=0
        while k+1<len(ts) and ts[k+1]<=t:k+=1
        n=min(k+1,len(ts)-1)
        u=0 if ts[n]==ts[k] or sampler.get('interpolation')=='STEP' else max(0,min(1,(t-ts[k])/(ts[n]-ts[k])))
        prop=channel['target']['path']
        if prop=='rotation':
            qa=Quaternion((values[k][3],*values[k][:3]));qb=Quaternion((values[n][3],*values[n][:3]))
            q=qa.slerp(qb,u);value=[q.x,q.y,q.z,q.w]
        else:value=[x+(y-x)*u for x,y in zip(values[k],values[n])]
        nodes[channel['target']['node']][prop]=value
    result={}
    def world(i):
        if i not in result:result[i]=(world(parents[i]) if i in parents else Matrix.Identity(4)) @ trs(nodes[i])
        return result[i]
    for i in range(len(nodes)):world(i)
    return result

def verify_import(rig):
    doc,binary,parents,rest=source_data()
    rows=[]
    for anim in doc['animations']:
        a=action(rig,anim['name'])
        duration=max(read_accessor(doc,binary,s['input'])[-1][0] for s in anim['samplers'])
        error=0;worst=''
        for t in sorted(set(v[0] for sampler in anim['samplers'] for v in read_accessor(doc,binary,sampler['input']))):
            frame(t)
            got=posed_globals(rig,doc,rest)
            want=reference_world(doc,binary,anim,t,parents)
            for i in doc['skins'][0]['joints']:
                e=max(abs(got[i][r][c]-want[i][r][c]) for r in range(4) for c in range(4))
                if e>error:error=e;worst=doc['nodes'][i]['name']
        rows.append({'clip':anim['name'],'duration':duration,'max_world_matrix_error':error,'worst_bone':worst})
    report={'clips':len(rows),'sampling':'every original glTF key timestamp','bones':58,'tolerance':0.0002,'max_error':max(r['max_world_matrix_error'] for r in rows),'results':rows}
    report['passed']=report['max_error']<report['tolerance']
    (ROOT/'docs/anim/hero/import-roundtrip.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({k:v for k,v in report.items() if k!='results'}))
    return report

if __name__=='__main__':
    rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
    bpy.context.scene.render.fps=24  # original import occurred in factory-startup at 24 FPS
    report=verify_import(rig)
    assert report['passed'], 'Import/bind-space conversion failed; do not author against this rig yet'
    bake(rig,['idle','releaseFlip','releaseCorkscrew'],ROOT/'.scratch/roundtrip-clips.json')
    action(rig,'idle');frame(0)
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'art/anim/hero.blend'))
