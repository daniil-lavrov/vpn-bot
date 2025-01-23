from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import text

start_ads_keyboard = [
    [InlineKeyboardButton(text=text.ads_button, pay=True, callback_data='ads')]
]
start_ads_keyboard = InlineKeyboardMarkup(inline_keyboard=start_ads_keyboard)
