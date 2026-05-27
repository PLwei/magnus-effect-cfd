#!/usr/bin/env python3
"""Batch run 70 Magnus effect cases (7 wind speeds × 10 rpm)."""
import os, sys, shutil, subprocess, math

# --- Configuration ---
BASE_DIR = r"c:\Users\29436\Desktop\好大儿的论文\openfoam_cases\magnus_2d"
RESULTS_CSV = r"c:\Users\29436\Desktop\好大儿的论文\openfoam_cases\results.csv"

WIND_SPEEDS = [8, 10, 12, 14, 16, 18, 20]  # m/s
RPMS = [60, 120, 180, 240, 300, 360, 420, 480, 540, 600]  # rpm
D = 4.0  # cylinder diameter
RHO = 1.225  # kg/m3
AREF = 4.0  # reference area (D × 1m depth for 2D)

TOTAL = len(WIND_SPEEDS) * len(RPMS)

# Template files that need modification
U_TEMPLATE = os.path.join(BASE_DIR, "0", "U")
CONTROLDICT = os.path.join(BASE_DIR, "system", "controlDict")
FORCE_COEFFS_FILE = os.path.join(BASE_DIR, "postProcessing", "forceCoeffs", "0", "forceCoeffs.dat")

def rpm_to_omega(rpm):
    """Convert rpm to rad/s. Negative for CW rotation (produces upward Magnus lift)."""
    return -rpm * 2.0 * math.pi / 60.0

def write_u_file(V, omega):
    """Write 0/U with given inlet velocity and cylinder rotation."""
    with open(U_TEMPLATE, "w") as f:
        f.write(f"""/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\    /   O peration     | Version:  12                                    |
|   \\  /    A nd           | Website:  www.openfoam.org                      |
|    \\/     M anipulation  |                                                 |
\\*---------------------------------------------------------------------------*/
FoamFile
{{
    version     2.0;
    format      ascii;
    class       volVectorField;
    object      U;
}}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

dimensions      [0 1 -1 0 0 0 0];
internalField   uniform ({V} 0 0);

boundaryField
{{
    inlet
    {{
        type            fixedValue;
        value           uniform ({V} 0 0);
    }}
    outlet
    {{
        type            inletOutlet;
        inletValue      uniform ({V} 0 0);
        value           uniform ({V} 0 0);
    }}
    top
    {{
        type            symmetry;
    }}
    bottom
    {{
        type            symmetry;
    }}
    cylinder
    {{
        type            rotatingWallVelocity;
        origin          (0 0 0);
        axis            (0 0 1);
        omega           {omega:.6f};
    }}
    frontAndBack
    {{
        type            empty;
    }}
}}

// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //
""")

def write_controldict(V):
    """Update magUInf in controlDict for force coefficients."""
    with open(CONTROLDICT, "r") as f:
        content = f.read()

    # Replace magUInf line
    import re
    content = re.sub(r'magUInf\s+\d+\.?\d*;', f'magUInf         {V};', content)

    with open(CONTROLDICT, "w") as f:
        f.write(content)

def clean_old_results():
    """Remove old time directories."""
    case_dir = BASE_DIR
    import glob
    for d in os.listdir(case_dir):
        full = os.path.join(case_dir, d)
        if os.path.isdir(full) and d[0].isdigit() and d != "0":
            shutil.rmtree(full)
    # Also remove postProcessing
    pp = os.path.join(case_dir, "postProcessing")
    if os.path.exists(pp):
        shutil.rmtree(pp)

def run_blockmesh():
    """Generate mesh from blockMeshDict."""
    print("Running blockMesh...")
    result = subprocess.run(
        ["blockMesh"],
        cwd=BASE_DIR,
        capture_output=True, text=True,
        timeout=60
    )
    if result.returncode != 0:
        print(f"blockMesh FAILED:\n{result.stderr}")
        sys.exit(1)
    print("blockMesh done.")

