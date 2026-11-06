"""Regenerate the hello-motion hub STL from hello_motion_fixture_prototype.py.

Reproduces ONLY the hub construction from that script, verbatim parameters:
  hub_shape = fuse of:
    Part.makeCylinder(14, 4, Vector(0, 0, 24.8))   # flange, r=14, h=4
    Part.makeCylinder(9, 12, Vector(0, 0, 28.8))   # neck,   r=9,  h=12
    Part.makeCylinder(2.5, 30.5, Vector(0, 0, 24.8))  # stub, r=2.5, h=30.5
  then cut 3 holes:
    Part.makeCylinder(1.65, 6, Vector(8.5*cos(a), 8.5*sin(a), 23.8))
    for a in [180, 60, -60] degrees
  then the print copy translates the shape by -ZMin (ZMin = 24.8),
  exactly as the script's hub_print block does.

Built with manifold3d (headless CSG) because FreeCAD is not installed here
and the script's STEP reference files are unavailable. No geometry was
redesigned: same primitives, same parameters, same order of operations.
"""

import math

import numpy as np
from manifold3d import Manifold, Mesh

SEGMENTS = 64  # circular segments per cylinder, for smooth circles

OUT_PATH = "/home/hatch/workspace/hello-motion/hello-motion_hub_PETG-FIT-CHECK-ONLY.stl"


def cyl(radius, height, x, y, z):
    """Manifold cylinder (axis +Z, base at z=0) translated to (x, y, z)."""
    return Manifold.cylinder(
        height, radius, radius, SEGMENTS, center=False
    ).translate([x, y, z])


def main():
    # Fuse the three primitives, exactly as the script's hub_shape.
    flange = cyl(14.0, 4.0, 0.0, 0.0, 24.8)
    neck = cyl(9.0, 12.0, 0.0, 0.0, 28.8)
    stub = cyl(2.5, 30.5, 0.0, 0.0, 24.8)
    hub = flange + neck + stub

    # Cut the three M3 clearance holes, exactly as the script's hub_holes.
    for a_deg in [180, 60, -60]:
        a = math.radians(a_deg)
        hole = cyl(
            1.65, 6.0,
            8.5 * math.cos(a), 8.5 * math.sin(a), 23.8,
        )
        hub = hub - hole

    # Print copy: translate by -ZMin so the bounding box starts at Z=0.
    bbox = hub.bounding_box()  # flat (min_x, min_y, min_z, max_x, max_y, max_z)
    zmin = float(bbox[2])
    print(f"pre-translation ZMin = {zmin}")
    assert abs(zmin - 24.8) < 1e-6, f"unexpected ZMin {zmin}"
    hub = hub.translate([0.0, 0.0, -zmin])

    # Manifold's own validity / measurements.
    print(f"status = {hub.status()}")
    print(f"volume = {hub.volume():.3f} mm^3")
    print(f"surface area = {hub.surface_area():.3f} mm^2")
    print(f"num_tris = {hub.num_tri()}, num_verts = {hub.num_vert()}")
    bb = hub.bounding_box()
    print(f"bounding box min = {bb[0:3]}, max = {bb[3:6]}")
    print(f"bbox size = {[float(bb[3 + i] - bb[i]) for i in range(3)]}")

    # Export binary STL via trimesh (manifold mesh -> trimesh -> STL).
    mesh = hub.to_mesh()
    verts = np.asarray(mesh.vert_properties, dtype=np.float64)
    faces = np.asarray(mesh.tri_verts, dtype=np.int64)
    import trimesh

    tm = trimesh.Trimesh(vertices=verts, faces=faces, process=False)
    tm.export(OUT_PATH, file_type="stl")
    print(f"exported binary STL to {OUT_PATH}")

    # Independent validation of the exported file with trimesh.
    loaded = trimesh.load(OUT_PATH, force="mesh")
    print(f"--- exported file validation ---")
    print(f"is_watertight = {loaded.is_watertight}")
    print(f"is_winding_consistent = {loaded.is_winding_consistent}")
    print(f"is_volume = {loaded.is_volume}")
    print(f"euler_number = {loaded.euler_number}")
    print(f"volume = {loaded.volume:.3f} mm^3")
    print(f"bounds = {loaded.bounds.tolist()}")
    print(f"extents = {loaded.extents.tolist()}")
    print(f"faces = {len(loaded.faces)}, vertices = {len(loaded.vertices)}")
    face_areas = loaded.area_faces
    print(f"degenerate faces (area == 0) = {int(np.sum(face_areas <= 0))}")
    print(f"min face area = {float(face_areas.min()):.6f} mm^2")

    # Analytic expectation (exact circular geometry, no tessellation error).
    pi = math.pi
    v_flange = pi * 14.0**2 * 4.0
    v_neck = pi * 9.0**2 * 12.0
    v_stub = pi * 2.5**2 * 30.5
    v_stub_flange = pi * 2.5**2 * 4.0   # stub inside flange, z 24.8-28.8
    v_stub_neck = pi * 2.5**2 * 12.0    # stub inside neck, z 28.8-40.8
    v_union = v_flange + v_neck + v_stub - v_stub_flange - v_stub_neck
    # Each hole removes pi*1.65^2*4 from the flange (full footprint inside
    # the flange, z 24.8-28.8) plus the lens where it clips the neck
    # (z 28.8-29.8, 1 mm) — circle-circle intersection of r=1.65 at
    # distance 8.5 from the neck axis (R=9).
    d, R, r = 8.5, 9.0, 1.65
    lens = (
        r**2 * math.acos((d**2 + r**2 - R**2) / (2 * d * r))
        + R**2 * math.acos((d**2 + R**2 - r**2) / (2 * d * R))
        - 0.5 * math.sqrt((-d + r + R) * (d + r - R) * (d - r + R) * (d + r + R))
    )
    v_hole_each = pi * 1.65**2 * 4.0 + lens * 1.0
    v_expected = v_union - 3 * v_hole_each
    print(f"--- analytic expectation ---")
    print(f"union volume (no holes) = {v_union:.3f} mm^3")
    print(f"hole-neck lens area = {lens:.4f} mm^2")
    print(f"volume removed per hole = {v_hole_each:.3f} mm^3")
    print(f"expected volume = {v_expected:.3f} mm^3")
    print(f"mesh volume vs expected: diff = {loaded.volume - v_expected:.3f} "
          f"mm^3 ({100 * (loaded.volume - v_expected) / v_expected:.3f}%)")


if __name__ == "__main__":
    main()
