from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext

from settings import Settings as sett

from .. import templates as templ
from .. import callback_datas as calls
from .. import states
from ..helpful import throw_float_message


router = Router()


@router.message(states.BumpItemsStates.waiting_for_bump_items_interval, F.text)
async def handler_waiting_for_bump_items_interval(message: types.Message, state: FSMContext):
    try: 
        await state.set_state(None)
        
        if not message.text.isdigit():
            raise Exception("❌ Вы должны ввести числовое значение")
        if int(message.text) <= 0:
            raise Exception("❌ Слишком низкое значение")

        interval = int(message.text)
        
        config = sett.get("config")
        config["playerok"]["auto_bump_items"]["interval"] = interval
        sett.set("config", config)

        await throw_float_message(
            state=state,
            message=message,
            text=templ.bump_float_text(f"✅ <b>Интервал поднятия товаров</b> был успешно изменён на <b>{interval}</b>"),
            reply_markup=templ.back_kb(calls.MenuNavigation(to="bump").pack())
        )
    except Exception as e:
        await throw_float_message(
            state=state,
            message=message,
            text=templ.bump_float_text(e), 
            reply_markup=templ.back_kb(calls.MenuNavigation(to="bump").pack())
        )


def _parse_hhmm(raw: str):
    raw = (raw or "").strip()
    if ":" not in raw:
        raise Exception("❌ Формат должен быть <code>чч:мм</code> (например, <code>02:00</code>)")
    parts = raw.split(":")
    if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
        raise Exception("❌ Формат должен быть <code>чч:мм</code> (например, <code>02:00</code>)")
    h, m = int(parts[0]), int(parts[1])
    if not (0 <= h < 24 and 0 <= m < 60):
        raise Exception("❌ Часы 0-23, минуты 0-59")
    return f"{h:02d}:{m:02d}"


@router.message(states.BumpItemsStates.waiting_for_bump_schedule_start, F.text)
async def handler_waiting_for_bump_schedule_start(message: types.Message, state: FSMContext):
    try:
        await state.set_state(None)
        value = _parse_hhmm(message.text)

        config = sett.get("config")
        config["playerok"]["auto_bump_items"].setdefault("schedule", {})
        config["playerok"]["auto_bump_items"]["schedule"]["pause_start"] = value
        sett.set("config", config)

        await throw_float_message(
            state=state,
            message=message,
            text=templ.bump_float_text(f"✅ <b>Начало паузы</b> установлено на <b>{value}</b>"),
            reply_markup=templ.back_kb(calls.MenuNavigation(to="bump").pack())
        )
    except Exception as e:
        await throw_float_message(
            state=state,
            message=message,
            text=templ.bump_float_text(e),
            reply_markup=templ.back_kb(calls.MenuNavigation(to="bump").pack())
        )


@router.message(states.BumpItemsStates.waiting_for_bump_schedule_end, F.text)
async def handler_waiting_for_bump_schedule_end(message: types.Message, state: FSMContext):
    try:
        await state.set_state(None)
        value = _parse_hhmm(message.text)

        config = sett.get("config")
        config["playerok"]["auto_bump_items"].setdefault("schedule", {})
        config["playerok"]["auto_bump_items"]["schedule"]["pause_end"] = value
        sett.set("config", config)

        await throw_float_message(
            state=state,
            message=message,
            text=templ.bump_float_text(f"✅ <b>Окончание паузы</b> установлено на <b>{value}</b>"),
            reply_markup=templ.back_kb(calls.MenuNavigation(to="bump").pack())
        )
    except Exception as e:
        await throw_float_message(
            state=state,
            message=message,
            text=templ.bump_float_text(e),
            reply_markup=templ.back_kb(calls.MenuNavigation(to="bump").pack())
        )


