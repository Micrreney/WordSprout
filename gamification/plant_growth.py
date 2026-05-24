"""植物成长阶段逻辑。"""

from database.models import PlantState

STAGES = [
    {"name": "种子", "icon": "🌰", "water": 0, "sunshine": 0},
    {"name": "发芽", "icon": "🌱", "water": 30, "sunshine": 3},
    {"name": "幼苗", "icon": "🌿", "water": 80, "sunshine": 8},
    {"name": "成长", "icon": "🪴", "water": 200, "sunshine": 20},
    {"name": "开花", "icon": "🌸", "water": 500, "sunshine": 50},
    {"name": "结果", "icon": "🍎", "water": 1000, "sunshine": 100},
    {"name": "大树", "icon": "🌳", "water": 2000, "sunshine": 200},
]


def get_current_stage() -> dict:
    plant = PlantState.get()
    stage_idx = min(plant.stage, len(STAGES) - 1)
    return {**STAGES[stage_idx], "index": stage_idx}


def update_stage() -> dict:
    """根据当前资源量更新植物阶段，返回最新阶段信息。"""
    plant = PlantState.get()

    new_stage = 0
    for i, s in enumerate(STAGES):
        if plant.total_water >= s["water"] and plant.total_sunshine >= s["sunshine"]:
            new_stage = i

    if new_stage != plant.stage:
        plant.stage = new_stage
        plant.save()

    return {**STAGES[new_stage], "index": new_stage}


def get_next_stage_info() -> dict:
    """获取升到下一阶段所需条件。"""
    current = get_current_stage()
    idx = current["index"]
    if idx >= len(STAGES) - 1:
        return {"name": "已满级", "water_needed": 0, "sunshine_needed": 0, "is_max": True}

    next_s = STAGES[idx + 1]
    plant = PlantState.get()
    return {
        "name": next_s["name"],
        "icon": next_s["icon"],
        "water_needed": max(0, next_s["water"] - plant.total_water),
        "sunshine_needed": max(0, next_s["sunshine"] - plant.total_sunshine),
        "water_total": next_s["water"],
        "sunshine_total": next_s["sunshine"],
        "current_water": plant.total_water,
        "current_sunshine": plant.total_sunshine,
        "is_max": False,
    }
