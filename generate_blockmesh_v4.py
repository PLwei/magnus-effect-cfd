#!/usr/bin/env python3
"""Generate 16-block blockMeshDict with rectangular far-field."""
import math, os
from collections import Counter

D = 4.0; R = 2.0; Ri = 5.0
Up = 40.0; Down = 80.0; Cross = 40.0
H = 0.5
SQ2 = math.sqrt(2.0)/2.0

verts = []
names = []

def add(name, x, y, z):
    names.append(name)
    verts.append((x, y, z))
    return len(verts) - 1

# Original 16 bottom vertices
E0 = add("E0",  R,  0, -H); N0 = add("N0",  0,  R, -H)
W0 = add("W0", -R,  0, -H); S0 = add("S0",  0, -R, -H)
E1 = add("E1", Ri,  0, -H); N1 = add("N1",  0, Ri, -H)
W1 = add("W1",-Ri,  0, -H); S1 = add("S1",  0,-Ri, -H)
E2 = add("E2",Down, 0, -H); N2 = add("N2",  0,Cross,-H)
W2 = add("W2",-Up,  0, -H); S2 = add("S2",  0,-Cross,-H)
SW = add("SW",-Up,-Cross,-H); SE = add("SE",Down,-Cross,-H)
NE = add("NE",Down,Cross,-H); NW = add("NW",-Up,Cross,-H)

# New cylinder vertices at 45-degree positions (R=2)
NE0 = add("NE0",  R*SQ2,  R*SQ2, -H)
NW0 = add("NW0", -R*SQ2,  R*SQ2, -H)
SW0 = add("SW0", -R*SQ2, -R*SQ2, -H)
SE0 = add("SE0",  R*SQ2, -R*SQ2, -H)

# New mid-ring vertices at 45-degree positions (R=5)
NE1 = add("NE1",  Ri*SQ2,  Ri*SQ2, -H)
NW1 = add("NW1", -Ri*SQ2,  Ri*SQ2, -H)
SW1 = add("SW1", -Ri*SQ2, -Ri*SQ2, -H)
SE1 = add("SE1",  Ri*SQ2, -Ri*SQ2, -H)

# New far-field vertices at rectangular edge midpoints
N2E = add("N2E",  40,  40, -H)   # top edge, right half midpoint
N2W = add("N2W", -20,  40, -H)   # top edge, left half midpoint
E2N = add("E2N",  80,  20, -H)   # right edge, upper half midpoint
E2S = add("E2S",  80, -20, -H)   # right edge, lower half midpoint
S2E = add("S2E",  40, -40, -H)   # bottom edge, right half midpoint
S2W = add("S2W", -20, -40, -H)   # bottom edge, left half midpoint
W2N = add("W2N", -40,  20, -H)   # left edge, upper half midpoint
W2S = add("W2S", -40, -20, -H)   # left edge, lower half midpoint

Nbot = len(verts)
for i in range(Nbot):
    vx, vy, vz = verts[i]
    add(f"top_{i}", vx, vy, H)

def signed_area2(indices):
    s = 0.0
    for i in range(len(indices)):
        v1 = (verts[indices[i]][0], verts[indices[i]][1])
        v2 = (verts[indices[(i+1)%len(indices)]][0], verts[indices[(i+1)%len(indices)]][1])
        s += v1[0]*v2[1] - v2[0]*v1[1]
    return s

def make_ccw(bot_idx):
    return tuple(reversed(bot_idx)) if signed_area2(bot_idx) < 0 else tuple(bot_idx)

def hex_str(bot_idx, nx, ny, nz, gx=1, gy=1):
    bot = list(bot_idx)
    top = [i + Nbot for i in bot]
    return f"    hex ({' '.join(map(str, bot + top))}) ({nx} {ny} {nz}) simpleGrading ({gx} {gy} 1)"

# 16 blocks: 8 inner + 8 outer (4 edge + 4 corner)
# Inner blocks: 50 radial, 15 arc (half the original arc, same resolution)
# Edge blocks: 40 radial, 15 arc
# Corner blocks: 40 x 40

