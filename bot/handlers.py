from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message
import re
import logging
from environs import Env

from aiogram import flags
from aiogram.fsm.context import FSMContext

import utils
from states import Gen
import loader

router = Router()
bot = loader.bot

# import env config file
env = Env()
env.read_env()#'../.env', recurse=False)


# Handler for start command at the beginning
@router.message(Command("start"))
async def start_handler(msg: Message, state: FSMContext):
    """
    Bot actions for start command
    """
    await utils.insert_user(msg.from_user.id, msg.from_user.username)
    conversation = await utils.get_user_conversation(msg.from_user.id)
    input = 'Здравствуйте!'
    answer = await utils.get_answer_from_llm(conversation, input)
    # Сохраняем сообщения в базе
    await utils.insert_chat(msg.from_user.id, input=input, output=answer)
    await msg.answer(answer
    )  # Greeting message to user
    await state.set_state(Gen.chat_state)  # change State to Initial State
    # logging.info(convesations)
    logging.info(input)
    logging.info(answer)



# Catch  "Questions" from client #Gen.chat_state
@router.message(F.content_type == 'text')
async def chat_with_client(msg: Message):
    """
    Bot actions in chat
    """
    await utils.insert_user(msg.from_user.id, msg.from_user.username)
    conversation = await utils.get_user_conversation(msg.chat.id)
    input = msg.text
    await bot.send_chat_action(chat_id=msg.chat.id, action="typing")
    answer = await utils.get_answer_from_llm(conversation, input)
    # Сохраняем сообщения в базе
    await utils.insert_chat(msg.from_user.id, input=input, output=answer)
    await msg.answer(
        answer
    )  # Greeting message to user
    # logging.info(utils.convesations)
    logging.info(input)
    logging.info(answer)
    
    
@router.message(F.content_type == 'document')
async def load_files(msg : Message, state: FSMContext):
    if msg.document:
        file_id = msg.document.file_id
        file_info = await bot.get_file(file_id)
        file_path = file_info.file_path
        file_name = msg.document.file_name
        # Download the file
        file = await bot.download_file(file_path)
        print('Take file:', file_name)
        try:
            print('Parsing..')
            parse_token = file_name.split('.')[0]
            print('Parsed_token:', parse_token)
            if parse_token == env('TOKEN_SYSTEM_PROMPT'):
                with open(f'docs/system_prompt.txt', 'wb') as new_file:
                    new_file.write(file.read())
                await msg.reply("Обновлен системный промпт. Модель переобучается...")
            elif parse_token == env('TOKEN_TRAIN_SCRIPT'):
                with open(f'docs/sales_scripts.xlsx', 'wb') as new_file:
                    new_file.write(file.read())
                await msg.reply("Обновлен скрипт продаж. Модель переобучается...")
            else:
                await msg.reply("Я не могу принимать документы.")
        except:
            await msg.reply("Неизвестный формат документа")
    else:
        await msg.reply("Я не могу принимать документы.")

