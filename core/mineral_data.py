"""
矿物数据库 - 含常见矿物的工艺矿物学参数
"""
import pandas as pd
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple


MINERAL_CATALOG_PATH = Path(__file__).resolve().parent.parent / "data" / "minerals.csv"

@dataclass
class Mineral:
    name: str
    formula: str = ""
    density: float = 0.0
    hardness: float = 0.0
    bond_wi: float = 0.0
    typical_grain_size: Tuple[float, float] = (0, 0)
    mineral_type: str = "others"
    color: str = "#888888"
    texture: str = "simple"  # simple, complex, veinlet, massive
    max_liberation: float = 0.0  # 0 = auto from texture
    source: str = "系统内置教学参数"
    note: str = ""

COMMON_MINERALS = {
    "黄铜矿": Mineral("黄铜矿","CuFeS2",4.2,3.5,14.2,(30,300),"valuable","#DAA520", "complex", 0.0),
    "黄铁矿": Mineral("黄铁矿","FeS2",5.0,6.5,11.5,(20,500),"gangue","#C0C0C0", "complex", 0.0),
    "方铅矿": Mineral("方铅矿","PbS",7.5,2.5,12.0,(40,500),"valuable","#708090", "simple", 0.0),
    "闪锌矿": Mineral("闪锌矿","ZnS",4.0,4.0,13.5,(30,400),"valuable","#8B4513", "complex", 0.0),
    "辉锑矿": Mineral("辉锑矿","Sb2S3",4.6,2.0,10.8,(50,300),"valuable","#696969", "veinlet", 0.0),
    "辉钼矿": Mineral("辉钼矿","MoS2",4.7,1.0,12.5,(50,500),"valuable","#191970", "simple", 0.0),
    "磁黄铁矿": Mineral("磁黄铁矿","Fe1-xS",4.6,4.0,12.0,(30,400),"gangue","#A0522D", "complex", 0.0),
    "赤铁矿": Mineral("赤铁矿","Fe2O3",5.3,6.0,13.8,(30,400),"valuable","#8B0000", "simple", 0.0),
    "磁铁矿": Mineral("磁铁矿","Fe3O4",5.2,5.5,11.0,(30,500),"valuable","#000000", "simple", 0.0),
    "褐铁矿": Mineral("褐铁矿","FeO(OH)-nH2O",3.8,4.0,10.5,(20,200),"valuable","#8B6914", "complex", 0.0),
    "软锰矿": Mineral("软锰矿","MnO2",5.0,4.0,8.5,(30,300),"valuable","#4B0082", "complex", 0.0),
    "锡石": Mineral("锡石","SnO2",7.0,6.5,14.0,(50,500),"valuable","#2F4F4F", "simple", 0.0),
    "石英": Mineral("石英","SiO2",2.65,7.0,13.6,(50,800),"gangue","#E8E8E8", "simple", 0.0),
    "方解石": Mineral("方解石","CaCO3",2.7,3.0,8.5,(50,600),"gangue","#F5F5DC", "simple", 0.0),
    "白云石": Mineral("白云石","CaMg(CO3)2",2.9,3.5,9.5,(50,500),"gangue","#F0E68C", "simple", 0.0),
    "长石": Mineral("长石","(K,Na,Ca)AlSi3O8",2.6,6.0,12.5,(50,700),"gangue","#FFE4B5", "simple", 0.0),
    "云母": Mineral("云母","KAl2(AlSi3O10)(OH)2",2.8,2.5,16.0,(20,200),"gangue","#DEB887", "simple", 0.0),
    "高岭石": Mineral("高岭石","Al4Si4O10(OH)8",2.6,2.0,7.0,(10,100),"gangue","#FFDEAD", "complex", 0.0),
    "萤石": Mineral("萤石","CaF2",3.2,4.0,10.2,(40,400),"valuable","#98FB98", "simple", 0.0),
    "磷灰石": Mineral("磷灰石","Ca5(PO4)3(F,Cl,OH)",3.2,5.0,10.5,(40,400),"valuable","#90EE90", "simple", 0.0),
    "锂辉石": Mineral("锂辉石","LiAlSi2O6",3.2,7.0,14.5,(30,300),"valuable","#DDA0DD", "simple", 0.0),
    "绿柱石": Mineral("绿柱石","Be3Al2Si6O18",2.8,7.5,16.0,(20,200),"valuable","#98FB98", "simple", 0.0),
}

