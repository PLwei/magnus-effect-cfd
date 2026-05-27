#!/usr/bin/env python3
"""Generate 3D blockMeshDict by extruding the 2D O-grid in z-direction."""
import math, os
from collections import Counter

# --- Geometry ---
D = 4.0; R = 2.0; Ri = 5.0
Up = 40.0; Down = 80.0; Cross = 40.0
SQ2 = math.sqrt(2.0)/2.0

# --- Z-domain (symmetry at mid-span) ---
# z_layers = [(z_start, z_end, n_cells, grading_z), ...]
z_layers = [
    (0.0,  32.0, 50, 0.1),   # cylinder region, grading: fine near tip
    (32.0, 52.0, 20, 1.0),   # far-field extension, uniform
]
z_planes = [0.0, 32.0, 52.0]  # vertex z-levels
L_half = 32.0  # cylinder half-span
L_far = 52.0   # far-field z extent

# --- Generate base x-y vertices (32 points at z=0) ---
verts = []
names = []

def add(name, x, y, z):
    names.append(name)
    verts.append((x, y, z))
    return len(verts) - 1

# Original 16 bottom vertices (cardinal + diagonal at R=2 and R=5)
E0 = add("E0z0",  R,  0, 0); N0 = add("N0z0",  0,  R, 0)
W0 = add("W0z0", -R,  0, 0); S0 = add("S0z0",  0, -R, 0)
E1 = add("E1z0", Ri,  0, 0); N1 = add("N1z0",  0, Ri, 0)
W1 = add("W1z0",-Ri,  0, 0); S1 = add("S1z0",  0,-Ri, 0)
E2 = add("E2z0",Down, 0, 0); N2 = add("N2z0",  0,Cross,0)
W2 = add("W2z0",-Up,  0, 0); S2 = add("S2z0",  0,-Cross,0)
SW = add("SWz0",-Up,-Cross,0); SE = add("SEz0",Down,-Cross,0)
NE = add("NEz0",Down,Cross,0); NW = add("NWz0",-Up,Cross,0)

# 45-degree positions
NE0 = add("NE0z0",  R*SQ2,  R*SQ2, 0)
NW0 = add("NW0z0", -R*SQ2,  R*SQ2, 0)
SW0 = add("SW0z0", -R*SQ2, -R*SQ2, 0)
SE0 = add("SE0z0",  R*SQ2, -R*SQ2, 0)

# Mid-ring 45-degree
NE1 = add("NE1z0",  Ri*SQ2,  Ri*SQ2, 0)
NW1 = add("NW1z0", -Ri*SQ2,  Ri*SQ2, 0)
SW1 = add("SW1z0", -Ri*SQ2, -Ri*SQ2, 0)
SE1 = add("SE1z0",  Ri*SQ2, -Ri*SQ2, 0)

# Far-field edge midpoints
N2E = add("N2Ez0",  40,  40, 0)
N2W = add("N2Wz0", -20,  40, 0)
E2N = add("E2Nz0",  80,  20, 0)
E2S = add("E2Sz0",  80, -20, 0)
S2E = add("S2Ez0",  40, -40, 0)
S2W = add("S2Wz0", -20, -40, 0)
W2N = add("W2Nz0", -40,  20, 0)
W2S = add("W2Sz0", -40, -20, 0)

n_xy = len(verts)  # 32

# --- Generate vertices at all z-planes ---
for zp in z_planes[1:]:  # skip z=0 (already done)
    for i in range(n_xy):
        vx, vy, _ = verts[i]
        add(f"{names[i].rstrip('z0')}z{zp:.0f}", vx, vy, zp)

# Total vertices: 32 * 3 = 96

def signed_area2(indices):
    s = 0.0
    for i in range(len(indices)):
        v1 = (verts[indices[i]][0], verts[indices[i]][1])
        v2 = (verts[indices[(i+1)%len(indices)]][0], verts[indices[(i+1)%len(indices)]][1])
        s += v1[0]*v2[1] - v2[0]*v1[1]
    return s

