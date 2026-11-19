"""
Bond 功指数法 - 磨矿能耗与时间计算
"""
import numpy as np

def bond_energy(wi, f80, p80):
    if f80 <= 0 or p80 <= 0 or p80 >= f80:
        return 0.0
    return wi * 10 * (1 / np.sqrt(p80) - 1 / np.sqrt(f80))

def grinding_time(energy, throughput, mill_power, efficiency=0.85, fill_ratio=0.35):
    if mill_power <= 0 or throughput <= 0:
        return 0.0
    total_energy = energy * throughput
    actual_power = mill_power * efficiency
    time_h = total_energy / actual_power
    return round(time_h * 60, 1)

def estimate_p80_from_time(wi, f80, time_min, mill_power, throughput, efficiency=0.85):
    total_energy_kwh = mill_power * efficiency * time_min / 60
    energy_per_ton = total_energy_kwh / throughput
    if energy_per_ton <= 0 or wi <= 0:
        return f80
    inv_sqrt_p80 = energy_per_ton / (wi * 10) + 1 / np.sqrt(f80)
    if inv_sqrt_p80 <= 0:
        return f80
    p80 = (1 / inv_sqrt_p80) ** 2
    return min(round(p80, 1), f80)

def reduction_ratio(f80, p80):
    if p80 <= 0:
        return 0
    return round(f80 / p80, 2)
