"""
矿物解离度分析 - 改进版
使用渐近线模型替代原 Gaudin 模型，解离度不超最大上限
"""
import numpy as np

def _get_max_liberation(texture):
    limits = {"simple": 0.93, "complex": 0.82, "veinlet": 0.87, "massive": 0.78}
    return limits.get(texture, 0.88)

def _get_rate_parameter(texture, mineral_ratio=0.5):
    base_k = {"simple": 1.8, "complex": 1.0, "veinlet": 1.3, "massive": 0.8}
    k = base_k.get(texture, 1.2)
    k *= (0.6 + 0.4 * mineral_ratio)
    return k

def liberation_degree(grain_size, grind_size, mineral_ratio=0.5,
                      texture="simple", max_liberation=0.0):
    """
    渐近线模型: L = L_max * (1 - exp(-k * ratio))
    ratio = grain_size / grind_size
    永远不超过 L_max
    """
    if grain_size <= 0 or grind_size <= 0:
        return 0.0
    if max_liberation <= 0:
        max_liberation = _get_max_liberation(texture)
    ratio = grain_size / grind_size
    k = _get_rate_parameter(texture, mineral_ratio)
    liberation = max_liberation * (1.0 - np.exp(-k * ratio))
    return max(0.0, min(liberation, max_liberation))

def optimal_grind_for_liberation(grain_sizes, target_liberation=0.85, texture="simple"):
    """渐近线反函数: 求达到目标解离度所需的 P80"""
    min_grain = min(grain_sizes)
    max_lib = _get_max_liberation(texture)
    if target_liberation <= 0:
        return float(min_grain)
    if target_liberation >= max_lib:
        return round(min_grain * 0.1, 1)
    k = _get_rate_parameter(texture, 0.5)
    ratio = -np.log(1 - target_liberation / max_lib) / k
    p80 = min_grain / ratio if ratio > 0 else float(min_grain)
    return round(p80, 1)

def get_liberation_summary(texture):
    s = {
        "simple": "粗粒均匀嵌布，最大理论解离度约93%",
        "complex": "细粒不规则嵌布，解离上限较低，最大理论解离度约82%",
        "veinlet": "脉状/网脉状嵌布，最大理论解离度约87%",
        "massive": "块状/稠密浸染状嵌布，解离难度大，最大理论解离度约78%",
    }
    return s.get(texture, "嵌布类型未知")

def recommend_grind_strategy(mineral_composition, target_liberation=0.85):
    valuable = [m for m in mineral_composition if m.get("mineral_type") == "valuable"]
    gangue = [m for m in mineral_composition if m.get("mineral_type") == "gangue"]
    if not valuable:
        return {"error": "未设置目的矿物"}
    main_v = max(valuable, key=lambda x: x["content"])
    texture = main_v.get("texture", "simple")
    max_lib = _get_max_liberation(texture)
    v_gs = [m["grain_size"] for m in valuable]
    p80_rec = optimal_grind_for_liberation(v_gs, target_liberation, texture)
    if gangue:
        g_min = min(m["grain_size"] for m in gangue)
        p80_rec = max(p80_rec, g_min * 0.3)
    total_c = sum(m["content"] for m in mineral_composition) or 1
    predictions = {}
    for m in mineral_composition:
        tex = m.get("texture", "simple")
        # 使用实际占比（归一化），而非假设总和为 100
        actual_ratio = m["content"] / total_c
        lib = liberation_degree(m["grain_size"], p80_rec,
                               mineral_ratio=actual_ratio, texture=tex)
        predictions[m["name"]] = round(lib * 100, 1)
    gr = max(v_gs) - min(v_gs)
    total_c = sum(m["content"] for m in mineral_composition) or 1
    avg_wi = sum(m.get("bond_wi", 12) * m["content"] for m in mineral_composition) / total_c
    return {
        "recommended_p80": round(p80_rec, 1),
        "target_liberation": target_liberation,
        "max_possible_liberation": round(max_lib * 100, 1),
        "texture": texture,
        "texture_description": get_liberation_summary(texture),
        "predicted_liberations": predictions,
        "grain_size_range": round(gr, 1),
        "valuable_grain_sizes": v_gs,
        "average_wi": round(avg_wi, 1),
        "mineral_composition": mineral_composition,
    }
