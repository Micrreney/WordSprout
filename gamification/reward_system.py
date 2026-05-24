"""水滴/阳光奖励计算与发放。"""

from datetime import date

from database.models import DailyReward, PlantState


def record_review(quality: int, is_new_word: bool = False) -> dict:
    """
    记录一次复习，更新今日奖励。
    返回本日累计奖励信息。
    """
    today = date.today().isoformat()
    reward = DailyReward.get_by_date(today)
    if reward is None:
        yesterday = date.today()
        if yesterday.day > 1:
            yesterday = yesterday.replace(day=yesterday.day - 1)
        else:
            yesterday = None
        prev_streak = DailyReward.get_by_date(yesterday.isoformat()).streak_days if yesterday else 0
        reward = DailyReward(date=today, streak_days=prev_streak)

    reward.words_reviewed += 1

    # 水滴计算
    water = 0
    if quality >= 5:
        water += 2
    elif quality >= 3:
        water += 1

    if is_new_word:
        water += 2

    reward.water_drops += water

    # 里程碑奖励
    bonus = 0
    if reward.words_reviewed == 10:
        bonus += 5
    elif reward.words_reviewed == 30:
        bonus += 10

    reward.water_drops += bonus

    reward.save()

    # 更新植物水滴
    plant = PlantState.get()
    plant.total_water += water + bonus
    plant.save()

    return {
        "words_reviewed": reward.words_reviewed,
        "water_gained": water + bonus,
        "total_water_today": reward.water_drops,
        "total_water_all": plant.total_water,
    }


def apply_daily_sunshine() -> dict:
    """
    每日打卡时调用，计算阳光奖励。
    在应用启动或每天第一次复习时触发。
    """
    today = date.today().isoformat()
    reward = DailyReward.get_today()
    if reward is None:
        return {"sunshine_gained": 0, "streak": 0}

    # 阳光在当天第一次复习时授予
    if reward.words_reviewed > 1:
        return {"sunshine_gained": 0, "streak": reward.streak_days}

    # 计算连续天数
    streak = DailyReward.get_streak()

    sunshine = 0
    if streak == 3:
        sunshine = 1
    elif streak == 7:
        sunshine = 3
    elif streak == 30:
        sunshine = 10
    elif streak > 0 and streak % 30 == 0:
        sunshine = 10
    else:
        # 每天给1点阳光，保持激励
        sunshine = 0

    if sunshine > 0:
        reward.sunshine += sunshine
        reward.streak_days = streak
        reward.save()

        plant = PlantState.get()
        plant.total_sunshine += sunshine
        plant.save()

    return {
        "sunshine_gained": sunshine,
        "streak": streak,
        "total_sunshine": PlantState.get().total_sunshine,
    }


def apply_water_decay() -> int:
    """应用每日水滴衰减（每天-2滴）。返回衰减的滴数。"""
    today = date.today().isoformat()
    plant = PlantState.get()

    if plant.last_water_decay_date == today:
        return 0

    plant.total_water = max(0, plant.total_water - 2)
    plant.last_water_decay_date = today
    plant.save()
    return 2
