from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message
import os
import logging
from environs import Env
import asyncio

from aiogram import flags
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, FSInputFile, KeyboardButton, ReplyKeyboardMarkup
import utils
import message_texts
from states import Gen
import loader


router = Router()
bot = loader.bot

# import env config file
env = Env()
env.read_env()#'../.env', recurse=False)


# Обработчик для команды Старт
@router.message(Command("start"))
async def start_handler(msg: Message, state: FSMContext):
    """
    Bot actions for start command
    """
    await utils.insert_user(msg.from_user.id, msg.from_user.username)
    conversation = await utils.get_user_conversation(msg.from_user.id)
    input = 'Здравствуйте!'
    logging.info(f"Обработка запроса пользователя {msg.from_user.id}. Запрос: {input}")
    answer = await utils.get_answer_from_llm(conversation, input)
    logging.info(f"Ответ на запрос пользователя {msg.from_user.id}. Ответ от ИИ: {answer}")
    # Сохраняем сообщения в базе
    await utils.insert_chat(msg.from_user.id, input=input, output=answer)
    is_admin = await utils.is_admin(user_id=msg.from_user.id)
    if is_admin:        
        admin_kb = [[KeyboardButton(text=message_texts.commands['report'], callback_data="get_report")], 
                    [KeyboardButton(text=message_texts.commands['delete_context'], callback_data="delete_context")]]
        admin_kb = ReplyKeyboardMarkup(keyboard=admin_kb, resize_keyboard=True)
            # Вывод ответа администратору
        await msg.answer(
        answer, reply_markup=admin_kb
    ) 
    else:
        # Вывод ответа обчному пользователю
        await msg.answer(answer)  
    await state.set_state(Gen.chat_state)  # change State to Chat State
   
    # logging.info(convesations)
    # logging.info(input)
    # logging.info(answer)



# Колбэк для отправки файла отчета по сообщениям
@router.message(F.text == message_texts.commands['report'])
async def get_chats_report(msg: Message):
    is_admin = await utils.is_admin(user_id=msg.from_user.id)
    if is_admin: 
        report_status = await utils.create_chats_report()
        if report_status:
            try:
                if os.path.exists('docs/chat_history.xlsx'):
                    doc_path = 'docs/chat_history.xlsx'
                    await msg.answer_document(FSInputFile(doc_path))
                    logging.info(f"Отчёт по чатам отправлен пользователю {msg.chat.id}")
                else:
                    await msg.answer("Файл отчета не найден")
            except Exception as e:
                logging.error(e)
        else:
            await msg.answer("Файл отчёта не создан()")
    else:
        await msg.answer("Вы не админ бота.")
        logging.info(f"Отчёт по чатам НЕ отправлен пользователю {msg.chat.id}. Так как он не админ")
        

# Колбэк для намерения удалить контекст общения с ИИ
@router.message(F.text == message_texts.commands['delete_context'])
async def delete_context(msg: Message):
    is_admin = await utils.is_admin(user_id=msg.from_user.id)
    if is_admin: 
        trash_context_kb = [[InlineKeyboardButton(text="🚮 Удалить у себя", callback_data="delete_self_context")], 
                        [InlineKeyboardButton(text="🚮 Удалить у всех ❗", callback_data="delete_all_context")]]
        trash_context_kb = InlineKeyboardMarkup(inline_keyboard=trash_context_kb)
            # Вывод ответа администратору
        await msg.answer("Можете удалить контекст только у себя или у всех пользователей.", reply_markup=trash_context_kb)
    else:
        await msg.answer("Вы не админ бота.")
        logging.info(f"Контекст сообщений НЕ очищен пользователю {msg.chat.id}. Так как он не админ")
    
        
# Обработка текстовых сообщений пользователей

