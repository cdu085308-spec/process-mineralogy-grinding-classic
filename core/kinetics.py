"""
磨矿动力学模型 - 一阶动力学 & Rosin-Rammler 粒度分布
"""
import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Tuple
from core.liberation import liberation_degree

_SIEVE = np.array([1, 5, 10, 20, 38, 45, 74, 100, 150, 200, 300, 400, 500, 1000, 2000, 5000], dtype=float)

@dataclass
class MineralComponent:
    """一种矿物组分的输入参数"""
    name: str
    content: float
    bond_wi: float
    grain_size: float
    texture: str = "simple"
    density: float = 3.0

def breakage_rate_params(wi, mill_type="球磨机"):
    """分粒级破碎速率参数: S(d) = a * d^alpha, 返回 (a, alpha, k100)"""
    c_map = {"球磨机": 4.0, "棒磨机": 3.2, "自磨机": 1.8}
    c = c_map.get(mill_type, 1.0)
    k100 = c / max(wi, 1)
    alpha = max(0.5, min(1.2, 1.2 - 0.03 * (wi - 8)))
    a = k100 / (100 ** alpha) if alpha > 0 else k100
    return a, alpha, k100

def first_order_kinetics(r0, k, t):
    return r0 * np.exp(-k * t)

def first_order_kinetics_curve(r0, k, times):
    return r0 * np.exp(-k * times)

def estimate_k_from_wi(wi, mill_type="球磨机"):
    c_map = {"球磨机": 4.0, "棒磨机": 3.2, "自磨机": 1.8, "破碎机": 2.0}
    c = c_map.get(mill_type, 1.0)
    return round(c / wi, 4)

def time_to_target_r(k, r0, r_target):
    if r_target <= 0 or r0 <= 0 or k <= 0: return 0
    ratio = r_target / r0
    if ratio <= 0: return 0
    return round(-np.log(ratio) / k, 2)

def rosin_rammler(d, d63, n):
    return 1 - np.exp(-((d / d63) ** n))

def rosin_rammler_oversize(d, d63, n):
    return np.exp(-((d / d63) ** n))

def estimate_rr_params(p80, n=1.0):
    d63 = p80 / (np.log(5)) ** (1 / n)
    return round(d63, 1), n

def simulate_grinding_curve(wi, f80, time_points, mill_type="球磨机"):
    k = estimate_k_from_wi(wi, mill_type)
    results = {}
    for t in time_points:
        p80 = f80 * np.exp(-k * t * 1.8)
        p80 = max(p80, 10)
        sieve_sizes = np.array([1, 5, 10, 20, 38, 45, 74, 100, 150, 200, 300, 400, 500, 1000, 2000, 5000])
        d63 = p80 / (np.log(5)) ** (1 / 1.2)
        passing = rosin_rammler(sieve_sizes, d63, 1.2) * 100
        results[round(t, 4)] = {"p80": round(p80, 1), "sieve": sieve_sizes, "passing": np.round(passing, 1)}
    return results

def optimal_grind_size(liberation_size, target_liberation=0.85):
    return round(liberation_size / (target_liberation ** (1 / 1.5)), 1)

