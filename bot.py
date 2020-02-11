from telegram.ext import Updater, CommandHandler, ConversationHandler, MessageHandler, Filters, CallbackQueryHandler
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton

# Typing
from telegram import Update, User, Bot

import logging
from os import environ
from config import TG_TOKEN, REQUEST_KWARGS

import backend_api

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def start(bot: Bot, update: Update, user_data):
    update.message.reply_text(
        "Привет! Ты вошел в телеграм-квиз с мемами про наш любимый КНиИТ.",
        reply_markup=ReplyKeyboardRemove()
    )

    user: User = update.message.from_user
    if user.username is None:
        update.message.reply_text(
            "По правилам квиза ты не можешь участвовать, если у тебя не указано "
            "имя пользователя, поэтому укажи его и возвращайся как только это сделаешь!",
            reply_markup=ReplyKeyboardMarkup([['Я указал имя пользователя']])
        )
        return USERNAME_CHECK

    else:
        logger.debug(backend_api.register_user(user.id, user.username, user.full_name))
        update.message.reply_text("Ты успешно зарегистрирован в системе!")

        update.message.reply_text("Твой счет: 0")
        update.message.reply_text(
            "Выбери следующее действие...",
            reply_markup=ReplyKeyboardMarkup([
                ["Сдать задачу"],
                ["Топ-10", "Правила"]
            ])
        )

        return MAIN_MENU


def username_check(bot: Bot, update: Update, user_data):
    user: User = update.message.from_user
    if user.username is None:
        update.message.reply_text(
            "Ты все еще не указал имя пользователя!",
            reply_markup=ReplyKeyboardMarkup([['Я указал имя пользователя']])
        )
        return USERNAME_CHECK

    else:
        logger.debug(backend_api.register_user(user.id, user.username, user.full_name))
        update.message.reply_text("Ты успешно зарегистрирован в системе!")

        update.message.reply_text("Твой счет: 0")
        update.message.reply_text(
            "Выбери следующее действие...",
            reply_markup=ReplyKeyboardMarkup([
                ["Сдать задачу"],
                ["Топ-10", "Правила"]
            ])
        )

        return MAIN_MENU


def main_menu(bot, update, user_data):
    text = update.message.text

    if text == "Сдать задачу":
        update.message.reply_text("А пока что нельзя!!")
        return MAIN_MENU

    elif text == "Топ-10":
        update.message.reply_text("Топ-1:\n1.Андрей Гущин")
        return MAIN_MENU

    elif text == "Правила":
        update.message.reply_text("Какие-то правила!!!!")
        return MAIN_MENU

    return MAIN_MENU


def rules(bot: Bot, update: Update, user_data):
    update.message.reply_text("Какие-то правила!!!!")
    return MAIN_MENU


def top_10(bot: Bot, update: Update, user_data):
    update.message.reply_text("Топ-1:\n1.Андрей Гущин")
    return MAIN_MENU


def task_choose(bot: Bot, update: Update, user_data):
    update.message.reply_text("А пока что нельзя!!")
    return MAIN_MENU


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


(
    USERNAME_CHECK, USERNAME_HOLD,
    MAIN_MENU, TOP_10, RULES,
    TASK_CHOOSE, CANCEL_CHOOSE,
    TASK_SHOW, CANCEL_SHOW,
    ENTER_ANSWER, CANCEL_ANSWER,
    *_
) = range(100)

conversation_handler = ConversationHandler(
    entry_points=[
        CommandHandler('start', start, pass_user_data=True)
    ],

    states={
        USERNAME_CHECK: [MessageHandler(Filters.text, username_check, pass_user_data=True)],
        MAIN_MENU: [MessageHandler(Filters.text, main_menu, pass_user_data=True)],
        RULES: [MessageHandler(Filters.text, rules, pass_user_data=True)],
        TOP_10: [MessageHandler(Filters.text, top_10, pass_user_data=True)],
        TASK_CHOOSE: [MessageHandler(Filters.text, task_choose, pass_user_data=True)],
    },

    fallbacks=[CommandHandler('stop', stop)]
)

if __name__ == '__main__':
    main()
