import telebot
import datetime
from typing import List
from pars import Parser
from config import socks5, token

bot = telebot.TeleBot(token)
telebot.apihelper.proxy = {"https": socks5}

buttons = ["предыдущая", "текущая", "следующая"]
keyboard = telebot.types.ReplyKeyboardMarkup(True)
keyboard.row(buttons[0], buttons[1], buttons[2])

all_groups = Parser.get_groups()

users_groups = {}
groups_schedule = {}


@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, "Привет ! Введи свою группу и год начала обуения.\n"
                                      "(Например, для разработчика ППО на python(2019) достаточно ввести 'python 2019')")


@bot.message_handler(commands=['set'])
def change_group(message):
    set_user(message)
    start_message(message)


def set_user(message):
    global users_groups
    users_groups[message.chat.id] = {"group_value": None, "time": datetime.datetime.now().date(), "user_parser": Parser()}


@bot.message_handler(func=lambda message: message.text in buttons, content_types=["text"])
def get_schedule(message, flag=False):
    global users_groups
    if not flag:
        if message.text == buttons[0]:
            users_groups[message.chat.id]["time"] -= datetime.timedelta(days=7)
        elif message.text == buttons[2]:
            users_groups[message.chat.id]["time"] += datetime.timedelta(days=7)
        else:
            users_groups[message.chat.id]["time"] = datetime.datetime.now().date()
    try:

        group_value = users_groups[message.chat.id]["group_value"]

        if not groups_schedule[group_value]:
            pars_schedule(message.text, group_value, message)
            for k, v in groups_schedule[group_value].items():
                week = groups_schedule[group_value][k]
                dates = k
            bot.send_message(message.chat.id, view(week, dates))

        else:
            time = users_groups[message.chat.id]["time"]
            for i in groups_schedule[group_value]:
                if i[0] <= time <= i[1]:
                    bot.send_message(message.chat.id, view(groups_schedule[group_value][i], i))
                    return
            pars_schedule(message.text, group_value, message)
            get_schedule(message, flag=True)

    except KeyError:
        start_message(message)


@bot.message_handler(func=lambda message: any([k.isdigit() for k in message.text.split()]), content_types=["text"])
def set_group(message):
    set_user(message)
    user_mess = message.text
    group = Parser.check_user_input(user_mess, all_groups)
    if len(group) < 1:
        bot.send_message(message.chat.id, "Не удалось найти группу. Попробуйте ввести иначе.")
    elif len(group) > 1:
        find_groups = ""
        for i in group:
            find_groups += (i + "\n")
        bot.send_message(message.chat.id,
                         "Были найдены слудющие группы:\n" + find_groups + "\nВведите точнее вашу группу.")
    else:
        users_groups[message.chat.id]["group_value"] = all_groups[group[0]]
        groups_schedule[all_groups[group[0]]] = None
        bot.send_message(message.chat.id,
                         f"Выбрана группа: {group}.\nДля смены группы напишите '/set'.\n\nВыберите неделю",
                         reply_markup=keyboard)


@bot.message_handler(content_types=["text"])
def wrong_input(message):
    bot.send_message(message.chat.id, "Введите как на примере (или используйте предоставленные кнопки).",
                     reply_markup=keyboard)


def pars_schedule(user_mess, group_value, message):
    global groups_schedule

    week_data = users_groups[message.chat.id]["user_parser"].parsing(group_value, user_mess)
    schedule = []
    days = []

    for i in week_data:
        days.append(i.split()[1])
        schedule.append({i.split()[0]: week_data[i]})

    first_day = datetime.date(*[int(k) for k in reversed(days[0].split("."))])
    last_day = datetime.date(*[int(k) for k in reversed(days[6].split("."))])

    groups_schedule[group_value] = {(first_day, last_day): schedule}


def view(week: List, dates: tuple) -> str:
    head = f"Неделя {dates[0].day}.{dates[0].month if dates[0].month > 10 else '0' + str(dates[0].month)} - " \
           f"{dates[1].day}.{dates[1].month if dates[1].month > 10 else '0' + str(dates[1].month)}\n\n"
    s = ""
    for days in week:  # days - dict
        for day in days:  # day - dict_key
            if isinstance(days[day], dict):  # days[day] - value (dct or str)
                s += "\n" + day.upper() + "\n"
                for value in days[day]:
                    if value == "Группа":
                        s += "Группы:\n"
                        for groups in days[day][value]:
                            s += groups + "\n"
                    else:
                        s += f"{value}: {days[day][value]}\n"
    return head + s if s else "На этой неделе пар нет."


if __name__ == "__main__":
    bot.polling(none_stop=True)
