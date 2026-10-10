"""
Offline render of the AlmLab portfolio book.

Builds a desk, a lamp and an 11-leaf hardback whose leaves bend with the same
maths as the web version, then renders a frame sequence:
  closed → cover opens (camera dollies in) → nine page flips → back cover closes.

Usage:
  python book_scene.py --out frames --test            # one open-spread frame at full quality
  python book_scene.py --out frames --start 0 --end 324
  python book_scene.py --out frames --width 1536 --samples 64
"""
import argparse, math, os, sys, time
import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
FACES = os.path.join(HERE, 'faces')
TEX = os.path.join(HERE, 'tex')

# ---------------------------------------------------------------- book geometry (metres)
PAGE_W, PAGE_D = 0.30, 0.16875          # 16:9 leaf, spine → fore edge along +X, depth along Y
LEAF_T = 0.0009                          # leaf thickness
BOARD_T = 0.0025                         # cover board thickness
OVER = 0.004                             # board overhang
SEGS = 48
N_LEAVES = 11                            # cover + 9 work leaves + back cover

# ---------------------------------------------------------------- timeline
F_OPEN = 32                              # cover flip + camera dolly
F_FLIP = 24                              # each page flip
F_CLOSE = 30                             # back cover closes + camera dolly out
SEGMENTS = [('open', F_OPEN)] + [('flip%d' % i, F_FLIP) for i in range(1, 10)] + [('close', F_CLOSE)]
TOTAL = 1 + sum(n for _, n in SEGMENTS)  # frame 0 is the closed book at rest


def ease(t):
    return t * t * (3 - 2 * t) if 0 <= t <= 1 else (0 if t < 0 else 1)


def ease_io(t):
    return 0.5 - 0.5 * math.cos(math.pi * max(0, min(1, t)))


def leaf_state(frame):
    """turn amount (0..1) per leaf and camera blend (0 closed, 1 open) at a frame."""
    turns = [0.0] * N_LEAVES
    cam = 0.0
    f = frame - 1
    if frame == 0:
        return turns, cam
    for idx, (name, n) in enumerate(SEGMENTS):
        if f < n:
            p = f / (n - 1)
            if name == 'open':
                turns[0] = ease_io(p); cam = ease_io(p)
            elif name == 'close':
                for i in range(N_LEAVES - 1): turns[i] = 1.0
                turns[N_LEAVES - 1] = ease_io(p); cam = 1 - ease_io(p)
            else:
                k = int(name[4:])
                for i in range(k): turns[i] = 1.0
                turns[k] = ease_io(p); cam = 1.0
            return turns, cam
        f -= n
        if name == 'open':
            turns[0] = 1.0; cam = 1.0
        elif name.startswith('flip'):
            turns[int(name[4:])] = 1.0
    return turns, cam


# ---------------------------------------------------------------- scene helpers
def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def image(path, non_color=False):
    img = bpy.data.images.load(path, check_existing=True)
    if non_color:
        img.colorspace_settings.name = 'Non-Color'
    return img


