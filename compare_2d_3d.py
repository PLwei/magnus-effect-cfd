#!/usr/bin/env python3
"""Compare 2D and 3D Magnus effect results."""

import csv, math, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

BASE = r"c:\Users\29436\Desktop\好大儿的论文\openfoam_cases"
RESULTS_2D = os.path.join(BASE, "results.csv")
RESULTS_3D = os.path.join(BASE, "results_3d.csv")
OUT_DIR = os.path.join(BASE, "comparison_plots")

os.makedirs(OUT_DIR, exist_ok=True)


def load_csv(path):
    """Load results CSV into list of dicts."""
    rows = []
    with open(path, "r") as f:
        reader = csv.DictReader(f)
        for r in reader:
            if r.get("status", "").strip() == "OK":
                rows.append({
                    "V": float(r["V(m/s)"]),
                    "rpm": float(r["rpm"]),
                    "alpha": float(r["alpha"]),
                    "Cl_mean": float(r["Cl_mean"]),
                    "Cl_std": float(r.get("Cl_std", 0)),
                    "Cd_mean": float(r["Cd_mean"]),
                    "Cm_mean": float(r.get("Cm_mean", 0)),
                })
    return rows


def match_cases(data_2d, data_3d):
    """Match 3D cases to their 2D counterparts by (V, rpm)."""
    pairs = []
    for r3 in data_3d:
        for r2 in data_2d:
            if abs(r2["V"] - r3["V"]) < 0.01 and abs(r2["rpm"] - r3["rpm"]) < 0.01:
                pairs.append((r2, r3))
                break
    return pairs


def plot_cl_cd_comparison(data_2d, data_3d, pairs):
    """Plot CL-alpha and CD-alpha: 2D curve vs 3D points."""
    # Sort 2D data by alpha for line plot
    d2_sorted = sorted(data_2d, key=lambda x: x["alpha"])
    alphas_2d = [r["alpha"] for r in d2_sorted]
    cl_2d = [r["Cl_mean"] for r in d2_sorted]
    cd_2d = [r["Cd_mean"] for r in d2_sorted]

    # 3D points
    alphas_3d = [r["alpha"] for r in data_3d]
    cl_3d = [r["Cl_mean"] for r in data_3d]
    cd_3d = [r["Cd_mean"] for r in data_3d]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))

    # --- CL vs alpha ---
    ax1.plot(alphas_2d, cl_2d, "b-", linewidth=1.5, label="2D (70 cases)")
    ax1.scatter(alphas_3d, cl_3d, c="red", s=80, zorder=5, label="3D")
    ax1.set_xlabel("Spin Ratio  α = ωD/(2V)", fontsize=12)
    ax1.set_ylabel("Lift Coefficient  $C_L$", fontsize=12)
    ax1.set_title("$C_L$ vs α: 2D vs 3D", fontsize=13)
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3)

    # --- CD vs alpha ---
    ax2.plot(alphas_2d, cd_2d, "b-", linewidth=1.5, label="2D (70 cases)")
    ax2.scatter(alphas_3d, cd_3d, c="red", s=80, zorder=5, label="3D")
    ax2.set_xlabel("Spin Ratio  α = ωD/(2V)", fontsize=12)
    ax2.set_ylabel("Drag Coefficient  $C_D$", fontsize=12)
    ax2.set_title("$C_D$ vs α: 2D vs 3D", fontsize=13)
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    path = os.path.join(OUT_DIR, "CL_CD_2D_vs_3D.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {path}")


def plot_ratio(pairs):
    """Plot 3D/2D ratio bars for CL and CD."""
    if not pairs:
        print("No matching 2D/3D pairs to compute ratios.")
        return

    labels = []
    cl_ratios = []
    cd_ratios = []

    for r2, r3 in pairs:
        alpha = r3["alpha"]
        lbl = f"α={alpha:.1f}\n(V={r3['V']:.0f}, {r3['rpm']:.0f}rpm)"
        labels.append(lbl)
        cl_ratios.append(r3["Cl_mean"] / r2["Cl_mean"] if r2["Cl_mean"] != 0 else 0)
        cd_ratios.append(r3["Cd_mean"] / r2["Cd_mean"] if r2["Cd_mean"] != 0 else 0)

    x = np.arange(len(labels))
    w = 0.35

    fig, ax = plt.subplots(figsize=(10, 5))
    bars1 = ax.bar(x - w/2, cl_ratios, w, label="$C_{L,3D} / C_{L,2D}$", color="steelblue", edgecolor="black")
    bars2 = ax.bar(x + w/2, cd_ratios, w, label="$C_{D,3D} / C_{D,2D}$", color="coral", edgecolor="black")

    ax.axhline(y=1.0, color="gray", linestyle="--", linewidth=1, alpha=0.7)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel("3D / 2D Ratio", fontsize=12)
    ax.set_title("3D End-Effect Ratio (3D/2D)", fontsize=13)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3, axis="y")

    # Annotate values
    for bar in bars1:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., h + 0.01, f"{h:.3f}",
                ha="center", va="bottom", fontsize=8)
    for bar in bars2:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., h + 0.01, f"{h:.3f}",
                ha="center", va="bottom", fontsize=8)

    plt.tight_layout()
    path = os.path.join(OUT_DIR, "ratio_3D_to_2D.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {path}")


