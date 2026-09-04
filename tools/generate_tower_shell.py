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
FIRE_CENTRE   = 180.0  # directly opposite the desk: behind you seated, facing
                       # you the moment you turn round or stand up
WINDOW_WIDTH  = 2.00   # m, along the arc — widened with the room to hold its 27deg
WALL_THICK    = 0.35   # m, wall thickness = depth of the window reveal
# Fireplace. Built rather than bought: the free Quaternius tier has no fireplace,
# and a hearth set into a curved wall is architecture, like the shell.
FIRE_BREAST_W = 2.00   # m across the chimney breast
FIRE_BREAST_D = 0.75   # m it projects into the room
FIRE_BREAST_H = 3.20   # m to the top of the breast
FIRE_OPEN_W   = 1.25   # m, the opening
FIRE_OPEN_H   = 1.15
FIRE_HEARTH_D = 0.45   # m the hearth slab reaches past the breast
FIRE_HEARTH_T = 0.09
FIRE_EMBED    = 0.15   # m set back into the wall, so the flat breast meets the curve

# Orb on a pedestal, in the middle of the room. Placeholder geometry — the orb is
# a plain sphere and the pedestal a turned column, both there to hold the position
# and the light until the real models arrive.
ORB_PED_H     = 1.05   # m to the top of the pedestal
ORB_RADIUS    = 0.16
ORB_GAP       = 0.10   # m the orb floats above the cap
ORB_SEGS      = 20

GLASS_OPACITY = 0.14   # how much the pane tints the view
ROOF_THICK    = 0.18   # m, roof thickness. Without an outer surface the cone is
                       # invisible from outside and casts no shadow.

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

DESK_W, DESK_D, DESK_H = 2.85, 1.10, 0.81   # matches props/Table_Large.usdc
ENVELOPE_W, ENVELOPE_D = 2.70, 3.00          # real clear floor
SEAT_SETBACK  = 0.30   # m you sit back from the desk edge

