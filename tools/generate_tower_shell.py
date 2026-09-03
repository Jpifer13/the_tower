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
from pathlib import Path

# ── Dimensions (docs/design/design-doc.md) ───────────────────────────────────
DIAMETER      = 5.5    # m, internal
WALL_HEIGHT   = 3.0    # m, floor to eaves
APEX_HEIGHT   = 6.0    # m, floor to roof apex
SEGMENTS      = 96     # around the circle

# visionOS puts the user at the origin looking down -Z, so the room is authored in
# USER-RELATIVE space: origin = your seat, -Z = the desk you face, +X = your right.
WINDOW_CENTRE = 55.0   # degrees; 0=desk(front), +ve=toward your right
FIRE_CENTRE   = -55.0  # mirrored, to your left
WINDOW_WIDTH  = 1.30   # m, along the arc
WINDOW_SILL   = 0.40   # m
WINDOW_HEAD   = 2.60   # m

DESK_W, DESK_D, DESK_H = 1.83, 0.91, 0.75   # 6ft x 3ft
ENVELOPE_W, ENVELOPE_D = 2.70, 3.00          # real clear floor
SEAT_SETBACK  = 0.30   # m you sit back from the desk edge

OUT = Path(__file__).parent.parent / (
    "app/Packages/RealityKitContent/Sources/RealityKitContent/"
    "RealityKitContent.rkassets/TowerShell.usda")

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


class Mesh:
    def __init__(self, name, color):
        self.name, self.color = name, color
        self.pts, self.counts, self.idx, self.normals = [], [], [], []

    def face(self, verts, normal):
        base = len(self.pts)
        self.pts.extend(verts)
        self.normals.extend([normal] * len(verts))
        self.counts.append(len(verts))
        self.idx.extend(range(base, base + len(verts)))

    def material_usda(self, indent="    "):
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
{i}    color3f[] primvars:displayColor = [({self.color[0]}, {self.color[1]}, {self.color[2]})]
{i}    rel material:binding = </TowerShell/{self.name}Mat>
{i}    uniform token subdivisionScheme = "none"
{i}}}
'''


def build():
    half = math.degrees(WINDOW_WIDTH / 2.0 / R)
    w0, w1 = WINDOW_CENTRE - half, WINDOW_CENTRE + half

    floor = Mesh("Floor", (0.28, 0.26, 0.24))
    wall  = Mesh("Wall",  (0.46, 0.44, 0.41))
    roof  = Mesh("Roof",  (0.20, 0.16, 0.13))

    step = 360.0 / SEGMENTS
    for s in range(SEGMENTS):
        a, b = s * step, (s + 1) * step
        mid = (a + b) / 2.0

        # Floor fan (centre of the room, not the seat)
        floor.face([(0.0, 0.0, -SEAT_Z), p(a, 0.0), p(b, 0.0)], (0.0, 1.0, 0.0))

        # Inward-facing wall normal
        t = math.radians(mid)
        n = (-math.sin(t), 0.0, -math.cos(t))

        in_window = (w0 <= mid <= w1)
        if in_window:
            # Below the sill and above the head; the gap is the opening.
            for lo, hi in ((0.0, WINDOW_SILL), (WINDOW_HEAD, WALL_HEIGHT)):
                wall.face([p(a, lo), p(b, lo), p(b, hi), p(a, hi)], n)
        else:
            wall.face([p(a, 0.0), p(b, 0.0), p(b, WALL_HEIGHT), p(a, WALL_HEIGHT)], n)

        # Cone to the apex
        roof.face([p(a, WALL_HEIGHT), p(b, WALL_HEIGHT), (0.0, APEX_HEIGHT, -SEAT_Z)],
                  (-math.sin(t) * 0.5, -0.5, -math.cos(t) * 0.5))

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
{shell}{desk}{fire}{human}{envelope}}}
''')
    print(f"wrote {OUT.relative_to(Path(__file__).parent.parent)}")
    print(f"  {DIAMETER} m across, eaves {WALL_HEIGHT} m, apex {APEX_HEIGHT} m")
    print(f"  window {WINDOW_WIDTH} m wide at {WINDOW_CENTRE}deg (right), {WINDOW_SILL}-{WINDOW_HEAD} m")
    print(f"  origin = seat; desk edge {abs(desk_z) - DESK_D / 2.0:.2f} m ahead")
    print(f"  wall ahead {R + SEAT_Z:.2f} m, room behind you {R - SEAT_Z:.2f} m")


if __name__ == "__main__":
    main()
