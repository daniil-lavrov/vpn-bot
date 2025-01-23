from aiogram import Router, types
from aiogram.filters import Command, StateFilter
from aiogram.types import Message
from user_manager import User_manager
import asyncio
from aiogram.utils.keyboard import InlineKeyboardBuilder

import kb
import text

router = Router()


@router.message(StateFilter(None), Command("start"))
async def start_handler(msg: Message):
    answer = await User_manager.create_user(msg.chat.id)
    if answer:
        if answer == 'error_repeat':
            await msg.answer(text.error_repeat)
        elif answer == 'no_available_config':
            await msg.answer(text.no_available_config)
        else:
            await msg.answer(text.greet)
    else:
        pass

@router.message(StateFilter(None), Command("connection"))
async def connection_handler(msg: Message):
    answer = await User_manager.get_link_config(msg.chat.id)
    if answer == 'error_repeat':
        await msg.answer(text.error_repeat)
    elif answer == 'no_available_config':
        await msg.answer(text.no_available_config)
    elif answer == 'go_to_status_to_unfroze':
        await msg.answer(text.go_to_status_to_unfroze)
    else:
        def link_keyboard():
            builder = InlineKeyboardBuilder()
            builder.button(text=text.config_button, callback_data=answer)
            return builder.as_markup()
        await msg.answer(text.connection, reply_markup=link_keyboard())

@router.message(StateFilter(None), Command("status"))
async def status_handler(msg: Message):
    status = await User_manager.get_status(msg.chat.id)
    if status == 'error_repeat':
        await msg.answer(text.error_repeat)
    elif status == 'active':
        await msg.answer(text.status_active, reply_markup=kb.start_ads_keyboard)
    elif status == 'inactive':
        await msg.answer(text.go_to_connection_to_activate)
    elif status == 'frozen':
        await msg.answer(text.status_frozen, reply_markup=kb.start_ads_keyboard)

@router.message(StateFilter(None), Command("about"))
async def about_handler(msg: Message):
    await msg.answer(text.about)

@router.callback_query()
async def process_callback(callback_query: types.CallbackQuery):
    data = callback_query.data

    if data == 'ads':
        ads_text = await User_manager.get_ads_text(callback_query.message.chat.id)
        if ads_text == 'error_repeat':
            await callback_query.message.answer(text.error_repeat)
        else:
            await callback_query.message.answer(ads_text)
            await callback_query.answer(text.wait_please)
            await asyncio.sleep(12)
            await callback_query.message.answer(text.config_unfroze_suc)
    else:
        answer = await User_manager.check_config_owner(callback_query.message.chat.id, data)
        if answer:
            if answer == 'error_repeat':
                await callback_query.message.answer(text.error_repeat)
            else:
                config_file = await User_manager.api_get_config(data)
                if config_file == 'error_repeat':
                    await callback_query.message.answer(text.error_repeat)
                else:
                    await callback_query.answer()
                    await callback_query.message.reply_document(document=config_file)
        else:
            await callback_query.message.answer(text.wrong_config)