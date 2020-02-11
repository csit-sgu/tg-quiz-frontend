import requests
import urllib
from config import BACKEND_URL
import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def register_user(tg_id, username, fullname) -> bool:
    logger.debug(f"Registering user with id={tg_id}; username={username}")
    try:
        response = requests.post(f"{BACKEND_URL}/profiles/", data={
            "tg_id": tg_id,
            "username": username,
            "fullname": fullname
        })
    except Exception as e:
        logger.debug(f"Got exception while making request: {e}")
        return False

    logger.debug(
        f"Got response from backend: "
        f"Status={response.status_code}; "
        f"Text={response.text[:200]}..."
    )

    return response.status_code == 201


def get_tasks():
    response = requests.get(f"{BACKEND_URL}/tasks/")
    return response.json()


def get_task(title: str):
    logger.debug(f"Trying to retrieve task with title={title}")
    try:
        response = requests.get(
            "http://127.0.0.1:8000/api/get_task/"
            + urllib.parse.quote(title)
        )
        task = response.json()

    except Exception as e:
        logger.debug(f"Got exception while making request: {e}")
        return 500, {}

    logger.debug(
        f"Got response from backend: "
        f"Status={response.status_code}; "
        f"Text={response.text[:200]}..."
    )

    return response.status_code, task
