import backend_api
from abc import ABC


class Keyboard(ABC):
    @classmethod
    def get_keyboard(cls, telegram_id=None):
        pass


class MenuKeyboard(Keyboard):
    CHOOSE_TASK = "Выбрать задание"
    TOP_10 = "Топ-10"
    RULES = "Правила"
    ADMIN = "/admin"

    @classmethod
    def get_keyboard(cls, telegram_id=None):
        return [
            [cls.CHOOSE_TASK],
            [cls.TOP_10, cls.RULES],
        ]


class BackToMenuKeyboard(Keyboard):
    CANCEL = "Вернуться в меню"

    @classmethod
    def get_keyboard(cls, telegram_id=None):
        return [[cls.CANCEL]]


class TasksKeyboard(Keyboard):
    CANCEL = "Вернуться в меню"

    @classmethod
    def get_keyboard(cls, telegram_id=None):
        tasks = backend_api.get_tasks()
        titles_keyboard = [[cls.CANCEL]]
        titles_keyboard.extend([task.get("title")] for task in tasks)
        return titles_keyboard


class TaskChosenKeyboard(Keyboard):
    TYPE_ANSWER = "Ввести ответ"
    CANCEL = "Назад"

    @classmethod
    def get_keyboard(cls, telegram_id=None):
        return [
            [cls.TYPE_ANSWER],
            [cls.CANCEL],
        ]


class ContinueKeyboard(Keyboard):
    CONTINUE = "Продолжить"

    @classmethod
    def get_keyboard(cls, telegram_id=None):
        return [[cls.CONTINUE]]


class AnsweringKeyboard(Keyboard):
    CANCEL = "Отмена"

    @classmethod
    def get_keyboard(cls, telegram_id=None):
        return [[cls.CANCEL]]