def fit_rosin_rammler(sieve_sizes, cumulative_passing):
    from numpy.polynomial import polynomial as P
    x = np.log(np.array(sieve_sizes, dtype=float))
    passing = np.array(cumulative_passing, dtype=float)
    valid = (passing > 0.5) & (passing < 99.5)
    if np.sum(valid) < 3: return 0.0, 0.0, 0.0, 0.0
    y = np.log(-np.log(1 - passing[valid] / 100.0))
    x_valid = x[valid]
    coeffs = P.polyfit(x_valid, y, 1)
    n = coeffs[1]; c = coeffs[0]
    if n <= 0: return 0.0, 0.0, 0.0, 0.0
    d63 = np.exp(-c / n)
    y_fit = P.polyval(x_valid, coeffs)
    ss_res = np.sum((y - y_fit) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0
    sizes = np.array([10, 20, 38, 45, 74, 100, 150, 200, 300, 400, 500, 600, 800, 1000, 2000, 3000, 5000, 10000])
    p80_v = d63 * (-np.log(0.2)) ** (1 / n)
    f80_v = d63 * (-np.log(0.2)) ** (1 / n)
    p50_v = d63 * (-np.log(0.5)) ** (1 / n)
    p20_v = d63 * (-np.log(0.8)) ** (1 / n)
    fitted_curve = {"sieve": sizes, "passing": np.round(100 * (1 - np.exp(-((sizes / d63) ** n))), 1)}
    return {"n": round(n,4), "d63": round(d63,1), "r_squared": round(r_squared,4), "p80": round(p80_v,1),
            "p50": round(p50_v,1), "p20": round(p20_v,1), "f80": round(f80_v,1),
            "fitted_curve": fitted_curve,
            "raw_data": {"sieve": np.round(sieve_sizes,1).tolist(), "passing": np.round(cumulative_passing,1).tolist()},
            "regression": {"x": np.round(x_valid,4).tolist(), "y": np.round(y,4).tolist(), "y_fit": np.round(y_fit,4).tolist()}}

def calc_p80_from_rr(n, d63, target=0.2):
    if n <= 0 or d63 <= 0: return 0.0
    return d63 * (-np.log(target)) ** (1 / n)

def read_sieve_csv(file_content):
    import numpy as np
    lines_raw = file_content.replace(chr(13), '').strip().split(chr(10))
    lines = [l for l in lines_raw if l.strip()]
    sizes, passing = [], []
    for line in lines:
        parts = [p.strip() for p in line.replace(chr(9), ',').split(',') if p.strip()]
        if len(parts) >= 2:
            try:
                s = float(parts[0])
                p = float(parts[1])
                if s > 0:
                    sizes.append(s)
                    passing.append(p)
            except ValueError:
                pass
    if len(sizes) < 2:
        raise ValueError('有效数据不足（至少需要 2 组筛析点）')
    paired = sorted(zip(sizes, passing), reverse=True)
    sizes = [p[0] for p in paired]
    passing = [p[1] for p in paired]
    return np.array(sizes, dtype=float), np.array(passing, dtype=float)

def _calc_pX(mass, sieve, pct=0.8):
    cum = np.cumsum(mass)
    idx = np.searchsorted(cum, pct)
    if idx == 0: return float(sieve[0])
    if idx >= len(sieve): return float(sieve[-1])
    low, high = cum[idx-1], cum[idx]
    f = (pct - low) / (high - low) if high > low else 0
    return float(sieve[idx-1] + (sieve[idx] - sieve[idx-1]) * f)

def _under_size_fraction(mass, sieve, threshold=10.0):
    if threshold <= sieve[0]: return 0.0
    if threshold >= sieve[-1]: return 1.0
    idx = np.searchsorted(sieve, threshold)
    if idx == 0: return 0.0
    f = (threshold - sieve[idx-1]) / (sieve[idx] - sieve[idx-1]) if sieve[idx] > sieve[idx-1] else 0
    cum_before = mass[:idx-1].sum() if idx > 1 else 0
    return float(cum_before + mass[idx-1] * f)

def _initial_mass_from_f80(f80, sieve, n=1.2):
    d63 = f80 / (np.log(5)) ** (1/n) if n > 0 else f80
    cum = 1 - np.exp(-((sieve / d63) ** n))
    mass = np.diff(cum, prepend=0)
    mass = np.maximum(mass, 0)
    s = mass.sum()
    return mass / s if s > 0 else mass

def _breakage_distribution_matrix(sieve, beta=0.8):
    """构建破碎分布矩阵 B[i,j] — j 类破碎后进入 i 类的质量份数 (i <= j, 即更细或同级)"""
    n = len(sieve)
    B = np.zeros((n, n))
    for j in range(n):
        # sieve 从细到粗: [0]=最细, [n-1]=最粗
        # j 类破碎后分配到 0..j (更细或同级)
        finer = np.arange(0, j+1)
        ratios = np.maximum(sieve[finer] / sieve[j], 1e-10)
        cum_b = ratios ** beta
        diff = np.diff(cum_b, prepend=0)
        diff = np.maximum(diff, 0)
        s = diff.sum()
        if s > 0:
            B[finer, j] = diff / s
    return B

def simulate_multi_mineral_grinding(components, f80, max_time=60.0, n_points=20, mill_type="球磨机"):
    """多矿物磨矿模拟 (简化版, 基于 P80 指数衰减)
    
    每种矿物:
      - P80_i(t) = F80 * exp(-k_eff * t)  其中 k_eff = c/Wi * 1.8
      - 粒度分布: Rosin-Rammler 在 P80_i 处
      - 解离度: liberation_degree(grain_size, P80_i)
    
    输出包含每矿物的 P80 轨迹和粒度分布
    """
    sieve = _SIEVE
    time_points = np.linspace(1, max_time, n_points)
    total_pct = sum(c.content for c in components) or 100
    MILL_C = {"球磨机": 4.0, "棒磨机": 3.2, "自磨机": 1.8}

    timeline = []
    for t in time_points:
        mineral_masses = {}
        mineral_p80s = {}
        overall_mass = np.zeros(len(sieve))

        for comp in components:
            c = MILL_C.get(mill_type, 1.0)
            k_eff = c / max(comp.bond_wi, 1) * 1.8
            p80_t = max(f80 * np.exp(-k_eff * t), 2)
            mineral_p80s[comp.name] = round(p80_t, 1)

            # Rosin-Rammler 分布 for current P80
            n_rr = max(0.8, min(1.8, 1.8 - 0.04 * (comp.bond_wi - 8)))
            d63 = p80_t / (np.log(5)) ** (1 / n_rr) if n_rr > 0 else p80_t
            cum = 1 - np.exp(-((sieve / max(d63, 1)) ** n_rr))
            mass = np.diff(cum, prepend=0)
            mass = np.maximum(mass, 0)
            s = mass.sum()
            if s > 0:
                mass = mass / s

            frac = comp.content / total_pct
            mineral_masses[comp.name] = mass
            overall_mass += mass * frac

        overall_mass = overall_mass / overall_mass.sum()
        overall_p80 = round(_calc_pX(overall_mass, sieve, 0.8), 1)

        round_t = round(t, 1)
        entry = {"time": round_t, "overall_p80": overall_p80,
                 "mineral_p80s": mineral_p80s, "mineral_masses": mineral_masses,
                 "overall_mass": overall_mass,
                 "passing": np.round(np.cumsum(overall_mass) * 100, 1)}
        timeline.append(entry)

    return {"timeline": timeline, "time_points": time_points, "sieve": sieve,
            "components": [(c.name, c.content, c.grain_size, c.texture) for c in components]}

def compute_liberation_timeline(sim_result):
    sieve = sim_result["sieve"]
    comp_info = sim_result.get("components", [])
    for entry in sim_result["timeline"]:
        p80 = entry["overall_p80"]
        entry["over_grind_frac"] = round(_under_size_fraction(entry["overall_mass"], sieve, 10) * 100, 1)
        if not comp_info:
            entry["liberations"] = {}
            entry["overall_liberation"] = 0.0
            continue
        libs = {}
        ws, tw = 0.0, 0.0
        for name, content, gs, texture in comp_info:
            lib = liberation_degree(gs, p80, mineral_ratio=content/100, texture=texture)
            libs[name] = round(lib * 100, 1)
            ws += lib * content
            tw += content
        entry["liberations"] = libs
        entry["overall_liberation"] = round(ws / tw * 100, 1) if tw > 0 else 0.0
    return sim_result

def find_optimal_time(sim_result):
    best = {"time": 0, "p80": 0, "liberation": 0, "over_grind": 0, "score": -1}
    for entry in sim_result["timeline"]:
        lib = entry.get("overall_liberation", 0)
        og = entry.get("over_grind_frac", 100)
        score = lib - og * 2.0
        if score > best["score"] and entry["time"] > 0:
            best = {"time": entry["time"], "p80": entry["overall_p80"],
                    "liberation": lib, "over_grind": og, "score": round(score, 1)}
    milestones = {"t_liberation_85": None, "t_liberation_90": None}
    for entry in sim_result["timeline"]:
        lib = entry.get("overall_liberation", 0)
        if milestones["t_liberation_85"] is None and lib >= 85:
            milestones["t_liberation_85"] = entry["time"]
        if milestones["t_liberation_90"] is None and lib >= 90:
            milestones["t_liberation_90"] = entry["time"]
    best.update(milestones)
    return best
