import logging
from pprint import pprint
from environs import Env
from typing import List, Dict, Any
import sqlite3    
import openpyxl
import datetime

from langchain_openai import ChatOpenAI
from langchain.memory import ConversationTokenBufferMemory
from langchain.prompts.prompt import PromptTemplate
from langchain.chains import ConversationChain


logging.basicConfig(
    filename="logging.txt",
    filemode="a",
    format="%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
    level=logging.DEBUG,
)

# import env config file
env = Env()
env.read_env()#'../.env', recurse=False)


class CustomConversationTokenBufferMemory(ConversationTokenBufferMemory):
    def clear(self):
        super().clear()
        buffer = self.chat_memory.messages
        curr_buffer_length = self.llm.get_num_tokens_from_messages(buffer)
        while curr_buffer_length > self.max_token_limit:
            buffer.pop(0)
            curr_buffer_length = self.llm.get_num_tokens_from_messages(buffer)
    
    extra_variables:List[str] = []

    @property
    def memory_variables(self) -> List[str]:
        """Will always return list of memory variables."""
        return [self.memory_key] + self.extra_variables

    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Return buffer with history and extra variables"""
        d = super().load_memory_variables(inputs)
        d.update({k:inputs.get(k) for k in self.extra_variables})        
        return d
    
                                 
system_prompt = ''
scripts_text = ''




    

async def update_info():
    '''
    Обновление системного промпта и скрипта продаж
    '''

    excel_script_path = 'docs/sales_scripts.xlsx'
    wb = openpyxl.load_workbook(excel_script_path)
    ws = wb.active
    scripts_text= ''
    for row in ws.iter_rows(min_row=2):
        scripts_text += "Клиент:" + str(row[0].value) + '\n' + "AI ассистент:" + str(row[1].value) + '\n'
    scripts_text 
    
    print('Считан скрипт продаж:\n', scripts_text)
    # with open('docs/train_script.txt', 'r') as f:
    #     scripts_text = f.read()
    
    with open('docs/system_prompt.txt', 'r') as f:
        system_prompt = f.read()
    print('Считан системный промпт\n', system_prompt)
    
    return system_prompt, scripts_text


async def get_prompt():
        system_prompt, scripts_text = await update_info()
        template = f"""{system_prompt}\n
        Скрипт продаж:\n {scripts_text}\n"""
        template += """История общения с текущим клиентом: \n
        {history}\n
        Клиент: \n
        {input} \n
        AI ассистент:\n"""
        prompt_template = PromptTemplate(input_variables= ["history", "input"],
            template=template,)
        
        return prompt_template
        
# async def get_conversation_chain_history(prompt_template, verbose=False):

#     llm = ChatOpenAI(openai_api_key=env("OPENAI_TOKEN"), temperature=0.7)
#     # conversation = LLMChain(llm=llm, prompt=prompt_template)
#     conversation = ConversationChain(
#     llm=llm, verbose=verbose, prompt=prompt_template, memory=CustomConversationTokenBufferMemory(llm=llm, max_token_limit=2000, human_prefix="Клиент", ai_prefix="AI ассистент", extra_variables=["scripts_text", "system_prompt"]))
#     return conversation



# async def get_conversation_chain_window(prompt_template, verbose=False):
#     llm = ChatOpenAI(openai_api_key=env("OPENAI_TOKEN"), temperature=0.7)
#     conversation = ConversationChain(
#     llm=llm, verbose=verbose, prompt=prompt_template, memory=ConversationBufferWindowMemory(k=1, human_prefix="Клиент", ai_prefix="AI ассистент")
# )
#     return conversation


# async def get_conversation_chain_summary(prompt_template, verbose=False):
#     llm = ChatOpenAI(openai_api_key=env("OPENAI_TOKEN"), temperature=0.7)
#     conversation = ConversationChain(
#     llm=llm, verbose=verbose, prompt=prompt_template, memory=ConversationSummaryMemory(llm=llm)
# )
#     return conversation


async def get_user_conversation(user_id, verbose=False):
    prompt_template = await get_prompt()
    llm = ChatOpenAI(openai_api_key=env("OPENAI_TOKEN"), temperature=0.7)
    conversation = ConversationChain(
    llm=llm, verbose=verbose, prompt=prompt_template, memory=CustomConversationTokenBufferMemory(llm=llm, max_token_limit=2000, human_prefix="Клиент", ai_prefix="AI ассистент"))
    connection = sqlite3.connect('seller_bot.db')
    cursor = connection.cursor()        
    # Извлекаем историю сообщений пользователя
    cursor.execute('SELECT input, output FROM (SELECT chat_id, input, output FROM chats WHERE user_id = ? ORDER BY chat_id DESC LIMIT 10) ORDER BY chat_id', (user_id, ))
    user_history= cursor.fetchall()
    if user_history:
        _ = [conversation.memory.save_context({"input": input }, {"output": output}) for input, output in user_history]    
    return conversation
    
async def get_answer_from_llm(conversation, input):
    prompt_template = await get_prompt()
    answer = await conversation.ainvoke(input=input)
    return answer['response']


async def insert_chat(user_id, input, output):
        connection = sqlite3.connect('seller_bot.db')
        cursor = connection.cursor()

        # Добавляем новое сообщение (вопрос-ответ) в базу
        cursor.execute('INSERT INTO chats (input, output, user_id, chat_datetime) VALUES (?, ?, ?, ?)', (input, output, user_id, datetime.datetime.now()))

        # Сохраняем изменения и закрываем соединение
        connection.commit()
        connection.close()
        

async def insert_user(user_id, username):
        connection = sqlite3.connect('seller_bot.db')
        cursor = connection.cursor()        
        # Проверяем наличие пользователя
        cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id, ))
        user_exists = cursor.fetchall()
        if user_exists == []:
        # Добавляем нового пользователя
            cursor.execute('INSERT INTO users (user_id, username) VALUES (?, ?)', (user_id, username))
        # Сохраняем изменения и закрываем соединение
        connection.commit()
        connection.close()
        
