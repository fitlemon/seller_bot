from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, FSInputFile, KeyboardButton, ReplyKeyboardMarkup   

import message_texts    
    
    
    
delete_context_kb = [[InlineKeyboardButton(text="🚮 Удалить у себя", callback_data="delete_self_context")], 
            [InlineKeyboardButton(text="🚮 Удалить у всех ❗", callback_data="delete_all_context")]]
delete_context_kb = InlineKeyboardMarkup(inline_keyboard=delete_context_kb)


admin_kb = [[KeyboardButton(text=message_texts.commands['report'], callback_data="get_report")], 
            [KeyboardButton(text=message_texts.commands['delete_context'], callback_data="delete_context")]]
admin_kb = ReplyKeyboardMarkup(keyboard=admin_kb, resize_keyboard=True)