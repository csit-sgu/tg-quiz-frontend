import requests
import urllib
from config import BACKEND_URL
import logging
import json
import datetime as dt

from typing import Tuple, Dict


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def make_request(method: str, url: str, **kwargs) -> Tuple[int, Dict]:
    try:
        response = requests.request(method, url, **kwargs)
        answer = response.json()

    except Exception as e:
        logger.debug(f"Got exception while making request: {e}")
        return 500, {}

    logger.debug(
        f"Got response from backend: "
        f"Status={response.status_code}; "
        f"Text={response.text[:200]}..."
    )

    return response.status_code, answer


def post_request(url: str, **kwargs):
    return make_request("post", url, **kwargs)


def put_request(url: str, **kwargs):
    return make_request("put", url, **kwargs)


def get_request(url: str, **kwargs):
    return make_request("get", url, **kwargs)


def patch_request(url: str, **kwargs):
    return make_request("patch", url, **kwargs)


def register_user(tg_id: int, username: str, fullname: str) -> Tuple[int, Dict]:
    logger.debug(f"Trying to register user with id={tg_id}; username={username}")
    return post_request(f"{BACKEND_URL}/profiles/", data={
        "tg_id": tg_id,
        "username": username,
        "fullname": fullname
    })


def get_profiles():
    logger.debug(f"Trying to retrieve all profiles")
    return get_request(f"{BACKEND_URL}/profiles/")


def get_tasks():
    logger.debug(f"Trying to retrieve all tasks")
    return get_request(f"{BACKEND_URL}/tasks/")


def get_published_tasks():
    logger.debug(f"Trying to retrieve all published tasks")
    return get_request(f"{BACKEND_URL}/api/tasks/published/")


def get_task(title: str) -> Tuple[int, Dict]:
    logger.debug(f"Trying to retrieve task with title={title}")
    return get_request(f"{BACKEND_URL}/api/get_task/" + urllib.parse.quote(title))


def save_state(last_state: int, tg_id: int, user_data: dict) -> Tuple[int, Dict]:
    user_data_dumped = json.dumps(user_data)
    logger.debug(f"Trying to save state for user with id={tg_id}; state={last_state}; user_data={user_data_dumped}")

    return put_request(f"{BACKEND_URL}/api/state/update/{tg_id}/", data={
        "last_state": last_state,
        "tg_id": tg_id,
        "user_data": user_data_dumped
    })


def get_state(tg_id: int) -> Tuple[int, dict]:
    logger.debug(f"Trying to get state for user with id={tg_id}")
    return get_request(f"{BACKEND_URL}/api/state/get/{tg_id}/")


def create_attempt(tg_id: int, task_title: str, answer: str):
    return post_request(f"{BACKEND_URL}/attempts/", data={
        "profile": json.dumps({"tg_id": tg_id}),
        "task": json.dumps({"title": task_title}),
        "answer": answer
    })


def get_attempts(tg_id: int=None, task_title: str=None):
    data = {}
    if tg_id is not None:
        data["tg_id"] = tg_id
    if task_title is not None:
        data["task_title"] = task_title

    return get_request(f"{BACKEND_URL}/api/attempts/", data=data)


def get_profile(tg_id: int):
    return get_request(f"{BACKEND_URL}/api/profile/get/{tg_id}")


def publish_task(title: str):
    url_title = urllib.parse.quote(title)
    code, resp = get_task(title)

    if code != 200:
        return code, {}

    if resp["first_published"] is None:
        return patch_request(f"{BACKEND_URL}/api/tasks/{url_title}/update/", data={
            "first_published": dt.datetime.now(),
            "is_public": True
        })
    else:
        return patch_request(f"{BACKEND_URL}/api/tasks/{url_title}/update/", data={
            "is_public": True
        })


def hide_task(title: str):
    url_title = urllib.parse.quote(title)
    return patch_request(f"{BACKEND_URL}/api/tasks/{url_title}/update/", data={
        "is_public": False
    })