# Blockout aids: 1.7 m reference figure, walkable-envelope slab, fireplace marker.
# Useful while sizing the room, in the way once there is real furniture.
#   TOWER_AIDS=1 python3 tools/generate_tower_shell.py
SHOW_AIDS     = os.environ.get("TOWER_AIDS", "0") == "1"

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
    flipped = 0
    flip_by_mesh = {}

    def __init__(self, name, color, texture=None, tint=(1.0, 1.0, 1.0), translate=None):
        self.name, self.color, self.texture, self.tint = name, color, texture, tint
        # Geometry is normally authored in world space, so the prim needs no
        # transform. Anything Swift attaches a *component* to needs one, because a
        # light lands on the entity's origin, not on its vertices.
        self.translate = translate
        self.pts, self.counts, self.idx, self.normals, self.uvs = [], [], [], [], []

    def face(self, verts, normal, uvs=None):
        """normal may be one vector for the whole face, or one per vertex for
        smooth shading across a curved surface."""
        # RealityKit ignores doubleSided and culls back faces, so a quad wound the
        # wrong way renders as nothing at all — which looks like missing geometry
        # rather than like a bug. Winding is easy to invert by accident whenever a
        # parameter runs downward. So: trust the supplied normal, and reorder the
        # vertices to match it.
        want = normal[0] if isinstance(normal, list) else normal
        e1 = [verts[1][k] - verts[0][k] for k in range(3)]
        e2 = [verts[2][k] - verts[0][k] for k in range(3)]
        geo = (e1[1] * e2[2] - e1[2] * e2[1],
               e1[2] * e2[0] - e1[0] * e2[2],
               e1[0] * e2[1] - e1[1] * e2[0])
        if sum(geo[k] * want[k] for k in range(3)) < 0.0:
            verts = list(reversed(verts))
            if uvs is not None:
                uvs = list(reversed(uvs))
            if isinstance(normal, list):
                normal = list(reversed(normal))
            Mesh.flipped += 1
            Mesh.flip_by_mesh[self.name] = Mesh.flip_by_mesh.get(self.name, 0) + 1

        if isinstance(normal, list):
            self.normals.extend(normal)
        else:
            self.normals.extend([normal] * len(verts))
        base = len(self.pts)
        self.pts.extend(verts)

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
        if self.name == "Glass":
            return self._glass_material(indent)
        if self.name.startswith("Flame"):
            return self._flame_material(indent)
        # Match "Fire_0", not "Fireplace" — the stone breast is not on fire.
        if self.name.startswith("Fire_"):
            return self._fire_material(indent)
        if self.name.startswith("Orb_"):
            return self._orb_material(indent)
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

    def _glass_material(self, indent):
        """Thin, mostly clear, slightly cool. Shadow casting is switched off in
        Swift — see TowerLighting — otherwise the pane blocks the window light it
        is supposed to let through."""
        i, n = indent, self.name
        return f'''{i}def Material "{n}Mat"
{i}{{
{i}    token outputs:surface.connect = </TowerShell/{n}Mat/Surface.outputs:surface>
{i}    def Shader "Surface"
{i}    {{
{i}        uniform token info:id = "UsdPreviewSurface"
{i}        color3f inputs:diffuseColor = (0.78, 0.85, 0.88)
{i}        float inputs:metallic = 0
{i}        float inputs:roughness = 0.06
{i}        float inputs:opacity = {GLASS_OPACITY}
{i}        float inputs:ior = 1.5
{i}        token outputs:surface
{i}    }}
{i}}}
'''

    def _flame_material(self, indent):
        """Emissive, so the flame reads as the source rather than as a lit object."""
        i, n = indent, self.name
        return f'''{i}def Material "{n}Mat"
{i}{{
{i}    token outputs:surface.connect = </TowerShell/{n}Mat/Surface.outputs:surface>
{i}    def Shader "Surface"
{i}    {{
{i}        uniform token info:id = "UsdPreviewSurface"
{i}        color3f inputs:diffuseColor = (0.05, 0.03, 0.01)
{i}        color3f inputs:emissiveColor = (2.0, 1.15, 0.42)
{i}        float inputs:metallic = 0
{i}        float inputs:roughness = 1
{i}        token outputs:surface
{i}    }}
{i}}}
'''

    def _fire_material(self, indent):
        """Hotter and more orange than a candle, and brighter, since it is the
        biggest source in the room once it is lit."""
        i, n = indent, self.name
        return f'''{i}def Material "{n}Mat"
{i}{{
{i}    token outputs:surface.connect = </TowerShell/{n}Mat/Surface.outputs:surface>
{i}    def Shader "Surface"
{i}    {{
{i}        uniform token info:id = "UsdPreviewSurface"
{i}        color3f inputs:diffuseColor = (0.08, 0.02, 0.0)
{i}        color3f inputs:emissiveColor = (2.6, 0.85, 0.18)
{i}        float inputs:metallic = 0
{i}        float inputs:roughness = 1
{i}        token outputs:surface
{i}    }}
{i}}}
'''

    def _orb_material(self, indent):
        """Cool and bright, deliberately against the warm candles and fire — the
        one thing in the room that is not firelight."""
        i, n = indent, self.name
        return f'''{i}def Material "{n}Mat"
{i}{{
{i}    token outputs:surface.connect = </TowerShell/{n}Mat/Surface.outputs:surface>
{i}    def Shader "Surface"
{i}    {{
{i}        uniform token info:id = "UsdPreviewSurface"
{i}        color3f inputs:diffuseColor = (0.06, 0.12, 0.16)
{i}        color3f inputs:emissiveColor = (0.55, 1.45, 2.20)
{i}        float inputs:metallic = 0
{i}        float inputs:roughness = 0.35
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
        xform = ""
        if self.translate is not None:
            tx, ty, tz = self.translate
            xform = (f'    double3 xformOp:translate = ({tx:.4f}, {ty:.4f}, {tz:.4f})\n'
                     f'        uniform token[] xformOpOrder = ["xformOp:translate"]\n    ')
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
{i}{xform}}}
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

        # Inward-facing wall normal. A wall point is (R sin t, y, -R cos t - SEAT_Z),
        # so the inward radial is (-sin t, 0, +cos t). The Z sign here was wrong.
        t = math.radians(mid)
        n = (-math.sin(t), 0.0, math.cos(t))

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
                  (-math.sin(t) * 0.5, -0.5, math.cos(t) * 0.5),
                  [(ua, 0.0), (ub, 0.0), ((ua + ub) / 2.0, slope / TILE)])

        # Outer skin of the cone. The inner surface faces into the room, so from
        # the sun's side it is back-facing and gets culled out of the shadow map —
        # the roof lit the room straight through itself.
        ro = R + WALL_THICK
        oa0 = (ro * math.sin(math.radians(a)), WALL_HEIGHT,
               -ro * math.cos(math.radians(a)) - SEAT_Z)
        ob0 = (ro * math.sin(math.radians(b)), WALL_HEIGHT,
               -ro * math.cos(math.radians(b)) - SEAT_Z)
        oapex = (0.0, APEX_HEIGHT + ROOF_THICK, -SEAT_Z)
        roof.face([ob0, oa0, oapex],
                  (math.sin(t) * 0.5, 0.5, -math.cos(t) * 0.5),
                  [(ub, 0.0), (ua, 0.0), ((ua + ub) / 2.0, slope / TILE)])

    # Window reveal — the faces you see when you lean into the opening. Design doc
    # calls this the one place worth spending detail, since it's read at ~30 cm.
    reveal = Mesh("Reveal", (0.42, 0.41, 0.39), texture="wall", tint=WALL_TINT)

    # Jambs, on the exact segment boundaries the opening was cut on.
    for side, th in ((1.0, w0), (-1.0, w1)):
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

    # Glazing. Sits mid-way through the reveal so the stone frames it on both
    # sides, and is emitted twice so it reads from inside and out.
    glass = Mesh("Glass", (0.78, 0.85, 0.88))
    glass_r = R + WALL_THICK / 2.0

    def gp(theta_deg, y):
        t = math.radians(theta_deg)
        return (glass_r * math.sin(t), y, -glass_r * math.cos(t) - SEAT_Z)

    for seg in range(SEG0, SEG1):
        a, b = seg * step_deg, (seg + 1) * step_deg
        mid = math.radians((a + b) / 2.0)
        inward = (-math.sin(mid), 0.0, math.cos(mid))
        outward = (math.sin(mid), 0.0, -math.cos(mid))
        quad = [gp(a, WINDOW_SILL), gp(b, WINDOW_SILL),
                gp(b, WINDOW_HEAD), gp(a, WINDOW_HEAD)]
        uv = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
        glass.face(quad, inward, uv)
        glass.face(list(reversed(quad)), outward, list(reversed(uv)))

    parts = [floor, wall, roof, reveal, glass]
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


def orb_and_pedestal():
    """A glowing orb on a turned pedestal at the middle of the room.

    Placeholder: the orb is a sphere and the pedestal a stack of tapered rings.
    The orb is named Orb_0 so Swift hangs a light on it, the same way flames work.
    """
    stone = Mesh("Pedestal", (0.40, 0.39, 0.37), texture=WALL_TEXTURE, tint=WALL_TINT)
    cx, cz = 0.0, -SEAT_Z          # middle of the room

    def ring(y0, y1, r0, r1):
        """A tapered band, plus a cap when it narrows to nothing."""
        for i in range(ORB_SEGS):
            t0 = 2.0 * math.pi * i / ORB_SEGS
            t1 = 2.0 * math.pi * (i + 1) / ORB_SEGS
            mid = (t0 + t1) / 2.0
            out = (math.sin(mid), 0.0, math.cos(mid))
            a0 = (cx + r0 * math.sin(t0), y0, cz + r0 * math.cos(t0))
            b0 = (cx + r0 * math.sin(t1), y0, cz + r0 * math.cos(t1))
            a1 = (cx + r1 * math.sin(t0), y1, cz + r1 * math.cos(t0))
            b1 = (cx + r1 * math.sin(t1), y1, cz + r1 * math.cos(t1))
            stone.face([a0, b0, b1, a1], out,
                       [(i / ORB_SEGS * 2, y0 / TILE), ((i + 1) / ORB_SEGS * 2, y0 / TILE),
                        ((i + 1) / ORB_SEGS * 2, y1 / TILE), (i / ORB_SEGS * 2, y1 / TILE)])

    def disc(y, r, normal):
        for i in range(ORB_SEGS):
            t0 = 2.0 * math.pi * i / ORB_SEGS
            t1 = 2.0 * math.pi * (i + 1) / ORB_SEGS
            stone.face([(cx, y, cz),
                        (cx + r * math.sin(t0), y, cz + r * math.cos(t0)),
                        (cx + r * math.sin(t1), y, cz + r * math.cos(t1))], normal,
                       [(0.5, 0.5), (0, 0), (1, 0)])

    ring(0.00, 0.10, 0.34, 0.30)          # plinth
    ring(0.10, 0.22, 0.26, 0.22)          # base moulding
    ring(0.22, 0.88, 0.20, 0.15)          # shaft, tapering
    ring(0.88, ORB_PED_H, 0.24, 0.22)     # cap
    disc(ORB_PED_H, 0.22, (0.0, 1.0, 0.0))

    centre = (cx, ORB_PED_H + ORB_GAP + ORB_RADIUS, cz)
    orb = Mesh("Orb_0", (0.55, 0.85, 1.0), translate=centre)
    sphere(orb, (0.0, 0.0, 0.0), ORB_RADIUS, 24, 16)
    return stone.material_usda() + stone.usda() + orb.material_usda() + orb.usda()


def fireplace():
    """Chimney breast, recessed opening, hearth, and the fire itself.

    Built in a local frame on the wall: u runs along the tangent, v is up, w goes
    inward from the wall surface. The breast starts slightly *inside* the wall so
    a flat face meets the curve without leaving a gap at its corners.
    """
    stone = Mesh("Hearth", (0.42, 0.41, 0.39), texture=WALL_TEXTURE, tint=WALL_TINT)
    th = math.radians(FIRE_CENTRE)
    base = (R * math.sin(th), 0.0, -R * math.cos(th) - SEAT_Z)
    tan = (math.cos(th), 0.0, math.sin(th))          # along the wall
    inw = (-math.sin(th), 0.0, math.cos(th))         # into the room

    def fp(u, v, w):
        return (base[0] + u * tan[0] + w * inw[0],
                base[1] + v,
                base[2] + u * tan[2] + w * inw[2])

    def face(corners, normal, size):
        stone.face([fp(*c) for c in corners], normal,
                   [(0, 0), (size[0] / TILE, 0), (size[0] / TILE, size[1] / TILE), (0, size[1] / TILE)])

    hw, ow = FIRE_BREAST_W / 2.0, FIRE_OPEN_W / 2.0
    d, h, oh = FIRE_BREAST_D, FIRE_BREAST_H, FIRE_OPEN_H
    back = -FIRE_EMBED
    out = tuple(inw)
    up, down = (0.0, 1.0, 0.0), (0.0, -1.0, 0.0)
    left = tuple(-c for c in tan)
    right = tuple(tan)

    # Face onto the room, in three pieces around the opening
    face([(-hw, 0, d), (-ow, 0, d), (-ow, oh, d), (-hw, oh, d)], out, (hw - ow, oh))
    face([(ow, 0, d), (hw, 0, d), (hw, oh, d), (ow, oh, d)], out, (hw - ow, oh))
    face([(-hw, oh, d), (hw, oh, d), (hw, h, d), (-hw, h, d)], out, (FIRE_BREAST_W, h - oh))
    # Sides and top of the breast
    face([(-hw, 0, back), (-hw, 0, d), (-hw, h, d), (-hw, h, back)], left, (d - back, h))
    face([(hw, 0, d), (hw, 0, back), (hw, h, back), (hw, h, d)], right, (d - back, h))
    face([(-hw, h, back), (-hw, h, d), (hw, h, d), (hw, h, back)], up, (FIRE_BREAST_W, d - back))
    # Inside the opening: back, jambs, lintel, and the floor of the firebox
    face([(-ow, 0, back), (ow, 0, back), (ow, oh, back), (-ow, oh, back)], out, (FIRE_OPEN_W, oh))
    face([(-ow, 0, back), (-ow, 0, d), (-ow, oh, d), (-ow, oh, back)], right, (d - back, oh))
    face([(ow, 0, d), (ow, 0, back), (ow, oh, back), (ow, oh, d)], left, (d - back, oh))
    face([(-ow, oh, back), (-ow, oh, d), (ow, oh, d), (ow, oh, back)], down, (FIRE_OPEN_W, d - back))
    # Firebox floor, raised to the hearth slab's level. At y=0 it was exactly
    # coplanar with the room floor, and the two z-fought — which shimmers as you
    # move. Flush with the slab is also how a hearth actually reads: one
    # continuous stone surface from inside the opening out onto the boards.
    face([(-ow, FIRE_HEARTH_T, back), (ow, FIRE_HEARTH_T, back),
          (ow, FIRE_HEARTH_T, d), (-ow, FIRE_HEARTH_T, d)], up, (FIRE_OPEN_W, d - back))
    # Hearth slab, reaching out onto the floor
    sw = ow + 0.22
    face([(-sw, FIRE_HEARTH_T, d), (sw, FIRE_HEARTH_T, d),
          (sw, FIRE_HEARTH_T, d + FIRE_HEARTH_D), (-sw, FIRE_HEARTH_T, d + FIRE_HEARTH_D)],
         up, (sw * 2, FIRE_HEARTH_D))
    face([(-sw, 0, d + FIRE_HEARTH_D), (sw, 0, d + FIRE_HEARTH_D),
          (sw, FIRE_HEARTH_T, d + FIRE_HEARTH_D), (-sw, FIRE_HEARTH_T, d + FIRE_HEARTH_D)],
         out, (sw * 2, FIRE_HEARTH_T))

    # The fire. Emissive, and named so Swift can hang a light and a flicker on it.
    centre = fp(0.0, FIRE_HEARTH_T + 0.10, d * 0.45)
    # A small glowing bed of coals. The flames themselves are particles, added in
    # Swift — fire has no shape worth modelling.
    fire = Mesh("Fire_0", (1.0, 0.45, 0.12), translate=centre)
    sphere(fire, (0.0, 0.0, 0.0), 0.13, 10, 8)
    return stone.material_usda() + stone.usda() + fire.material_usda() + fire.usda()


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


# Converted Quaternius props (CC0). Placed user-relative: origin is the seat,
# -Z is the desk you face, +X is your right.
# (file, x, y, z, yaw deg)
PROPS = [
    ("Table_Large",       0.00, 0.00, -0.85,   0.0),
    ("Chair_1",           0.00, 0.00,  0.20, 180.0),
    ("Bookcase_2",        2.67, 0.00,  6.13,  40.0),   # moved: the fireplace took 180deg
    ("Shelf_Arch",       -3.30, 0.00,  2.60,  90.0),
    ("Chest_Wood",       -2.60, 0.00,  5.20,  30.0),
    ("Stool",             2.30, 0.00,  4.20,   0.0),
    ("Book_Stack_1",     -0.80, 0.81, -0.90,  15.0),
    ("BookGroup_Medium_1", 0.00, 0.81, -1.15, -8.0),
    ("Scroll_1",          0.35, 0.81, -0.70,  40.0),
    ("Potion_1",         -1.15, 0.81, -0.75,   0.0),
]


# Candles. Each entry places a prop and puts flames above it. The flame prims are
# named Flame_N, and Swift finds them by name to hang the lights on — so positions
# live here only, rather than being duplicated in TowerLighting.
# (prop, x, y, z, yaw, [(dx, dy, dz) per flame])
CANDLES = [
    # Offsets measured from the meshes by isolating the wax material (the candles
    # share a mesh with the metalwork, so clustering raw vertices counts arms and
    # bowls as cups — which is how the stands were first read as six and the
    # chandelier as four). Splitting by MI_Trim_Props_Vertex gives the real count:
    # eight candles on each stand at r 0.31, eight on the chandelier at r 0.575,
    # and three on the triple. The chandelier hangs *below* its origin.
    ("CandleStick_Triple", 0.85, 0.81, -0.95,   0.0,
     [(-0.172, 0.36, 0.0), (0.0, 0.48, 0.0), (0.172, 0.36, 0.0)]),
    ("Candle_1",           1.35, 0.81, -0.80,   0.0, [(0.0, 0.15, 0.0)]),
    ("Candle_2",          -0.95, 0.81, -1.05,  20.0, [(0.0, 0.27, 0.0)]),
    ("CandleStick",       -2.60, 0.69,  5.20,   0.0, [(-0.14, 0.18, 0.0)]),
    ("CandleStick_Stand", -2.90, 0.00,  1.40,  25.0, [(0.000, 1.31, 0.312), (0.221, 1.31, 0.221), (0.312, 1.31, 0.000), (0.221, 1.31, -0.221), (0.000, 1.31, -0.312), (-0.221, 1.31, -0.221), (-0.312, 1.31, -0.000), (-0.221, 1.31, 0.221)]),
    ("CandleStick_Stand",  2.70, 0.00,  4.30, -20.0, [(0.000, 1.31, 0.312), (0.221, 1.31, 0.221), (0.312, 1.31, 0.000), (0.221, 1.31, -0.221), (0.000, 1.31, -0.312), (-0.221, 1.31, -0.221), (-0.312, 1.31, -0.000), (-0.221, 1.31, 0.221)]),
    ("Chandelier",         0.00, 4.30,  2.95,   0.0, [(0.000, -0.89, 0.575), (0.407, -0.89, 0.407), (0.575, -0.89, 0.000), (0.407, -0.89, -0.407), (0.000, -0.89, -0.575), (-0.407, -0.89, -0.407), (-0.575, -0.89, -0.000), (-0.407, -0.89, 0.407)]),
]

FLAME_RADIUS = 0.016


def candles():
    """Candle props, plus a small emissive flame above each wick."""
    out = []
    index = 0

    for group, (name, x, y, z, yaw, offsets) in enumerate(CANDLES):
        out.append(f'''    def "{name}_{index}" (
        prepend references = @props/{name}.usdc@
    )
    {{
        double3 xformOp:translate = ({x}, {y}, {z})
        float3 xformOp:rotateXYZ = (0, {yaw}, 0)
        uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:rotateXYZ"]
    }}
