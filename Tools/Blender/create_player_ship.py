"""Generate the player speeder with Blender 3.3+ (no external dependencies).

Run through Blender MCP run_blender_script for the geometry/save stage only.
For subsequent stages, use run_blender_python with:
    import runpy
    runpy.run_path('Tools/Blender/create_player_ship.py',
                   init_globals={'PLAYER_SHIP_STAGE': 'render'})
Use stage 'inspect' to validate saved geometry and 'export' after preview review.
Each stage loads its own inputs and prints elapsed checkpoints with flush=True.
Use MCP timeout_seconds=45 for build/export, 30 for inspect, and 60 for render.
If a stage times out, inspect player_ship_progress.log before retrying that stage.
Coordinates intentionally match the game: X right, Y up, -Z forward.
GLB export disables Blender's usual Z-up conversion to preserve these axes.
"""
import time
from datetime import datetime, timezone
from pathlib import Path
START = time.perf_counter()
ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / 'Tools' / 'Blender' / 'player_ship_progress.log'

def checkpoint(message):
    line = f'[{datetime.now(timezone.utc).isoformat()} +{time.perf_counter() - START:.3f}s] {message}'
    print(line, flush=True)
    with LOG.open('a', encoding='utf-8') as stream:
        stream.write(line + '\n')

STAGE = globals().get('PLAYER_SHIP_STAGE', 'build')
checkpoint('Python entered; stage=' + STAGE)
import bpy
import bmesh
from mathutils import Matrix, Vector
checkpoint('Blender Python imports complete; version=' + bpy.app.version_string)
OUT = ROOT / 'Assets' / 'Models'
OUT.mkdir(parents=True, exist_ok=True)
TARGET_DIMENSIONS = (2.53, 1.2, 3.8)  # X width, Y height, Z length.

def verify_file(path):
    assert path.is_file() and path.stat().st_size > 0, str(path)
    checkpoint(f'File verified: {path.name}; {path.stat().st_size} bytes')

def validate_glb(path):
    # Check the exported coordinate data without an importer changing its axes.
    import json
    import struct
    raw = path.read_bytes()
    assert struct.unpack_from('<4sII', raw) == (b'glTF', 2, len(raw))
    size, kind = struct.unpack_from('<II', raw, 12)
    assert kind == 0x4E4F534A
    document = json.loads(raw[20:20 + size])
    assert not document.get('cameras') and not document.get('animations')
    assert len(document['meshes']) == 10
    for node in document['nodes']:
        assert not any(key in node for key in ('matrix', 'translation', 'rotation', 'scale'))
    bounds = {}
    for node in document['nodes']:
        if 'mesh' in node:
            primitive = document['meshes'][node['mesh']]['primitives'][0]
            bounds[node['name']] = document['accessors'][primitive['attributes']['POSITION']]
    dimensions = [max(a['max'][i] for a in bounds.values()) -
                  min(a['min'][i] for a in bounds.values()) for i in range(3)]
    assert all(abs(a - b) < 0.001 for a, b in zip(dimensions, TARGET_DIMENSIONS))
    assert bounds['Pointed_Nose']['min'][2] < -1.89
    assert all(bounds['Engine_Glow_' + side]['min'][2] > 1.89
               for side in ('Left', 'Right'))
    checkpoint(f'GLB VERIFIED: dimensions XYZ={dimensions}; -Z forward; asset only')

def validate():
    objects = [obj for obj in bpy.data.collections['Player_Ship'].objects
               if obj.type == 'MESH']
    points = [obj.matrix_world @ vert.co for obj in objects for vert in obj.data.vertices]
    lower = [min(p[i] for p in points) for i in range(3)]
    upper = [max(p[i] for p in points) for i in range(3)]
    dimensions = [upper[i] - lower[i] for i in range(3)]
    for actual, expected in zip(dimensions, TARGET_DIMENSIONS):
        assert abs(actual - expected) < 0.001, (dimensions, expected)
    assert abs(lower[1]) < 0.0001
    assert bpy.data.objects['PlayerShip'].location.length < 0.0001
    assert min(v.co.z for v in bpy.data.objects['Pointed_Nose'].data.vertices) < -1.89
    assert all(v.co.z > 1.89 for side in ('Left', 'Right')
               for v in bpy.data.objects['Engine_Glow_' + side].data.vertices)
    triangles = 0
    for obj in objects:
        obj.data.calc_loop_triangles()
        triangles += len(obj.data.loop_triangles)
        assert all(poly.area > 1e-9 for poly in obj.data.polygons), obj.name
    checkpoint(f'VALIDATED: dimensions XYZ={dimensions}; {len(objects)} meshes; '
               f'{triangles} triangles; {len(bpy.data.materials)} materials')

