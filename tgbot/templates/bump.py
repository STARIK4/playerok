import textwrap
from datetime import datetime
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from settings import Settings as sett
from utils import get_event_next_time

from .. import callback_datas as calls


def _normalize_entry(entry):
    if isinstance(entry, dict):
        return {
            "keyphrases": list(entry.get("keyphrases") or []),
            "interval": entry.get("interval")
        }
    if isinstance(entry, list):
        return {"keyphrases": list(entry), "interval": None}
    return {"keyphrases": [], "interval": None}


def _current_cycle_interval(config, auto_bump_items):
    default_interval = config["playerok"]["auto_bump_items"].get("interval") or 5400
    use_all = config["playerok"]["auto_bump_items"].get("all", False)
    if use_all:
        return default_interval
    included = [_normalize_entry(e) for e in (auto_bump_items.get("included") or [])]
    if not included:
        return default_interval
    idx = (config["playerok"]["auto_bump_items"].get("current_index", 0) or 0) % len(included)
    return included[idx].get("interval") or default_interval


def bump_text():
    config = sett.get("config")

    enabled = "✅" if config["playerok"]["auto_bump_items"]["enabled"] else "❌"
    all = "Все товары" if config["playerok"]["auto_bump_items"]["all"] else "Указанные товары"
    interval = config["playerok"]["auto_bump_items"]["interval"] or "❌ Не указано"

    auto_bump_items = sett.get("auto_bump_items")
    included_list = auto_bump_items["included"] or []
    included = len(included_list)
    excluded = len(auto_bump_items["excluded"] or [])
    current_index = config["playerok"]["auto_bump_items"].get("current_index", 0) or 0

    last_time_iso = config["playerok"]["auto_bump_items"]["last_time"]
    last_time = datetime.fromisoformat(last_time_iso).strftime("%d.%m.%Y %H:%M:%S") if last_time_iso else "никогда"

    cycle_interval = _current_cycle_interval(config, auto_bump_items)

    if config["playerok"]["auto_bump_items"]["enabled"]:
        if not last_time_iso:
            next_time = "прямо сейчас"
        else:
            next_time = get_event_next_time(last_time_iso, cycle_interval).strftime("%d.%m.%Y %H:%M:%S")
    else:
        next_time = "никогда"

    if not config["playerok"]["auto_bump_items"].get("all", False) and included > 0:
        pos_index = current_index % included
        current_keyphrases = ", ".join(_normalize_entry(included_list[pos_index]).get("keyphrases") or []) or "(пусто)"
        cycle_position = f"{pos_index + 1}/{included} (<code>{current_keyphrases}</code>)"
    else:
        cycle_position = "—"

    schedule = config["playerok"]["auto_bump_items"].get("schedule") or {}
    sched_enabled = "✅" if schedule.get("enabled") else "❌"
    pause_start = schedule.get("pause_start") or "—"
    pause_end = schedule.get("pause_end") or "—"

    txt = textwrap.dedent(f"""
        <b>⬆️ Авто-поднятие</b>
        <blockquote><b>(?)</b> Бот поднимает товары по очереди: 1 → 2 → 3 → ... → последний → снова 1. Для каждого товара можно задать собственный интервал.</blockquote>

        <b>💡 Включено:</b> {enabled}
        <b>⏰ Общий интервал:</b> {interval} сек.
        <b>🔁 Текущая позиция в цикле:</b> {cycle_position}

        <b>📦 Поднимать:</b> {all}
        <blockquote><b>(?)</b> Если вы выберете "Все товары", то будут подниматься все товары, кроме тех, что указаны в исключениях. Если вы выберете "Указанные товары", то будут подниматься только те товары, которые вы добавите во включенные.</blockquote>

        <b>🌙 Расписание паузы:</b> {sched_enabled} (с <b>{pause_start}</b> до <b>{pause_end}</b>)
        <blockquote><b>(?)</b> Во время паузы бот не поднимает товары. Интервал «замораживается»: товар, который должен был подняться в паузу, поднимется через оставшееся время после её окончания.</blockquote>

        <b>➕ Включенные:</b> {included}
        <b>➖ Исключенные:</b> {excluded}

        ⏮️ Последний раз было <b>{last_time}</b>
        ⏭️ Следующий раз будет <b>{next_time}</b>
    """)
    return txt


def bump_kb():
    config = sett.get("config")
    
    enabled = "✅" if config["playerok"]["auto_bump_items"]["enabled"] else "❌"
    all = "Все товары" if config["playerok"]["auto_bump_items"]["all"] else "Указанные товары"
    interval = config["playerok"]["auto_bump_items"]["interval"] or "❌ Не указано"
    
    auto_bump_items = sett.get("auto_bump_items")
    included = len(auto_bump_items["included"])
    excluded = len(auto_bump_items["excluded"])
    
    schedule = config["playerok"]["auto_bump_items"].get("schedule") or {}
    sched_enabled = "✅" if schedule.get("enabled") else "❌"
    pause_start = schedule.get("pause_start") or "—"
    pause_end = schedule.get("pause_end") or "—"

    rows = [
        [InlineKeyboardButton(text=f"⬆️ Поднять товары", callback_data="confirm_bump_items")],
        [InlineKeyboardButton(text=f"💡 Включено: {enabled}", callback_data="switch_auto_bump_items_enabled")],
        [InlineKeyboardButton(text=f"📦 Поднимать: {all}", callback_data="switch_auto_bump_items_all")],
        [InlineKeyboardButton(text=f"⏰ Интервал: {interval} сек.", callback_data="enter_auto_bump_items_interval")],
        [InlineKeyboardButton(text=f"🌙 Расписание паузы: {sched_enabled}", callback_data="switch_auto_bump_schedule_enabled")],
        [
            InlineKeyboardButton(text=f"🌙 Начало: {pause_start}", callback_data="enter_auto_bump_schedule_start"),
            InlineKeyboardButton(text=f"☀️ Конец: {pause_end}", callback_data="enter_auto_bump_schedule_end"),
        ],
        [
        InlineKeyboardButton(text=f"➕ Включенные: {included}", callback_data=calls.IncludedBumpItemsPagination(page=0).pack()),
        InlineKeyboardButton(text=f"➖ Исключенные: {excluded}", callback_data=calls.ExcludedBumpItemsPagination(page=0).pack())
        ],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data=calls.MenuNavigation(to="default").pack())]
    ]
    kb = InlineKeyboardMarkup(inline_keyboard=rows)
    return kb


def bump_float_text(placeholder: str):
    txt = textwrap.dedent(f"""
        <b>⬆️ Авто-поднятие</b>
        \n{placeholder}
    """)
    return txt