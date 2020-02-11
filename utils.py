def get_input(update, user_data):
    if "resuming" in user_data and user_data["resuming"] == True:
        return user_data["text"]
    else:
        return update.message.text


(
    WAIT_FOR_USERNAME,
    MAIN_MENU, TOP_10, RULES,
    TASK_CHOOSING, TASK_SHOWN, ANSWERING,
    ANSWER_RIGHT, ANSWER_WRONG,
    *_
) = range(100)