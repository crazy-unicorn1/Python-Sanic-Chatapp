# -*- coding: utf-8 -*-
# import sys
# sys.path.append('/www/project_kfShare')
import logging,datetime,shortuuid,six,re,copy,telegram,asyncio
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, ConversationHandler, filters
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)
token = '6471505983:AAE7JvJcxk75lzzoHWoox810xWvdVBw3Htc'
# uId = '1131694507'


RECEIVE_US = [
    {
        "chat_id": "5676707895",
        "first_name": "EasyChat24",
    },{
        "chat_id": "1131694507",
        "first_name": "Awlanan",
    },
]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = '欢迎使用!'
    await context.bot.send_message(update.effective_chat.id, text=text)


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = '''
    欢迎使用！
    '''
    await context.bot.send_message(update.effective_chat.id, text=text)


# 监控其它信息
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # if not update or not update.message or not update.message.text:
    #     return
    # newText = update.message.text
    # print('newText:', newText)
    print('Update:', update)
    print('context:', context)



async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    ''' 监控其他命令 '''
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")



async def sendMessage(text):

    try:
        application = telegram.Bot(token=token)
        for dd in RECEIVE_US:
            await application.send_message(chat_id=dd.get('chat_id'), text=text)
    except:
        pass

def sendTelMag(text):
    asyncio.get_event_loop().run_until_complete(sendMessage(text=text))


def main() -> None:
    """Run the bot."""
    application = Application.builder().token(token).build()

    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    help_handler = CommandHandler('help', help)
    application.add_handler(help_handler)

    unknown_handler = MessageHandler(filters.COMMAND, unknown)
    application.add_handler(unknown_handler)

    echo_handler = MessageHandler(filters.TEXT, echo)
    application.add_handler(echo_handler)

    application.run_polling()

# if __name__ == '__main__':
#     sendMag()