raw = [
    # 8 inner blocks (radial grading=5 clusters cells near cylinder wall)
    ((E0,  E1,  NE1, NE0), 50, 15, 1, 5, 1),
    ((NE0, NE1, N1,  N0),  50, 15, 1, 5, 1),
    ((N0,  N1,  NW1, NW0), 50, 15, 1, 5, 1),
    ((NW0, NW1, W1,  W0),  50, 15, 1, 5, 1),
    ((W0,  W1,  SW1, SW0), 50, 15, 1, 5, 1),
    ((SW0, SW1, S1,  S0),  50, 15, 1, 5, 1),
    ((S0,  S1,  SE1, SE0), 50, 15, 1, 5, 1),
    ((SE0, SE1, E1,  E0),  50, 15, 1, 5, 1),

    # 8 edge outer blocks (uniform)
    ((E1,  E2,  E2N, NE1), 40, 15, 1, 1, 1),
    ((NE1, N2E, N2,  N1),  40, 15, 1, 1, 1),
    ((N1,  N2,  N2W, NW1), 40, 15, 1, 1, 1),
    ((NW1, W2N, W2,  W1),  40, 15, 1, 1, 1),
    ((W1,  W2,  W2S, SW1), 40, 15, 1, 1, 1),
    ((SW1, S2W, S2,  S1),  40, 15, 1, 1, 1),
    ((S1,  S2,  S2E, SE1), 40, 15, 1, 1, 1),
    ((SE1, E2S, E2,  E1),  40, 15, 1, 1, 1),

    # 4 corner outer blocks (uniform)
    ((NE1, E2N, NE,  N2E), 40, 40, 1, 1, 1),
    ((NW1, W2N, NW,  N2W), 40, 40, 1, 1, 1),
    ((SW1, S2W, SW,  W2S), 40, 40, 1, 1, 1),
    ((SE1, E2S, SE,  S2E), 40, 40, 1, 1, 1),
]

blocks = [(make_ccw(bot), nx, ny, nz, gx, gy) for bot, nx, ny, nz, gx, gy in raw]
for (bot, _, _, _, _, _), (orig_bot, _, _, _, _, _) in zip(blocks, raw):
    if tuple(bot) != tuple(orig_bot):
        print(f"Fixed CW: {[names[i] for i in orig_bot]} -> {[names[i] for i in bot]}")

block_strs = [hex_str(bot, nx, ny, nz, gx, gy) for bot, nx, ny, nz, gx, gy in blocks]

def hex_faces(bot):
    a, b, c, d = bot
    e, f, g, h = [v + Nbot for v in bot]
    return [(a, d, c, b), (e, f, g, h), (a, e, h, d), (b, c, g, f), (a, b, f, e), (c, d, h, g)]

def classify(face):
    xs = [verts[i][0] for i in face]
    ys = [verts[i][1] for i in face]
    zs = [verts[i][2] for i in face]
    # Cylinder wall: all points on R=2
    if all(abs(math.sqrt(x*x + y*y) - R) < 0.01 for x, y in zip(xs, ys)):
        return 'cylinder'
    # FrontAndBack: all same z
    if len(set(round(z, 3) for z in zs)) == 1:
        return 'frontAndBack'
    # Inlet/outlet/top/bottom by x/y
    ux = set(round(x, 1) for x in xs)
    uy = set(round(y, 1) for y in ys)
    if len(ux) == 1:
        x0 = list(ux)[0]
        if abs(x0 + Up) < 0.1:
            return 'inlet'
        if abs(x0 - Down) < 0.1:
            return 'outlet'
    if len(uy) == 1:
        y0 = list(uy)[0]
        if abs(y0 - Cross) < 0.1:
            return 'top'
        if abs(y0 + Cross) < 0.1:
            return 'bottom'
    return 'undefined'