''')
        # The prop is placed with a yaw, so its candles turn with it. The offsets
        # have to turn too, or the flames land between the candles rather than on
        # them — invisible on anything with yaw 0, obvious on the stands at 25 deg.
        ry = math.radians(yaw)
        cos_y, sin_y = math.cos(ry), math.sin(ry)
        for wick, (dx, dy, dz) in enumerate(offsets):
            rx = dx * cos_y + dz * sin_y
            rz = -dx * sin_y + dz * cos_y
            centre = (x + rx, y + dy, z + rz)
            # Built around the local origin with the position on the prim, so the
            # light Swift attaches lands on the flame rather than at (0, 0, 0).
            # Named by candle, then wick: Swift gives each candle one light rather
            # than one per flame, so a six-cup candelabra costs a single light.
            flame = Mesh(f"Flame_{group}_{wick}", (1.0, 0.78, 0.42), translate=centre)
            sphere(flame, (0.0, 0.0, 0.0), FLAME_RADIUS, 8, 6)
            out.append(flame.material_usda() + flame.usda())
            index += 1

    return "".join(out)


def sphere(mesh, centre, radius, segments, rings):
    """Low-poly sphere. Small enough that eight segments is plenty."""
    for iy in range(rings):
        ph0 = math.pi * iy / rings
        ph1 = math.pi * (iy + 1) / rings
        for ix in range(segments):
            th0 = 2.0 * math.pi * ix / segments
            th1 = 2.0 * math.pi * (ix + 1) / segments

            def pt(ph, th):
                return (centre[0] + radius * math.sin(ph) * math.sin(th),
                        centre[1] + radius * math.cos(ph),
                        centre[2] + radius * math.sin(ph) * math.cos(th))

            quad = [pt(ph0, th0), pt(ph0, th1), pt(ph1, th1), pt(ph1, th0)]
            nrm = [tuple((c[k] - centre[k]) / radius for k in range(3)) for c in quad]
            mesh.face(quad, nrm, [(0, 0), (1, 0), (1, 1), (0, 1)])


def props():
    """Reference the converted props into the scene."""
    out = []
    for name, x, y, z, yaw in PROPS:
        out.append(f'''    def "{name}" (
        prepend references = @props/{name}.usdc@
    )
    {{
        double3 xformOp:translate = ({x}, {y}, {z})
        float3 xformOp:rotateXYZ = (0, {yaw}, 0)
        uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:rotateXYZ"]
    }}
