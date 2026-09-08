"""Separate pedestrian materials in-place via Blender MCP; preserve all geometry/animation.

Top-of-head faces form the hair region because the original asset has no hair shell.
Set HAIR_COLOUR below to choose the initial appearance independently of runtime tinting.
"""
import bpy
import json
import struct
from pathlib import Path

OUT = Path(__file__).resolve().parents[2] / 'Assets' / 'Models'
HAIR_COLOUR = 'Charcoal'
bpy.ops.wm.open_mainfile(filepath=str(OUT / 'pedestrian.blend'))
scene = bpy.context.scene
obj = bpy.data.objects['Pedestrian']
rig = bpy.data.objects['PedestrianRig']
mesh = obj.data
frame = scene.frame_current

def geometry():
    return ([tuple(v.co) for v in mesh.vertices],
            [tuple(p.vertices) for p in mesh.polygons],
            [[(g.group, g.weight) for g in v.groups] for v in mesh.vertices],
            [(b.name, b.parent.name if b.parent else None, tuple(map(tuple, b.matrix_local))) for b in rig.data.bones])

def poses():
    result = []
    for f in range(1, 26):
        scene.frame_set(f)
        result.append([tuple(v.co) for v in obj.evaluated_get(bpy.context.evaluated_depsgraph_get()).data.vertices])
    scene.frame_set(frame)
    return result

def read_glb(path):
    raw = path.read_bytes()
    n = struct.unpack_from('<I', raw, 12)[0]
    return json.loads(raw[20:20+n]), raw[28+n:]

def accessor(g, binary, index):
    a = g['accessors'][index]; view = g['bufferViews'][a['bufferView']]
    count = {'SCALAR':1, 'VEC2':2, 'VEC3':3, 'VEC4':4, 'MAT4':16}[a['type']]
    fmt = '<' + {5126:'f', 5123:'H', 5125:'I', 5121:'B'}[a['componentType']] * count
    offset = view.get('byteOffset', 0) + a.get('byteOffset', 0)
    return [struct.unpack_from(fmt, binary, offset + i * view.get('byteStride', struct.calcsize(fmt))) for i in range(a['count'])]

before = geometry()
before_poses = poses()
old_g, old_bin = read_glb(OUT / 'pedestrian.glb')
assert rig.animation_data.action.name == 'Run'
assert obj.parent == rig and any(m.type == 'ARMATURE' and m.object == rig for m in obj.modifiers)
original = list(mesh.materials)
if [m.name for m in original] == ['Skin', 'Hair', 'Shirt', 'Trousers', 'Shoes', 'Details']:
    materials = original
else:
    assert len(original) == 4
    shirt, trousers, skin, details = original
    shirt.name = 'Shirt'; trousers.name = 'Trousers'; skin.name = 'Skin'; details.name = 'Details'
    hair = (skin if HAIR_COLOUR == 'Skin' else details).copy(); hair.name = 'Hair'
    shoes = details.copy(); shoes.name = 'Shoes'
    assignments = []
    for p in mesh.polygons:
        ys = [mesh.vertices[i].co.y for i in p.vertices]
        if min(ys) >= 1.7499:
            assert p.material_index == 2
            assignments.append(1)
        elif p.material_index == 3 and max(ys) < .14:
            assignments.append(4)
        else:
            assignments.append({0:2, 1:3, 2:0, 3:5}[p.material_index])
    materials = [skin, hair, shirt, trousers, shoes, details]
    mesh.materials.clear()
    for m in materials: mesh.materials.append(m)
    for p, index in zip(mesh.polygons, assignments): p.material_index = index

assert geometry() == before
after_poses = poses()
assert before_poses == after_poses
assert before_poses[0] != before_poses[6]
assert max(abs(a-b) for p,q in zip(after_poses[0],after_poses[-1]) for a,b in zip(p,q)) < 1e-6
counts = {m.name:sum(p.material_index == i for p in mesh.polygons) for i,m in enumerate(materials)}
assert counts['Hair'] == 9 and counts['Shoes'] == 20 and counts['Details'] == 20
for m in materials:
    assert not any(n.type == 'TEX_IMAGE' for n in m.node_tree.nodes)
bpy.ops.object.select_all(action='DESELECT')
obj.select_set(True); rig.select_set(True); bpy.context.view_layer.objects.active = rig
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'pedestrian.blend'))
bpy.ops.export_scene.gltf(filepath=str(OUT / 'pedestrian.glb'), export_format='GLB',
    use_selection=True, export_yup=False, export_animations=True, export_frame_range=True,
    export_force_sampling=True, export_nla_strips=True, export_skins=True,
    export_all_influences=False, export_cameras=False, export_lights=False)
g, binary = read_glb(OUT / 'pedestrian.glb')
assert len(g['skins']) == 1 and len(g['skins'][0]['joints']) == 17
assert [a['name'] for a in g['animations']] == ['Run']
assert g['nodes'] == old_g['nodes']
for new_a, old_a in zip(g['animations'], old_g['animations']):
    assert new_a['channels'] == old_a['channels']
    for ns, os in zip(new_a['samplers'], old_a['samplers']):
        for key in ('input','output'):
            assert accessor(g,binary,ns[key]) == accessor(old_g,old_bin,os[key])
def points(doc, data):
    return {p for m in doc['meshes'] for prim in m['primitives'] for p in accessor(doc,data,prim['attributes']['POSITION'])}
assert points(g,binary) == points(old_g,old_bin)
names = [m['name'] for m in g['materials']]
assert set(names) == {m.name for m in materials}
assert len(g['meshes'][0]['primitives']) == 6
pts = points(g,binary)
report = dict(blend_material_order=[m.name for m in materials], glb_material_order=names,
    polygon_counts=counts, geometry_skinning_skeleton_unchanged=True,
    all_25_run_frames_unchanged=True, exported_animation_unchanged=True,
    dimensions_xyz=[max(p[i] for p in pts)-min(p[i] for p in pts) for i in range(3)],
    minimum_y=min(p[1] for p in pts), axes='+Y up, -Z forward', glb_validation='PASS')
(OUT / 'pedestrian_material_validation.json').write_text(json.dumps(report, indent=2) + '\n')
print('MATERIAL_VALIDATION ' + json.dumps(report))
scene.render.filepath = str(OUT / 'pedestrian_preview.png')
bpy.ops.render.render(write_still=True)
