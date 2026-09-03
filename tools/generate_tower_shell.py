#!/usr/bin/env python3
"""Generate the tower room shell as USD, straight from the design-doc dimensions.

The shell is a cylinder, a cone and a disc — trivial geometry that no purchased
asset would match. Regenerating is cheaper than remodelling, so treat the output
as build output: edit THIS file, never TowerShell.usda.

Compose on top of it in Reality Composer Pro via Tower.usda, which references
this and is safe to hand-edit.

    python3 tools/generate_tower_shell.py
"""
import math
import os
from pathlib import Path

# ── Dimensions (docs/design/design-doc.md) ───────────────────────────────────
FT = 0.3048            # because the room was specified in feet

DIAMETER      = 8.8           # m, internal (28.9 ft) — was 5.5, widened 60%
WALL_HEIGHT   = 18.0 * FT     # 5.49 m, floor to eaves
# 45-degree roof pitch: the cone rises by the radius, so it reads as a tower cap
# rather than a shallow lid. Apex ends up ~27 ft off the floor.
APEX_HEIGHT   = WALL_HEIGHT + DIAMETER / 2.0
SEGMENTS      = 96     # around the circle

# visionOS puts the user at the origin looking down -Z, so the room is authored in
# USER-RELATIVE space: origin = your seat, -Z = the desk you face, +X = your right.
WINDOW_CENTRE = 55.0   # degrees; 0=desk(front), +ve=toward your right
FIRE_CENTRE   = -55.0  # mirrored, to your left
WINDOW_WIDTH  = 1.30   # m, along the arc
WINDOW_SILL   = 0.40   # m
WINDOW_HEAD   = 3.60   # m — raised with the wall; a 2.6 m head looked stubby at 18 ft

# Roof structure. Radiating rafters were tried and cut — they read as a busy
# starburst from below and fought the calm the room wants.
PLATE_H       = 0.28   # m, wall plate height where the cone lands on the stone
PLATE_D       = 0.22   # m, how far it projects into the room
BEAM_TINT     = (0.26, 0.19, 0.13)   # dark timber

DESK_W, DESK_D, DESK_H = 1.83, 0.91, 0.75   # 6ft x 3ft
ENVELOPE_W, ENVELOPE_D = 2.70, 3.00          # real clear floor
SEAT_SETBACK  = 0.30   # m you sit back from the desk edge

# Wall look. Tint multiplies the albedo, so darkness and warmth can be dialled without
# re-downloading a texture: (1,1,1) is untouched, lower = darker, blue-biased = cooler.
WALL_TEXTURE  = os.environ.get("TOWER_WALL_TEX", "wall")
# The wall diffuse is desaturated on download (see tools/fetch_assets.sh), so this
# only darkens and cools. Override to taste, e.g.
#   TOWER_WALL_TINT=0.5,0.6,0.85 python3 tools/generate_tower_shell.py
WALL_TINT     = tuple(float(v) for v in
                      os.environ.get("TOWER_WALL_TINT", "0.58,0.68,0.88").split(","))
OUT_NAME      = os.environ.get("TOWER_OUT", "TowerShell.usda")

OUT = (Path(__file__).parent.parent
       / "app/Packages/RealityKitContent/Sources/RealityKitContent/RealityKitContent.rkassets"
       / OUT_NAME)

R = DIAMETER / 2.0


# Room-space seat position: desk sits against the wall at theta=0 (-Z), you sit just
# behind its front edge. Everything is then shifted so the seat lands on the origin.
SEAT_Z = -(R - DESK_D - 0.05) + SEAT_SETBACK


def p(theta_deg, y):
    """Point on the wall circle, already shifted into user-relative space.

    theta 0 = straight ahead (the desk), +ve = toward your right.
    """
    t = math.radians(theta_deg)
    return (R * math.sin(t), y, -R * math.cos(t) - SEAT_Z)


TILE = 2.0  # metres per texture repeat, so texel density is uniform everywhere


