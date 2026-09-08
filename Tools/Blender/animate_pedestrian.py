"""Add Run to existing pedestrian; render poses and export native Y-up GLB.

Execute through Blender MCP. Does not regenerate geometry or skin weights.
Frames 1..25 at 24 FPS contain one second plus the matching loop endpoint.
"""
import bpy
import math
import json
import struct
from pathlib import Path
from mathutils import Vector, Quaternion, Matrix

OUT = Path(__file__).resolve().parents[2] / 'Assets' / 'Models'
bpy.ops.wm.open_mainfile(filepath=str(OUT / 'pedestrian.blend'))
scene = bpy.context.scene
rig = bpy.data.objects['PedestrianRig']
mesh = bpy.data.objects['Pedestrian']
assert mesh.parent == rig and len(rig.data.bones) == 17
assert any(m.type == 'ARMATURE' and m.object == rig for m in mesh.modifiers)
rig.animation_data_clear()
for a in list(bpy.data.actions):
    if a.name == 'Run': bpy.data.actions.remove(a)
rig.animation_data_create()
action = bpy.data.actions.new('Run'); rig.animation_data.action = action
scene.render.fps = 24; scene.render.fps_base = 1
scene.frame_start = 1; scene.frame_end = 25

def rotate(name, degrees, axis=(1,0,0)):
    pb = rig.pose.bones[name]
    local_axis = pb.bone.matrix_local.to_3x3().inverted() @ Vector(axis)
    pb.rotation_quaternion = Quaternion(local_axis, math.radians(degrees))

def positions():
    return [v.co.copy() for v in mesh.evaluated_get(bpy.context.evaluated_depsgraph_get()).data.vertices]

rest = [v.co.copy() for v in mesh.data.vertices]
for frame in range(1,26):
    scene.frame_set(frame)
    t = 2 * math.pi * (frame-1)/24
    for pb in rig.pose.bones:
        pb.rotation_mode='QUATERNION'; pb.rotation_quaternion=(1,0,0,0)
        pb.location=(0,0,0); pb.scale=(1,1,1)
    rotate('spine', -7)
    rotate('chest', 3*math.sin(t), (0,1,0))
    # Counter-rotation keeps the head facing the travel direction.
    rig.pose.bones['head'].rotation_quaternion = (rig.pose.bones['spine'].rotation_quaternion @ rig.pose.bones['chest'].rotation_quaternion).inverted()
    for side,phase in [('L',t),('R',t+math.pi)]:
        stride=math.cos(phase)
        rotate('upper_leg.'+side, 34*stride+8)
        knee=30+25*math.sin(phase)
        rotate('lower_leg.'+side, -knee)
        rotate('foot.'+side, -(34*stride+8-knee)*.75)
        rotate('upper_arm.'+side, -30*stride-5)
        rotate('lower_arm.'+side, 65+10*math.sin(phase))
    bpy.context.view_layer.update()
    # Ground clearance with two short flight phases; pelvis moves only on Y.
    lowest=min(v.y for v in positions())
    clearance=.004+.045*math.sin(t)**2
    rig.pose.bones['pelvis'].location.y=clearance-lowest
    for pb in rig.pose.bones:
        pb.keyframe_insert(data_path='rotation_quaternion',frame=frame,group=pb.name)
        if pb.name in ('root','pelvis'):
            pb.keyframe_insert(data_path='location',frame=frame,group=pb.name)
for fc in action.fcurves:
    for k in fc.keyframe_points: k.interpolation='LINEAR'
    fc.modifiers.new('CYCLES')
action['loop']=True
action['description']='One-second in-place run. Repeat at playback; frame 25 duplicates frame 1.'
rig['pose']='Run action; unchanged neutral bind pose'

samples=[]; heights=[]; stretches=[]
for f in range(1,26):
    scene.frame_set(f); p=positions(); samples.append(p)
    assert rig.location.length < 1e-7
    assert rig.pose.bones['root'].location.length < 1e-7
    pelvis=rig.pose.bones['pelvis'].location
    assert abs(pelvis.x)+abs(pelvis.z)<1e-7
    assert min(v.y for v in p)>-.001
    heights.append(max(v.y for v in p))
    for e in mesh.data.edges:
        i,j=e.vertices
        ratio=(p[i]-p[j]).length/(rest[i]-rest[j]).length
        assert .15 < ratio < 2.5, (f,ratio)
        stretches.append(ratio)
