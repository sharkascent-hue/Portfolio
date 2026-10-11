"""Bake the lit desk (wood, lamp pool, pencil) as one top-down image for the real-time scene.
The plate covers x in [-1.2, 1.2] and y in [-0.8, 0.8] metres around the book hinge."""
import sys, os, math
sys.argv = ['x']
import bpy
import book_scene as B
W, H = 4096, 2731
scene, cam, leaves = B.build(W, H, 48)
keep = {'desk', 'lamp', 'fill', 'pencil', 'pencil_shadow'}
for o in list(bpy.data.objects):
    if o.name not in keep and o.type != 'CAMERA':
        bpy.data.objects.remove(o, do_unlink=True)
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 2.4; cam.data.dof.use_dof = False
cam.location = (0, 0, 3.0); cam.rotation_euler = (0, 0, 0)
scene.render.filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'desk_baked.png')
bpy.ops.render.render(write_still=True)
print('baked', scene.render.filepath)
