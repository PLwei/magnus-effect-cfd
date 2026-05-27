# Magnus Effect CFD Simulation — Flettner Rotor Aerodynamics

基于 OpenFOAM-12 的马格努斯效应（Magnus Effect）旋转圆柱 CFD 数值模拟研究。二维 70 工况参数扫描 + 三维有限展长验证。

## 项目概述

Flettner 转子是一种利用 Magnus 效应的风力推进装置——旋转圆柱在来流中产生垂直于流动方向的升力。本项目通过 CFD 模拟系统研究了自旋比（α = ωD/2V）和雷诺数对圆柱气动性能的影响，并量化了二维无限展长假设与三维真实流动之间的差异。

| 参数 | 二维 | 三维 |
|------|------|------|
| 网格 | 17,200 单元（O-grid） | 1,204,000 单元（O-grid 挤压） |
| 工况数 | 70（7 风速 × 10 转速） | 6（代表性工况） |
| Re 范围 | 2.1×10⁶ ~ 5.3×10⁶ | 2.1×10⁶ ~ 5.3×10⁶ |
| α 范围 | 0.63 ~ 15.71 | 0.63 ~ 15.71 |
| 展弦比 | ∞（2D） | 16（64m/4m） |

## 核心结论

1. **升力特性**：CL 随 α 单调递增，最大 CL=22.25（V=8m/s, α=15.71），超过经典 Prandtl 极限（4π≈12.57）
2. **阻力特性**：CD 在 α≈2-3 达到最小值 ~0.12-0.15，旋转抑制涡脱落
3. **三维端部效应**：3D CL 平均为 2D 的 82%；高自旋比（α>10）时降至 46-49%，翼尖涡显著削弱性能
4. **雷诺数效应**：CL 随 Re 增大而减小，中等 α 区差异可达 137%

## 文件结构

```
openfoam_cases/
├── magnus_2d/                    # 二维案例目录
│   ├── 0/                        #   初始/边界条件 (U, p, k, omega, nut)
│   ├── constant/                 #   物理属性 (transportProperties, turbulenceProperties)
│   └── system/                   #   OpenFOAM 配置 (controlDict, fvSchemes, fvSolution, blockMeshDict)
├── magnus_3d/                    # 三维案例目录
│   ├── 0/                        #   初始/边界条件 (7 patches)
│   ├── constant/                 #   物理属性
│   └── system/                   #   OpenFOAM 配置 (含 decomposeParDict)
├── generate_blockmesh_v4.py      # 二维网格生成脚本 (O-grid, 20 块)
├── generate_blockmesh_v5_3d.py   # 三维网格生成脚本 (z 方向挤压)
├── batch_run.py                  # 二维批量运行 (70 工况)
├── batch_run_3d.py               # 三维批量运行 (6 工况, 串行)
├── plot_results.py               # 二维 CL/CD 基础绘图
├── plot_with_literature.py       # 二维 + 理论对比绘图 (Kutta-Joukowski, Prandtl)
├── compare_2d_3d.py              # 二维 vs 三维对比分析
├── generate_final_report.py      # 最终 Word 报告生成器
└── results.csv / results_3d.csv  # 计算结果数据
```

## 使用方法

### 环境要求

- [OpenFOAM-12](https://www.openfoam.org/) (Windows: BlueCFD-Core 2024)
- Python 3.8+ (matplotlib, python-docx, numpy)

### 二维仿真

```bash
# 1. 生成网格
python generate_blockmesh_v4.py
# 在 BlueCFD 终端中运行 blockMesh
blockMesh -case magnus_2d

# 2. 批量运行 (70 工况, 约 3-5 小时)
python batch_run.py
# 在 BlueCFD 终端中执行

# 3. 生成图表
python plot_results.py
python plot_with_literature.py
```

### 三维仿真

```bash
# 1. 生成网格
python generate_blockmesh_v5_3d.py
blockMesh -case magnus_3d
checkMesh -case magnus_3d

# 2. 批量运行 (6 工况, 串行约 20 小时)
python batch_run_3d.py
# 在 BlueCFD 终端中执行

# 3. 对比分析
python compare_2d_3d.py
```

### 生成报告

```bash
python generate_final_report.py
# 输出: Magnus效应CFD仿真最终报告.docx
```

## 数值方法

| 项目 | 设置 |
|------|------|
| 求解器 | foamRun -solver incompressibleFluid (SIMPLE) |
| 湍流模型 | k-ω SST |
| 动量离散 | bounded Gauss linearUpwind grad(U) (二阶) |
| 湍流离散 | bounded Gauss upwind (一阶) |
| 梯度 | cellLimited Gauss linear 1 |
| 收敛判据 | p/U: 1e-5, k/ω: 1e-4 |

## 参考文献

- Karabelas, S.J., et al. (2012). High Reynolds number turbulent flow past a rotating cylinder. *Applied Mathematical Modelling*, 36(1), 379-398.
- Swanson, W.M. (1961). The Magnus effect: A summary of investigations to date. *Journal of Basic Engineering*, 83(3), 461-470.
- Prandtl, L., & Tietjens, O.G. (1957). *Applied Hydro- and Aeromechanics*. Dover Publications.

## License

MIT
