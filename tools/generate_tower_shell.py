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
import json
import os
import random
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
WINDOW_WIDTH  = 1.60   # m, along the arc
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
# 0 leaves the pane as clear as it was; 1 is heavy frosting that keeps only
# colour and glow. TOWER_GLASS_FROST overrides it.
GLASS_FROST   = float(os.environ.get("TOWER_GLASS_FROST", "0.62"))
# Diamond leading. Frosting alone cannot hide detail -- RealityKit does not
# refract, so a blended pane lowers contrast but leaves every edge sharp. Lead
# cames are geometry, and geometry actually occludes.
GLASS_LEAD    = os.environ.get("TOWER_GLASS_LEAD", "1") == "1"
LEAD_SPACING  = 0.17   # m between cames, measured along the pane
LEAD_WIDTH    = 0.018  # m
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

# The town is ~2500 module placements. As plain references that is 2500 entities
# and as many draw calls, which is CPU work the M5's GPU gains do not help with.
# A PointInstancer per module type collapses each into one. Set TOWER_INSTANCED=0
# to fall back to plain references if anything looks wrong.
# RealityKit does NOT expand a USD PointInstancer: measured on visionOS 26.5, it
# loads the prototype subtree and throws the placements away, so the whole town
# collapses to one pile at the origin. Batching has to be done by merging
# geometry ahead of time instead -- see tools/merge_town.py.
MERGED        = os.environ.get("TOWER_MERGED", "1") == "1"

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
        if self.name.startswith("WinGlow"):
            return self._window_material(indent)
        if self.name.startswith("Lamp_") or self.name.startswith("LampPool_"):
            return self._lamp_material(indent)
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
        base = f"</TowerShell/{n}Mat"
        # RealityKit ignores a texture-connected `opacity` on UsdPreviewSurface:
        # measured, a constant 0.85 veiled the village while the same value fed
        # through a texture did nothing at all. So opacity is a constant, and the
        # unevenness that makes it read as old glass rather than as fog comes
        # from the mottling driving diffuseColor, which does work.
        # Measured through the window: opacity 0.48 dropped the view's contrast
        # from 23 to 17, which is barely noticeable; 0.85 flattened it to 4,
        # which is fog on a screen rather than glass. The useful range is
        # between, so map frost across the whole span and default near the top.
        opacity = GLASS_OPACITY + (0.88 - GLASS_OPACITY) * GLASS_FROST
        rough = 0.06 + 0.55 * GLASS_FROST
        return f'''{i}def Material "{n}Mat"
{i}{{
{i}    token outputs:surface.connect = {base}/Surface.outputs:surface>
{i}    def Shader "stReader"
{i}    {{
{i}        uniform token info:id = "UsdPrimvarReader_float2"
{i}        token inputs:varname = "st"
{i}        float2 outputs:result
{i}    }}
{i}    def Shader "frostTex"
{i}    {{
{i}        uniform token info:id = "UsdUVTexture"
{i}        asset inputs:file = @textures/glass_frost.png@
{i}        float4 inputs:scale = (0.80, 0.86, 0.90, 1)
{i}        float4 inputs:bias = (0.15, 0.16, 0.18, 0)
{i}        float2 inputs:st.connect = {base}/stReader.outputs:result>
{i}        token inputs:wrapS = "clamp"
{i}        token inputs:wrapT = "clamp"
{i}        float3 outputs:rgb
{i}    }}
{i}    def Shader "Surface"
{i}    {{
{i}        uniform token info:id = "UsdPreviewSurface"
{i}        color3f inputs:diffuseColor.connect = {base}/frostTex.outputs:rgb>
{i}        float inputs:metallic = 0
{i}        float inputs:roughness = {rough:.2f}
{i}        float inputs:opacity = {opacity:.3f}
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

    def _window_material(self, indent):
        """A lit pane. Unlit and emissive so it holds its warmth in a dark
        village instead of going out with everything else."""
        i, n = indent, self.name
        # Rooms are not all lit the same. Three tiers is enough to stop the
        # village reading as a grid of identical rectangles.
        emit = {"A": (3.00, 1.85, 0.70),
                "B": (2.05, 1.28, 0.52)}.get(n[-1], (1.30, 0.78, 0.30))
        return f'''{i}def Material "{n}Mat"
{i}{{
{i}    token outputs:surface.connect = </TowerShell/{n}Mat/Surface.outputs:surface>
{i}    def Shader "Surface"
{i}    {{
{i}        uniform token info:id = "UsdPreviewSurface"
{i}        color3f inputs:diffuseColor = (0.05, 0.03, 0.01)
{i}        color3f inputs:emissiveColor = ({emit[0]}, {emit[1]}, {emit[2]})
{i}        float inputs:metallic = 0
{i}        float inputs:roughness = 1
{i}        token outputs:surface
{i}    }}
{i}}}
'''

    def _lamp_material(self, indent):
        """Street lamps, warm against the blue of a moonlit night.

        Emissive values run well above 1 so the heads still read as sources
        rather than pale dots once the night exposure pulls the scene down. The
        ground pools are the same colour an order of magnitude weaker — they are
        what makes the street look lit rather than merely dotted with lamps.
        """
        i, n = indent, self.name
        if n.startswith("LampPool_"):
            return self._lamp_pool_material(indent)
        emit = (5.60, 3.80, 1.65)
        diff = (0.35, 0.28, 0.16)
        return f'''{i}def Material "{n}Mat"
{i}{{
{i}    token outputs:surface.connect = </TowerShell/{n}Mat/Surface.outputs:surface>
{i}    def Shader "Surface"
{i}    {{
{i}        uniform token info:id = "UsdPreviewSurface"
{i}        color3f inputs:diffuseColor = ({diff[0]}, {diff[1]}, {diff[2]})
{i}        color3f inputs:emissiveColor = ({emit[0]}, {emit[1]}, {emit[2]})
{i}        float inputs:metallic = 0
{i}        float inputs:roughness = 0.6
{i}        token outputs:surface
{i}    }}
{i}}}
'''

    def _lamp_pool_material(self, indent):
        """The lit ground under a lamp. Diffuse is black and the gradient drives
        emission alone, so the disc fades to nothing at its rim instead of
        showing an edge."""
        i, n = indent, self.name
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
{i}    def Shader "poolTex"
{i}    {{
{i}        uniform token info:id = "UsdUVTexture"
{i}        asset inputs:file = @textures/lamp_pool.png@
{i}        float4 inputs:scale = (0.80, 0.54, 0.24, 1)
{i}        float2 inputs:st.connect = {base}/stReader.outputs:result>
{i}        token inputs:wrapS = "clamp"
{i}        token inputs:wrapT = "clamp"
{i}        float3 outputs:rgb
{i}    }}
{i}    def Shader "Surface"
{i}    {{
{i}        uniform token info:id = "UsdPreviewSurface"
{i}        color3f inputs:diffuseColor = (0, 0, 0)
{i}        color3f inputs:emissiveColor.connect = {base}/poolTex.outputs:rgb>
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
    write_glass_frost_texture()
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
        # UVs run across the whole window, not 0..1 per segment: otherwise the
        # frost pattern restarts at every segment and the pane reads as strips.
        u0 = (seg - SEG0) / float(SEG1 - SEG0)
        u1 = (seg + 1 - SEG0) / float(SEG1 - SEG0)
        uv = [(u0, 0.0), (u1, 0.0), (u1, 1.0), (u0, 1.0)]
        glass.face(quad, inward, uv)
        glass.face(list(reversed(quad)), outward, list(reversed(uv)))

    # --- diamond leading over the pane ---
    lead = Mesh("Leading", (0.10, 0.10, 0.12))
    if GLASS_LEAD:
        lead_r = glass_r - 0.025          # just inside the glass, toward the room
        arc0, arc1 = SEG0 * step_deg, SEG1 * step_deg
        width = lead_r * math.radians(arc1 - arc0)
        height = WINDOW_HEAD - WINDOW_SILL

        def lp(u, v):
            """Parametric point on the pane: u along the arc, v up from the sill."""
            t = math.radians(arc0) + u / lead_r
            return (lead_r * math.sin(t), WINDOW_SILL + v,
                    -lead_r * math.cos(t) - SEAT_Z)

        def inward_at(u):
            t = math.radians(arc0) + u / lead_r
            return (-math.sin(t), 0.0, math.cos(t))

        half = LEAD_WIDTH / 2.0
        for sign in (1.0, -1.0):
            # Diagonals of both families: u - sign*v = c.
            k = -int((height + width) / LEAD_SPACING) - 1
            while k * LEAD_SPACING <= width + height:
                c = k * LEAD_SPACING
                k += 1
                # Clip the line to the pane rectangle before drawing any of it,
                # rather than stepping along it and discarding what falls off.
                v0 = max(0.0, min((0.0 - c) * sign, (width - c) * sign))
                v1 = min(height, max((0.0 - c) * sign, (width - c) * sign))
                if v1 - v0 < 0.02:
                    continue
                steps = 6
                for i in range(steps):
                    va = v0 + (v1 - v0) * i / steps
                    vb = v0 + (v1 - v0) * (i + 1) / steps
                    ua, ub = c + sign * va, c + sign * vb
                    # Offset perpendicular to the came, in the pane's own plane.
                    du, dv = ub - ua, vb - va
                    ln = math.hypot(du, dv) or 1.0
                    ox, oy = -dv / ln * half, du / ln * half
                    quad = [lp(ua - ox, va - oy), lp(ub - ox, vb - oy),
                            lp(ub + ox, vb + oy), lp(ua + ox, va + oy)]
                    lead.face(quad, inward_at((ua + ub) / 2.0))

    parts = [floor, wall, roof, reveal, glass]
    if GLASS_LEAD and lead.pts:
        parts.append(lead)
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


# The village below, seen through the window. This is what gives parallax at eye
# level: the shaft is almost underfoot and only shows if you lean out, and the
# skydome sits at infinity and never shifts.
#
# The Medieval Village kit is modular — walls, corners and roofs on a 2 m grid,
# with no whole buildings — so houses are assembled here rather than placed.
#   wall panel                2.00 m wide x 3.12 m tall
#   Roof_RoundTiles_WxD       covers a W x D metre building, overhang included
WALL_MODULE_W = 2.00
STOREY_H      = 3.12

# The village sits in its own local frame, then gets placed in the window's view
# cone. Local +X runs along the main street, +Z crosses it.
VILLAGE_BEARING = 50.0     # deg from the desk
VILLAGE_DIST    = 46.0     # m from the tower
VILLAGE_TURN    = -18.0    # deg the village is rotated, so streets are not square on
WALL_RADIUS     = 45.0     # m — hugs the built area; wider left a ring of empty grass
WALL_HEIGHT_V   = 6.20     # m to the walkway
WALL_THICK_V    = 1.30
MERLON_H        = 1.10
GATE_HALF_ANGLE = 7.0      # deg of wall left open for the road
LIT_WINDOW      = 0.28     # share of upper windows with a light behind them
SQUARE_HALF     = 10.0     # half-width of the market square at the crossroads
SQUARE_LAMPS    = 8        # lamps ringing it
STREET_W        = 7.0      # main street
LANE_W          = 5.5      # cross lane


def village_to_world(vx, vz):
    """Village-local metres into the room's user-relative frame, on the ground."""
    t = math.radians(VILLAGE_TURN)
    rx = vx * math.cos(t) - vz * math.sin(t)
    rz = vx * math.sin(t) + vz * math.cos(t)
    b = math.radians(VILLAGE_BEARING)
    cx = VILLAGE_DIST * math.sin(b)
    cz = -VILLAGE_DIST * math.cos(b) - SEAT_Z
    return (cx + rx, cz + rz)


# Streets: (axis the street runs along, offset across, half-length)
STREETS = [
    ("x",   0.0, 36.0),
    ("x",  19.0, 32.0),
    ("x", -19.0, 32.0),
    ("z",   0.0, 27.0),
    ("z",  24.0, 22.0),
    ("z", -24.0, 22.0),
]


def village_layout():
    """Houses lining the streets, rejected where they would overlap.

    Deterministic, so the village never reshuffles between runs.
    """
    rng = random.Random(7)
    plots = []
    taken = []          # axis-aligned footprints already used, in village space
    # Street rows: depth is capped at 6 m. Streets are 19 m apart, so two
    # back-to-back rows of deeper houses simply cannot fit between them — which
    # is why the first attempt rejected nearly everything it tried to place.
    roofs = [(4, 4), (4, 6), (6, 4), (6, 6), (6, 4), (4, 4), (6, 6)]
    infill_roofs = [(4, 4), (4, 6), (6, 4)]

    def free(cx, cz, hx, hz):
        """Reject overlaps, keep street corridors clear, and leave the square."""
        # The two main streets already cross at the village origin; holding a
        # box clear around it turns that crossing into a proper market square.
        if abs(cx) < SQUARE_HALF + hx and abs(cz) < SQUARE_HALF + hz:
            return False
        for axis, fixed, _ in STREETS:
            width = (STREET_W if fixed == 0.0 else LANE_W) / 2.0 + 0.5
            if axis == "x" and abs(cz - fixed) < width + hz:
                return False
            if axis == "z" and abs(cx - fixed) < width + hx:
                return False
        for ox, oz, ohx, ohz in taken:
            if abs(cx - ox) < hx + ohx + 0.5 and abs(cz - oz) < hz + ohz + 0.5:
                return False
        return True

    for axis, fixed, span in STREETS:
        half_street = (STREET_W if fixed == 0.0 else LANE_W) / 2.0
        for side in (-1, 1):
            pos = -span
            while pos < span:
                w, d = rng.choice(roofs)
                # The house's width always runs along the street; its depth always
                # runs away from it. Getting these the wrong way round on the
                # cross lanes is what jammed the houses into each other.
                along, deep = w, d
                # Must exceed the clearance in free(), or every house rejects itself.
                setback = half_street + deep / 2.0 + 1.0
                if axis == "x":
                    cx, cz = pos + along / 2.0, fixed + side * setback
                    hx, hz = along / 2.0, deep / 2.0
                    yaw = 0.0 if side < 0 else 180.0
                else:
                    cx, cz = fixed + side * setback, pos + along / 2.0
                    hx, hz = deep / 2.0, along / 2.0
                    yaw = 90.0 if side < 0 else 270.0

                if free(cx, cz, hx, hz):
                    taken.append((cx, cz, hx, hz))
                    plots.append({
                        "vx": cx, "vz": cz, "w": w, "d": d,
                        "storeys": rng.choice([2, 2, 3, 3, 3, 4, 1]),
                        "yaw": yaw + rng.uniform(-2.0, 2.0),
                        "brick": rng.random() < 0.45,
                        "timber": rng.random() < 0.35,
                    })
                    # Terraced: near enough touching, as a walled town would be.
                    pos += along + rng.uniform(0.1, 0.7)
                else:
                    pos += 2.0

    # Infill. Street frontages alone leave the blocks hollow, and everything
    # square to the grid looks planned rather than grown. These sit at any angle
    # in whatever space is left.
    for _ in range(2500):
        ang = rng.uniform(0, 2 * math.pi)
        rad = math.sqrt(rng.random()) * (WALL_RADIUS - 7.0)
        cx, cz = rad * math.sin(ang), rad * math.cos(ang)
        w, d = rng.choice(infill_roofs)
        yaw = rng.uniform(0, 360)
        # Conservative half-extents, since the footprint is turned freely.
        half = max(w, d) / 2.0
        if not free(cx, cz, half, half):
            continue
        taken.append((cx, cz, half, half))
        plots.append({
            "vx": cx, "vz": cz, "w": w, "d": d,
            "storeys": rng.choice([1, 2, 2, 3, 3]),
            "yaw": yaw,
            "brick": rng.random() < 0.5,
            "timber": rng.random() < 0.4,
        })
    return plots


GROUND_RADIUS = 137.0
# The horizon: the flat ground disc used to end in a hard circular cut against
# the skydome. A ring of hills hides that join and gives the eye somewhere to
# stop. Starts beyond the village, which reaches about 89 m from the tower.
HILL_IN, HILL_OUT = 102.0, 138.0
HILL_NEAR = 11.0   # m, rolling foreground hills
HILL_FAR  = 34.0   # m, the range behind them
HILL_BASE = 7.0    # m, so the outer rim never drops back to flat


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


def _ridge(t, *waves):
    """Sum of sines, 0..1.

    Every frequency is an integer multiple of theta so the ridge line closes on
    itself: any other frequency leaves a visible seam where the ring wraps.
    """
    total = 0.0
    scale = 0.0
    for n, amp, phase in waves:
        total += amp * math.sin(n * t + phase)
        scale += amp
    return (total / scale + 1.0) * 0.5


def hill_height(r, t):
    """Height of the horizon ring at radius r, bearing t."""
    if r <= HILL_IN:
        return 0.0
    u = min((r - HILL_IN) / (HILL_OUT - HILL_IN), 1.0)

    def smooth(a, b, x):
        if b == a:
            return 0.0 if x < a else 1.0
        k = min(max((x - a) / (b - a), 0.0), 1.0)
        return k * k * (3.0 - 2.0 * k)

    near = _ridge(t, (3, 0.55, 0.7), (7, 0.33, 2.1), (13, 0.20, 4.3),
                  (23, 0.11, 1.2), (37, 0.06, 2.8), (53, 0.035, 0.9))
    far = _ridge(t, (2, 0.60, 1.9), (5, 0.30, 0.4), (11, 0.18, 3.3),
                 (19, 0.09, 5.1), (29, 0.05, 2.2))

    # Where each range *starts* varies with bearing too. Without this every
    # slope begins at the same radius and the whole thing reads as a ring
    # around the tower rather than as country going on past it.
    near_at = 0.02 + 0.15 * _ridge(t, (2, 0.6, 3.1), (5, 0.3, 1.4))
    far_at = 0.28 + 0.20 * _ridge(t, (3, 0.5, 2.2), (7, 0.25, 5.0))

    return (0.10
            + HILL_NEAR * smooth(near_at, near_at + 0.30, u) * near
            + smooth(far_at, far_at + 0.52, u) * (HILL_BASE + HILL_FAR * far))


def hills():
    """A ring of hills and a range behind them, closing off the horizon.

    Seen from the tower the eye is about 27 m above the plain, so the near hills
    stay below the horizon and only the far peaks break the skyline -- which is
    what makes it read as distance rather than as a wall.
    """
    m = Mesh("Hills", (0.30, 0.33, 0.26), texture="ground", tint=(0.62, 0.70, 0.62))
    y0 = -TOWER_ELEV
    cz = -SEAT_Z
    segs, rings = 180, 26
    TILE_H = 17.0

    def gp(r, t):
        return (r * math.sin(t), y0 + hill_height(r, t), -r * math.cos(t) + cz)

    def normal(r, t):
        # Finite differences: the height is a sum of sines and a smoothstep, so
        # differentiating it by hand is more error than it is worth.
        e = 0.6
        dr = (hill_height(r + e, t) - hill_height(r - e, t)) / (2.0 * e)
        da = e / max(r, 1.0)
        dt = (hill_height(r, t + da) - hill_height(r, t - da)) / (2.0 * e)
        rx, rz = math.sin(t), -math.cos(t)      # radial unit vector
        tx, tz = math.cos(t), math.sin(t)       # tangential unit vector
        nx = -dr * rx - dt * tx
        nz = -dr * rz - dt * tz
        n = math.sqrt(nx * nx + 1.0 + nz * nz)
        return (nx / n, 1.0 / n, nz / n)

    for iy in range(rings):
        # Denser rings toward the outside, where the peaks and the silhouette are.
        r0 = HILL_IN + (HILL_OUT - HILL_IN) * (iy / rings) ** 0.85
        r1 = HILL_IN + (HILL_OUT - HILL_IN) * ((iy + 1) / rings) ** 0.85
        for ix in range(segs):
            t0 = 2.0 * math.pi * ix / segs
            t1 = 2.0 * math.pi * (ix + 1) / segs
            quad = [gp(r0, t0), gp(r0, t1), gp(r1, t1), gp(r1, t0)]
            nrm = [normal(r0, t0), normal(r0, t1), normal(r1, t1), normal(r1, t0)]
            m.face(quad, nrm, [(q[0] / TILE_H, q[2] / TILE_H) for q in quad])
    return m.material_usda() + m.usda()


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


def village_streets():
    """Cobbled main street and cross lane, laid a little above the ground so they
    do not z-fight with it."""
    m = Mesh("Streets", (0.42, 0.40, 0.38), texture="street")
    y = -TOWER_ELEV + 0.02
    TILE_S = 4.0

    def strip(x0, x1, z0, z1):
        corners = [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]
        pts, uvs = [], []
        for vx, vz in corners:
            wx, wz = village_to_world(vx, vz)
            pts.append((wx, y, wz))
            uvs.append((vx / TILE_S, vz / TILE_S))
        m.face(pts, (0.0, 1.0, 0.0), uvs)

    strip(-42.0, 42.0, -STREET_W / 2, STREET_W / 2)
    strip(-LANE_W / 2, LANE_W / 2, -30.0, -STREET_W / 2)
    strip(-LANE_W / 2, LANE_W / 2, STREET_W / 2, 30.0)
    return m.material_usda() + m.usda()


def village_wall():
    """The curtain wall: a crenellated stone ring with a gate on the main street.

    Generated rather than assembled — it is architecture, like the tower, and a
    kit wall panel repeated two hundred times would cost far more than this does.
    """
    m = Mesh("VillageWall", (0.44, 0.43, 0.41), texture=WALL_TEXTURE, tint=WALL_TINT)
    y0 = -TOWER_ELEV
    segments = 160
    r_in = WALL_RADIUS - WALL_THICK_V / 2.0
    r_out = WALL_RADIUS + WALL_THICK_V / 2.0
    step = 360.0 / segments
    circumference = 2.0 * math.pi * WALL_RADIUS
    wraps = max(1, round(circumference / 3.0))

    def wp(theta_deg, radius, y):
        t = math.radians(theta_deg)
        wx, wz = village_to_world(radius * math.sin(t), -radius * math.cos(t))
        return (wx, y0 + y, wz)

    for i in range(segments):
        a0, a1 = i * step, (i + 1) * step
        mid = (a0 + a1) / 2.0
        # The gate: the main street leaves through local +X, i.e. 90 degrees.
        if abs(((mid - 90.0 + 180) % 360) - 180) < GATE_HALF_ANGLE:
            continue
        u0, u1 = a0 / 360.0 * wraps, a1 / 360.0 * wraps
        t = math.radians(mid)
        n_out = (math.sin(t), 0.0, -math.cos(t))
        n_in = (-math.sin(t), 0.0, math.cos(t))
        vh = WALL_HEIGHT_V / 3.0

        m.face([wp(a0, r_out, 0), wp(a1, r_out, 0),
                wp(a1, r_out, WALL_HEIGHT_V), wp(a0, r_out, WALL_HEIGHT_V)], n_out,
               [(u0, 0), (u1, 0), (u1, vh), (u0, vh)])
        m.face([wp(a0, r_in, 0), wp(a1, r_in, 0),
                wp(a1, r_in, WALL_HEIGHT_V), wp(a0, r_in, WALL_HEIGHT_V)], n_in,
               [(u0, 0), (u1, 0), (u1, vh), (u0, vh)])
        m.face([wp(a0, r_in, WALL_HEIGHT_V), wp(a1, r_in, WALL_HEIGHT_V),
                wp(a1, r_out, WALL_HEIGHT_V), wp(a0, r_out, WALL_HEIGHT_V)],
               (0.0, 1.0, 0.0), [(u0, 0), (u1, 0), (u1, 0.4), (u0, 0.4)])

        # Merlons: every other pair of segments carries one.
        if i % 4 < 2:
            top = WALL_HEIGHT_V + MERLON_H
            for radius, nrm in ((r_out, n_out), (r_in, n_in)):
                m.face([wp(a0, radius, WALL_HEIGHT_V), wp(a1, radius, WALL_HEIGHT_V),
                        wp(a1, radius, top), wp(a0, radius, top)], nrm,
                       [(u0, 0), (u1, 0), (u1, 0.4), (u0, 0.4)])
            m.face([wp(a0, r_in, top), wp(a1, r_in, top),
                    wp(a1, r_out, top), wp(a0, r_out, top)], (0.0, 1.0, 0.0),
                   [(u0, 0), (u1, 0), (u1, 0.4), (u0, 0.4)])
            if i % 4 == 0:      # the face left exposed by the gap beside it
                m.face([wp(a0, r_in, WALL_HEIGHT_V), wp(a0, r_out, WALL_HEIGHT_V),
                        wp(a0, r_out, top), wp(a0, r_in, top)],
                       (math.cos(t), 0.0, math.sin(t)),
                       [(0, 0), (0.4, 0), (0.4, 0.4), (0, 0.4)])
    return m.material_usda() + m.usda()


def _write_gray_png(path, size, sample):
    """Write a size x size 8-bit greyscale PNG from sample(u, v) in 0..1.

    Hand-rolled rather than pulled from a library: these are small procedural
    textures generated at build time, and the project has no imaging dependency.
    """
    import binascii
    import struct
    import zlib

    rows = bytearray()
    for y in range(size):
        rows.append(0)                       # PNG filter byte: none
        for x in range(size):
            v = sample((x + 0.5) / size, (y + 0.5) / size)
            rows.append(int(max(0.0, min(1.0, v)) * 255))

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", binascii.crc32(tag + data) & 0xFFFFFFFF))

    path.write_bytes(b"\x89PNG\r\n\x1a\n"
                     + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 0, 0, 0, 0))
                     + chunk(b"IDAT", zlib.compress(bytes(rows), 9))
                     + chunk(b"IEND", b""))
    return path


def _value_noise(x, y, seed):
    """Smooth lattice noise, deterministic across runs."""
    def h(ix, iy):
        n = (ix * 374761393 + iy * 668265263 + seed * 2147483647) & 0xFFFFFFFF
        n = (n ^ (n >> 13)) * 1274126177 & 0xFFFFFFFF
        return ((n ^ (n >> 16)) & 0xFFFFFFFF) / 0xFFFFFFFF

    ix, iy = math.floor(x), math.floor(y)
    fx, fy = x - ix, y - iy
    u = fx * fx * (3 - 2 * fx)
    v = fy * fy * (3 - 2 * fy)
    a = h(ix, iy) + (h(ix + 1, iy) - h(ix, iy)) * u
    b = h(ix, iy + 1) + (h(ix + 1, iy + 1) - h(ix, iy + 1)) * u
    return a + (b - a) * v


def write_glass_frost_texture():
    """Mottling for the window pane.

    RealityKit will not blur what is behind a transparent surface -- roughness
    drives reflection, not transmission -- so the pane cannot literally defocus
    the village. What it can do is veil it: an uneven, milky sheet that flattens
    contrast and swallows fine detail while colour and light still read through.
    Uneven is the point; a flat wash looks like fog on a screen, whereas old
    glass is thick in some places and thin in others.
    """
    def sample(u, v):
        n = (0.55 * _value_noise(u * 4.0, v * 3.0, 11)
             + 0.30 * _value_noise(u * 9.0, v * 7.0, 29)
             + 0.15 * _value_noise(u * 19.0, v * 15.0, 47))
        # Streak it slightly along the pane, the way drawn glass runs.
        n = 0.8 * n + 0.2 * _value_noise(u * 2.0, v * 26.0, 71)
        return 0.15 + 0.85 * n

    return _write_gray_png(OUT.parent / "textures" / "glass_frost.png", 256, sample)


def write_lamp_pool_texture():
    """A soft radial gradient for the pool of light under each street lamp.

    A flat disc of constant emissive colour reads as a patch of sand, not as
    light. The falloff has to be in the texture. Written here rather than
    committed as a binary, and with no third-party imaging dependency.
    """
    def sample(u, v):
        r = min(1.0, math.hypot(u * 2.0 - 1.0, v * 2.0 - 1.0))
        # Eased to exactly zero at the rim so the disc has no visible edge
        # against the dark ground. The exponent sets how far the glow carries:
        # squared dies close to the post, so keep it gentler.
        return (1.0 - r) ** 1.6

    return _write_gray_png(OUT.parent / "textures" / "lamp_pool.png", 128, sample)


def village_lamps():
    """Street lamps. Emissive only — thirty more point lights would cost far more
    than they are worth for something forty metres away behind glass."""
    write_lamp_pool_texture()
    posts = Mesh("LampPosts", (0.16, 0.15, 0.14), texture="roof", tint=(0.30, 0.28, 0.26))
    glows = []
    y0 = -TOWER_ELEV
    spots = []
    for x in range(-36, 40, 9):
        spots.append((float(x), -STREET_W / 2 - 0.9))
        spots.append((float(x), STREET_W / 2 + 0.9))
    for z in range(-26, 30, 9):
        spots.append((-LANE_W / 2 - 0.9, float(z)))

    # A ring around the market square. These are the closest lamps to the tower,
    # so they are the ones that get real point lights rather than only a glow.
    for k in range(SQUARE_LAMPS):
        a = 2.0 * math.pi * k / SQUARE_LAMPS
        spots.append((math.cos(a) * (SQUARE_HALF - 2.2),
                      math.sin(a) * (SQUARE_HALF - 2.2)))

    for index, (vx, vz) in enumerate(spots):
        wx, wz = village_to_world(vx, vz)
        for lo, hi, half in ((0.0, 3.1, 0.07), (3.1, 3.35, 0.16)):
            for sx, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                pass
        # Simple square post, then a glowing head.
        for face_i in range(4):
            ang = math.radians(face_i * 90)
            nx, nz = math.sin(ang), math.cos(ang)
            tx, tz = math.cos(ang), -math.sin(ang)
            hwv = 0.07
            corners = [
                (wx + nx * hwv + tx * hwv, y0, wz + nz * hwv + tz * hwv),
                (wx + nx * hwv - tx * hwv, y0, wz + nz * hwv - tz * hwv),
                (wx + nx * hwv - tx * hwv, y0 + 3.1, wz + nz * hwv - tz * hwv),
                (wx + nx * hwv + tx * hwv, y0 + 3.1, wz + nz * hwv + tz * hwv)]
            posts.face(corners, (nx, 0.0, nz), [(0, 0), (0.1, 0), (0.1, 1.5), (0, 1.5)])
        head = Mesh(f"Lamp_{index}", (1.0, 0.80, 0.45),
                    translate=(wx, y0 + 3.32, wz))
        sphere(head, (0.0, 0.0, 0.0), 0.15, 8, 6)
        glows.append(head.material_usda() + head.usda())

        # A pool of light on the cobbles under each lamp. Cheaper than the point
        # light it stands in for, and at forty metres it reads the same.
        pool = Mesh(f"LampPool_{index}", (1.0, 0.80, 0.45),
                    texture="lamp_pool", translate=(wx, y0 + 0.03, wz))
        seg, rad = 28, 3.0
        for k in range(seg):
            a0 = 2.0 * math.pi * k / seg
            a1 = 2.0 * math.pi * (k + 1) / seg
            c0, s0 = math.cos(a0), math.sin(a0)
            c1, s1 = math.cos(a1), math.sin(a1)
            pool.face([(0.0, 0.0, 0.0), (c0 * rad, 0.0, s0 * rad),
                       (c1 * rad, 0.0, s1 * rad)],
                      (0.0, 1.0, 0.0),
                      [(0.5, 0.5), (0.5 + c0 * 0.5, 0.5 + s0 * 0.5),
                       (0.5 + c1 * 0.5, 0.5 + s1 * 0.5)])
        glows.append(pool.material_usda() + pool.usda())
    return posts.material_usda() + posts.usda() + "".join(glows)


def village():
    """Houses assembled from the modular kit, lining the streets."""
    out = []
    placements = {}
    glows = [Mesh(f"WinGlow_{k}", (1.0, 0.74, 0.38)) for k in ("A", "B", "C")]
    ground_y = -TOWER_ELEV
    counter = [0]
    rng = random.Random(11)

    for index, plot in enumerate(village_layout()):
        w, d, storeys = plot["w"], plot["d"], plot["storeys"]
        yaw = plot["yaw"]
        cx, cz = village_to_world(plot["vx"], plot["vz"])
        ry = math.radians(yaw)
        cos_y, sin_y = math.cos(ry), math.sin(ry)

        group = f"House{index:02d}"

        def place(name, lx, ly, lz, local_yaw, group=group):
            # Positions are baked to world space here but grouped per building,
            # so tools/merge_town.py can join each house into a single mesh.
            counter[0] += 1
            wx = cx + lx * cos_y + lz * sin_y
            wz = cz - lx * sin_y + lz * cos_y
            # Full XYZ euler, not just yaw: tools/edit_house.py lets a house be
            # rearranged in Reality Composer Pro, and nothing there stops you
            # tilting a piece.
            placements.setdefault(group, []).append(
                [name, round(wx, 4), round(ground_y + ly, 4), round(wz, 4),
                 0.0, round(yaw + local_yaw, 2), 0.0])
            return ""

        def lit_window(lx, ly, lz, nx, nz):
            """A warm pane just proud of the wall, facing out of the house.

            The outward direction comes from which wall this is, not from the
            kit module's own axes -- the modules disagree about which way is
            out, and a pane on the wrong side is simply invisible inside a
            sealed house.
            """
            wx = cx + lx * cos_y + lz * sin_y
            wz = cz - lx * sin_y + lz * cos_y
            wnx = nx * cos_y + nz * sin_y
            wnz = -nx * sin_y + nz * cos_y
            tx, tz = wnz, -wnx
            # Just clear of the wall. Further out and the pane visibly floats.
            px, pz = wx + wnx * 0.21, wz + wnz * 0.21
            cy = ground_y + ly + 1.92
            g = glows[rng.randrange(len(glows))]
            g.face([(px - tx * 0.50, cy - 0.62, pz - tz * 0.50),
                    (px + tx * 0.50, cy - 0.62, pz + tz * 0.50),
                    (px + tx * 0.50, cy + 0.62, pz + tz * 0.50),
                    (px - tx * 0.50, cy + 0.62, pz - tz * 0.50)],
                   (wnx, 0.0, wnz))

        brick = plot["brick"]
        wall = "Wall_UnevenBrick_Straight" if brick else "Wall_Plaster_Straight"
        if plot["timber"] and not brick:
            wall = "Wall_Plaster_WoodGrid"
        window = ("Wall_UnevenBrick_Window_Wide_Round" if brick
                  else "Wall_Plaster_Window_Wide_Round")
        corner = "Corner_Exterior_Brick" if brick else "Corner_Exterior_Wood"
        shutter = "WindowShutters_Wide_Round_Closed"
        hw, hd = w / 2.0, d / 2.0
        across, deep = int(w / WALL_MODULE_W), int(d / WALL_MODULE_W)

        for storey in range(storeys):
            ly = storey * STOREY_H
            for i in range(across):
                lx = -hw + WALL_MODULE_W * (i + 0.5)
                if storey == 0:
                    front = ("Wall_Plaster_Door_Round"
                             if (i == across // 2 and not brick) else wall)
                else:
                    front = window
                out.append(place(front, lx, ly, -hd, 0.0))
                if front == window:
                    out.append(place(shutter, lx, ly, -hd, 0.0))
                    if rng.random() < LIT_WINDOW:
                        lit_window(lx, ly, -hd, 0.0, -1.0)
                out.append(place(window if storey else wall, lx, ly, hd, 180.0))
                if storey:
                    out.append(place(shutter, lx, ly, hd, 180.0))
                    if rng.random() < LIT_WINDOW:
                        lit_window(lx, ly, hd, 0.0, 1.0)
            for i in range(deep):
                lz = -hd + WALL_MODULE_W * (i + 0.5)
                out.append(place(window if storey else wall, -hw, ly, lz, 90.0))
                out.append(place(window if storey else wall, hw, ly, lz, 270.0))
                if storey:
                    out.append(place(shutter, -hw, ly, lz, 90.0))
                    out.append(place(shutter, hw, ly, lz, 270.0))
                    if rng.random() < LIT_WINDOW:
                        lit_window(-hw, ly, lz, -1.0, 0.0)
                    if rng.random() < LIT_WINDOW:
                        lit_window(hw, ly, lz, 1.0, 0.0)
            for sx, sz in ((-hw, -hd), (hw, -hd), (hw, hd), (-hw, hd)):
                out.append(place(corner, sx, ly, sz, 0.0))

        top = storeys * STOREY_H
        out.append(place(f"Roof_RoundTiles_{w}x{d}", 0.0, top, 0.0, 0.0))
        out.append(place("Prop_Chimney", hw - 1.0, top, hd - 1.4, 0.0))

        # Dormers, balconies and vines: the kit has only one roof style, so
        # variety has to come from what is hung on the buildings.
        if storeys >= 2 and rng.random() < 0.45:
            out.append(place("Roof_Dormer_RoundTile", rng.uniform(-hw + 1, hw - 1),
                             top - 0.4, -hd + 0.3, 0.0))
        if storeys >= 3 and rng.random() < 0.4:
            out.append(place("Balcony_Simple_Straight",
                             0.0, STOREY_H * (storeys - 1), -hd, 0.0))
        if rng.random() < 0.3:
            out.append(place("Prop_Support", -hw - 0.2, 0.0, -hd + 0.4, 0.0))

        # A little clutter against the street frontage.
        if rng.random() < 0.5:
            out.append(place(rng.choice(["Prop_Crate", "Prop_Wagon"]),
                             rng.uniform(-hw, hw), 0.0, -hd - 1.6, rng.uniform(0, 360)))
        if rng.random() < 0.35:
            out.append(place("Prop_WoodenFence_Single", -hw - 0.6, 0.0,
                             rng.uniform(-hd, hd), 90.0))

    # Hand edits win over the procedural layout. A house rearranged in Reality
    # Composer Pro and imported with tools/edit_house.py lands here, and survives
    # every regeneration until its override file is deleted.
    edits = Path(__file__).parent.parent / "assets" / "house_edits"
    applied = []
    for edit in sorted(edits.glob("*.json")) if edits.exists() else []:
        if edit.stem in placements:
            placements[edit.stem] = json.loads(edit.read_text())
            applied.append(edit.stem)
        else:
            print(f"  ! {edit.stem} has an edit but no such building; ignoring")
    if applied:
        print(f"  hand-edited: {', '.join(applied)}")

    with open(Path(__file__).parent.parent / "build" / "town_placements.json", "w") as fh:
        json.dump(placements, fh)
    total = sum(len(v) for v in placements.values())
    baked = sum(1 for g in placements
                if (OUT.parent / "village" / "merged" / f"{g}.usdc").exists())
    how = (f"batched into {baked} baked meshes" if MERGED and baked
           else "UNBATCHED -- run tools/merge_town.py")
    print(f"  town: {total} module placements in {len(placements)} buildings, {how}")
    lit = sum(len(g.pts) for g in glows) // 4
    print(f"  windows lit: {lit}")
    panes = "".join(g.material_usda() + g.usda() for g in glows if g.pts)
    return "".join(out) + emit_placements(placements) + panes


def emit_placements(placements):
    """One Xform per building.

    Each holds either the individual kit modules, or -- once tools/merge_town.py
    has baked them -- a single merged mesh. Merging trades about 30 MB of
    duplicated vertices for a 40x cut in draw calls, and keeping one Xform per
    building means the renderer can still frustum-cull the town a house at a time.
    """
    merged_dir = OUT.parent / "village" / "merged"
    out = []
    for group, rows in sorted(placements.items()):
        merged = merged_dir / f"{group}.usdc"
        out.append(f'    def Xform "Town_{group}"\n    {{\n')
        if MERGED and merged.exists():
            out.append(f'        def "Baked" (\n'
                       f'            prepend references = '
                       f'@village/merged/{group}.usdc@\n'
                       f'        )\n        {{\n        }}\n')
        else:
            for i, (name, x, y, z, rx, ry, rz) in enumerate(rows):
                out.append(f'        def "M{i}" (\n'
                           f'            prepend references = @village/{name}.usdc@\n'
                           f'        )\n'
                           f'        {{\n'
                           f'            double3 xformOp:translate = '
                           f'({x:.3f}, {y:.3f}, {z:.3f})\n'
                           f'            float3 xformOp:rotateXYZ = '
                           f'({rx:.2f}, {ry:.2f}, {rz:.2f})\n'
                           f'            uniform token[] xformOpOrder = '
                           f'["xformOp:translate", "xformOp:rotateXYZ"]\n'
                           f'        }}\n')
        out.append('    }\n')
    return "".join(out)


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
    hood = village() + village_streets() + village_wall() + village_lamps()
    grnd = ground() + hills()
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
    print(f"  village: {len(village_layout())} houses inside a {WALL_RADIUS:.0f} m wall")
    print(f"  shaft: {TOWER_ELEV:.0f} m down to the ground, battered to "
          f"{(R + WALL_THICK) * SHAFT_BATTER * 2:.1f} m across at the base")


if __name__ == "__main__":
    main()