@router.message(F.content_type == 'text' )
async def chat_with_client(msg: Message):
    """
    Bot actions in chat
    """
    if msg.text == env('ADMIN_TOKEN'):
        await utils.make_admin(msg.from_user.id)
        admin_kb = [[KeyboardButton(text=message_texts.commands['report'], callback_data="get_report")], 
                    [KeyboardButton(text=message_texts.commands['delete_context'], callback_data="delete_context")]]
        admin_kb = ReplyKeyboardMarkup(keyboard=admin_kb, resize_keyboard=True)
         # Вывод ответа администратору
        await msg.answer(f"Пользователь {msg.from_user.id} успешно добавлен в администраторы.", reply_markup=admin_kb)
        return None
    #Добавляем пользователя в БД, есои его нет
    await utils.insert_user(msg.from_user.id, msg.from_user.username)
    conversation = await utils.get_user_conversation(msg.chat.id)
    input = msg.text
    logging.info(f"Обработка запроса пользователя {msg.from_user.id}. Запрос: {input}")
    await bot.send_chat_action(chat_id=msg.chat.id, action="typing")
    # Получаем ответ от ОпенАИ
    answer = await utils.get_answer_from_llm(conversation, input)
    logging.info(f"Ответ на запрос пользователя {msg.from_user.id}. Ответ от ИИ: {answer}")
    # Сохраняем сообщения в базе
    await utils.insert_chat(msg.from_user.id, input=input, output=answer)
    # Проверка является ли пользователь админом
    is_admin = await utils.is_admin(user_id=msg.from_user.id)
    if is_admin:        
        admin_kb = [[KeyboardButton(text=message_texts.commands['report'], callback_data="get_report")], 
                    [KeyboardButton(text=message_texts.commands['delete_context'], callback_data="delete_context")]]
        admin_kb = ReplyKeyboardMarkup(keyboard=admin_kb, resize_keyboard=True)
         # Вывод ответа администратору
        await msg.answer(
        answer, reply_markup=admin_kb
    ) 
    else:
        # Вывод ответа обчному пользователю
        await msg.answer(answer)  
    
    # logging.info(input)
    # logging.info(answer)
    

# Обработка сообщений с прикрепленным файлом
@router.message(F.content_type == 'document')
async def load_files(msg : Message, state: FSMContext):
    is_admin = await utils.is_admin(user_id=msg.from_user.id)
    if is_admin:
        if msg.document:
            file_id = msg.document.file_id
            file_info = await bot.get_file(file_id)
            file_path = file_info.file_path
            file_name = msg.document.file_name
            # Download the file
            file = await bot.download_file(file_path)
            print('Take file:', file_name)
            try:
                if file_name == 'system_prompt.txt':
                    with open(f'docs/system_prompt.txt', 'wb') as new_file:
                        new_file.write(file.read())
                    await asyncio.sleep(1)
                    await msg.reply("Обновлен системный промпт. Модель переобучится в скором времени...")
                    logging.info(f"Обновлен системный промпт пользователем {msg.from_user.id}")
                elif file_name == 'sales_scripts.xlsx':
                    with open(f'docs/sales_scripts.xlsx', 'wb') as new_file:
                        new_file.write(file.read())
                    await asyncio.sleep(1) 
                    await msg.reply("Обновлен скрипт продаж. Модель переобучится в скором времени...")
                    logging.info(f"Обновлен скрипт продаж пользователем {msg.from_user.id}")
                else:
                    await msg.reply("Я принимаю только магические документы...")
            except:
                await msg.reply("Неизвестный формат документа")
    else:
        await msg.reply("Я не могу принимать документы.")




    

# Колбэк для удаления контекста общения ИИ только у себя
@router.callback_query(F.data == "delete_self_context")
async def delete_self_context(clbck: CallbackQuery, state: FSMContext):
    await utils.delete_self_context(clbck.message.chat.id)
    await clbck.message.answer("Контекст Вашего общения с ИИ удален") 



# Колбэк для удаления контекста общения ИИ только у себя
@router.callback_query(F.data == "delete_all_context")
async def delete_self_context(clbck: CallbackQuery, state: FSMContext):
    await utils.delete_all_context(clbck.message.chat.id)
    await clbck.message.answer("Контекст общения с ИИ всех пользователей очищен") 
