import backend_api
from abc import ABC


class Keyboard(ABC):
    @classmethod
    def get_keyboard(cls, telegram_id=None):
        pass


class MenuKeyboard(Keyboard):
    CHOOSE_TASK = "Выбрать задание📚"
    TOP_10 = "Топ-10📊"
    RULES = "Правилаℹ️"
    ADMIN = "/admin"

    @classmethod
    def get_keyboard(cls, telegram_id=None):
        if telegram_id is not None:
            status_code, data = backend_api.get_profile(telegram_id)
            if status_code == 200 and data["is_admin"]:
                return [
                    [cls.ADMIN],
                    [cls.CHOOSE_TASK],
                    [cls.TOP_10, cls.RULES],
                ]

        return [
            [cls.CHOOSE_TASK],
            [cls.TOP_10, cls.RULES],
        ]


class BackToMenuKeyboard(Keyboard):
    CANCEL = "Вернуться в меню↩️"

    @classmethod
    def get_keyboard(cls, telegram_id=None):
        return [[cls.CANCEL]]


class TasksKeyboard(Keyboard):
    CANCEL = "Вернуться в меню↩️"

    @classmethod
    def get_keyboard(cls, telegram_id=None):
        status, tasks = backend_api.get_published_tasks()
        titles_keyboard = [[cls.CANCEL]]
        if status == 200:
            titles_keyboard.extend([task.get("title")] for task in tasks)

        return titles_keyboard


class PublishTasksKeyboard(Keyboard):
    CANCEL = "Вернуться в меню↩️"

    @classmethod
    def get_keyboard(cls, telegram_id=None):
        status, tasks = backend_api.get_tasks()
        titles_keyboard = [[cls.CANCEL]]
        if status == 200:
            titles_keyboard.extend([task.get("title")] for task in tasks)

        return titles_keyboard


class TaskChosenKeyboard(Keyboard):
    TYPE_ANSWER = "Ввести ответ✏️"
    CANCEL = "Назад↩️"

    @classmethod
    def get_keyboard(cls, telegram_id=None):
        return [
            # [cls.TYPE_ANSWER],
            [cls.CANCEL],
        ]


class ContinueKeyboard(Keyboard):
    CONTINUE = "Продолжить➡️"

    @classmethod
    def get_keyboard(cls, telegram_id=None):
        return [[cls.CONTINUE]]


class AnsweringKeyboard(Keyboard):
    CANCEL = "Отмена↩️"

    @classmethod
    def get_keyboard(cls, telegram_id=None):
        return [[cls.CANCEL]]


class AdminKeyboard(Keyboard):
    CANCEL = "Вернуться в меню↩️"
    PUBLISH_TASK = "Опубликовать задачу"
    HIDE_TASK = "Скрыть задачу"
    ANNOUNCE = "Сделать объявление"
    MESSAGE_PLAYER = "Написать сообщение от имени бота"

    @classmethod
    def get_keyboard(cls, telegram_id=None):
        return [
            [cls.CANCEL],
            [cls.PUBLISH_TASK],
            [cls.HIDE_TASK],
            [cls.ANNOUNCE],
            [cls.MESSAGE_PLAYER],
        ]