def make_ccw(bot_idx):
    return tuple(reversed(bot_idx)) if signed_area2(bot_idx) < 0 else tuple(bot_idx)

# --- Raw x-y blocks (same as v4) ---
raw_xy = [
    # 8 inner blocks (radial grading=5)
    ((E0,  E1,  NE1, NE0), 50, 15, 5, 1),
    ((NE0, NE1, N1,  N0),  50, 15, 5, 1),
    ((N0,  N1,  NW1, NW0), 50, 15, 5, 1),
    ((NW0, NW1, W1,  W0),  50, 15, 5, 1),
    ((W0,  W1,  SW1, SW0), 50, 15, 5, 1),
    ((SW0, SW1, S1,  S0),  50, 15, 5, 1),
    ((S0,  S1,  SE1, SE0), 50, 15, 5, 1),
    ((SE0, SE1, E1,  E0),  50, 15, 5, 1),
    # 8 edge outer blocks (uniform)
    ((E1,  E2,  E2N, NE1), 40, 15, 1, 1),
    ((NE1, N2E, N2,  N1),  40, 15, 1, 1),
    ((N1,  N2,  N2W, NW1), 40, 15, 1, 1),
    ((NW1, W2N, W2,  W1),  40, 15, 1, 1),
    ((W1,  W2,  W2S, SW1), 40, 15, 1, 1),
    ((SW1, S2W, S2,  S1),  40, 15, 1, 1),
    ((S1,  S2,  S2E, SE1), 40, 15, 1, 1),
    ((SE1, E2S, E2,  E1),  40, 15, 1, 1),
    # 4 corner outer blocks (uniform)
    ((NE1, E2N, NE,  N2E), 40, 40, 1, 1),
    ((NW1, W2N, NW,  N2W), 40, 40, 1, 1),
    ((SW1, S2W, SW,  W2S), 40, 40, 1, 1),
    ((SE1, E2S, SE,  S2E), 40, 40, 1, 1),
]

# Make CCW
xy_blocks = [(make_ccw(bot), nx, ny, gx, gy) for bot, nx, ny, gx, gy in raw_xy]

# --- Generate 3D blocks ---
# For each x-y block, create one hex per z-layer
def vertex_at_z(base_idx, z_value):
    """Find vertex index at a specific z-plane for the same x-y position."""
    if z_value == 0:
        return base_idx
    z_idx = z_planes.index(z_value)
    return base_idx + z_idx * n_xy

blocks_3d = []  # (bot4, top4, nx, ny, nz, gx, gy, gz)
for bot_idx, nx, ny, gx, gy in xy_blocks:
    for k, (z0, z1, nz, gz) in enumerate(z_layers):
        # bottom face at z0, top face at z1
        bot_z0 = tuple(vertex_at_z(i, z0) for i in bot_idx)
        top_z1 = tuple(vertex_at_z(i, z1) for i in bot_idx)
        # Combine: hex requires (bottom_4 top_4) all from same z-plane
        # Actually blockMesh: hex (v0 v1 v2 v3 v4 v5 v6 v7) where v0-3 bottom, v4-7 top
        blocks_3d.append((bot_z0, top_z1, nx, ny, nz, gx, gy, gz))

def hex_str_3d(bot, top, nx, ny, nz, gx, gy, gz):
    indices = list(bot) + list(top)
    return f"    hex ({' '.join(map(str, indices))}) ({nx} {ny} {nz}) simpleGrading ({gx} {gy} {gz})"

block_strs = [hex_str_3d(bot, top, nx, ny, nz, gx, gy, gz)
              for bot, top, nx, ny, nz, gx, gy, gz in blocks_3d]

# --- Face classification ---
def hex_faces_3d(bot, top):
    a, b, c, d = bot
    e, f, g, h = top
    return [(a, d, c, b), (e, f, g, h), (a, e, h, d), (b, c, g, f), (a, b, f, e), (c, d, h, g)]

