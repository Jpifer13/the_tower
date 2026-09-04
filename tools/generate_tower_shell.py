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
WINDOW_WIDTH  = 2.00   # m, along the arc — widened with the room to hold its 27deg
WALL_THICK    = 0.35   # m, wall thickness = depth of the window reveal

# Skydome — what you see through the window until real exterior geometry exists.
SKY_RADIUS    = 140.0
SKY_SEG, SKY_RING = 96, 48
SKY_TEXTURE   = os.environ.get("TOWER_SKY", "sky_day")
# How high the room sits above the ground. Drops the skydome by the same amount so
# you look *down* on the landscape, which is the whole point of being up a tower.
TOWER_ELEV    = 26.0
# The shaft below the room. Slightly battered — wider at the base — which is both
# how towers are actually built and what makes it read as tall when you look down.
SHAFT_BATTER  = 1.14
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
                      os.environ.get("TOWER_WALL_TINT", "0.80,0.84,0.92").split(","))
OUT_NAME      = os.environ.get("TOWER_OUT", "TowerShell.usda")

OUT = (Path(__file__).parent.parent
       / "app/Packages/RealityKitContent/Sources/RealityKitContent/RealityKitContent.rkassets"
       / OUT_NAME)

R = DIAMETER / 2.0


# Room-space seat position: desk sits against the wall at theta=0 (-Z), you sit just
# behind its front edge. Everything is then shifted so the seat lands on the origin.
SEAT_Z = -(R - DESK_D - 0.05) + SEAT_SETBACK


def p(theta_deg, y):
    """Point on the inner wall face, in user-relative space.

    theta 0 = straight ahead (the desk), +ve = toward your right.
    """
    t = math.radians(theta_deg)
    return (R * math.sin(t), y, -R * math.cos(t) - SEAT_Z)


def po(theta_deg, y):
    """Same, on the outer face of the wall."""
    t = math.radians(theta_deg)
    ro = R + WALL_THICK
    return (ro * math.sin(t), y, -ro * math.cos(t) - SEAT_Z)


TILE = 2.0  # metres per texture repeat, so texel density is uniform everywhere