DEFAULT_MINERAL_NAMES = [
    "黄铜矿","方铅矿","闪锌矿","辉锑矿","辉钼矿",
    "赤铁矿","磁铁矿","褐铁矿","锡石",
    "石英","方解石","长石","云母","萤石","磷灰石",
]


def load_mineral_catalog(path: Optional[Path] = None) -> int:
    """从外部 CSV 加载矿物参数；文件缺失时保留代码内置数据。"""
    catalog_path = Path(path) if path is not None else MINERAL_CATALOG_PATH
    if not catalog_path.exists():
        return 0
    try:
        frame = pd.read_csv(catalog_path, encoding="utf-8-sig")
    except Exception:
        return 0
    required = {
        "name",
        "formula",
        "density",
        "hardness",
        "bond_wi",
        "grain_min",
        "grain_max",
        "mineral_type",
        "texture",
    }
    if not required.issubset(frame.columns):
        return 0
    loaded = 0
    for _, row in frame.iterrows():
        name = str(row["name"]).strip()
        if not name:
            continue
        COMMON_MINERALS[name] = Mineral(
            name=name,
            formula=str(row.get("formula", "") or ""),
            density=float(row["density"]),
            hardness=float(row["hardness"]),
            bond_wi=float(row["bond_wi"]),
            typical_grain_size=(float(row["grain_min"]), float(row["grain_max"])),
            mineral_type=str(row.get("mineral_type", "others") or "others"),
            color=COMMON_MINERALS.get(name, Mineral(name)).color,
            texture=str(row.get("texture", "simple") or "simple"),
            max_liberation=float(row.get("max_liberation", 0) or 0),
            source=str(row.get("source", "外部参数库") or "外部参数库"),
            note=str(row.get("note", "") or ""),
        )
        loaded += 1
    if loaded:
        DEFAULT_MINERAL_NAMES[:] = list(COMMON_MINERALS.keys())
    return loaded

def get_mineral(name):
    return COMMON_MINERALS.get(name)

def add_custom_mineral(name, density, hardness, bond_wi, gmin, gmax, mineral_type="valuable", texture="simple", max_liberation=0.0):
    m = Mineral(name,"",density,hardness,bond_wi,(gmin,gmax),mineral_type,"#888888",texture,max_liberation)
    COMMON_MINERALS[name] = m
    return m

def estimate_bond_wi_from_hardness(hardness):
    return round(3.0 + 1.8 * hardness, 1)

def classify_grindability(wi):
    if wi < 8: return "易磨"
    elif wi < 12: return "中等可磨"
    elif wi < 16: return "难磨"
    else: return "极难磨"

def mineral_list_to_dataframe(mineral_names):
    rows = []
    for name in mineral_names:
        m = get_mineral(name)
        if m:
            rows.append({
                "矿物": m.name, "化学式": m.formula,
                "密度(g/cm3)": m.density, "莫氏硬度": m.hardness,
                "Bond Wi(kWh/t)": m.bond_wi,
                "嵌布粒度(um)": f"{m.typical_grain_size[0]}-{m.typical_grain_size[1]}",
                "类型": m.mineral_type,
                "参数来源": m.source,
            })
    return pd.DataFrame(rows)


def mineral_catalog_dataframe():
    rows = []
    for mineral in COMMON_MINERALS.values():
        rows.append(
            {
                "矿物": mineral.name,
                "化学式": mineral.formula,
                "密度(g/cm3)": mineral.density,
                "莫氏硬度": mineral.hardness,
                "Bond Wi(kWh/t)": mineral.bond_wi,
                "嵌布粒度(um)": f"{mineral.typical_grain_size[0]:g}-{mineral.typical_grain_size[1]:g}",
                "类型": mineral.mineral_type,
                "嵌布类型": mineral.texture,
                "参数来源": mineral.source,
                "备注": mineral.note,
            }
        )
    return pd.DataFrame(rows)


# 经典版使用代码内置的原始矿物参数，不加载后续新增的外部参数库。
LOADED_MINERAL_COUNT = 0
