"""Generate the Y-up, -Z-forward arcade pedestrian using Blender 3.3+.

Run with Blender MCP run_blender_script from the repository root.
No animation is created. Joint pose probes are restored before saving.
"""
import bpy
import math
import json
from pathlib import Path
from mathutils import Vector, Matrix

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'Assets' / 'Models'
OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for action in list(bpy.data.actions):
    bpy.data.actions.remove(action)

def material(name, color):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*color, 1)
    bsdf.inputs['Roughness'].default_value = .85
    return m

mats = [material('Primary • teal shirt', (.035, .38, .40)),
        material('Secondary • slate trousers', (.12, .17, .24)),
        material('Skin • warm tan', (.64, .36, .20)),
        material('Details • charcoal', (.025, .034, .045))]
verts, faces, face_mats, weights = [], [], [], []
# Chamfered rectangular cross section, in the X/Z plane.
outline = [(-.7,-1),(.7,-1),(1,-.7),(1,.7),(.7,1),(-.7,1),(-1,.7),(-1,-.7)]

def part(rings, mat):
    """Rings are (center XYZ, half width, half depth, bone weight mapping)."""
    start = len(verts)
    for center, w, d, influence in rings:
        for x,z in outline:
            verts.append((center[0]+x*w,center[1],center[2]+z*d))
            weights.append(influence)
    faces.append(tuple(start+i for i in reversed(range(8))))
    face_mats.append(mat)
    for r in range(len(rings)-1):
        for i in range(8):
            a=start+r*8+i; b=start+r*8+(i+1)%8
            faces.append((a,b,b+8,a+8)); face_mats.append(mat)
    faces.append(tuple(start+(len(rings)-1)*8+i for i in range(8)))
    face_mats.append(mat)

def solid(center, size, bone, mat):
    x,y,z=center; w,h,d=size
    part([((x,y-h/2,z),w/2,d/2,{bone:1}),((x,y+h/2,z),w/2,d/2,{bone:1})],mat)

solid((0,.89,0),(.34,.22,.23),'pelvis',1)
part([((0,.98,0),.165,.115,{'spine':1}),
      ((0,1.20,0),.195,.13,{'spine':.4,'chest':.6}),
      ((0,1.43,0),.235,.135,{'chest':1}),
      ((0,1.48,0),.17,.105,{'chest':1})],0)
solid((0,1.505,0),(.12,.10,.13),'head',2)
part([((0,1.55,-.005),.105,.105,{'head':1}),
      ((0,1.59,-.005),.13,.12,{'head':1}),
      ((0,1.75,-.005),.13,.12,{'head':1}),
      ((0,1.80,-.005),.10,.09,{'head':1})],2)
# Nose and small dark eyes make forward direction readable.
solid((0,1.655,-.138),(.055,.052,.055),'head',2)
for x in [-.052,.052]:
    solid((x,1.70,-.127),(.027,.019,.009),'head',3)

for side,s in [('L',1),('R',-1)]:
    ua,la,hand = 'upper_arm.'+side,'lower_arm.'+side,'hand.'+side
    thigh,shin,foot = 'upper_leg.'+side,'lower_leg.'+side,'foot.'+side
    part([((s*.215,1.42,0),.082,.095,{ua:1}),
          ((s*.29,1.24,0),.072,.078,{ua:1})],0)
    part([((s*.286,1.25,0),.060,.066,{ua:1}),
          ((s*.33,1.12,0),.058,.065,{ua:.5,la:.5}),
          ((s*.355,1.055,0),.052,.06,{la:1}),
          ((s*.40,.91,-.01),.045,.05,{la:1})],2)
    solid((s*.413,.855,-.012),(.10,.13,.105),hand,2)
    part([((s*.098,.91,0),.087,.105,{thigh:1}),
          ((s*.105,.59,0),.077,.088,{thigh:1}),
          ((s*.11,.49,-.008),.071,.080,{thigh:.5,shin:.5}),
          ((s*.115,.40,0),.068,.074,{shin:1}),
          ((s*.12,.13,0),.057,.061,{shin:1})],1)
    solid((s*.12,.065,-.05),(.15,.13,.28),foot,3)