class Mesh:
    def __init__(self, name, color, texture=None, tint=(1.0, 1.0, 1.0)):
        self.name, self.color, self.texture, self.tint = name, color, texture, tint
        self.pts, self.counts, self.idx, self.normals, self.uvs = [], [], [], [], []

    def face(self, verts, normal, uvs=None):
        """normal may be one vector for the whole face, or one per vertex for
        smooth shading across a curved surface."""
        base = len(self.pts)
        self.pts.extend(verts)
        if isinstance(normal, list):
            self.normals.extend(normal)
        else:
            self.normals.extend([normal] * len(verts))
        if uvs is None:
            # Planar fallback: project onto whichever plane the face least faces.
            ax, ay, az = abs(normal[0]), abs(normal[1]), abs(normal[2])
            if ay >= ax and ay >= az:
                uvs = [(v[0] / TILE, v[2] / TILE) for v in verts]
            elif ax >= az:
                uvs = [(v[2] / TILE, v[1] / TILE) for v in verts]
            else:
                uvs = [(v[0] / TILE, v[1] / TILE) for v in verts]
        self.uvs.extend(uvs)
        self.counts.append(len(verts))
        self.idx.extend(range(base, base + len(verts)))

    def material_usda(self, indent="    "):
        if self.texture:
            return self._textured_material(indent)
        return self._flat_material(indent)

    def _textured_material(self, indent):
        i, n, t = indent, self.name, self.texture
        tr, tg, tb = self.tint
        base = f"</TowerShell/{n}Mat"
        return f'''{i}def Material "{n}Mat"
{i}{{
{i}    token outputs:surface.connect = {base}/Surface.outputs:surface>
{i}    def Shader "stReader"
{i}    {{
{i}        uniform token info:id = "UsdPrimvarReader_float2"
{i}        token inputs:varname = "st"
{i}        float2 outputs:result
{i}    }}
{i}    def Shader "diffuseTex"
{i}    {{
{i}        uniform token info:id = "UsdUVTexture"
{i}        asset inputs:file = @textures/{t}_diff.jpg@
{i}        float2 inputs:st.connect = {base}/stReader.outputs:result>
{i}        token inputs:wrapS = "repeat"
{i}        token inputs:wrapT = "repeat"
{i}        float4 inputs:scale = ({tr}, {tg}, {tb}, 1)
{i}        float3 outputs:rgb
{i}    }}
{i}    def Shader "normalTex"
{i}    {{
{i}        uniform token info:id = "UsdUVTexture"
{i}        asset inputs:file = @textures/{t}_nor.jpg@
{i}        float2 inputs:st.connect = {base}/stReader.outputs:result>
{i}        token inputs:wrapS = "repeat"
{i}        token inputs:wrapT = "repeat"
{i}        token inputs:sourceColorSpace = "raw"
{i}        float4 inputs:scale = (2, 2, 2, 1)
{i}        float4 inputs:bias = (-1, -1, -1, 0)
{i}        float3 outputs:rgb
{i}    }}
{i}    def Shader "roughTex"
{i}    {{
{i}        uniform token info:id = "UsdUVTexture"
{i}        asset inputs:file = @textures/{t}_rough.jpg@
{i}        float2 inputs:st.connect = {base}/stReader.outputs:result>
{i}        token inputs:wrapS = "repeat"
{i}        token inputs:wrapT = "repeat"
{i}        token inputs:sourceColorSpace = "raw"
{i}        float outputs:r
{i}    }}
{i}    def Shader "Surface"
{i}    {{
{i}        uniform token info:id = "UsdPreviewSurface"
{i}        color3f inputs:diffuseColor.connect = {base}/diffuseTex.outputs:rgb>
{i}        normal3f inputs:normal.connect = {base}/normalTex.outputs:rgb>
{i}        float inputs:roughness.connect = {base}/roughTex.outputs:r>
{i}        float inputs:metallic = 0
{i}        token outputs:surface
{i}    }}
{i}}}
'''

    def _flat_material(self, indent):
        """Low emissive floor so nothing is pure black; real light comes from the scene."""
        r, g, b = self.color
        i = indent
        return f'''{i}def Material "{self.name}Mat"
{i}{{
{i}    token outputs:surface.connect = </TowerShell/{self.name}Mat/Surface.outputs:surface>
{i}    def Shader "Surface"
{i}    {{
{i}        uniform token info:id = "UsdPreviewSurface"
{i}        color3f inputs:diffuseColor = ({r}, {g}, {b})
{i}        color3f inputs:emissiveColor = ({r * 0.10:.4f}, {g * 0.10:.4f}, {b * 0.10:.4f})
{i}        float inputs:metallic = 0
{i}        float inputs:roughness = 0.9
{i}        token outputs:surface
{i}    }}
{i}}}
'''

    def usda(self, indent="    "):
        if not self.pts:
            return ""
        xs = [v[0] for v in self.pts]; ys = [v[1] for v in self.pts]; zs = [v[2] for v in self.pts]
        f = lambda seq: ", ".join(f"({a:.4f}, {b:.4f}, {c:.4f})" for a, b, c in seq)
        i = indent
        return f'''{i}def Mesh "{self.name}"
{i}{{
{i}    uniform bool doubleSided = 1
{i}    float3[] extent = [({min(xs):.4f}, {min(ys):.4f}, {min(zs):.4f}), ({max(xs):.4f}, {max(ys):.4f}, {max(zs):.4f})]
{i}    int[] faceVertexCounts = [{", ".join(map(str, self.counts))}]
{i}    int[] faceVertexIndices = [{", ".join(map(str, self.idx))}]
{i}    point3f[] points = [{f(self.pts)}]
{i}    normal3f[] normals = [{f(self.normals)}] (interpolation = "vertex")
{i}    texCoord2f[] primvars:st = [{", ".join(f"({u:.4f}, {v:.4f})" for u, v in self.uvs)}] (
{i}        interpolation = "vertex"
{i}    )
{i}    color3f[] primvars:displayColor = [({self.color[0]}, {self.color[1]}, {self.color[2]})]
{i}    rel material:binding = </TowerShell/{self.name}Mat>
{i}    uniform token subdivisionScheme = "none"
{i}}}
'''