def plot_cl_cd_curve(data_2d, data_3d):
    """CL-CD polar plot comparing 2D and 3D."""
    d2 = sorted(data_2d, key=lambda x: x["alpha"])
    cd_2d = [r["Cd_mean"] for r in d2]
    cl_2d = [r["Cl_mean"] for r in d2]

    cd_3d = [r["Cd_mean"] for r in data_3d]
    cl_3d = [r["Cl_mean"] for r in data_3d]

    fig, ax = plt.subplots(figsize=(7, 6))
    ax.plot(cd_2d, cl_2d, "b-", linewidth=1.5, label="2D")
    ax.scatter(cd_3d, cl_3d, c="red", s=80, zorder=5, label="3D")
    ax.set_xlabel("$C_D$", fontsize=12)
    ax.set_ylabel("$C_L$", fontsize=12)
    ax.set_title("$C_L$–$C_D$ Polar: 2D vs 3D", fontsize=13)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.set_aspect("auto")

    plt.tight_layout()
    path = os.path.join(OUT_DIR, "CL_CD_polar_2D_vs_3D.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {path}")


def print_analysis(data_2d, data_3d, pairs):
    """Print quantitative comparison to console."""
    print("\n" + "=" * 80)
    print("2D vs 3D Comparison Analysis")
    print("=" * 80)

    if not pairs:
        print("No matching 2D/3D pairs found.")
        return

    print(f"{'V':>5s} {'rpm':>5s} {'α':>7s}  "
          f"{'Cl_2D':>9s} {'Cl_3D':>9s} {'Cl_ratio':>9s}  "
          f"{'Cd_2D':>9s} {'Cd_3D':>9s} {'Cd_ratio':>9s}")
    print("-" * 80)

    cl_ratios = []
    cd_ratios = []
    for r2, r3 in pairs:
        cl_r = r3["Cl_mean"] / r2["Cl_mean"] if r2["Cl_mean"] != 0 else 0
        cd_r = r3["Cd_mean"] / r2["Cd_mean"] if r2["Cd_mean"] != 0 else 0
        cl_ratios.append(cl_r)
        cd_ratios.append(cd_r)
        print(f"{r3['V']:5.0f} {r3['rpm']:5.0f} {r3['alpha']:7.4f}  "
              f"{r2['Cl_mean']:9.4f} {r3['Cl_mean']:9.4f} {cl_r:9.4f}  "
              f"{r2['Cd_mean']:9.4f} {r3['Cd_mean']:9.4f} {cd_r:9.4f}")

    print("-" * 80)
    if cl_ratios:
        print(f"Mean Cl_ratio (3D/2D) = {np.mean(cl_ratios):.4f}  "
              f"Std = {np.std(cl_ratios):.4f}")
    if cd_ratios:
        print(f"Mean Cd_ratio (3D/2D) = {np.mean(cd_ratios):.4f}  "
              f"Std = {np.std(cd_ratios):.4f}")
    print()
    print("Interpretation:")
    print("- Ratio < 1: 3D end effects reduce force compared to infinite-span 2D")
    print("- Ratio > 1: Possible 3D tip vortex enhancement")
    print("- Cl_ratio closer to 1 at high spin ratios suggests tip effects")
    print("  are dominated by strong rotation-induced flow.")


def main():
    print("Loading 2D data...")
    data_2d = load_csv(RESULTS_2D)
    print(f"  {len(data_2d)} cases loaded.")

    print("Loading 3D data...")
    if not os.path.exists(RESULTS_3D):
        print(f"  ERROR: {RESULTS_3D} not found.")
        print("  Run batch_run_3d.py first to generate 3D results.")
        sys.exit(1)

    data_3d = load_csv(RESULTS_3D)
    print(f"  {len(data_3d)} cases loaded.")

    pairs = match_cases(data_2d, data_3d)
    print(f"  {len(pairs)} matching 2D/3D pairs found.")

    plot_cl_cd_comparison(data_2d, data_3d, pairs)
    plot_ratio(pairs)
    plot_cl_cd_curve(data_2d, data_3d)
    print_analysis(data_2d, data_3d, pairs)

    print(f"\nAll comparison plots saved to: {OUT_DIR}")


if __name__ == "__main__":
    import sys
    main()