mesh=bpy.data.meshes.new('PedestrianGeometry')
mesh.from_pydata(verts,[],faces); mesh.update()
obj=bpy.data.objects.new('Pedestrian',mesh)
bpy.context.collection.objects.link(obj)
for m in mats: mesh.materials.append(m)
for poly,mi in zip(mesh.polygons,face_mats): poly.material_index=mi
bpy.context.view_layer.objects.active=obj; obj.select_set(True)
# Recalculate outward normals for all disconnected shells.
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.normals_make_consistent(inside=False); bpy.ops.object.mode_set(mode='OBJECT')
obj.select_set(False)

arm=bpy.data.armatures.new('PedestrianSkeleton')
rig=bpy.data.objects.new('PedestrianRig',arm); bpy.context.collection.objects.link(rig)
bpy.context.view_layer.objects.active=rig; rig.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
def bone(name,head,tail,parent=None):
    b=arm.edit_bones.new(name); b.head=head; b.tail=tail
    if parent: b.parent=arm.edit_bones[parent]
    b.use_deform=name!='root'
bone('root',(0,0,0),(0,.20,0))
bone('pelvis',(0,.85,0),(0,1.0,0),'root')
bone('spine',(0,1.0,0),(0,1.23,0),'pelvis')
bone('chest',(0,1.23,0),(0,1.49,0),'spine')
bone('head',(0,1.49,0),(0,1.77,0),'chest')
for side,s in [('L',1),('R',-1)]:
    bone('upper_arm.'+side,(s*.215,1.42,0),(s*.33,1.12,0),'chest')
    bone('lower_arm.'+side,(s*.33,1.12,0),(s*.40,.91,-.01),'upper_arm.'+side)
    bone('hand.'+side,(s*.40,.91,-.01),(s*.425,.80,-.012),'lower_arm.'+side)
    bone('upper_leg.'+side,(s*.098,.88,0),(s*.11,.49,-.008),'pelvis')
    bone('lower_leg.'+side,(s*.11,.49,-.008),(s*.12,.13,0),'upper_leg.'+side)
    bone('foot.'+side,(s*.12,.13,0),(s*.12,.065,-.17),'lower_leg.'+side)
bpy.ops.object.mode_set(mode='OBJECT')
rig.show_in_front=True; arm.display_type='OCTAHEDRAL'
obj.parent=rig
mod=obj.modifiers.new('Humanoid skin','ARMATURE'); mod.object=rig
for name in sorted({n for w in weights for n in w}):
    group=obj.vertex_groups.new(name=name)
    for i,w in enumerate(weights):
        if name in w: group.add([i],w[name],'REPLACE')
rig['up_axis']='+Y'; rig['forward_axis']='-Z'
rig['pose']='Neutral A-pose; no animation'
rig['rig_notes']='Root at ground; local bone X bends limbs; blended knee/elbow rings.'

# Validate rest skin and temporary joint probes without creating keyframes.
bpy.context.view_layer.update()
def evaluated_positions():
    evaluated=obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    return [v.co.copy() for v in evaluated.data.vertices]