def classify(face):
    xs = [verts[i][0] for i in face]
    ys = [verts[i][1] for i in face]
    zs = [verts[i][2] for i in face]

    # Check midSpan (z=0 symmetry)
    if all(abs(z) < 0.001 for z in zs):
        return 'midSpan'

    # Check farField (z=52)
    if all(abs(z - L_far) < 0.001 for z in zs):
        return 'farField'

    # Cylinder wall: all on R=2 AND z between 0 and L_half
    if all(abs(math.sqrt(x*x + y*y) - R) < 0.01 for x, y in zip(xs, ys)):
        z_avg = sum(zs) / len(zs)
        if z_avg <= L_half + 0.01:
            return 'cylinder'

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
for blk_i, (bot, top, nx, ny, nz, gx, gy, gz) in enumerate(blocks_3d):
    for face in hex_faces_3d(bot, top):
        fs = frozenset(face)
        face_counts[fs] += 1
        all_info.append((face, fs, blk_i))

boundaries = {'inlet': [], 'outlet': [], 'top': [], 'bottom': [],
              'cylinder': [], 'midSpan': [], 'farField': [], 'undefined': []}
seen = set()
for face, fs, blk_i in all_info:
    btype = classify(face)
    if btype in boundaries and face_counts[fs] == 1 and fs not in seen:
        seen.add(fs)
        boundaries[btype].append(face)

# --- Arc edges ---
def arc_midpoint(a_idx, b_idx, radius):
    ax, ay = verts[a_idx][0], verts[a_idx][1]
    bx, by = verts[b_idx][0], verts[b_idx][1]
    sx, sy = ax + bx, ay + by
    norm = math.sqrt(sx*sx + sy*sy)
    return (radius * sx / norm, radius * sy / norm)

cyl_pairs = [(E0, NE0), (NE0, N0), (N0, NW0), (NW0, W0),
             (W0, SW0), (SW0, S0), (S0, SE0), (SE0, E0)]
mid_pairs = [(E1, NE1), (NE1, N1), (N1, NW1), (NW1, W1),
             (W1, SW1), (SW1, S1), (S1, SE1), (SE1, E1)]

edges = []
# Arcs only on z-planes that intersect cylinder: z=0 and z=32
for z_val in [0.0, L_half]:
    offset = z_planes.index(z_val) * n_xy
    z = z_val
    for a, b in cyl_pairs:
        mx, my = arc_midpoint(a, b, R)
        edges.append(f"    arc {a+offset} {b+offset} ({mx:.6f} {my:.6f} {z})")
    for a, b in mid_pairs:
        mx, my = arc_midpoint(a, b, Ri)
        edges.append(f"    arc {a+offset} {b+offset} ({mx:.6f} {my:.6f} {z})")

# --- Format face for boundary ---
def fmt_face(f):
    return f"({f[0]} {f[1]} {f[2]} {f[3]})"

# --- Write ---
output_dir = os.path.join("magnus_3d", "system")
os.makedirs(output_dir, exist_ok=True)

with open(os.path.join(output_dir, "blockMeshDict"), "w") as f:
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
                   ('cylinder', 'wall'), ('midSpan', 'symmetry'),
                   ('farField', 'patch'), ('undefined', 'patch')]
    for pname, ptype in patch_types:
        faces_list = boundaries.get(pname, [])
        if not faces_list:
            continue
        f.write(f"    {pname}\n    {{\n        type {ptype};\n        faces\n        (\n")
        for face in faces_list:
            f.write(f"            {fmt_face(face)}\n")
        f.write("        );\n    }\n")
    f.write(");\n")

total_cells = sum(nx * ny * nz for _, _, nx, ny, nz, _, _, _ in blocks_3d)
print(f"Generated: {len(verts)} vertices, {len(blocks_3d)} blocks, {total_cells} cells")
for k, v in boundaries.items():
    print(f"  {k}: {len(v)} faces")