def run_foam_run():
    """Run foamRun and return success/failure."""
    result = subprocess.run(
        ["foamRun", "-solver", "incompressibleFluid"],
        cwd=BASE_DIR,
        capture_output=True, text=True,
        timeout=600  # 10 min timeout per case
    )
    return result.returncode == 0, result.stdout, result.stderr

def extract_forces():
    """Extract time-averaged Cl, Cd from forceCoeffs.dat using last 60% of data."""
    if not os.path.exists(FORCE_COEFFS_FILE):
        return None, None, None, None

    try:
        with open(FORCE_COEFFS_FILE, "r") as f:
            lines = f.readlines()

        # Parse data lines (skip comment header)
        data = []
        for line in lines:
            if line.startswith("#") or not line.strip():
                continue
            parts = line.split()
            if len(parts) >= 4:
                data.append([float(p) for p in parts[:4]])

        if len(data) < 5:
            return None, None, None, None

        arr = data
        n = len(arr)
        start = max(n // 2, n * 2 // 5)
        subset = arr[start:]

        cm_vals = [r[1] for r in subset]
        cd_vals = [r[2] for r in subset]
        cl_vals = [r[3] for r in subset]

        cl_mean = sum(cl_vals) / len(cl_vals)
        cd_mean = sum(cd_vals) / len(cd_vals)
        cm_mean = sum(cm_vals) / len(cm_vals)

        # Standard deviation
        cl_var = sum((x - cl_mean)**2 for x in cl_vals) / len(cl_vals)
        cl_std = math.sqrt(cl_var)

        return cl_mean, cd_mean, cm_mean, cl_std
    except Exception as e:
        print(f"  Error reading forces: {e}")
        return None, None, None, None

def main():
    print(f"=== Magnus Effect Batch Simulation ===")
    print(f"Wind speeds: {WIND_SPEEDS}")
    print(f"RPMs: {RPMS}")
    print(f"Total cases: {TOTAL}\n")

    # Generate mesh first
    run_blockmesh()

    # Backup old results if any
    if os.path.exists(RESULTS_CSV):
        bak = RESULTS_CSV.replace(".csv", "_bak_xfine.csv")
        if not os.path.exists(bak):
            shutil.copy(RESULTS_CSV, bak)
            print(f"Old results backed up to: {bak}")

    # Initialize results CSV
    with open(RESULTS_CSV, "w") as f:
        f.write("V(m/s),rpm,alpha,Cl_mean,Cl_std,Cd_mean,Cm_mean,status\n")

    case_num = 0
    for V in WIND_SPEEDS:
        for rpm in RPMS:
            case_num += 1
            omega = rpm_to_omega(rpm)
            alpha = abs(omega) * D / (2.0 * V)

            print(f"[{case_num}/{TOTAL}] V={V} m/s, rpm={rpm}, alpha={alpha:.2f} ... ", end="", flush=True)

            # Update input files
            write_u_file(V, omega)
            write_controldict(V)

            # Clean old results
            clean_old_results()

            # Run solver
            success, stdout, stderr = run_foam_run()

            if not success:
                # Check if solver ran at all (has output)
                if "Time = 0" in stdout or "Time = 1" in stdout:
                    print("partial run - extracting results")
                else:
                    print("FAILED")
                    with open(RESULTS_CSV, "a") as f:
                        f.write(f"{V},{rpm},{alpha:.4f},,,,FAILED\n")
                    continue

            # Extract forces
            cl_mean, cd_mean, cm_mean, cl_std = extract_forces()

            if cl_mean is None:
                print("FAILED (no force data)")
                with open(RESULTS_CSV, "a") as f:
                    f.write(f"{V},{rpm},{alpha:.4f},,,,FAILED\n")
                continue

            print(f"Cl={cl_mean:.3f}+-{cl_std:.3f} Cd={cd_mean:.3f}")

            with open(RESULTS_CSV, "a") as f:
                f.write(f"{V},{rpm},{alpha:.4f},{cl_mean:.6f},{cl_std:.6f},{cd_mean:.6f},{cm_mean:.6f},OK\n")

    print(f"\n=== Done! Results saved to: {RESULTS_CSV} ===")

if __name__ == "__main__":
    main()
