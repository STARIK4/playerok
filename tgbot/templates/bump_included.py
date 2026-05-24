import math
import textwrap
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from settings import Settings as sett

from .. import callback_datas as calls


def bump_included_text():
    included_bump_items = sett.get("auto_bump_items").get("included")
    config = sett.get("config")
    default_interval = config["playerok"]["auto_bump_items"]["interval"]
    txt = textwrap.dedent(f"""
        <b>⬆️➕ Включенные</b>
        Всего <b>{len(included_bump_items)}</b> включенных товаров.

        <blockquote><b>(?)</b> Товары поднимаются по очереди (1 → 2 → ... → N → 1). Для каждого товара можно задать <b>свой интервал</b> кнопкой ⏰. Если интервал не задан — используется общий ({default_interval} сек.).</blockquote>
    """)
    return txt


def bump_included_kb(page=0):
    auto_bump_items = sett.get("auto_bump_items")
    included_bump_items: list[list] = auto_bump_items.get("included") or []
    intervals: list = auto_bump_items.get("intervals") or []

    rows = []
    items_per_page = 7
    total_pages = math.ceil(len(included_bump_items) / items_per_page)
    total_pages = total_pages if total_pages > 0 else 1

    if page < 0: page = 0
    elif page >= total_pages: page = total_pages - 1

    start_offset = page * items_per_page
    end_offset = start_offset + items_per_page

    for keyphrases in list(included_bump_items)[start_offset:end_offset]:
        keyphrases_frmtd = ", ".join(keyphrases) or "❌ Не указано"
        idx = included_bump_items.index(keyphrases)

        interval_val = None
        if idx < len(intervals):
            try:
                v = int(intervals[idx])
                if v > 0:
                    interval_val = v
            except (TypeError, ValueError):
                interval_val = None
        interval_label = f"⏰ {interval_val} сек." if interval_val else "⏰ Общий"

        rows.append([
            InlineKeyboardButton(text=f"{keyphrases_frmtd}", callback_data="null_answer"),
        ])
        rows.append([
            InlineKeyboardButton(text=interval_label, callback_data=calls.EnterIncludedBumpItemInterval(index=idx).pack()),
            InlineKeyboardButton(text=f"🗑️", callback_data=calls.DeleteIncludedBumpItem(index=idx).pack()),
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