def build():
    half = math.degrees(WINDOW_WIDTH / 2.0 / R)
    w0, w1 = WINDOW_CENTRE - half, WINDOW_CENTRE + half

    floor = Mesh("Floor", (0.28, 0.26, 0.24), texture="floor")
    wall  = Mesh("Wall",  (0.46, 0.44, 0.41), texture=WALL_TEXTURE, tint=WALL_TINT)
    roof  = Mesh("Roof",  (0.20, 0.16, 0.13), texture="roof")

    # Slope length of the cone, for roof UVs that don't stretch.
    slope = math.hypot(R, APEX_HEIGHT - WALL_HEIGHT)

    # The texture has to meet itself where it wraps, so the repeat count round the
    # circumference must be a whole number. Nudge the tile size to the nearest fit
    # rather than leaving a seam.
    circumference = 2.0 * math.pi * R
    wrap_repeats = max(1, round(circumference / TILE))
    print(f"  wall wraps {wrap_repeats}x ({circumference / wrap_repeats:.3f} m/tile, "
          f"nudged from {TILE:.2f})")

    def arc_u(theta_deg):
        """U along the circumference, in whole repeats so the seam closes."""
        return theta_deg / 360.0 * wrap_repeats

    step = 360.0 / SEGMENTS
    for s in range(SEGMENTS):
        a, b = s * step, (s + 1) * step
        mid = (a + b) / 2.0

        # Floor fan (centre of the room, not the seat) — planar XZ UVs
        fa, fb, fc = (0.0, 0.0, -SEAT_Z), p(a, 0.0), p(b, 0.0)
        floor.face([fa, fb, fc], (0.0, 1.0, 0.0),
                   [(v[0] / TILE, v[2] / TILE) for v in (fa, fb, fc)])

        # Inward-facing wall normal
        t = math.radians(mid)
        n = (-math.sin(t), 0.0, -math.cos(t))

        in_window = (w0 <= mid <= w1)
        # Cylindrical UVs: u follows the circumference, v is height. No stretching.
        ua, ub = arc_u(a), arc_u(b)
        if in_window:
            # Below the sill and above the head; the gap is the opening.
            for lo, hi in ((0.0, WINDOW_SILL), (WINDOW_HEAD, WALL_HEIGHT)):
                wall.face([p(a, lo), p(b, lo), p(b, hi), p(a, hi)], n,
                          [(ua, lo / TILE), (ub, lo / TILE), (ub, hi / TILE), (ua, hi / TILE)])
        else:
            wall.face([p(a, 0.0), p(b, 0.0), p(b, WALL_HEIGHT), p(a, WALL_HEIGHT)], n,
                      [(ua, 0.0), (ub, 0.0), (ub, WALL_HEIGHT / TILE), (ua, WALL_HEIGHT / TILE)])

        # Cone to the apex
        # Conical UVs: u round the eaves, v up the slope to the apex.
        roof.face([p(a, WALL_HEIGHT), p(b, WALL_HEIGHT), (0.0, APEX_HEIGHT, -SEAT_Z)],
                  (-math.sin(t) * 0.5, -0.5, -math.cos(t) * 0.5),
                  [(ua, 0.0), (ub, 0.0), ((ua + ub) / 2.0, slope / TILE)])

    parts = [floor, wall, roof]
    body = "".join(m.material_usda() + m.usda() for m in parts)
    return floor, body