face_counts = Counter()
all_info = []
for blk_i, (bot, nx, ny, nz, gx, gy) in enumerate(blocks):
    for face in hex_faces(bot):
        fs = frozenset(face)
        face_counts[fs] += 1
        all_info.append((face, fs, blk_i))

boundaries = {'inlet': [], 'outlet': [], 'top': [], 'bottom': [],
              'cylinder': [], 'frontAndBack': [], 'undefined': []}
seen = set()
for face, fs, blk_i in all_info:
    btype = classify(face)
    if btype in boundaries and face_counts[fs] == 1 and fs not in seen:
        seen.add(fs)
        boundaries[btype].append(face)

def fmt_face(f):
    return f"({f[0]} {f[1]} {f[2]} {f[3]})"

# Arc edges for cylinder and mid-ring (all 45-degree segments)
# Cylinder arcs (R=2): 8 arcs
cyl_pairs = [(E0, NE0), (NE0, N0), (N0, NW0), (NW0, W0),
             (W0, SW0), (SW0, S0), (S0, SE0), (SE0, E0)]
# Mid-ring arcs (R=5): 8 arcs
mid_pairs = [(E1, NE1), (NE1, N1), (N1, NW1), (NW1, W1),
             (W1, SW1), (SW1, S1), (S1, SE1), (SE1, E1)]

def arc_midpoint(a_idx, b_idx, radius):
    """Midpoint on circle of given radius, on the arc between vertices a and b."""
    ax, ay = verts[a_idx][0], verts[a_idx][1]
    bx, by = verts[b_idx][0], verts[b_idx][1]
    sx, sy = ax + bx, ay + by
    norm = math.sqrt(sx*sx + sy*sy)
    return (radius * sx / norm, radius * sy / norm)

edges = []
for a, b in cyl_pairs:
    mx, my = arc_midpoint(a, b, R)
    edges.append(f"    arc {a} {b} ({mx:.6f} {my:.6f} {-H})")
for a, b in mid_pairs:
    mx, my = arc_midpoint(a, b, Ri)
    edges.append(f"    arc {a} {b} ({mx:.6f} {my:.6f} {-H})")
# Top face arcs
for a, b in cyl_pairs:
    mx, my = arc_midpoint(a, b, R)
    edges.append(f"    arc {a+Nbot} {b+Nbot} ({mx:.6f} {my:.6f} {H})")
for a, b in mid_pairs:
    mx, my = arc_midpoint(a, b, Ri)
    edges.append(f"    arc {a+Nbot} {b+Nbot} ({mx:.6f} {my:.6f} {H})")

# Write
with open(os.path.join("magnus_2d", "system", "blockMeshDict"), "w") as f:
    f.write("""FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      blockMeshDict;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

scale 1;

vertices
(
""")
    for i, (x, y, z) in enumerate(verts):
        f.write(f"    ({x:.6f} {y:.6f} {z:.6f})  // {i} {names[i]}\n")
    f.write(");\n\nblocks\n(\n")
    f.write('\n'.join(block_strs))
    f.write("\n);\n\nedges\n(\n")
    f.write('\n'.join(edges))
    f.write("\n);\n\nboundary\n(\n")

    patch_types = [('inlet', 'patch'), ('outlet', 'patch'),
                   ('top', 'symmetry'), ('bottom', 'symmetry'),
                   ('cylinder', 'wall'), ('frontAndBack', 'empty'),
                   ('undefined', 'patch')]
    for pname, ptype in patch_types:
        faces_list = boundaries.get(pname, [])
        if not faces_list:
            continue
        f.write(f"    {pname}\n    {{\n        type {ptype};\n        faces\n        (\n")
        for face in faces_list:
            f.write(f"            {fmt_face(face)}\n")
        f.write("        );\n    }\n")
    f.write(");\n")

print(f"Generated: {len(verts)} vertices, {len(blocks)} blocks")
for k, v in boundaries.items():
    print(f"  {k}: {len(v)} faces")
