"""Solve the camera rigs so the book lands where it does in the reference.
Targets are fractions of the frame: x left→right, y top→bottom, w = width of the book's bounding box."""
import sys, math, json
sys.argv = ['x']
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
import book_scene as B

TARGETS = {
    'landscape': {'closed': dict(el=58.0, cx=0.55, cy=0.62, w=0.30), 'open': dict(el=56.0, cx=0.50, cy=0.56, w=0.86)},
    'portrait':  {'closed': dict(el=60.0, cx=0.50, cy=0.60, w=0.82), 'open': dict(el=60.0, cx=0.42, cy=0.57, w=1.70)},
}

def bbox(scene, cam, pts):
    vs = [world_to_camera_view(scene, cam, p) for p in pts]
    xs = [v.x for v in vs]; ys = [1 - v.y for v in vs]
    return min(xs), max(xs), min(ys), max(ys)

out = {}
for orient in ('landscape', 'portrait'):
    B.ORIENT = orient
    w, h = (1280, 720) if orient == 'landscape' else (540, 960)
    scene, cam, leaves = B.build(w, h, 1)
    out[orient] = {}
    for state, frame in (('closed', 0), ('open', B.F_OPEN)):
        B.apply_frame(frame, cam, leaves)
        bpy.context.view_layer.update()
        if state == 'closed':
            ow, od = B.PAGE_W + B.OVER, B.PAGE_D / 2 + B.OVER
            pts = [Vector((x, y, 0.02)) for x in (-0.004, ow) for y in (-od, od)]
        else:
            ow, od = B.PAGE_W + B.OVER, B.PAGE_D / 2 + B.OVER
            pts = [Vector((x, y, 0.02)) for x in (-ow, ow) for y in (-od, od)]
        T = TARGETS[orient][state]
        tgt = Vector((0.0, 0.0, 0.0)); d = 0.8
        for it in range(200):
            B.RIGS[orient][state] = (tgt.copy(), T['el'], d)
            B.place_camera(cam, 0.0 if state == 'closed' else 1.0)
            bpy.context.view_layer.update()
            x0, x1, y0, y1 = bbox(scene, cam, pts)
            cx, cy, bw = (x0 + x1) / 2, (y0 + y1) / 2, x1 - x0
            d *= (bw / T['w']) ** 0.6
            tgt.x += (cx - T['cx']) * d * 0.6
            tgt.y -= (cy - T['cy']) * d * 0.6
        out[orient][state] = dict(t=[round(tgt.x, 4), round(tgt.y, 4)], el=T['el'], d=round(d, 4), got=[round(cx, 3), round(cy, 3), round(bw, 3)])
print(json.dumps(out))