# Floor under roughness. The slate maps dip near zero in places, which renders as
# mirror-bright highlights and makes the stone look wet. Remap into [ROUGH_MIN, 1].
ROUGH_MIN = 0.45


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
        if self.name == "Sky":
            return self._sky_material(indent)
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
{i}        float4 inputs:scale = ({1.0 - ROUGH_MIN}, {1.0 - ROUGH_MIN}, {1.0 - ROUGH_MIN}, 1)
{i}        float4 inputs:bias = ({ROUGH_MIN}, {ROUGH_MIN}, {ROUGH_MIN}, 0)
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

    def _sky_material(self, indent):
        """Unlit: the sky emits, so it doesn't darken with the room's lighting."""
        i, n, t = indent, self.name, self.texture
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
{i}    def Shader "skyTex"
{i}    {{
{i}        uniform token info:id = "UsdUVTexture"
{i}        asset inputs:file = @textures/{t}.jpg@
{i}        float2 inputs:st.connect = {base}/stReader.outputs:result>
{i}        token inputs:wrapS = "repeat"
{i}        token inputs:wrapT = "clamp"
{i}        float3 outputs:rgb
{i}    }}
{i}    def Shader "Surface"
{i}    {{
{i}        uniform token info:id = "UsdPreviewSurface"
{i}        color3f inputs:diffuseColor.connect = {base}/skyTex.outputs:rgb>
{i}        color3f inputs:emissiveColor.connect = {base}/skyTex.outputs:rgb>
{i}        float inputs:metallic = 0
{i}        float inputs:roughness = 1
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
    step_deg = 360.0 / SEGMENTS
    # Snap the opening to whole wall segments. Testing segment midpoints against a
    # free-floating angle put the actual hole up to half a segment away from where
    # the reveal was built, which buried one jamb in the wall and left the other
    # hanging in mid air.
    SEG0 = int(round((WINDOW_CENTRE - half) / step_deg))
    SEG1 = max(SEG0 + 1, int(round((WINDOW_CENTRE + half) / step_deg)))
    w0, w1 = SEG0 * step_deg, SEG1 * step_deg

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

        in_window = (SEG0 <= s < SEG1)
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

        # Outer skin. Without this the wall is a single curved surface with no
        # thickness, so the reveal projects into thin air and reads as a floating
        # frame. Same opening, cut on the same segments.
        n_out = (math.sin(t), 0.0, -math.cos(t))
        if in_window:
            for lo, hi in ((0.0, WINDOW_SILL), (WINDOW_HEAD, WALL_HEIGHT)):
                wall.face([po(b, lo), po(a, lo), po(a, hi), po(b, hi)], n_out,
                          [(ub, lo / TILE), (ua, lo / TILE), (ua, hi / TILE), (ub, hi / TILE)])
        else:
            wall.face([po(b, 0.0), po(a, 0.0), po(a, WALL_HEIGHT), po(b, WALL_HEIGHT)], n_out,
                      [(ub, 0.0), (ua, 0.0), (ua, WALL_HEIGHT / TILE), (ub, WALL_HEIGHT / TILE)])

        # Cap the top of the wall so the thickness is closed at the eaves.
        wall.face([p(a, WALL_HEIGHT), p(b, WALL_HEIGHT),
                   po(b, WALL_HEIGHT), po(a, WALL_HEIGHT)], (0.0, 1.0, 0.0),
                  [(ua, 0.0), (ub, 0.0), (ub, WALL_THICK / TILE), (ua, WALL_THICK / TILE)])

        # Cone to the apex
        # Conical UVs: u round the eaves, v up the slope to the apex.
        roof.face([p(a, WALL_HEIGHT), p(b, WALL_HEIGHT), (0.0, APEX_HEIGHT, -SEAT_Z)],
                  (-math.sin(t) * 0.5, -0.5, -math.cos(t) * 0.5),
                  [(ua, 0.0), (ub, 0.0), ((ua + ub) / 2.0, slope / TILE)])

    # Window reveal — the faces you see when you lean into the opening. Design doc
    # calls this the one place worth spending detail, since it's read at ~30 cm.
    reveal = Mesh("Reveal", (0.42, 0.41, 0.39), texture="wall", tint=WALL_TINT)

    # Jambs, on the exact segment boundaries the opening was cut on.
    for side, th in ((-1.0, w0), (1.0, w1)):
        t = math.radians(th)
        nrm = (side * math.cos(t), 0.0, side * math.sin(t))
        reveal.face([p(th, WINDOW_SILL), po(th, WINDOW_SILL),
                     po(th, WINDOW_HEAD), p(th, WINDOW_HEAD)], nrm,
                    [(0.0, WINDOW_SILL / TILE), (WALL_THICK / TILE, WINDOW_SILL / TILE),
                     (WALL_THICK / TILE, WINDOW_HEAD / TILE), (0.0, WINDOW_HEAD / TILE)])

    # Sill and head follow the curve of the wall rather than cutting across it.
    for y, nrm in ((WINDOW_SILL, (0.0, 1.0, 0.0)), (WINDOW_HEAD, (0.0, -1.0, 0.0))):
        for seg in range(SEG0, SEG1):
            a, b = seg * step_deg, (seg + 1) * step_deg
            u0 = (a - w0) / 360.0 * (2.0 * math.pi * R) / TILE
            u1 = (b - w0) / 360.0 * (2.0 * math.pi * R) / TILE
            reveal.face([p(a, y), p(b, y), po(b, y), po(a, y)], nrm,
                        [(u0, 0.0), (u1, 0.0), (u1, WALL_THICK / TILE), (u0, WALL_THICK / TILE)])

    parts = [floor, wall, roof, reveal]
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


def skydome():
    """Inward-facing sphere carrying the sky. Placeholder for the real exterior
    geometry the hybrid decision calls for — this is the far half of that."""
    m = Mesh("Sky", (0.5, 0.6, 0.8), texture=SKY_TEXTURE)
    cx, cy, cz = 0.0, -TOWER_ELEV, -SEAT_Z
    for iy in range(SKY_RING):
        ph0 = math.pi * iy / SKY_RING
        ph1 = math.pi * (iy + 1) / SKY_RING
        for ix in range(SKY_SEG):
            th0 = 2.0 * math.pi * ix / SKY_SEG
            th1 = 2.0 * math.pi * (ix + 1) / SKY_SEG

            def pt(ph, th):
                return (cx + SKY_RADIUS * math.sin(ph) * math.sin(th),
                        cy + SKY_RADIUS * math.cos(ph),
                        cz - SKY_RADIUS * math.sin(ph) * math.cos(th))

            def uv(ph, th):
                return (th / (2.0 * math.pi), 1.0 - ph / math.pi)

            # Wound so the front faces point inward. Viewed from the middle, the
            # other winding is back-facing and gets culled, which shows as the sky
            # simply not being there rather than as anything obviously broken.
            quad = [pt(ph1, th0), pt(ph1, th1), pt(ph0, th1), pt(ph0, th0)]
            # Normals point inward, since it's viewed from the middle.
            nrm = [tuple(-(c[k] - (cx, cy, cz)[k]) / SKY_RADIUS for k in range(3)) for c in quad]
            m.face(quad, nrm, [uv(ph1, th0), uv(ph1, th1), uv(ph0, th1), uv(ph0, th0)])
    return m.material_usda() + m.usda()


def tower_shaft():
    """The tower continuing down below the room, to the ground far below.

    This is the near half of the hybrid decision: the skydome sits at infinity and
    never shifts, so the shaft is what actually gives parallax when you lean out
    and look down.
    """
    m = Mesh("Shaft", (0.44, 0.43, 0.41), texture=WALL_TEXTURE, tint=WALL_TINT)
    r_top = R + WALL_THICK
    r_bot = r_top * SHAFT_BATTER
    rings = 12
    circumference = 2.0 * math.pi * r_top
    wraps = max(1, round(circumference / TILE))
    step = 360.0 / SEGMENTS

    def sp(theta_deg, frac):
        """frac 0 at the room floor, 1 at the ground."""
        t = math.radians(theta_deg)
        rr = r_top + (r_bot - r_top) * frac
        y = -TOWER_ELEV * frac
        return (rr * math.sin(t), y, -rr * math.cos(t) - SEAT_Z)

    for iy in range(rings):
        f0, f1 = iy / rings, (iy + 1) / rings
        v0, v1 = -f0 * TOWER_ELEV / TILE, -f1 * TOWER_ELEV / TILE
        for sgm in range(SEGMENTS):
            a, b = sgm * step, (sgm + 1) * step
            ua, ub = a / 360.0 * wraps, b / 360.0 * wraps
            t = math.radians((a + b) / 2.0)
            nrm = (math.sin(t), 0.0, -math.cos(t))
            m.face([sp(b, f0), sp(a, f0), sp(a, f1), sp(b, f1)], nrm,
                   [(ub, v0), (ua, v0), (ua, v1), (ub, v1)])
    return m.material_usda() + m.usda()


# Buildings below, in the cone visible through the window. These are what give
# parallax at eye level: the shaft is almost directly underfoot and only shows if
# you lean out, while the skydome sits at infinity and never shifts at all.
# (angle deg, distance m, width, depth, wall height, roof height, yaw deg)
NEIGHBOURS = [
    (34.0, 21.0, 7.0, 9.0, 6.5, 3.0, 18.0),
    (48.0, 33.0, 9.0, 7.0, 8.0, 3.6, -25.0),
    (61.0, 26.0, 6.0, 6.0, 5.5, 2.6, 40.0),
    (72.0, 44.0, 11.0, 8.0, 7.0, 3.2, 8.0),
    (44.0, 57.0, 8.0, 8.0, 9.0, 3.4, -12.0),
]


GROUND_RADIUS = 130.0


def ground():
    """Ground for the neighbours to stand on. Without it the buildings hover in
    front of the skydome image with nothing under them."""
    m = Mesh("Ground", (0.32, 0.34, 0.24), texture="ground")
    y = -TOWER_ELEV
    cz = -SEAT_Z
    rings, segs = 10, 72
    TILE_G = 14.0    # ground tiles much larger than interior surfaces
    for iy in range(rings):
        r0 = GROUND_RADIUS * (iy / rings) ** 1.6
        r1 = GROUND_RADIUS * ((iy + 1) / rings) ** 1.6
        for ix in range(segs):
            t0 = 2.0 * math.pi * ix / segs
            t1 = 2.0 * math.pi * (ix + 1) / segs

            def gp(r, t):
                return (r * math.sin(t), y, -r * math.cos(t) + cz)

            quad = [gp(r0, t0), gp(r0, t1), gp(r1, t1), gp(r1, t0)]
            m.face(quad, (0.0, 1.0, 0.0),
                   [(q[0] / TILE_G, q[2] / TILE_G) for q in quad])
    return m.material_usda() + m.usda()


def neighbourhood():
    """A few roofs below the window, for parallax at eye level."""
    walls = Mesh("Roofs_Walls", (0.44, 0.42, 0.39), texture=WALL_TEXTURE, tint=(0.62, 0.66, 0.74))
    roofs = Mesh("Roofs_Tops", (0.32, 0.22, 0.16), texture="roof", tint=(0.55, 0.40, 0.32))

    for ang, dist, w, d, h, rh, yaw in NEIGHBOURS:
        t = math.radians(ang)
        cx = dist * math.sin(t)
        cz = -dist * math.cos(t) - SEAT_Z
        base = -TOWER_ELEV
        ry = math.radians(yaw)
        ca, sa = math.cos(ry), math.sin(ry)

        def pt(dx, dz, y):
            return (cx + dx * ca - dz * sa, y, cz + dx * sa + dz * ca)

        hw, hd = w / 2.0, d / 2.0
        top = base + h
        # Four walls
        for (x0, z0), (x1, z1), nx, nz in (
                ((-hw, -hd), (hw, -hd), 0.0, -1.0), ((hw, -hd), (hw, hd), 1.0, 0.0),
                ((hw, hd), (-hw, hd), 0.0, 1.0), ((-hw, hd), (-hw, -hd), -1.0, 0.0)):
            nrm = (nx * ca - nz * sa, 0.0, nx * sa + nz * ca)
            span = math.hypot(x1 - x0, z1 - z0)
            walls.face([pt(x0, z0, base), pt(x1, z1, base), pt(x1, z1, top), pt(x0, z0, top)],
                       nrm, [(0.0, 0.0), (span / TILE, 0.0),
                             (span / TILE, h / TILE), (0.0, h / TILE)])
        # Gabled roof, ridge running along x
        apex_a, apex_b = pt(-hw, 0.0, top + rh), pt(hw, 0.0, top + rh)
        slope = math.hypot(hd, rh)
        for sgn in (-1.0, 1.0):
            e0, e1 = pt(-hw, sgn * hd, top), pt(hw, sgn * hd, top)
            nrm = (-sa * 0.0 + 0.0, rh / slope, sgn * hd / slope)
            nrm = (nrm[2] * -sa, nrm[1], nrm[2] * ca)
            roofs.face([e0, e1, apex_b, apex_a], nrm,
                       [(0.0, 0.0), (w / TILE, 0.0), (w / TILE, slope / TILE), (0.0, slope / TILE)])
        # Gable ends
        for sx in (-hw, hw):
            roofs.face([pt(sx, -hd, top), pt(sx, hd, top), pt(sx, 0.0, top + rh)],
                       (ca if sx > 0 else -ca, 0.0, sa if sx > 0 else -sa),
                       [(0.0, 0.0), (d / TILE, 0.0), (d / 2.0 / TILE, rh / TILE)])
    return walls.material_usda() + walls.usda() + roofs.material_usda() + roofs.usda()


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
    sky = skydome()
    shaft = tower_shaft()
    hood = neighbourhood()
    grnd = ground()

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
{shell}{beams}{shaft}{grnd}{hood}{sky}{desk}{fire}{human}{envelope}}}
''')
    print(f"wrote {OUT.relative_to(Path(__file__).parent.parent)}")
    print(f"  {DIAMETER} m across ({DIAMETER / FT:.1f} ft)")
    print(f"  eaves {WALL_HEIGHT:.2f} m ({WALL_HEIGHT / FT:.1f} ft), "
          f"apex {APEX_HEIGHT:.2f} m ({APEX_HEIGHT / FT:.1f} ft)")
    print(f"  window {WINDOW_WIDTH} m wide at {WINDOW_CENTRE}deg (right), "
          f"{WINDOW_SILL}-{WINDOW_HEAD} m, reveal {WALL_THICK} m deep")
    print(f"  origin = seat; desk edge {abs(desk_z) - DESK_D / 2.0:.2f} m ahead")
    print(f"  wall ahead {R + SEAT_Z:.2f} m, room behind you {R - SEAT_Z:.2f} m")
    print(f"  roof: wall plate + apex boss (no rafters)")
    print(f"  sky: {SKY_TEXTURE}, room {TOWER_ELEV:.0f} m above the ground")
    print(f"  neighbours: {len(NEIGHBOURS)} roofs below, {min(n[1] for n in NEIGHBOURS):.0f}-{max(n[1] for n in NEIGHBOURS):.0f} m out")
    print(f"  shaft: {TOWER_ELEV:.0f} m down to the ground, battered to "
          f"{(R + WALL_THICK) * SHAFT_BATTER * 2:.1f} m across at the base")


if __name__ == "__main__":
    main()