@router.message(states.BumpItemsStates.waiting_for_included_bump_item_interval, F.text)
async def handler_waiting_for_included_bump_item_interval(message: types.Message, state: FSMContext):
    try:
        await state.set_state(None)

        data = await state.get_data()
        last_page = data.get("last_page", 0)
        index = data.get("included_bump_item_index")

        raw = message.text.strip().lower()
        if raw in ("", "0", "общий", "сброс", "default", "-", "reset"):
            new_interval = None
        else:
            if not raw.isdigit():
                raise Exception("❌ Вы должны ввести числовое значение (или 0/Enter — общий)")
            new_interval = int(raw)
            if new_interval <= 0:
                raise Exception("❌ Слишком низкое значение")

        auto_bump_items = sett.get("auto_bump_items")
        included = auto_bump_items.get("included") or []
        if index is None or index < 0 or index >= len(included):
            raise Exception("❌ Товар не найден")

        entry = included[index]
        if isinstance(entry, dict):
            entry["interval"] = new_interval
            if "keyphrases" not in entry:
                entry["keyphrases"] = []
        else:
            included[index] = {"keyphrases": list(entry) if isinstance(entry, list) else [], "interval": new_interval}
        auto_bump_items["included"] = included
        sett.set("auto_bump_items", auto_bump_items)

        info = f"{new_interval} сек." if new_interval else "общий интервал"
        await throw_float_message(
            state=state,
            message=message,
            text=templ.bump_included_float_text(f"✅ Интервал товара успешно установлен: <b>{info}</b>"),
            reply_markup=templ.back_kb(calls.IncludedBumpItemsPagination(page=last_page).pack())
        )
    except Exception as e:
        data = await state.get_data()
        last_page = data.get("last_page", 0)
        await throw_float_message(
            state=state,
            message=message,
            text=templ.bump_included_float_text(e),
            reply_markup=templ.back_kb(calls.IncludedBumpItemsPagination(page=last_page).pack())
        )


@router.message(states.BumpItemsStates.waiting_for_new_included_bump_item_keyphrases, F.text)
async def handler_waiting_for_new_included_bump_item_keyphrases(message: types.Message, state: FSMContext):
    try:
        await state.set_state(None)

        if len(message.text) <= 0:
            raise Exception("❌ Слишком короткое значение")

        keyphrases = [phrase.strip() for phrase in message.text.split(",") if phrase.strip()]

        auto_bump_items = sett.get("auto_bump_items")
        auto_bump_items["included"].append({"keyphrases": keyphrases, "interval": None})
        sett.set("auto_bump_items", auto_bump_items)

        data = await state.get_data()
        last_page = data.get("last_page", 0)
        
        await throw_float_message(
            state=state,
            message=message,
            text=templ.new_bump_included_float_text(f"✅ Товар с ключевыми фразами <code>{'</code>, <code>'.join(keyphrases)}</code> успешно включён в поднятие"),
            reply_markup=templ.back_kb(calls.IncludedBumpItemsPagination(page=last_page).pack())
        )
    except Exception as e:
        data = await state.get_data()
        last_page = data.get("last_page", 0)
        await throw_float_message(
            state=state,
            message=message,
            text=templ.new_bump_included_float_text(e), 
            reply_markup=templ.back_kb(calls.IncludedBumpItemsPagination(page=last_page).pack())
        )


@router.message(
    states.BumpItemsStates.waiting_for_new_included_bump_items_keyphrases_file, 
    F.document.file_name.lower().endswith('.txt')
)
async def handler_waiting_for_new_included_bump_items_keyphrases_file(message: types.Message, state: FSMContext):
    try:
        await state.set_state(None)
        
        file = await message.bot.get_file(message.document.file_id)
        downloaded_file = await message.bot.download_file(file.file_path)
        file_content = downloaded_file.read().decode('utf-8')

        keyphrases_list = []
        for line in file_content.splitlines():
            line = line.strip()
            if len(line) > 0:
                keyphrases = [phrase.strip() for phrase in line.split(",") if phrase.strip()]
                if len(keyphrases) > 0:
                    keyphrases_list.append(keyphrases)

        if len(keyphrases_list) <= 0:
            raise Exception("❌ Файл не содержит валидных ключевых фраз")

        auto_bump_items = sett.get("auto_bump_items")
        auto_bump_items["included"].extend(
            [{"keyphrases": kp, "interval": None} for kp in keyphrases_list]
        )
        sett.set("auto_bump_items", auto_bump_items)

        data = await state.get_data()
        last_page = data.get("last_page", 0)
        
        await throw_float_message(
            state=state,
            message=message,
            text=templ.new_bump_included_float_text(f"✅ Успешно включено <b>{len(keyphrases_list)}</b> товаров из файла в поднятие"),
            reply_markup=templ.back_kb(calls.IncludedBumpItemsPagination(page=last_page).pack())
        )
    except Exception as e:
        data = await state.get_data()
        last_page = data.get("last_page", 0)
        await throw_float_message(
            state=state,
            message=message,
            text=templ.new_bump_included_float_text(e), 
            reply_markup=templ.back_kb(calls.IncludedBumpItemsPagination(page=last_page).pack())
        )


