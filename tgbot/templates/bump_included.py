import math
import textwrap
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from settings import Settings as sett

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


def bump_included_text():
    included_bump_items = sett.get("auto_bump_items").get("included")
    txt = textwrap.dedent(f"""
        <b>⬆️➕ Включенные</b>
        Всего <b>{len(included_bump_items)}</b> включенных товаров:
        <blockquote><b>(?)</b> Товары поднимаются по очереди. Для каждого товара можно задать свой интервал поднятия, либо использовать общий.</blockquote>
    """)
    return txt


def bump_included_kb(page=0):
    included_bump_items: list = sett.get("auto_bump_items").get("included") or []
    config = sett.get("config")
    default_interval = config["playerok"]["auto_bump_items"].get("interval") or 5400

    rows = []
    items_per_page = 5
    total_pages = math.ceil(len(included_bump_items) / items_per_page)
    total_pages = total_pages if total_pages > 0 else 1

    if page < 0: page = 0
    elif page >= total_pages: page = total_pages - 1

    start_offset = page * items_per_page
    end_offset = start_offset + items_per_page

    for index, raw_entry in enumerate(included_bump_items[start_offset:end_offset], start=start_offset):
        entry = _normalize_entry(raw_entry)
        keyphrases = entry["keyphrases"]
        interval = entry["interval"]

        keyphrases_frmtd = ", ".join(keyphrases) or "❌ Не указано"
        interval_lbl = f"{interval} сек." if interval else f"{default_interval} сек. (общ.)"

        rows.append([
            InlineKeyboardButton(text=f"{keyphrases_frmtd}", callback_data="null_answer"),
        ])
        rows.append([
            InlineKeyboardButton(
                text=f"⏰ Интервал: {interval_lbl}",
                callback_data=calls.EnterIncludedBumpItemInterval(index=index).pack()
            ),
            InlineKeyboardButton(
                text=f"🗑️",
                callback_data=calls.DeleteIncludedBumpItem(index=index).pack()
            ),
        ])

    if total_pages > 1:
        buttons_row = []
        btn_back = InlineKeyboardButton(text="←", callback_data=calls.IncludedBumpItemsPagination(page=page-1).pack()) if page > 0 else InlineKeyboardButton(text="🛑", callback_data="null_answer")
        buttons_row.append(btn_back)

        btn_pages = InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="null_answer")
        buttons_row.append(btn_pages)

        btn_next = InlineKeyboardButton(text="→", callback_data=calls.IncludedBumpItemsPagination(page=page+1).pack()) if page < total_pages - 1 else InlineKeyboardButton(text="🛑", callback_data="null_answer")
        buttons_row.append(btn_next)
        rows.append(buttons_row)

    rows.append([
        InlineKeyboardButton(text="➕ Добавить", callback_data="enter_new_included_bump_item_keyphrases"),
        InlineKeyboardButton(text="➕📄 Добавить много", callback_data="send_new_included_bump_items_keyphrases_file"),
    ])
    rows.append([
        InlineKeyboardButton(text="⬅️ Назад", callback_data=calls.MenuNavigation(to="bump").pack()),
    ])

    kb = InlineKeyboardMarkup(inline_keyboard=rows)
    return kb


def bump_included_float_text(placeholder: str):
    txt = textwrap.dedent(f"""
        <b>⬆️➕ Включенные</b>
        \n{placeholder}
    """)
    return txt


def new_bump_included_float_text(placeholder: str):
    txt = textwrap.dedent(f"""
        <b>⬆️➕ Добавление включенного товара</b>
        \n{placeholder}
    """)
    return txt
