"""Plot CL-alpha and CD-alpha curves from batch results."""
import csv
import os

out_dir = r"c:\Users\29436\Desktop\好大儿的论文\openfoam_cases"
csv_path = os.path.join(out_dir, "results.csv")

# Read data
data = {}
with open(csv_path, "r") as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row["status"] != "OK":
            continue
        V = int(row["V(m/s)"])
        rpm = int(row["rpm"])
        alpha = float(row["alpha"])
        cl = float(row["Cl_mean"])
        cd = float(row["Cd_mean"])
        cl_std = float(row["Cl_std"])
        if V not in data:
            data[V] = {"alpha": [], "cl": [], "cd": [], "cl_std": []}
        data[V]["alpha"].append(alpha)
        data[V]["cl"].append(cl)
        data[V]["cd"].append(cd)
        data[V]["cl_std"].append(cl_std)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# Use a readable style
plt.rcParams.update({"font.size": 11, "figure.dpi": 150})

colors = plt.cm.viridis(np.linspace(0, 1, len(data)))

# ---- CL vs Alpha ----
fig1, ax1 = plt.subplots(figsize=(10, 6))
for (V, d), c in zip(sorted(data.items()), colors):
    ax1.errorbar(d["alpha"], d["cl"], yerr=d["cl_std"],
                 fmt="o-", capsize=3, markersize=5, linewidth=1.2,
                 color=c, label=f"V={V} m/s")

ax1.set_xlabel(r"Spin Ratio $\alpha = \omega D / (2V)$")
ax1.set_ylabel(r"Lift Coefficient $C_L$")
ax1.set_title("Magnus Effect: $C_L$ vs Spin Ratio (k-$\\omega$ SST, 2D)")
ax1.legend(loc="upper left", ncol=2)
ax1.grid(True, alpha=0.3)
fig1.tight_layout()
fig1.savefig(os.path.join(out_dir, "CL_vs_alpha.png"))
print("Saved: CL_vs_alpha.png")

# ---- CD vs Alpha ----
fig2, ax2 = plt.subplots(figsize=(10, 6))
for (V, d), c in zip(sorted(data.items()), colors):
    ax2.plot(d["alpha"], d["cd"], "o-", markersize=5, linewidth=1.2,
             color=c, label=f"V={V} m/s")

ax2.set_xlabel(r"Spin Ratio $\alpha = \omega D / (2V)$")
ax2.set_ylabel(r"Drag Coefficient $C_D$")
ax2.set_title("Magnus Effect: $C_D$ vs Spin Ratio (k-$\\omega$ SST, 2D)")
ax2.legend(loc="upper left", ncol=2)
ax2.grid(True, alpha=0.3)
fig2.tight_layout()
fig2.savefig(os.path.join(out_dir, "CD_vs_alpha.png"))
print("Saved: CD_vs_alpha.png")

# ---- CL/CD (Efficiency) vs Alpha ----
fig3, ax3 = plt.subplots(figsize=(10, 6))
for (V, d), c in zip(sorted(data.items()), colors):
    eff = [cl / cd if cd > 0 else 0 for cl, cd in zip(d["cl"], d["cd"])]
    ax3.plot(d["alpha"], eff, "o-", markersize=5, linewidth=1.2,
             color=c, label=f"V={V} m/s")

ax3.set_xlabel(r"Spin Ratio $\alpha = \omega D / (2V)$")
ax3.set_ylabel(r"Aerodynamic Efficiency $C_L / C_D$")
ax3.set_title("Magnus Effect: $C_L/C_D$ vs Spin Ratio (k-$\\omega$ SST, 2D)")
ax3.legend(loc="upper left", ncol=2)
ax3.grid(True, alpha=0.3)
fig3.tight_layout()
fig3.savefig(os.path.join(out_dir, "CLCD_ratio_vs_alpha.png"))
print("Saved: CLCD_ratio_vs_alpha.png")

# ---- Print summary table ----
print("\n=== Summary Table ===")
sep = "V\\rpm"
print(f"{sep:<6}", end="")
for rpm in [60, 120, 180, 240, 300, 360, 420, 480, 540, 600]:
    print(f"{rpm:>8}", end="")
print()
for V in sorted(data.keys()):
    print(f"{V:<6}", end="")
    for cl in data[V]["cl"]:
        print(f"{cl:>8.2f}", end="")
    print()

print("\nDone!")
