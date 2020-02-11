from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove

from keyboards import (
    MenuKeyboard, TasksKeyboard, TaskChosenKeyboard, ContinueKeyboard,
    AnsweringKeyboard,
)
from utils import *
import backend_api

# Typing
from telegram import Update, User, Bot


def save_state(func):
    def wrapper(bot: Bot, update: Update, user_data: dict, *args, **kwargs):
        print(user_data)
        last_state = func(bot, update, user_data, *args, **kwargs)
        backend_api.save_state(last_state, update.message.from_user.id, user_data)
        return last_state

    return wrapper


class States:
    @staticmethod
    @save_state
    def wait_for_username(bot: Bot, update: Update, user_data: dict):
        update.message.reply_text(
            "По правилам квиза ты не можешь участвовать, если у тебя не указано "
            "имя пользователя, поэтому укажи его и возвращайся как только это сделаешь!",
            reply_markup=ReplyKeyboardMarkup([['Я указал имя пользователя']])
        )
        return WAIT_FOR_USERNAME

    @staticmethod
    @save_state
    def main_menu(bot: Bot, update: Update, user_data: dict):
        user_data["chosen_task"] = None

        update.message.reply_text("Твой счет: 0")
        update.message.reply_text(
            "Выбери следующее действие...",
            reply_markup=ReplyKeyboardMarkup(MenuKeyboard.get_keyboard())
        )

        return MAIN_MENU

    @staticmethod
    @save_state
    def choose_task(bot: Bot, update: Update, user_data: dict):
        user_data["chosen_task"] = None

        update.message.reply_text(
            "Какую задачу ты хочешь сдать?",
            reply_markup=ReplyKeyboardMarkup(TasksKeyboard.get_keyboard())
        )
        return TASK_CHOOSING

    @staticmethod
    @save_state
    def top_10(bot: Bot, update: Update, user_data: dict):
        update.message.reply_text("какая то хуйня")
        return MAIN_MENU

    @staticmethod
    @save_state
    def rules(bot: Bot, update: Update, user_data: dict):
        update.message.reply_text("какая то хуйня")
        return MAIN_MENU

    @staticmethod
    @save_state
    def show_task(bot: Bot, update: Update, user_data: dict):
        if "chosen_task" in user_data and user_data["chosen_task"] is not None:
            task_title = user_data["chosen_task"]
        else:
            task_title = update.message.text
            user_data["chosen_task"] = task_title

        status_code, task = backend_api.get_task(task_title)
        if status_code != 200:
            message = "Произошла ошибка в работе квиза. Мы уже работаем над её устранением!"
            keyboard = ContinueKeyboard.get_keyboard()

        else:
            message = '\n'.join([
                f"*{task['title']}*",
                f"{task['statement']}",
                "",
                f"_Теги: {task['tags']}_",
            ])
            keyboard = TaskChosenKeyboard.get_keyboard()

        update.message.reply_text(
            message, parse_mode="Markdown",
            reply_markup=ReplyKeyboardMarkup(keyboard)
        )

        return TASK_SHOWN

    @staticmethod
    @save_state
    def type_answer(bot: Bot, update: Update, user_data: dict):
        update.message.reply_text(
            "Вводи свой ответ, я его проверю.",
            reply_markup=ReplyKeyboardMarkup(AnsweringKeyboard.get_keyboard())
        )
        return ANSWERING

    @staticmethod
    @save_state
    def accept_answer(bot: Bot, update: Update, user_data: dict):
        answer = update.message.text
        if answer == "хуй":
            update.message.reply_text(
                "Ты ввел правильный ответ! Возвращайся к другим задачам",
                reply_markup=ReplyKeyboardMarkup(ContinueKeyboard.get_keyboard())
            )

            return ANSWER_RIGHT
        else:
            update.message.reply_text(
                "К сожалению, твой ответ неверный =(",
                reply_markup=ReplyKeyboardMarkup(ContinueKeyboard.get_keyboard())
            )

            return ANSWER_WRONG