@router.message(states.BumpItemsStates.waiting_for_new_excluded_bump_item_keyphrases, F.text)
async def handler_waiting_for_new_excluded_bump_item_keyphrases(message: types.Message, state: FSMContext):
    try: 
        await state.set_state(None)
        
        if len(message.text) <= 0:
            raise Exception("❌ Слишком короткое значение")
        
        keyphrases = [phrase.strip() for phrase in message.text.split(",") if phrase.strip()]
        
        auto_bump_items = sett.get("auto_bump_items")
        auto_bump_items["excluded"].append(keyphrases)
        sett.set("auto_bump_items", auto_bump_items)

        data = await state.get_data()
        last_page = data.get("last_page", 0)
        
        await throw_float_message(
            state=state,
            message=message,
            text=templ.new_bump_excluded_float_text(f"✅ Товар с ключевыми фразами <code>{'</code>, <code>'.join(keyphrases)}</code> успешно добавлен в исключения для поднятия"),
            reply_markup=templ.back_kb(calls.ExcludedBumpItemsPagination(page=last_page).pack())
        )
    except Exception as e:
        data = await state.get_data()
        last_page = data.get("last_page", 0)
        await throw_float_message(
            state=state,
            message=message,
            text=templ.new_bump_excluded_float_text(e), 
            reply_markup=templ.back_kb(calls.ExcludedBumpItemsPagination(page=last_page).pack())
        )


@router.message(
    states.BumpItemsStates.waiting_for_new_excluded_bump_items_keyphrases_file, 
    F.document.file_name.lower().endswith('.txt')
)
async def handler_waiting_for_new_excluded_bump_items_keyphrases_file(message: types.Message, state: FSMContext):
    try:
        await state.set_state(None)
        
        file = await message.bot.get_file(message.document.file_id)
        downloaded_file = await message.bot.download_file(file.file_path)
        file_content = downloaded_file.read().decode('utf-8')

        keyphrases_list = []
        for line in file_content.splitlines():
            line = line.strip()
            if len(line) > 0:
                keyphrases = [phrase.strip() for phrase in line.split(",") if phrase.strip()]
                if len(keyphrases) > 0:
                    keyphrases_list.append(keyphrases)

        if len(keyphrases_list) <= 0:
            raise Exception("❌ Файл не содержит валидных ключевых фраз")

        auto_bump_items = sett.get("auto_bump_items")
        auto_bump_items["excluded"].extend(keyphrases_list)
        sett.set("auto_bump_items", auto_bump_items)

        data = await state.get_data()
        last_page = data.get("last_page", 0)
        
        await throw_float_message(
            state=state,
            message=message,
            text=templ.new_bump_excluded_float_text(f"✅ Успешно добавлено <b>{len(keyphrases_list)}</b> товаров из файла в исключения для поднятия"),
            reply_markup=templ.back_kb(calls.ExcludedBumpItemsPagination(page=last_page).pack())
        )
    except Exception as e:
        data = await state.get_data()
        last_page = data.get("last_page", 0)
        await throw_float_message(
            state=state,
            message=message,
            text=templ.new_bump_excluded_float_text(e), 
            reply_markup=templ.back_kb(calls.ExcludedBumpItemsPagination(page=last_page).pack())
        )