assert max((a-b).length for a,b in zip(samples[0],samples[-1]))<1e-6
# The root and pelvis have no horizontal displacement at any sampled time.
report={'animation':'Run','frames':[1,25],'fps':24,'seconds':1.0,'bones':17,
        'loop_endpoint_error':max((a-b).length for a,b in zip(samples[0],samples[-1])),
        'height_range':[min(heights),max(heights)],'edge_stretch_range':[min(stretches),max(stretches)],
        'root_translation':0,'pelvis_horizontal_translation':0}
rig['run_validation']=json.dumps(report)
scene.frame_set(1)
bpy.ops.object.select_all(action='DESELECT')
mesh.select_set(True); rig.select_set(True); bpy.context.view_layer.objects.active=rig
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'pedestrian.blend'))
# Native coordinates already satisfy glTF Y-up. Disable Blender's Z-up conversion.
bpy.ops.export_scene.gltf(filepath=str(OUT/'pedestrian.glb'),export_format='GLB',
    use_selection=True,export_yup=False,export_animations=True,export_frame_range=True,
    export_force_sampling=True,export_nla_strips=True,export_skins=True,
    export_all_influences=False,export_cameras=False,export_lights=False)

# Inspect actual exported binary animation accessors, skin and bind geometry.
raw=(OUT/'pedestrian.glb').read_bytes()
assert raw[:4]==b'glTF'
n=struct.unpack_from('<I',raw,12)[0]
g=json.loads(raw[20:20+n]); binary=raw[28+n:]
def accessor(index):
    a=g['accessors'][index]; bv=g['bufferViews'][a['bufferView']]
    count={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']]
    fmt={5126:'f',5123:'H',5125:'I',5121:'B'}[a['componentType']]
    size=struct.calcsize(fmt)*count; offset=bv.get('byteOffset',0)+a.get('byteOffset',0)
    return [struct.unpack_from('<'+fmt*count,binary,offset+i*bv.get('byteStride',size)) for i in range(a['count'])]
assert len(g['animations'])==1 and g['animations'][0]['name']=='Run'
assert len(g['skins'])==1 and len(g['skins'][0]['joints'])==17
anim=g['animations'][0]
durations=[]
for channel in anim['channels']:
    sampler=anim['samplers'][channel['sampler']]
    times=accessor(sampler['input']); vals=accessor(sampler['output'])
    durations.append(times[-1][0]-times[0][0])
    assert max(abs(a-b) for a,b in zip(vals[0],vals[-1]))<1e-5
    node=g['nodes'][channel['target']['node']]
    if channel['target']['path']=='translation':
        if node['name']=='pelvis':
            assert max(v[0] for v in vals)-min(v[0] for v in vals)<1e-6
            assert max(v[2] for v in vals)-min(v[2] for v in vals)<1e-6
        else:
            assert all(max(abs(a-b) for a,b in zip(v,vals[0]))<1e-6 for v in vals)
assert abs(max(durations)-1)<1e-6
points=[p for m in g['meshes'] for prim in m['primitives'] for p in accessor(prim['attributes']['POSITION'])]
dims=[max(p[i] for p in points)-min(p[i] for p in points) for i in range(3)]
assert abs(dims[1]-1.8)<1e-5
assert min(p[1] for p in points)==0
for node in g['nodes']:
    if node.get('name') in ('Pedestrian','PedestrianRig','root'):
        assert all(abs(a-b)<1e-6 for a,b in zip(node.get('rotation',[0,0,0,1]),[0,0,0,1]))
report['glb_dimensions_xyz']=dims; report['glb_validation']='PASS'
print('RUN_VALIDATION '+json.dumps(report))

# Temporary evaluated pose copies make a single four-pose preview, not saved/exported.
mesh.hide_render=True
copies=[]
for f,x in zip([1,7,13,19],[-1.65,-.55,.55,1.65]):
    scene.frame_set(f)
    evaluated=mesh.evaluated_get(bpy.context.evaluated_depsgraph_get())
    data=bpy.data.meshes.new_from_object(evaluated)
    o=bpy.data.objects.new('Preview frame '+str(f),data); scene.collection.objects.link(o)
    o.location.x=x; copies.append(o)
cam=scene.camera; cam.location=(2.5,2.2,-7)
back=(cam.location-Vector((0,.92,0))).normalized()
right=Vector((0,1,0)).cross(back).normalized(); up=back.cross(right)
cam.rotation_euler=Matrix((right,up,back)).transposed().to_euler()
cam.data.ortho_scale=5.3
scene.render.resolution_x=1600; scene.render.resolution_y=720
scene.render.filepath=str(OUT/'pedestrian_run_preview.png')
bpy.ops.render.render(write_still=True)
# All preview-only mutations disappear when the saved source is reopened.
