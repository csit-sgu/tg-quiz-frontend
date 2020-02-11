import requests
from config import BACKEND_URL
import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def register_user(tg_id, username, fullname) -> bool:
    logger.debug(f"Registering user with id={tg_id}; username={username}")
    response = requests.post(f"{BACKEND_URL}/profiles/", data={
        "tg_id": tg_id,
        "username": username,
        "fullname": fullname
    })
    logger.debug(
        f"Got response from backend: "
        f"Status={response.status_code}; "
        f"Text={response.text}"
    )

    return response.status_code == 201


def get_tasks():
    response = requests.get(f"{BACKEND_URL}/tasks/")
    return response.json()