''')
    return "".join(out)


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
    desk = ""   # replaced by props/Table_Large.usdc

    if SHOW_AIDS:
        human = box("HumanReference_1m7", 0.45, 1.70, 0.25,
                    (0.0, 0.0, 1.80), (0.85, 0.35, 0.35))
        envelope = box("WalkableEnvelope", ENVELOPE_W, 0.01, ENVELOPE_D,
                       (0.0, 0.0, 0.35 + ENVELOPE_D / 2.0), (0.25, 0.55, 0.35))
        ft = math.radians(FIRE_CENTRE)
        fire = box("FireplaceMarker", 1.20, 1.40, 0.40,
                   ((R - 0.2) * math.sin(ft), 0.0, -(R - 0.2) * math.cos(ft) - SEAT_Z),
                   (0.55, 0.25, 0.15))
    else:
        human = envelope = fire = ""

    beams = roof_structure()
    sky = skydome()
    shaft = tower_shaft()
    hearth = fireplace()
    orb = orb_and_pedestal()
    hood = neighbourhood()
    grnd = ground()
    prp = props()
    cnd = candles()

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
{shell}{beams}{hearth}{orb}{shaft}{grnd}{hood}{sky}{prp}{cnd}{desk}{fire}{human}{envelope}}}
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
    print(f"  winding: {Mesh.flipped} faces reordered to match their normals")
    for k, v in sorted(Mesh.flip_by_mesh.items(), key=lambda kv: -kv[1]):
        print(f"      {k}: {v}")
    print(f"  sky: {SKY_TEXTURE}, room {TOWER_ELEV:.0f} m above the ground")
    print(f"  orb: pedestal {ORB_PED_H} m, orb r{ORB_RADIUS} at the room centre")
    print(f"  fireplace: {FIRE_BREAST_W} m breast at {FIRE_CENTRE}deg, "
          f"{FIRE_OPEN_W}x{FIRE_OPEN_H} m opening")
    print(f"  candles: {len(CANDLES)} props, "
          f"{sum(len(c[5]) for c in CANDLES)} flames")
    print(f"  props: {len(PROPS)} placed" + ("" if SHOW_AIDS else "; blockout aids off (TOWER_AIDS=1 to show)"))
    print(f"  neighbours: {len(NEIGHBOURS)} roofs below, {min(n[1] for n in NEIGHBOURS):.0f}-{max(n[1] for n in NEIGHBOURS):.0f} m out")
    print(f"  shaft: {TOWER_ELEV:.0f} m down to the ground, battered to "
          f"{(R + WALL_THICK) * SHAFT_BATTER * 2:.1f} m across at the base")


if __name__ == "__main__":
    main()
