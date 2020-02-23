from telegram.ext import Updater, CommandHandler, ConversationHandler, MessageHandler, Filters, CallbackQueryHandler
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton

# Typing
from telegram import Update, User, Bot

import logging
from os import environ
import json
from config import TG_TOKEN, REQUEST_KWARGS

import backend_api
from keyboards import (
    MenuKeyboard, TasksKeyboard, TaskChosenKeyboard, ContinueKeyboard,
    AnsweringKeyboard, AdminKeyboard, BackToMenuKeyboard
)
from utils import *
from states import States, AdminStates

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

raiseExceptions = True


def start(bot: Bot, update: Update, user_data: dict):
    user_data.update({"chosen_task": None})

    update.message.reply_text(
        "Привет! Ты вошел в телеграм-квиз с мемами про наш любимый КНиИТ!",
        reply_markup=ReplyKeyboardRemove()
    )

    user: User = update.message.from_user
    if user.username is None:
        return States.wait_for_username(bot, update, user_data)

    else:
        logger.debug(backend_api.register_user(user.id, user.username, user.full_name))
        update.message.reply_text("Ты успешно зарегистрирован в системе!")
        return States.main_menu(bot, update, user_data)


def username_check(bot: Bot, update: Update, user_data):
    user: User = update.message.from_user
    if user.username is None:
        return States.wait_for_username(bot, update, user_data)

    else:
        logger.debug(backend_api.register_user(user.id, user.username, user.full_name))
        update.message.reply_text("Ты успешно зарегистрирован в системе!")
        return States.main_menu(bot, update, user_data)


def resume_bot(bot: Bot, update: Update, user_data):
    status_code, state = backend_api.get_state(update.message.from_user.id)

    user_data.update(json.loads(state["user_data"]))
    last_state = state["last_state"]

    for handler in conversation_handler.states[last_state]:
        if handler.filters.filter(update):
            return handler.callback(bot, update, user_data)

    return last_state


def stop(bot, update):
    update.message.reply_text('Пока!', reply_markup=ReplyKeyboardRemove())
    update.message.reply_text('Для того, чтобы начать работу с ботом заново напишите /start')
    return ConversationHandler.END


def error(bot, update, error):
    logger.warning('Update "%s" caused error "%s"', update, error)


def main():
    updater = Updater(TG_TOKEN, request_kwargs=REQUEST_KWARGS)

    dp = updater.dispatcher
    dp.add_error_handler(error)
    dp.add_handler(conversation_handler)

    updater.start_polling()
    updater.idle()


conversation_handler = ConversationHandler(
    entry_points=[
        CommandHandler('start', start, pass_user_data=True),
        MessageHandler(Filters.text, resume_bot, pass_user_data=True),
    ],

    states={
        WAIT_FOR_USERNAME: [MessageHandler(Filters.text, username_check, pass_user_data=True)],

        MAIN_MENU: [
            MessageHandler(Filters.regex(MenuKeyboard.CHOOSE_TASK), States.choose_task, pass_user_data=True),
            MessageHandler(Filters.regex(MenuKeyboard.TOP_10), States.top_10, pass_user_data=True),
            MessageHandler(Filters.regex(MenuKeyboard.RULES), States.rules, pass_user_data=True),
            CommandHandler('admin', AdminStates.admin_panel, pass_user_data=True)
        ],
        TASK_CHOOSING: [
            MessageHandler(Filters.regex(TasksKeyboard.CANCEL), States.main_menu, pass_user_data=True),
            MessageHandler(Filters.text, States.show_task, pass_user_data=True),
        ],
        TASK_SHOWN: [
            MessageHandler(Filters.regex(TaskChosenKeyboard.CANCEL), States.choose_task, pass_user_data=True),
            MessageHandler(Filters.text, States.accept_answer, pass_user_data=True),
            # MessageHandler(Filters.regex(TaskChosenKeyboard.TYPE_ANSWER), States.type_answer, pass_user_data=True),
        ],
        ANSWERING: [
            MessageHandler(Filters.regex(AnsweringKeyboard.CANCEL), States.show_task, pass_user_data=True),
            MessageHandler(Filters.text, States.accept_answer, pass_user_data=True),
        ],
        ANSWER_RIGHT: [MessageHandler(Filters.text, States.main_menu, pass_user_data=True)],
        ANSWER_WRONG: [MessageHandler(Filters.text, States.show_task, pass_user_data=True)],

        # ADMIN PANEL

        ADMIN_MENU: [
            MessageHandler(Filters.regex(AdminKeyboard.CANCEL), States.main_menu, pass_user_data=True),
            MessageHandler(Filters.regex(AdminKeyboard.PUBLISH_TASK), AdminStates.choose_task_publish, pass_user_data=True),
            MessageHandler(Filters.regex(AdminKeyboard.HIDE_TASK), AdminStates.choose_task_hide, pass_user_data=True),
            MessageHandler(Filters.regex(AdminKeyboard.ANNOUNCE), AdminStates.wait_for_announcement, pass_user_data=True),
            MessageHandler(Filters.regex(AdminKeyboard.MESSAGE_PLAYER), AdminStates.wait_for_message, pass_user_data=True),
        ],

        ADMIN_WAIT_FOR_ANNOUNCEMENT: [
            MessageHandler(Filters.regex(BackToMenuKeyboard.CANCEL), AdminStates.admin_panel, pass_user_data=True),
            MessageHandler(Filters.text, AdminStates.announce_message, pass_user_data=True),
        ],
        ADMIN_WAIT_FOR_MESSAGE: [
            MessageHandler(Filters.regex(BackToMenuKeyboard.CANCEL), AdminStates.admin_panel, pass_user_data=True),
            MessageHandler(Filters.text, AdminStates.message_plr, pass_user_data=True),
        ],

        ADMIN_TASK_CHOOSE_HIDE: [
            MessageHandler(Filters.regex(TasksKeyboard.CANCEL), AdminStates.admin_panel, pass_user_data=True),
            MessageHandler(Filters.text, AdminStates.hide_task, pass_user_data=True),
        ],

        ADMIN_TASK_CHOOSE_PUBLISH: [
            MessageHandler(Filters.regex(TasksKeyboard.CANCEL), AdminStates.admin_panel, pass_user_data=True),
            MessageHandler(Filters.text, AdminStates.publish_task, pass_user_data=True),
        ],

        ADMIN_TASK_PUBLISHED: [MessageHandler(Filters.text, AdminStates.admin_panel, pass_user_data=True)],
        ADMIN_ACCESS_DENIED: [MessageHandler(Filters.text, States.main_menu, pass_user_data=True)],
    },

    fallbacks=[CommandHandler('stop', stop)]
)

if __name__ == '__main__':
    main()
