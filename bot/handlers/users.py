from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

import logging
from environs import Env

import utils
import kb
from states import Gen

router = Router()

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
    # Вывод ответа обчному пользователю
    await msg.answer(answer)  
    await state.set_state(Gen.chat_state)  # change State to Chat State   
    # logging.info(convesations)
    # logging.info(input)
    # logging.info(answer)

      
@router.message(F.text == env('ADMIN_TOKEN'))
async def catch_admin_token(msg: Message, admins_set: set[int]):
    """
    Bot actions in chat
    """
    
    admins_set.add(msg.from_user.id)
    await utils.make_admin(msg.from_user.id)
    # Вывод ответа администратору
    await msg.answer(f"Пользователь {msg.from_user.id} успешно добавлен в администраторы.", reply_markup=kb.admin_kb)     


# Обработка текстовых сообщений пользователей
@router.message(F.content_type == 'text' )
async def chat_with_client(msg: Message, bot):
    """
    Bot actions in chat
    """
    print("chat_with_client")
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
    # Вывод ответа обчному пользователю
    await msg.answer(answer)    
    # logging.info(input)
    # logging.info(answer)
    

# Обработка сообщений с прикрепленным файлом
@router.message(F.content_type == 'document')
async def load_files(msg : Message, state: FSMContext):
    await msg.reply("Я к сожалению не могу обрабатывать документы.")

