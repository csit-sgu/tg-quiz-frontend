from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove

from keyboards import (
    MenuKeyboard, TasksKeyboard, TaskChosenKeyboard, ContinueKeyboard,
    AnsweringKeyboard, AdminKeyboard, PublishTasksKeyboard, BackToMenuKeyboard
)
from utils import *
import backend_api
from time import sleep
import datetime as dt
from decimal import Decimal

# Typing
from telegram import Update, User, Bot
from typing import List

from botlogging import logger


def save_state(func):
    def wrapper(bot: Bot, update: Update, user_data: dict, *args, **kwargs):
        last_state = func(bot, update, user_data, *args, **kwargs)
        backend_api.save_state(last_state, update.message.from_user.id, user_data)
        return last_state

    return wrapper


def calc_score(t, base_score=1000):
    base_score = Decimal(base_score)
    min_score = Decimal(100)
    max_t = Decimal(720)
    k = (base_score - min_score) / (max_t * max_t)

    return round(min(k * (t - max_t) * (t - max_t) + min_score, base_score), 2)


class States:
    @staticmethod
    @save_state
    def prompt_question(bot: Bot, update: Update, user_data: dict):
        update.message.reply_text(
            "Введите свой вопрос, админы вам ответят, как только появится возможность, "
            "поэтому следите за сообщениями от бота.",
            reply_markup=ReplyKeyboardMarkup(BackToMenuKeyboard.get_keyboard())
        )

        return ASKING_QUESTION

    @staticmethod
    @save_state
    def ask_question(bot: Bot, update: Update, user_data: dict):
        question = update.message.text

        code, profiles = backend_api.get_profiles()
        if code != 200:
            pass

        user_id = update.message.from_user.id
        username = update.message.from_user.full_name

        for profile in profiles:
            if profile["is_admin"]:
                bot.send_message(
                    profile["tg_id"], f"*ВОПРОС ОТ ПОЛЬЗОВАТЕЛЯ {username} ({user_id})*:\n\n{question}",
                    parse_mode="Markdown"
                )

        update.message.reply_text(
            "Ваш вопрос был отправлен на рассмотрение, ожидайте ответ.",
            reply_markup=ReplyKeyboardMarkup(ContinueKeyboard.get_keyboard())
        )

        return ANSWER_RIGHT


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

        status_code, response = backend_api.get_attempts(
            tg_id=update.message.from_user.id,
            task_title=user_data["chosen_task"]
        )

        menu_text = [

        ]

        full_score = Decimal(0.0)
        if status_code == 200:
            if len(response) != 0:
                menu_text.append("Твои решенные задачи:")

                for attempt in response:
                    try:
                        ts = dt.datetime.strptime(attempt["timestamp"], "%Y-%m-%dT%H:%M:%S.%fZ")
                    except ValueError:
                        ts = dt.datetime.strptime(attempt["timestamp"], "%Y-%m-%dT%H:%M:%SZ")

                    try:
                        fp = dt.datetime.strptime(attempt["task"]["first_published"], "%Y-%m-%dT%H:%M:%S.%fZ")
                    except ValueError:
                        fp = dt.datetime.strptime(attempt["task"]["first_published"], "%Y-%m-%dT%H:%M:%SZ")

                    t = Decimal((ts - fp).total_seconds()) / Decimal(60)
                    plr_score = calc_score(t, attempt["task"]["base_score"])
                    full_score += plr_score

                    menu_text.append(
                        f"_{attempt['task']['title']}_ "
                        f"({plr_score})"
                    )
            else:
                menu_text.append("У тебя еще нет решенных задач")
        else:
            menu_text.append(
                "К сожалению, не удалось получить данные о твоих попытках =(\n"
                "Попробуй обратиться к боту чуть позже."
            )

        menu_text.append(f"\n*Итоговый счет*: {full_score}\n*Место в топе*: 0")

        update.message.reply_text("\n".join(menu_text), parse_mode="Markdown")

        update.message.reply_text(
            "Выбери следующее действие...",
            reply_markup=ReplyKeyboardMarkup(MenuKeyboard.get_keyboard(update.message.from_user.id))
        )

        return MAIN_MENU

    @staticmethod
    @save_state
    def choose_task(bot: Bot, update: Update, user_data: dict):
        user_data["chosen_task"] = None

        status, published = backend_api.get_published_tasks()
        if len(published) == 0:
            update.message.reply_text(
                "Пока что не опубликовано ни одной задачи =(",
                reply_markup=ReplyKeyboardMarkup(ContinueKeyboard.get_keyboard())
            )

            # okay this is epic (pile of shit)
            return ANSWER_RIGHT
        else:
            update.message.reply_text(
                "Какую задачу ты хочешь сдать?",
                reply_markup=ReplyKeyboardMarkup(TasksKeyboard.get_keyboard())
            )
            return TASK_CHOOSING

    @staticmethod
    @save_state
    def top_10(bot: Bot, update: Update, user_data: dict):
        code, attempts = backend_api.get_attempts()

        top = {}

        for attempt in attempts:
            if not attempt["solved"] or attempt["profile"]["is_hidden"]:
                continue

            if attempt["profile"]["tg_id"] not in top:
                top[attempt["profile"]["tg_id"]] = {
                    "fullname": attempt["profile"]["fullname"],
                    "username": attempt["profile"]["username"],
                    "score": Decimal(0.0)
                }

            try:
                ts = dt.datetime.strptime(attempt["timestamp"], "%Y-%m-%dT%H:%M:%S.%fZ")
            except ValueError:
                ts = dt.datetime.strptime(attempt["timestamp"], "%Y-%m-%dT%H:%M:%SZ")

            try:
                fp = dt.datetime.strptime(attempt["task"]["first_published"], "%Y-%m-%dT%H:%M:%S.%fZ")
            except ValueError:
                fp = dt.datetime.strptime(attempt["task"]["first_published"], "%Y-%m-%dT%H:%M:%SZ")

            t = Decimal((ts - fp).total_seconds()) / Decimal(60)
            plr_score = calc_score(t, attempt["task"]["base_score"])
            top[attempt["profile"]["tg_id"]]["score"] += plr_score

        try:
            top_list = []
            for tg_id, stats in top.items():
                top_list.append((
                    stats['score'],
                    f"{stats['fullname']} (@{stats['username']}) -- {stats['score']}pts"
                ))

            top_list.sort(key=lambda p: p[0], reverse=True)

            top = ["Топ-10:"]
            print(top_list)
            for place, (score, text) in enumerate(top_list, 1):
                top.append(str(place).rjust(2, " ") + ". " + text)
        except Exception as e:
            print(e)

        update.message.reply_text("\n".join(top))
        return MAIN_MENU

    @staticmethod
    @save_state
    def rules(bot: Bot, update: Update, user_data: dict):
        with open("rules.jpg", "rb") as f:
            try:
                print(update.message.reply_photo(f, timeout=5))
            except Exception as e:
                print(e)

        return MAIN_MENU

    @staticmethod
    @save_state
    def show_task(bot: Bot, update: Update, user_data: dict):
        if "chosen_task" in user_data and user_data["chosen_task"] is not None:
            task_title = user_data["chosen_task"]
        else:
            task_title = update.message.text
            user_data["chosen_task"] = task_title

        status_code, response = backend_api.get_attempts(
            tg_id=update.message.from_user.id,
            task_title=user_data["chosen_task"]
        )
        if status_code != 200:
            user_data["chosen_task"] = None

            update.message.reply_text(
                "Произошла ошибка в работе квиза. Мы уже работаем над её устранением!",
                reply_markup=ReplyKeyboardMarkup(TasksKeyboard.get_keyboard())
            )

            return TASK_CHOOSING

        if len(response) != 0:
            user_data["chosen_task"] = None

            update.message.reply_text(
                "Ты уже решил эту задачу! Выбери другую.",
                reply_markup=ReplyKeyboardMarkup(TasksKeyboard.get_keyboard())
            )

            return TASK_CHOOSING

        status_code, tasks_response = backend_api.get_published_tasks()
        if status_code != 200:
            update.message.reply_text(
                "Произошла ошибка в работе квиза. Мы уже работаем над её устранением!",
                reply_markup=ReplyKeyboardMarkup(ContinueKeyboard.get_keyboard())
            )

            return MAIN_MENU

        titles = {task.get("title"): task for task in tasks_response}

        if task_title not in titles.keys():
            update.message.reply_text(
                "Такой задачи не найдено, попробуй ввести другое название!",
                reply_markup=ReplyKeyboardMarkup(TasksKeyboard.get_keyboard())
            )

            return TASK_CHOOSING

        task = titles[task_title]

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

        update.message.reply_text(
            "Вводи свой ответ и я его проверю, "
            "или нажми кнопку Назад, чтобы выбрать другую задачу"
        )

        return TASK_SHOWN

    @staticmethod
    @save_state
    def type_answer(bot: Bot, update: Update, user_data: dict):
        status_code, response = backend_api.get_attempts(
            tg_id=update.message.from_user.id,
            task_title=user_data["chosen_task"]
        )
        if len(response) != 0:
            update.message.reply_text(
                "Ты уже решил эту задачу! Выбери другую.",
                reply_markup=ReplyKeyboardMarkup(ContinueKeyboard.get_keyboard())
            )

            return TASK_CHOOSING

        else:
            update.message.reply_text(
                "Вводи свой ответ, я его проверю.",
                reply_markup=ReplyKeyboardMarkup(AnsweringKeyboard.get_keyboard())
            )
            return ANSWERING

    @staticmethod
    @save_state
    def accept_answer(bot: Bot, update: Update, user_data: dict):
        answer = update.message.text
        status_code, task = backend_api.get_task(user_data["chosen_task"])
        if status_code == 200:
            backend_api.create_attempt(update.message.from_user.id, user_data["chosen_task"], answer)

            if answer == task["answer"]:
                update.message.reply_text(
                    "Ты ввел правильный ответ! Возвращайся к другим задачам",
                    reply_markup=ReplyKeyboardMarkup(ContinueKeyboard.get_keyboard())
                )

                return ANSWER_RIGHT
            else:
                update.message.reply_text(
                    "К сожалению, твой ответ неверный =( Попробуй ввести другой ответ.",
                    reply_markup=ReplyKeyboardMarkup(TaskChosenKeyboard.get_keyboard())
                )

                # return ANSWER_WRONG
                return TASK_SHOWN

        else:
            update.message.reply_text(
                "Произошла ошибка в работе квиза. Мы уже работаем над её устранением!",
                reply_markup=ReplyKeyboardMarkup(ContinueKeyboard.get_keyboard())
            )

            return ANSWER_RIGHT


