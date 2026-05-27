#!/usr/bin/env python3
"""Batch run 3D Magnus effect cases (serial)."""

import os, sys, shutil, subprocess, math, re, time

# --- Configuration ---
BASE_DIR = r"c:\Users\29436\Desktop\好大儿的论文\openfoam_cases\magnus_3d"
RESULTS_CSV = r"c:\Users\29436\Desktop\好大儿的论文\openfoam_cases\results_3d.csv"

D = 4.0
AREF = 128.0
LREF = 4.0

V_REF = 12.0
K_REF = 0.005
OMEGA_REF = 10.0

CASES = [
    # (12, 120) already done — see results_3d.csv
    (12, 360),
    (12, 600),
    (8,  600),
    (20, 360),
    (20, 60),
]

U_FILE      = os.path.join(BASE_DIR, "0", "U")
K_FILE      = os.path.join(BASE_DIR, "0", "k")
OMEGA_FILE  = os.path.join(BASE_DIR, "0", "omega")
CONTROLDICT = os.path.join(BASE_DIR, "system", "controlDict")
FORCE_COEFFS = os.path.join(BASE_DIR, "postProcessing", "forceCoeffs", "0", "forceCoeffs.dat")

TIMEOUT = 18000  # 5 hours per case


def rpm_to_omega(rpm):
    return -rpm * 2.0 * math.pi / 60.0


def scale_turbulence(V):
    ratio = V / V_REF
    return K_REF * ratio ** 2, OMEGA_REF * ratio


# --- File writers ---

def write_u_file(V, omega):
    with open(U_FILE, "w") as f:
        f.write(f"""/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\\\    /   O peration     | Version:  12                                    |
|   \\\\  /    A nd           | Website:  www.openfoam.org                      |
|    \\\\/     M anipulation  |                                                 |
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
    midSpan
    {{
        type            symmetry;
    }}
    farField
    {{
        type            inletOutlet;
        inletValue      uniform ({V} 0 0);
        value           uniform ({V} 0 0);
    }}
    undefined
    {{
        type            zeroGradient;
    }}
}}

// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //
""")


def write_k_file(V):
    k_val, _ = scale_turbulence(V)
    with open(K_FILE, "w") as f:
        f.write(f"""/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\\\    /   O peration     | Version:  12                                    |
|   \\\\  /    A nd           | Website:  www.openfoam.org                      |
|    \\\\/     M anipulation  |                                                 |
\\*---------------------------------------------------------------------------*/
FoamFile
{{
    version     2.0;
    format      ascii;
    class       volScalarField;
    object      k;
}}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

dimensions      [0 2 -2 0 0 0 0];
internalField   uniform {k_val:.6g};

boundaryField
{{
    inlet
    {{
        type            fixedValue;
        value           uniform {k_val:.6g};
    }}
    outlet
    {{
        type            zeroGradient;
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
        type            kqRWallFunction;
        value           uniform 0;
    }}
    midSpan
    {{
        type            symmetry;
    }}
    farField
    {{
        type            inletOutlet;
        inletValue      uniform {k_val:.6g};
        value           uniform {k_val:.6g};
    }}
    undefined
    {{
        type            zeroGradient;
    }}
}}

// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //
""")


def write_omega_file(V):
    _, omega_val = scale_turbulence(V)
    with open(OMEGA_FILE, "w") as f:
        f.write(f"""/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\\\    /   O peration     | Version:  12                                    |
|   \\\\  /    A nd           | Website:  www.openfoam.org                      |
|    \\\\/     M anipulation  |                                                 |
\\*---------------------------------------------------------------------------*/
FoamFile
{{
    version     2.0;
    format      ascii;
    class       volScalarField;
    object      omega;
}}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

dimensions      [0 0 -1 0 0 0 0];
internalField   uniform {omega_val:.6g};

boundaryField
{{
    inlet
    {{
        type            fixedValue;
        value           uniform {omega_val:.6g};
    }}
    outlet
    {{
        type            zeroGradient;
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
        type            omegaWallFunction;
        value           uniform {omega_val:.6g};
    }}
    midSpan
    {{
        type            symmetry;
    }}
    farField
    {{
        type            inletOutlet;
        inletValue      uniform {omega_val:.6g};
        value           uniform {omega_val:.6g};
    }}
    undefined
    {{
        type            zeroGradient;
    }}
}}

// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //
""")


def write_control_dict(V):
    with open(CONTROLDICT, "r") as f:
        content = f.read()
    content = re.sub(r'magUInf\s+\d+\.?\d*;', f'magUInf         {V};', content)
    with open(CONTROLDICT, "w") as f:
        f.write(content)