def box(name, w, h, d, pos, color):
    x, y, z = pos
    hw, hd = w / 2.0, d / 2.0
    v = [(x-hw, y, z-hd), (x+hw, y, z-hd), (x+hw, y, z+hd), (x-hw, y, z+hd),
         (x-hw, y+h, z-hd), (x+hw, y+h, z-hd), (x+hw, y+h, z+hd), (x-hw, y+h, z+hd)]
    m = Mesh(name, color)
    faces = [((0,1,2,3),(0,-1,0)), ((4,7,6,5),(0,1,0)), ((0,4,5,1),(0,0,-1)),
             ((3,2,6,7),(0,0,1)), ((0,3,7,4),(-1,0,0)), ((1,5,6,2),(1,0,0))]
    for ids, n in faces:
        m.face([v[i] for i in ids], n)
    return m.material_usda() + m.usda()


def prism(mesh, start, end, width, depth, tangent):
    """A rectangular beam running from start to end, boxed around that axis."""
    ax = [e - s for e, s in zip(end, start)]
    L = math.sqrt(sum(c * c for c in ax)) or 1.0
    ax = [c / L for c in ax]
    # tangent is already perpendicular to the axis; third completes the frame
    third = (ax[1] * tangent[2] - ax[2] * tangent[1],
             ax[2] * tangent[0] - ax[0] * tangent[2],
             ax[0] * tangent[1] - ax[1] * tangent[0])
    hw, hd = width / 2.0, depth / 2.0

    def corner(base, sw, sd):
        return tuple(base[k] + sw * hw * tangent[k] + sd * hd * third[k] for k in range(3))

    a = [corner(start, sw, sd) for sw, sd in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    b = [corner(end, sw, sd) for sw, sd in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    quads = [(a[0], a[1], a[2], a[3]), (b[3], b[2], b[1], b[0]),
             (a[0], a[3], b[3], b[0]), (a[1], b[1], b[2], a[2]),
             (a[0], b[0], b[1], a[1]), (a[3], a[2], b[2], b[3])]
    for q in quads:
        e1 = [q[1][k] - q[0][k] for k in range(3)]
        e2 = [q[2][k] - q[0][k] for k in range(3)]
        nrm = (e1[1] * e2[2] - e1[2] * e2[1],
               e1[2] * e2[0] - e1[0] * e2[2],
               e1[0] * e2[1] - e1[1] * e2[0])
        ln = math.sqrt(sum(c * c for c in nrm)) or 1.0
        mesh.face(list(q), tuple(c / ln for c in nrm))


def roof_structure():
    """Wall plate where the cone lands, and a boss at the apex for the lantern.

    The plate is a single continuous ring. Built as a row of separate boxes it
    showed the end cap of every segment as a thin line, with wedge gaps between
    them — a continuous strip shares its vertices, so there is nothing to see.
    """
    m = Mesh("RoofTrim", (0.30, 0.24, 0.18), texture="roof", tint=BEAM_TINT)

    steps = 96
    y_top = WALL_HEIGHT            # flush with the eaves, so no stone shows through
    y_bot = WALL_HEIGHT - PLATE_H
    r_in = R - PLATE_D

    def ring_pt(t, radius, y):
        return (radius * math.sin(t), y, -radius * math.cos(t) - SEAT_Z)

    circumference = 2.0 * math.pi * r_in
    wraps = max(1, round(circumference / TILE))

    def inward_at(t):
        return (-math.sin(t), 0.0, math.cos(t))

    for i in range(steps):
        t0 = i * 2.0 * math.pi / steps
        t1 = (i + 1) * 2.0 * math.pi / steps
        u0, u1 = i / steps * wraps, (i + 1) / steps * wraps
        n0, n1 = inward_at(t0), inward_at(t1)

        # Face onto the room. Per-vertex normals so the ring reads as curved
        # rather than as a run of flat facets.
        m.face([ring_pt(t0, r_in, y_bot), ring_pt(t1, r_in, y_bot),
                ring_pt(t1, r_in, y_top), ring_pt(t0, r_in, y_top)],
               [n0, n1, n1, n0],
               [(u0, 0.0), (u1, 0.0), (u1, PLATE_H / TILE), (u0, PLATE_H / TILE)])
        # Underside
        m.face([ring_pt(t0, R, y_bot), ring_pt(t1, R, y_bot),
                ring_pt(t1, r_in, y_bot), ring_pt(t0, r_in, y_bot)],
               (0.0, -1.0, 0.0),
               [(u0, 0.0), (u1, 0.0), (u1, PLATE_D / TILE), (u0, PLATE_D / TILE)])

    # Apex boss — the lantern hangs from this.
    prism(m, (0.0, APEX_HEIGHT - 0.10, -SEAT_Z), (0.0, APEX_HEIGHT - 0.85, -SEAT_Z),
          0.26, 0.26, (1.0, 0.0, 0.0))
    return m.material_usda() + m.usda()


def main():
    floor, shell = build()

    # All positions are user-relative: you are at (0, 0, 0), facing -Z.
    desk_z = -(R - DESK_D / 2.0 - 0.05) - SEAT_Z
    desk = box("DeskBlock", DESK_W, DESK_H, DESK_D,
               (0.0, 0.0, desk_z), (0.32, 0.22, 0.14))

    # Reference figure stood in the pacing area, so scale can be judged at a glance.
    human = box("HumanReference_1m7", 0.45, 1.70, 0.25,
                (0.0, 0.0, 1.80), (0.85, 0.35, 0.35))

    # Your real clear floor, laid on the virtual one. Behind you, starting at the chair.
    envelope = box("WalkableEnvelope", ENVELOPE_W, 0.01, ENVELOPE_D,
                   (0.0, 0.0, 0.35 + ENVELOPE_D / 2.0), (0.25, 0.55, 0.35))

    # Fireplace marker, to your left, level with the window.
    ft = math.radians(FIRE_CENTRE)
    fire = box("FireplaceMarker", 1.20, 1.40, 0.40,
               ((R - 0.2) * math.sin(ft), 0.0, -(R - 0.2) * math.cos(ft) - SEAT_Z),
               (0.55, 0.25, 0.15))

    beams = roof_structure()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(f'''#usda 1.0
(
    defaultPrim = "TowerShell"
    metersPerUnit = 1
    upAxis = "Y"
)

# GENERATED by tools/generate_tower_shell.py — do not hand-edit.
# {DIAMETER} m across, {WALL_HEIGHT} m to eaves, {APEX_HEIGHT} m apex.
# Window {WINDOW_WIDTH} m wide at {WINDOW_CENTRE}deg (your right), {WINDOW_SILL}-{WINDOW_HEAD} m.
# Authored user-relative: origin = your seat, -Z = the desk, +X = your right.

def Xform "TowerShell"
{{
{shell}{beams}{desk}{fire}{human}{envelope}}}
''')
    print(f"wrote {OUT.relative_to(Path(__file__).parent.parent)}")
    print(f"  {DIAMETER} m across ({DIAMETER / FT:.1f} ft)")
    print(f"  eaves {WALL_HEIGHT:.2f} m ({WALL_HEIGHT / FT:.1f} ft), "
          f"apex {APEX_HEIGHT:.2f} m ({APEX_HEIGHT / FT:.1f} ft)")
    print(f"  window {WINDOW_WIDTH} m wide at {WINDOW_CENTRE}deg (right), {WINDOW_SILL}-{WINDOW_HEAD} m")
    print(f"  origin = seat; desk edge {abs(desk_z) - DESK_D / 2.0:.2f} m ahead")
    print(f"  wall ahead {R + SEAT_Z:.2f} m, room behind you {R - SEAT_Z:.2f} m")
    print(f"  roof: wall plate + apex boss (no rafters)")


if __name__ == "__main__":
    main()