def principled_material(name, color_img=None, normal_img=None, roughness=0.5, tint=None, mirror=False, normal_strength=0.5, tex_scale=(1, 1), spec=0.5, emit=0.0, flat_color=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs['Roughness'].default_value = roughness
    if 'Specular IOR Level' in bsdf.inputs:
        bsdf.inputs['Specular IOR Level'].default_value = spec
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    uv = nt.nodes.new('ShaderNodeTexCoord')
    mapping = nt.nodes.new('ShaderNodeMapping')
    mapping.inputs['Scale'].default_value = (tex_scale[0], tex_scale[1], 1)
    if mirror:
        mapping.inputs['Scale'].default_value = (-1, 1, 1); mapping.inputs['Location'].default_value = (1, 0, 0)
    nt.links.new(uv.outputs['UV'], mapping.inputs['Vector'])
    if flat_color is not None:
        bsdf.inputs['Base Color'].default_value = (*flat_color, 1)
    if color_img is not None:
        tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = color_img
        tex.extension = 'REPEAT'
        nt.links.new(mapping.outputs['Vector'], tex.inputs['Vector'])
        col_out = tex.outputs['Color']
        if tint is not None:
            mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'
            mix.inputs['Factor'].default_value = 1.0
            mix.inputs[7].default_value = (*tint, 1)
            nt.links.new(col_out, mix.inputs[6])
            col_out = mix.outputs[2]
        nt.links.new(col_out, bsdf.inputs['Base Color'])
        if emit > 0:
            nt.links.new(col_out, bsdf.inputs['Emission Color'])
            bsdf.inputs['Emission Strength'].default_value = emit
    if normal_img is not None:
        ntex = nt.nodes.new('ShaderNodeTexImage'); ntex.image = normal_img; ntex.extension = 'REPEAT'
        nt.links.new(mapping.outputs['Vector'], ntex.inputs['Vector'])
        nm = nt.nodes.new('ShaderNodeNormalMap'); nm.inputs['Strength'].default_value = normal_strength
        nt.links.new(ntex.outputs['Color'], nm.inputs['Color'])
        nt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
    return m


def procedural_wood():
    """Photo oak for the look, with a fine procedural grain multiplied in for sharpness at any zoom."""
    m = bpy.data.materials.new('wood'); m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    coord = nt.nodes.new('ShaderNodeTexCoord')
    mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (4.5, 4.5, 1)
    nt.links.new(coord.outputs['UV'], mp.inputs['Vector'])
    tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = image(os.path.join(TEX, 'wood.png')); tex.extension = 'REPEAT'
    nt.links.new(mp.outputs['Vector'], tex.inputs['Vector'])
    tint = nt.nodes.new('ShaderNodeMix'); tint.data_type = 'RGBA'; tint.blend_type = 'MULTIPLY'; tint.inputs['Factor'].default_value = 1.0
    tint.inputs[7].default_value = (0.42, 0.39, 0.35, 1)
    nt.links.new(tex.outputs['Color'], tint.inputs[6])
    # fine grain: long thin streaks, multiplied in gently
    mp2 = nt.nodes.new('ShaderNodeMapping'); mp2.inputs['Scale'].default_value = (1.0, 22.0, 1.0)
    nt.links.new(coord.outputs['Object'], mp2.inputs['Vector'])
    grain = nt.nodes.new('ShaderNodeTexNoise'); grain.inputs['Scale'].default_value = 90.0; grain.inputs['Detail'].default_value = 6.0; grain.inputs['Roughness'].default_value = 0.7
    nt.links.new(mp2.outputs['Vector'], grain.inputs['Vector'])
    gr = nt.nodes.new('ShaderNodeMapRange'); gr.inputs['To Min'].default_value = 0.78; gr.inputs['To Max'].default_value = 1.18
    nt.links.new(grain.outputs['Fac'], gr.inputs['Value'])
    mul = nt.nodes.new('ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs['Factor'].default_value = 1.0
    nt.links.new(tint.outputs[2], mul.inputs[6])
    gcol = nt.nodes.new('ShaderNodeCombineColor')
    nt.links.new(gr.outputs['Result'], gcol.inputs[0]); nt.links.new(gr.outputs['Result'], gcol.inputs[1]); nt.links.new(gr.outputs['Result'], gcol.inputs[2])
    nt.links.new(gcol.outputs['Color'], mul.inputs[7])
    nt.links.new(mul.outputs[2], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = 0.46
    if 'Specular IOR Level' in bsdf.inputs: bsdf.inputs['Specular IOR Level'].default_value = 0.35
    # normal map from the photo plus a micro bump from the grain
    ntex = nt.nodes.new('ShaderNodeTexImage'); ntex.image = image(os.path.join(TEX, 'wood_n.png'), True); ntex.extension = 'REPEAT'
    nt.links.new(mp.outputs['Vector'], ntex.inputs['Vector'])
    nm = nt.nodes.new('ShaderNodeNormalMap'); nm.inputs['Strength'].default_value = 0.7
    nt.links.new(ntex.outputs['Color'], nm.inputs['Color'])
    bump = nt.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.08; bump.inputs['Distance'].default_value = 0.0005
    nt.links.new(grain.outputs['Fac'], bump.inputs['Height']); nt.links.new(nm.outputs['Normal'], bump.inputs['Normal'])
    nt.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    return m


def _unused_procedural_wood():
    """Dark stained oak: straight grain with gentle wander, pores, satin finish."""
    m = bpy.data.materials.new('wood'); m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    coord = nt.nodes.new('ShaderNodeTexCoord')
    # stretch along X so bands become long grain lines
    mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (1.0, 14.0, 1.0)
    nt.links.new(coord.outputs['Object'], mp.inputs['Vector'])
    wave = nt.nodes.new('ShaderNodeTexWave')
    wave.wave_type = 'BANDS'; wave.bands_direction = 'Y'
    wave.inputs['Scale'].default_value = 3.2; wave.inputs['Distortion'].default_value = 4.0
    wave.inputs['Detail'].default_value = 12.0; wave.inputs['Detail Scale'].default_value = 2.0; wave.inputs['Detail Roughness'].default_value = 0.6
    nt.links.new(mp.outputs['Vector'], wave.inputs['Vector'])
    # fine pores
    pores = nt.nodes.new('ShaderNodeTexNoise'); pores.inputs['Scale'].default_value = 260.0; pores.inputs['Detail'].default_value = 4.0
    mp2 = nt.nodes.new('ShaderNodeMapping'); mp2.inputs['Scale'].default_value = (1.0, 0.12, 1.0)
    nt.links.new(coord.outputs['Object'], mp2.inputs['Vector']); nt.links.new(mp2.outputs['Vector'], pores.inputs['Vector'])
    mixg = nt.nodes.new('ShaderNodeMix'); mixg.data_type = 'FLOAT'; mixg.inputs['Factor'].default_value = 0.35
    nt.links.new(wave.outputs['Fac'], mixg.inputs[2]); nt.links.new(pores.outputs['Fac'], mixg.inputs[3])
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = 0.0; ramp.color_ramp.elements[0].color = (0.012, 0.0085, 0.006, 1)
    ramp.color_ramp.elements[1].position = 1.0; ramp.color_ramp.elements[1].color = (0.11, 0.075, 0.045, 1)
    e = ramp.color_ramp.elements.new(0.55); e.color = (0.035, 0.024, 0.016, 1)
    nt.links.new(mixg.outputs[0], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])
    # satin finish: a little rougher in the grain
    rr = nt.nodes.new('ShaderNodeMapRange'); rr.inputs['From Min'].default_value = 0; rr.inputs['From Max'].default_value = 1
    rr.inputs['To Min'].default_value = 0.32; rr.inputs['To Max'].default_value = 0.5
    nt.links.new(mixg.outputs[0], rr.inputs['Value']); nt.links.new(rr.outputs['Result'], bsdf.inputs['Roughness'])
    if 'Specular IOR Level' in bsdf.inputs: bsdf.inputs['Specular IOR Level'].default_value = 0.45
    bump = nt.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.12; bump.inputs['Distance'].default_value = 0.0008
    nt.links.new(mixg.outputs[0], bump.inputs['Height']); nt.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    return m


def cutout_material(name, img_path, emit=0.12, rough=0.8):
    """Photo cutout: image colour, image alpha, a little self-light so it reads under the lamp."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    try: m.blend_method = 'HASHED'
    except Exception: pass
    nt = m.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled'); bsdf.inputs['Roughness'].default_value = rough
    tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = image(img_path)
    nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    nt.links.new(tex.outputs['Alpha'], bsdf.inputs['Alpha'])
    if emit:
        nt.links.new(tex.outputs['Color'], bsdf.inputs['Emission Color']); bsdf.inputs['Emission Strength'].default_value = emit
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return m


def shadow_blob_material():
    m = bpy.data.materials.new('blob'); m.use_nodes = True
    try: m.blend_method = 'BLEND'
    except Exception: pass
    nt = m.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    dk = nt.nodes.new('ShaderNodeBsdfDiffuse'); dk.inputs['Color'].default_value = (0, 0, 0, 1)
    mix = nt.nodes.new('ShaderNodeMixShader')
    coord = nt.nodes.new('ShaderNodeTexCoord')
    grad = nt.nodes.new('ShaderNodeTexGradient'); grad.gradient_type = 'SPHERICAL'
    mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Location'].default_value = (-0.5, -0.5, 0)
    nt.links.new(coord.outputs['UV'], mp.inputs['Vector']); nt.links.new(mp.outputs['Vector'], grad.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB'); ramp.color_ramp.elements[0].position = 0.55; ramp.color_ramp.elements[0].color = (0, 0, 0, 1)
    ramp.color_ramp.elements[1].position = 1.0; ramp.color_ramp.elements[1].color = (0.7, 0.7, 0.7, 1)
    nt.links.new(grad.outputs['Fac'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], mix.inputs['Fac'])
    nt.links.new(tr.outputs['BSDF'], mix.inputs[1]); nt.links.new(dk.outputs['BSDF'], mix.inputs[2])
    nt.links.new(mix.outputs['Shader'], out.inputs['Surface'])
    return m


def image_plane(name, mat, w, h, loc, rot, cast_shadow=True):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc)
    o = bpy.context.active_object; o.name = name
    o.scale = (w, h, 1); o.rotation_euler = rot
    o.data.materials.append(mat)
    if not cast_shadow:
        o.visible_shadow = False
    return o


def add_props():
    """The reference desk: plant top-left, coffee top-right, pencil bottom-left, set square bottom-right."""
    blob = shadow_blob_material()
    def standing(name, img, height, x, y, lean=52.0):
        im = bpy.data.images.load(os.path.join(TEX, img), check_existing=True)
        w = height * im.size[0] / im.size[1]
        mat = cutout_material('m_' + name, os.path.join(TEX, img))
        o = image_plane(name, mat, w, height, (x, y, 0), (math.radians(lean), 0, 0), cast_shadow=False)
        o.location.z = math.sin(math.radians(lean)) * height / 2
        o.location.y = y - math.cos(math.radians(lean)) * height / 2
        image_plane(name + '_shadow', blob, w * 1.15, w * 0.6, (x, y + 0.01, 0.0005), (0, 0, 0), cast_shadow=False)
    def flat(name, img, width, x, y, rotz):
        im = bpy.data.images.load(os.path.join(TEX, img), check_existing=True)
        h = width * im.size[1] / im.size[0]
        mat = cutout_material('m_' + name, os.path.join(TEX, img), emit=0.06, rough=0.55)
        image_plane(name, mat, width, h, (x, y, 0.0012), (0, 0, rotz))
        sh = cutout_material('m_' + name + '_sh', os.path.join(TEX, img), emit=0.0)
        sh.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0, 0, 0, 1)
        for l in list(sh.node_tree.links):
            if l.to_socket.name == 'Base Color': sh.node_tree.links.remove(l)
        image_plane(name + '_shadow', sh, width * 1.02, h * 1.04, (x + 0.004, y - 0.006, 0.0006), (0, 0, rotz), cast_shadow=False)
    # just the pencil: a sleek desk, nothing to compete with the book
    flat('pencil', 'pencil.png', 0.19, -0.14, -0.14, math.radians(25))


def box(name, size, loc, mat):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object; o.name = name
    o.scale = (size[0], size[1], size[2])
    o.data.materials.append(mat)
    return o


class Leaf:
    def __init__(self, index, front, back, width, depth, stiff, mats):
        self.index, self.width, self.depth, self.stiff = index, width, depth, stiff
        cols = SEGS + 1
        verts, faces, uvs = [], [], []
        for r in range(2):
            for c in range(cols):
                verts.append((c / SEGS * width, (depth / 2) if r == 0 else (-depth / 2), 0))
        for c in range(SEGS):
            a, b, d, e = c, c + 1, cols + c, cols + c + 1
            faces.append((a, d, e, b))
        me = bpy.data.meshes.new('leaf%d' % index)
        me.from_pydata(verts, [], faces)
        me.update()
        uvl = me.uv_layers.new(name='UVMap')
        for poly in me.polygons:
            for li in poly.loop_indices:
                vi = me.loops[li].vertex_index
                x, y, _ = verts[vi]
                uvl.data[li].uv = (x / width, 0.5 + y / depth)
        for p in me.polygons:
            p.use_smooth = True
        for m in mats: me.materials.append(m)
        self.obj = bpy.data.objects.new('leaf%d' % index, me)
        bpy.context.collection.objects.link(self.obj)
        sol = self.obj.modifiers.new('solid', 'SOLIDIFY')
        sol.thickness = LEAF_T if index not in (0, N_LEAVES - 1) else BOARD_T
        sol.offset = 1.0
        sol.use_even_offset = True
        sol.material_offset = 1
        sol.material_offset_rim = 2
        self.me = me

    def elevation(self, t):
        right = BOARD_T + (N_LEAVES - 1 - self.index) * LEAF_T
        left = BOARD_T + self.index * LEAF_T
        return right + (left - right) * t

    def set_turn(self, t, vel):
        """t 0..1; vel is the signed flip speed used for the trailing curl."""
        theta = math.pi * t
        curl = math.sin(math.pi * t) * self.stiff * max(-1, min(1, vel))
        z0 = self.elevation(t) + 0.0004
        x, z = 0.0, z0
        ds = self.width / SEGS
        cols = SEGS + 1
        for c in range(cols):
            s = c / SEGS
            if c > 0:
                a = theta - curl * (s ** 1.25)
                x += ds * math.cos(a); z += ds * math.sin(a)
            zz = max(z, 0.0003)
            for r in range(2):
                v = self.me.vertices[r * cols + c]
                v.co.x = x; v.co.z = zz
        self.me.update()


def build(width, height, samples):
    clear()
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = samples
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = 0.04
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = 'OPENIMAGEDENOISE'
    scene.cycles.max_bounces = 6
    scene.cycles.caustics_reflective = False
    scene.cycles.caustics_refractive = False
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGB'
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.look = 'AgX - Medium High Contrast'
    scene.view_settings.exposure = 0.0
    scene.render.film_transparent = False
    try:
        scene.render.threads_mode = 'AUTO'
    except Exception:
        pass

    # world: black
    world = bpy.data.worlds.new('w'); scene.world = world; world.use_nodes = True
    bg = world.node_tree.nodes['Background']; bg.inputs[0].default_value = (0, 0, 0, 1); bg.inputs[1].default_value = 0.0

    # desk: procedural dark oak — resolution-independent, no tiling
    wood = procedural_wood()
    bpy.ops.mesh.primitive_plane_add(size=8, location=(0, 0, 0))
    desk = bpy.context.active_object; desk.name = 'desk'; desk.data.materials.append(wood)

    # lamp: a hard spot overhead, a little in front, plus a faint cool fill
    bpy.ops.object.light_add(type='SPOT', location=(0.15, 0.35, 1.7))
    lamp = bpy.context.active_object; lamp.name = 'lamp'
    lamp.data.energy = 640; lamp.data.color = (1.0, 0.93, 0.84)
    lamp.data.spot_size = math.radians(38); lamp.data.spot_blend = 0.9
    lamp.data.shadow_soft_size = 0.34
    lamp.rotation_euler = (math.radians(-11), 0, 0)
    bpy.ops.object.light_add(type='AREA', location=(-1.6, 0.6, 0.9))
    fill = bpy.context.active_object; fill.name = 'fill'
    fill.data.energy = 22; fill.data.size = 2.2; fill.data.color = (0.75, 0.82, 1.0)
    fill.rotation_euler = (math.radians(55), math.radians(-5), math.radians(-60))

    # book materials
    cloth = principled_material('cloth', image(os.path.join(TEX, 'cloth.png')), image(os.path.join(TEX, 'cloth_n.png'), True),
                                roughness=0.62, tint=(0.22, 0.22, 0.22), normal_strength=0.5, tex_scale=(6, 6), spec=0.45)
    face = lambda k: image(os.path.join(FACES, k + '.png'))
    rim = principled_material('rim', None, None, roughness=0.9, flat_color=(0.86, 0.84, 0.78))
    def paper(f, b, name, rough=0.32, emit=0.32):
        return [principled_material(name + '_f', face(f), None, roughness=rough, spec=0.5, emit=emit),
                principled_material(name + '_b', face(b), None, roughness=rough, spec=0.5, emit=emit, mirror=True), rim]

    # boards and spine
    box('backboard', (PAGE_W + OVER, PAGE_D + 2 * OVER, BOARD_T), ((PAGE_W + OVER) / 2, 0, BOARD_T / 2), cloth)
    full = N_LEAVES * LEAF_T + 2 * BOARD_T
    box('spine', (BOARD_T * 1.6, PAGE_D + 2 * OVER, full), (-BOARD_T * 0.6, 0, full / 2), cloth)

    leaves = []
    works = ['work%02d' % i for i in range(1, 19)]
    cov = paper('cover', 'contents', 'm_cover', rough=0.55, emit=0.0)
    cov[1].node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = 0.32
    cov[1].node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.32
    leaves.append(Leaf(0, 'cover', 'contents', PAGE_W + OVER, PAGE_D + 2 * OVER, 0.22, cov))
    for k in range(9):
        leaves.append(Leaf(k + 1, works[2 * k], works[2 * k + 1], PAGE_W, PAGE_D, 0.62, paper(works[2 * k], works[2 * k + 1], 'm_leaf%d' % (k + 1))))
    bk = paper('end', 'coverback', 'm_back', rough=0.32, emit=0.32)
    bk[1].node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = 0.0
    bk[1].node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.55
    leaves.append(Leaf(10, 'end', 'coverback', PAGE_W + OVER, PAGE_D + 2 * OVER, 0.22, bk))

    add_props()

    # camera
    bpy.ops.object.camera_add()
    cam = bpy.context.active_object; cam.name = 'cam'
    cam.data.lens = 40; cam.data.sensor_width = 36
    cam.data.dof.use_dof = True; cam.data.dof.aperture_fstop = 9.0
    scene.camera = cam
    return scene, cam, leaves


# closed and open camera rigs: target, elevation (deg), distance
RIG_CLOSED = (Vector((0.07, 0.05, 0.0)), 43.0, 0.92)
RIG_OPEN = (Vector((0.0, -0.01, 0.0)), 37.0, 0.96)


def place_camera(cam, blend):
    t0, e0, d0 = RIG_CLOSED; t1, e1, d1 = RIG_OPEN
    tgt = t0.lerp(t1, blend); el = math.radians(e0 + (e1 - e0) * blend); d = d0 + (d1 - d0) * blend
    pos = tgt + Vector((0, -math.cos(el) * d, math.sin(el) * d))
    cam.location = pos
    direction = tgt - pos
    cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    cam.data.dof.focus_distance = d


def apply_frame(frame, cam, leaves):
    turns, camb = leaf_state(frame)
    turns_prev, _ = leaf_state(max(0, frame - 1))
    for i, lf in enumerate(leaves):
        vel = (turns[i] - turns_prev[i]) * 10.0
        lf.set_turn(turns[i], vel)
    place_camera(cam, camb)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default='frames')
    ap.add_argument('--width', type=int, default=1536)
    ap.add_argument('--samples', type=int, default=64)
    ap.add_argument('--start', type=int, default=0)
    ap.add_argument('--end', type=int, default=TOTAL - 1)
    ap.add_argument('--test', action='store_true')
    ap.add_argument('--frame', type=int, default=None)
    a = ap.parse_args()
    height = round(a.width * 9 / 16)
    os.makedirs(a.out, exist_ok=True)
    scene, cam, leaves = build(a.width, height, a.samples)
    frames = [a.frame] if a.frame is not None else ([1 + F_OPEN + F_FLIP * 2 + 10] if a.test else list(range(a.start, a.end + 1)))
    print('total frames in sequence:', TOTAL, '| rendering', len(frames), flush=True)
    for f in frames:
        t = time.time()
        apply_frame(f, cam, leaves)
        scene.render.filepath = os.path.join(a.out, 'f%04d.png' % f)
        bpy.ops.render.render(write_still=True)
        print('frame %d done in %.1fs' % (f, time.time() - t), flush=True)


if __name__ == '__main__':
    main()