class AdminStates:
    @staticmethod
    @save_state
    def admin_panel(bot: Bot, update: Update, user_data: dict):
        status_code, data = backend_api.get_profile(update.message.from_user.id)
        if status_code != 200:
            update.message.reply_text(
                "Не удалось аутентифицировать пользователя. Доступ запрещен.",
                reply_markup=ReplyKeyboardMarkup(ContinueKeyboard.get_keyboard())
            )

            return ADMIN_ACCESS_DENIED

        if not data["is_admin"]:
            update.message.reply_text(
                "Вы не являетесь администратором. Доступ запрещен.",
                reply_markup=ReplyKeyboardMarkup(ContinueKeyboard.get_keyboard())
            )

            return ADMIN_ACCESS_DENIED

        update.message.reply_text(
            "Выберите действие",
            reply_markup=ReplyKeyboardMarkup(AdminKeyboard.get_keyboard())
        )

        return ADMIN_MENU

    @staticmethod
    @save_state
    def choose_task_hide(bot: Bot, update: Update, user_data: dict):
        update.message.reply_text(
            "Выберите задачу, которую хотите скрыть",
            reply_markup=ReplyKeyboardMarkup(PublishTasksKeyboard.get_keyboard())
        )

        return ADMIN_TASK_CHOOSE_HIDE

    @staticmethod
    @save_state
    def choose_task_publish(bot: Bot, update: Update, user_data: dict):
        update.message.reply_text(
            "Выберите задачу, которую хотите опубликовать",
            reply_markup=ReplyKeyboardMarkup(PublishTasksKeyboard.get_keyboard())
        )

        return ADMIN_TASK_CHOOSE_PUBLISH

    @staticmethod
    @save_state
    def hide_task(bot: Bot, update: Update, user_data: dict):
        title = update.message.text
        status, data = backend_api.hide_task(title)
        if status != 200:
            update.message.reply_text(
                "Не удалось скрыть задачу.",
                reply_markup=ReplyKeyboardMarkup(ContinueKeyboard.get_keyboard())
            )
        else:
            update.message.reply_text(
                "Задача была скрыта.",
                reply_markup=ReplyKeyboardMarkup(ContinueKeyboard.get_keyboard())
            )

        return ADMIN_TASK_PUBLISHED

    @staticmethod
    @save_state
    def publish_task(bot: Bot, update: Update, user_data: dict):
        title = update.message.text
        status, data = backend_api.publish_task(title)
        if status != 200:
            update.message.reply_text(
                "Не удалось опубликовать задачу.",
                reply_markup=ReplyKeyboardMarkup(ContinueKeyboard.get_keyboard())
            )
        else:
            update.message.reply_text(
                "Задача была опубликована.",
                reply_markup=ReplyKeyboardMarkup(ContinueKeyboard.get_keyboard())
            )

        return ADMIN_TASK_PUBLISHED

    @staticmethod
    @save_state
    def wait_for_announcement(bot: Bot, update: Update, user_data: dict):
        update.message.reply_text(
            "Введите объявление (Отправка сообщений может занять несколько секунд)",
            reply_markup=ReplyKeyboardMarkup(BackToMenuKeyboard.get_keyboard())
        )

        return ADMIN_WAIT_FOR_ANNOUNCEMENT

    @staticmethod
    @save_state
    def wait_for_message(bot: Bot, update: Update, user_data: dict):
        update.message.reply_text(
            "Введите сообщение (Отправка сообщений может занять несколько секунд)",
            reply_markup=ReplyKeyboardMarkup(BackToMenuKeyboard.get_keyboard())
        )

        return ADMIN_WAIT_FOR_MESSAGE

    @staticmethod
    @save_state
    def announce_message(bot: Bot, update: Update, user_data: dict):
        status, profiles = backend_api.get_profiles()
        if status != 200:
            pass
        else:
            ids = []
            for profile in profiles:
                ids.append(int(profile["tg_id"]))

            return AdminStates.send_to_ids(ids, "ОБЪЯВЛЕНИЕ ОТ МОДЕРАТОРОВ:", update.message.text, bot, update)

    @staticmethod
    @save_state
    def message_plr(bot: Bot, update: Update, user_data: dict):
        text = update.message.text
        _ = text.split(maxsplit=1)

        if len(_) != 2:
            update.message.reply_text(
                "Ошибка в сообщении, попробуйте еще раз",
                reply_markup=ReplyKeyboardMarkup(ContinueKeyboard.get_keyboard())
            )
            return ADMIN_TASK_PUBLISHED

        ids_text, msg = _
        ids_split = filter(lambda s: len(s) > 0 and s.isnumeric(), ids_text.split(','))
        ids = list(map(int, ids_split))

        if len(ids) == 0:
            update.message.reply_text(
                "Все id пользователей неверно введены",
                reply_markup=ReplyKeyboardMarkup(ContinueKeyboard.get_keyboard())
            )

            return ADMIN_TASK_PUBLISHED

        else:
            return AdminStates.send_to_ids(ids, "СООБЩЕНИЕ ОТ МОДЕРАТОРОВ:", msg, bot, update)

    @staticmethod
    def send_to_ids(ids: List[int], prefix: str, message: str, bot: Bot, update: Update):
        errors = []
        for tg_id in ids:
            try:
                bot.send_message(tg_id, f"*{prefix}*\n\n{message}", parse_mode="Markdown")
                print(tg_id)
            except Exception as e:
                logger.debug(f"Got exception while announcing message: {e}")
                errors.append((tg_id, str(e)))
                sleep(0.3)

            sleep(0.05)

        if len(errors) == 0:
            update.message.reply_text(
                "Сообщение успешно отправлено всем пользователям",
                reply_markup=ReplyKeyboardMarkup(ContinueKeyboard.get_keyboard()),
            )

            # OKAY
            return ADMIN_TASK_PUBLISHED

        else:
            error_msg = []
            user_ids = []

            for err in errors:
                user_ids.append(str(err[0]))
                error_msg.append(f"{err[0]}. Reason: {err[1]}")

            msg = "\n".join(error_msg)
            user_ids = ",".join(user_ids)

            update.message.reply_text(
                "Во время отправки сообщений возникли следующие ошибки:\n"
                f"{msg}\n\n{user_ids}",
                reply_markup=ReplyKeyboardMarkup(ContinueKeyboard.get_keyboard())
            )

            # OKAY
            return ADMIN_TASK_PUBLISHED