def clean_case():
    for d in os.listdir(BASE_DIR):
        full = os.path.join(BASE_DIR, d)
        if os.path.isdir(full) and d[0].isdigit() and d != "0":
            shutil.rmtree(full)
        elif os.path.isdir(full) and d.startswith("processor"):
            shutil.rmtree(full)
    pp = os.path.join(BASE_DIR, "postProcessing")
    if os.path.exists(pp):
        shutil.rmtree(pp)


def run_foam_run():
    """Run foamRun serially with streaming output."""
    t0 = time.time()
    cmd = ["foamRun", "-solver", "incompressibleFluid"]
    proc = subprocess.Popen(
        cmd, cwd=BASE_DIR,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1,
    )
    lines = []
    try:
        for line in proc.stdout:
            print(line, end="", flush=True)
            lines.append(line)
        proc.wait(timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
        elapsed = time.time() - t0
        return False, "".join(lines), "TIMEOUT", elapsed

    elapsed = time.time() - t0
    return proc.returncode == 0, "".join(lines), "", elapsed


def extract_forces():
    if not os.path.exists(FORCE_COEFFS):
        return None, None, None, None

    try:
        with open(FORCE_COEFFS, "r") as f:
            lines = f.readlines()

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

        cl_var = sum((x - cl_mean) ** 2 for x in cl_vals) / len(cl_vals)
        cl_std = math.sqrt(cl_var)

        return cl_mean, cd_mean, cm_mean, cl_std
    except Exception as e:
        print(f"  Error reading forces: {e}")
        return None, None, None, None


def main():
    print(f"=== 3D Magnus Effect Batch Simulation (Serial) ===")
    print(f"Cases: {len(CASES)}")
    print(f"Aref = {AREF} m2, lRef = {LREF} m")
    print(f"Timeout per case: {TIMEOUT}s ({TIMEOUT/3600:.0f}h)\n")

    if os.path.exists(RESULTS_CSV):
        bak = RESULTS_CSV.replace(".csv", "_bak.csv")
        if not os.path.exists(bak):
            shutil.copy(RESULTS_CSV, bak)

    with open(RESULTS_CSV, "w") as f:
        f.write("V(m/s),rpm,alpha,Cl_mean,Cl_std,Cd_mean,Cm_mean,status\n")

    for i, (V, rpm) in enumerate(CASES):
        omega = rpm_to_omega(rpm)
        alpha = abs(omega) * D / (2.0 * V)
        k_val, omega_val = scale_turbulence(V)

        print(f"[{i+1}/{len(CASES)}] V={V} m/s, rpm={rpm}, alpha={alpha:.4f}")
        print(f"  omega={omega:.4f} rad/s, k={k_val:.6g}, omega_turb={omega_val:.6g}")

        write_u_file(V, omega)
        write_k_file(V)
        write_omega_file(V)
        write_control_dict(V)

        clean_case()

        print("  Running foamRun...")
        ok, stdout, stderr, elapsed = run_foam_run()

        if not ok:
            if "Time = " in str(stdout):
                print(f"\n  Partial run ({elapsed/60:.0f} min) - extracting results")
            else:
                print(f"\n  FAILED after {elapsed/60:.0f} min")
                err_lines = (stderr or "").strip().split("\n")
                for line in err_lines[-5:]:
                    print(f"  [stderr] {line}")
                with open(RESULTS_CSV, "a") as f:
                    f.write(f"{V},{rpm},{alpha:.4f},,,,FAILED\n")
                continue

        print(f"\n  Done ({elapsed/60:.1f} min)")

        cl_mean, cd_mean, cm_mean, cl_std = extract_forces()

        if cl_mean is None:
            print(f"  FAILED (no force data)")
            with open(RESULTS_CSV, "a") as f:
                f.write(f"{V},{rpm},{alpha:.4f},,,,FAILED\n")
            continue

        print(f"  Cl={cl_mean:.4f} +- {cl_std:.4f}, Cd={cd_mean:.4f}, Cm={cm_mean:.4f}")

        with open(RESULTS_CSV, "a") as f:
            f.write(f"{V},{rpm},{alpha:.4f},{cl_mean:.6f},{cl_std:.6f},{cd_mean:.6f},{cm_mean:.6f},OK\n")

    print(f"\n=== Done! Results saved to: {RESULTS_CSV} ===")


if __name__ == "__main__":
    main()