def saved_stage():
    assert STAGE in {'inspect', 'render', 'export'}, STAGE
    checkpoint('Opening saved blend')
    verify_file(OUT / 'player_ship.blend')
    bpy.ops.wm.open_mainfile(filepath=str(OUT / 'player_ship.blend'))
    checkpoint('Saved blend opened')
    validate()
    if STAGE == 'render':
        checkpoint('Eevee render starting: 512x512, 16 samples')
        bpy.ops.render.render(write_still=True)
        verify_file(OUT / 'player_ship_preview.png')
        checkpoint('Preview PNG saved')
    elif STAGE == 'export':
        bpy.ops.object.select_all(action='DESELECT')
        for obj in bpy.data.collections['Player_Ship'].objects:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = bpy.data.objects['PlayerShip']
        checkpoint('GLB export starting')
        bpy.ops.export_scene.gltf(filepath=str(OUT / 'player_ship.glb'),
            export_format='GLB', use_selection=True, export_yup=False,
            export_cameras=False, export_lights=False, export_animations=False)
        verify_file(OUT / 'player_ship.glb')
        validate_glb(OUT / 'player_ship.glb')
        checkpoint('GLB export complete')
    checkpoint('STAGE COMPLETE: ' + STAGE)

if STAGE != 'build':
    saved_stage()
    # SystemExit exits only this script; Blender then closes normally.
    raise SystemExit(0)

checkpoint('Clearing scene')
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for collection in list(bpy.data.collections):
    bpy.data.collections.remove(collection)
for material in list(bpy.data.materials):
    bpy.data.materials.remove(material)

def material(name, color, metallic=0.0, roughness=0.5, emission=0.0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*color, 1)
    bsdf.inputs['Metallic'].default_value = metallic
    bsdf.inputs['Roughness'].default_value = roughness
    if emission:
        bsdf.inputs['Emission'].default_value = (*color, 1)
        bsdf.inputs['Emission Strength'].default_value = emission
    return mat

body = material('Hull_Light_Blue', (0.24, 0.62, 0.86), 0.25)
dark = material('Cockpit_Dark', (0.012, 0.035, 0.065), 0.35, 0.22)
panel = material('Panels_Slate_Blue', (0.045, 0.12, 0.22), 0.3)
engine = material('Engine_Cyan', (0.015, 0.7, 1.0), 0.1, 0.3, 2.0)
asset = bpy.data.collections.new('Player_Ship')
bpy.context.scene.collection.children.link(asset)
root = bpy.data.objects.new('PlayerShip', None)
asset.objects.link(root)
root['forward_axis'] = '-Z'
root['up_axis'] = '+Y'
root['origin'] = 'centre/bottom; mesh bounds X +/-1.265, Z +/-1.9, Y >=0'
checkpoint('Four materials and asset root created')

def mesh(name, verts, faces, mat):
    data = bpy.data.meshes.new(name)
    # Normalize the original longitudinal stations to a compact 3.8-unit ship.
    data.from_pydata([(x, y * (1.2 / 1.35), z * (3.8 / 34))
                      for x, y, z in verts], [], faces)
    data.materials.append(mat)
    data.update()
    obj = bpy.data.objects.new(name, data)
    asset.objects.link(obj)
    obj.parent = root
    bm = bmesh.new()
    bm.from_mesh(data)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    # Explicit triangles avoid exporter-dependent tessellation of warped quads.
    bmesh.ops.triangulate(bm, faces=list(bm.faces))
    bm.to_mesh(data)
    bm.free()
    data.update()
    checkpoint('Mesh created: ' + name)
    return obj