rest=evaluated_positions()
assert all(abs(sum(w.values())-1)<1e-6 for w in weights)
assert max((p-v.co).length for p,v in zip(rest,mesh.vertices))<1e-5
probes={}
for name in ['lower_arm.L','lower_arm.R','lower_leg.L','lower_leg.R','upper_leg.L','upper_leg.R']:
    pb=rig.pose.bones[name]; pb.rotation_mode='XYZ'; pb.rotation_euler.x=math.radians(45)
    bpy.context.view_layer.update(); posed=evaluated_positions()
    assert all(math.isfinite(c) for p in posed for c in p)
    moved=max((a-b).length for a,b in zip(posed,rest)); assert moved>.02
    # Edges must not tear or explode under a representative joint rotation.
    ratios=[(posed[e.vertices[0]]-posed[e.vertices[1]]).length / (rest[e.vertices[0]]-rest[e.vertices[1]]).length for e in mesh.edges]
    assert max(ratios)<2.5 and min(ratios)>.2
    probes[name]={'max_displacement':round(moved,4),'max_edge_stretch':round(max(ratios),4)}
    pb.rotation_euler=(0,0,0); bpy.context.view_layer.update()
assert max((a-b).length for a,b in zip(evaluated_positions(),rest))<1e-5
mins=[min(v.co[i] for v in mesh.vertices) for i in range(3)]
maxs=[max(v.co[i] for v in mesh.vertices) for i in range(3)]
assert abs(mins[1])<1e-6 and abs(maxs[1]-1.8)<1e-5
assert obj.location.length==0 and rig.location.length==0
assert obj.parent==rig and mod.object==rig and len(bpy.data.actions)==0
mesh.calc_loop_triangles()
report={'dimensions_xyz':[round(b-a,4) for a,b in zip(mins,maxs)],'bounds_min':mins,'bounds_max':maxs,
        'meshes':1,'vertices':len(mesh.vertices),'triangles':len(mesh.loop_triangles),
        'bones':{b.name:b.parent.name if b.parent else None for b in arm.bones},
        'materials':[m.name for m in mats],'pose_probes':probes,'rigging_validation':'PASS'}
rig['validation_report']=json.dumps(report)

# Render helpers live in a separate collection; ground uses the existing dark material.
stage=bpy.data.collections.new('Preview studio'); bpy.context.scene.collection.children.link(stage)
def stage_object(o):
    for c in list(o.users_collection): c.objects.unlink(o)
    stage.objects.link(o)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,-.008,0),rotation=(math.pi/2,0,0))
ground=bpy.context.object; ground.name='Preview ground'; ground.data.materials.append(mats[3]); stage_object(ground)
def aim(o,target):
    backward=(o.location-Vector(target)).normalized()
    right=Vector((0,1,0)).cross(backward).normalized()
    up=backward.cross(right).normalized()
    o.rotation_euler=Matrix((right,up,backward)).transposed().to_euler()
bpy.ops.object.camera_add(location=(2.8,2.1,-4.8))
cam=bpy.context.object; cam.name='Preview camera'; aim(cam,(0,.92,0)); cam.data.type='ORTHO'; cam.data.ortho_scale=2.35; stage_object(cam)
scene=bpy.context.scene; scene.camera=cam
for name,loc,power,size in [('Key',(-3,5,-4),450,4),('Fill',(3,2,-2),220,3),('Rim',(0,3,3),500,3)]:
    bpy.ops.object.light_add(type='AREA',location=loc); light=bpy.context.object; light.name=name
    light.data.energy=power; light.data.shape='DISK'; light.data.size=size; aim(light,(0,1,0)); stage_object(light)
scene.render.engine='BLENDER_EEVEE'; scene.eevee.use_gtao=True; scene.eevee.gtao_distance=3
scene.world.color=(.18,.18,.18)
scene.view_settings.view_transform='Standard'; scene.view_settings.look='Medium High Contrast'
scene.render.resolution_x=800; scene.render.resolution_y=900; scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'; scene.render.filepath=str(OUT/'pedestrian_preview.png')
scene['asset_axes']='Native +Y up, -Z forward; dimensions measured in scene coordinates'
bpy.ops.object.select_all(action='DESELECT'); rig.select_set(True); obj.select_set(True); bpy.context.view_layer.objects.active=rig
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'pedestrian.blend'))
bpy.ops.render.render(write_still=True)
print('PEDESTRIAN_VALIDATION '+json.dumps(report))