def hull(name, rings, mat, x=0):
    # Four-corner cross sections keep every silhouette deliberate and low-poly.
    verts = []
    for z, width, bottom, top in rings:
        verts.extend([(x-width, bottom, z), (x+width, bottom, z),
                      (x+width*.82, top, z), (x-width*.82, top, z)])
    faces = [(3, 2, 1, 0)]
    for i in range(len(rings)-1):
        a, b = i*4, (i+1)*4
        faces.extend([(a+j, a+(j+1)%4, b+(j+1)%4, b+j) for j in range(4)])
    faces.append(tuple(range(len(verts)-4, len(verts))))
    return mesh(name, verts, faces, mat)

hull('Tapered_Hull', [(-16,.09,.2,.3),(-7,.43,.05,.65),
                     (4,.62,0,.85),(14,.52,.12,.68),(16,.4,.18,.55)], body)
mesh('Pointed_Nose', [(0,.24,-17),(-.09,.2,-16),(.09,.2,-16),
                     (.0738,.3,-16),(-.0738,.3,-16)],
     [(0,2,1),(0,3,2),(0,4,3),(0,1,4),(1,2,3,4)], body)
hull('Cockpit', [(-3,.22,.58,.65),(0,.32,.7,1.28),
                 (5,.34,.8,1.35),(7,.27,.76,.88)], dark)
hull('Rear_Deck', [(7,.29,.72,.88),(12,.29,.7,.87),(14,.22,.65,.72)], panel)
for side, sign in [('Left',-1),('Right',1)]:
    outline = [(.44,-1), (1.265,9), (1.1,14), (.46,10)]
    verts = [(sign*x,y,z) for y in (.28,.45) for x,z in outline]
    mesh('Swept_Fin_'+side, verts,
         [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)], body)
    hull('Engine_Pod_'+side, [(8,.18,.23,.62),(10,.25,.12,.8),
                            (16.8,.25,.12,.8),(16.98,.2,.2,.7)], panel, sign*.88)
    mesh('Engine_Glow_'+side,
         [(sign*.88-.15,.27,17),(sign*.88+.15,.27,17),
          (sign*.88+.15,.61,17),(sign*.88-.15,.61,17)], [(0,1,2,3)], engine)

scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.eevee.taa_render_samples = 16
scene.eevee.use_gtao = False
scene.eevee.use_bloom = False
scene.eevee.use_soft_shadows = False
scene.render.threads_mode = 'FIXED'
scene.render.threads = 4
scene.world.color = (.09,.09,.09)
scene.view_settings.view_transform = 'Standard'
scene.view_settings.look = 'Medium High Contrast'
scene.view_settings.exposure = 0
scene.view_settings.gamma = 1
scene.render.resolution_x = 512
scene.render.resolution_y = 512
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = str(OUT / 'player_ship_preview.png')
scene.render.film_transparent = False
scene.render.use_compositing = False
scene.render.use_sequencer = False

def aim(obj, target):
    # This asset is Y-up; explicitly avoid Blender's default world Z-up roll.
    backward = (obj.location - Vector(target)).normalized()
    right = Vector((0, 1, 0)).cross(backward).normalized()
    up = backward.cross(right).normalized()
    obj.rotation_euler = Matrix((right, up, backward)).transposed().to_euler()

bpy.ops.object.camera_add(location=(4,4.4,6))
camera = bpy.context.object
camera.name = 'Preview_Camera'
aim(camera, (0,.4,0))
camera.data.type = 'ORTHO'
camera.data.ortho_scale = 5.2
scene.camera = camera
for name, location, power, size in [
    ('Key', (2,5,-3), 550, 5),
    ('Fill',(-3,3,4), 350, 4)]:
    bpy.ops.object.light_add(type='AREA', location=location)
    light = bpy.context.object
    light.name = 'Preview_'+name
    light.data.energy = power
    light.data.size = size
    light.data.use_shadow = False
    aim(light,(0,.4,0))

bpy.ops.object.select_all(action='DESELECT')
for obj in asset.objects:
    obj.select_set(True)
bpy.context.view_layer.objects.active = root
scene['asset_dimensions_xyz'] = list(TARGET_DIMENSIONS)
scene['coordinate_system'] = 'Y up, -Z forward; export_yup=False'
checkpoint('Preview camera and two lights configured')
bpy.context.view_layer.update()
validate()
bpy.context.preferences.filepaths.save_version = 0
checkpoint('Saving blend')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'player_ship.blend'))
verify_file(OUT / 'player_ship.blend')
checkpoint('STAGE COMPLETE: build (no render or export)')
