import asyncio
import datetime
import json
import logging
import re
import os
import math

import get_mc
from src import Account
from src import Bank
from src import Ref

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.enums import ParseMode
from dotenv import load_dotenv

load_dotenv()


logging.basicConfig(level=logging.INFO)

# Параметры бота и глобальные переменные (интеграция telebot-логики)
ADMIN_ID = 813373727  # Замените на ID создателя бота
DEV_ID = 1461832447
GROUP_ID = -1002480162505 #For logs
IP_PORT = '5.9.97.124:20706' #address

bot = Bot(token=os.getenv('TOKEN'))  # текущий токен для aiogram
dp = Dispatcher()

users_data = {}          # Хранение времени начала работы (user_id -> datetime)
banned_users = set()     # Заблокированные пользователи
PAY_RATE = 5             # AR в час
MAX_HOURS = 12           # Максимум рабочего времени
all_users = set()        # Пользователи, которые нажали /работать

# Флаги для ожидания ввода сообщений от админа
waiting_for_message = False
target_user_id = None
waiting_for_user_id_check = False

# Флаги для ожидания ввода от пользователей
waiting_for_admin_message = {}  # user_id -> bool
waiting_for_video = {}          # user_id -> bool

# Путь к файлу для хранения забаненных пользователей
BANNED_USERS_FILE = "banned_users.json"
WORK_FILE = "data/work.json"

# Функции для загрузки/сохранения забаненных пользователей
def load_banned_users():
    global banned_users
    if os.path.exists(BANNED_USERS_FILE):
        with open(BANNED_USERS_FILE, 'r') as f:
            try:
                banned_users = set(json.load(f))
            except json.JSONDecodeError:
                logging.error("Ошибка при чтении списка забаненных пользователей, создаем новый список.")
                banned_users = set()

def save_banned_users():
    with open(BANNED_USERS_FILE, 'w') as f:
        json.dump(list(banned_users), f)

def load_work_data():
    global users_data
    if os.path.exists(WORK_FILE):
        try:
            with open(WORK_FILE, "r") as f:
                data = json.load(f)
            # Преобразуем сохранённые строки в объекты datetime
            users_data = {int(uid): datetime.datetime.fromisoformat(dt_str) for uid, dt_str in data.items()}
        except Exception as e:
            logging.error("Ошибка при чтении work.json, создаем новый словарь. Ошибка: %s", e)
            users_data = {}
    else:
        users_data = {}

def save_work_data():
    with open(WORK_FILE, "w") as f:
        # Преобразуем объекты datetime в строки ISO
        data_to_save = {str(uid): dt.isoformat() for uid, dt in users_data.items()}
        json.dump(data_to_save, f)

# Загружаем рабочие данные из файла work.json
load_work_data()
load_banned_users()


# Новая клавиатура для рабочего процесса
work_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Статус"), KeyboardButton(text="Завершить работу")],
        [KeyboardButton(text="Поддержка"), KeyboardButton(text='назад')]
    ],
    resize_keyboard=True
)

# Клавиатура для обычного пользователя (Main User Keyboard)
common_user_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="помощь"), KeyboardButton(text="финансы")],
        [KeyboardButton(text="поддержка")]
    ],
    resize_keyboard=True
)

adm_user_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="помощь"), KeyboardButton(text="финансы")],
        [KeyboardButton(text="поддержка"), KeyboardButton(text='назад')]
    ],
    resize_keyboard=True
)

# Клавиатура для раздела "финансы"
finances_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="создать карту"), KeyboardButton(text="профиль")],
        [KeyboardButton(text="перевод"), KeyboardButton(text="поддержка")],
        [KeyboardButton(text="назад")]
    ],
    resize_keyboard=True
)

# Клавиатура для админа (Admin Keyboard)
admin_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="юзер"), KeyboardButton(text="работа")],
        [KeyboardButton(text="админ")]
    ],
    resize_keyboard=True
)

# Клавиатура для раздела "работа" у админа
admin_work_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="начать работать"), KeyboardButton(text="статистика")],
        [KeyboardButton(text="завершить работу"), KeyboardButton(text="статус")],
        [KeyboardButton(text="назад")]
    ],
    resize_keyboard=True
)

# Клавиатура для раздела "админ" с действиями
admin_actions_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="отправить")],
        [KeyboardButton(text="проверить айди"), KeyboardButton(text="состояние")],
        [KeyboardButton(text="назад")]
    ],
    resize_keyboard=True
)

# Новая клавиатура для банкира – раздел "работа"
banker_work_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="начать работать"), KeyboardButton(text="статус"), KeyboardButton(text="пополнить")],
        [KeyboardButton(text="завершить работу"), KeyboardButton(text="отчет"), KeyboardButton(text='назад')]
    ],
    resize_keyboard=True
)

# Новая клавиатура для банкира – раздел "финансы"
banker_finances_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="создать карту"), KeyboardButton(text="профиль")],
        [KeyboardButton(text="назад")]
    ],
    resize_keyboard=True
)

# Добавляем новую клавиатуру для банкира (начальное меню)
banker_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="работа"), KeyboardButton(text="финансы")],
        [KeyboardButton(text="поддержка"), KeyboardButton(text="помощь")]
    ],
    resize_keyboard=True
)

############ Bot commands



@dp.message(Command('start'))
async def cmd_start(message: types.Message):
    await message.answer(f'Добро пожаловавть, {message.from_user.username}!\nДля продолжения пользования ботом, введите на сервере команду /telegram link , затем в этом чате /auth [полученный_код]')

@dp.message(Command('auth'))
async def cmd_auth(message: types.Message):
    all_users.add(message.from_user.id)
    mess = message.text.split(' ')
    if len(mess) < 2:
        await message.answer('Введите код аутентификации!')
    else:
        auth_code = mess[1]
        response = get_mc.auth(auth_code, IP_PORT) #auth response
        if response:
            if Account.check_prof(message.from_user.id, message.from_user.username, response.uuid, response.name) and \
               Account.add_username(message.from_user.id, message.from_user.username, response.uuid, response.name) and \
                Ref.gen_code(str(message.from_user.id)):
                Account.create_acc(response.name, response.uuid, message.from_user.id, message.from_user.username)
                role = Account.get_prof(message.from_user.id)['role']
                if role == "admin":
                    kb = admin_keyboard
                elif role == "bank":
                    kb = banker_keyboard
                else:
                    kb = common_user_kb
                await message.answer(
                    f'Вы успешно запустили бота MC Store!\nДобро пожаловать, *{message.from_user.username}*!',
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=kb
                )
                await bot.send_message(GROUP_ID, f'Зарегестрирован: {message.from_user.username}\nНик: {response.name}', message_thread_id = 153)
            else:
                await message.answer("Произошла ошибка при регистрации!")
        else:
            await message.answer("Произошла ошибка при регистрации!")

@dp.message(F.text.lower() == 'старт')
async def cmd_start_text(message: types.Message):
    all_users.add(message.from_user.id)
    role = Account.get_prof(message.from_user.id)['role']
    if role == "admin":
        kb = admin_keyboard
    elif role == "bank":
        kb = banker_keyboard
    else:
        kb = common_user_kb
    await message.answer(
        f'Вы успешно запустили бота MC Store!\nДобро пожаловать, *{message.from_user.first_name}*!',
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=kb
    )

# --- Команды связанные с картами и профилем (сохранены из предыдущей версии) ---







@dp.message(F.text.lower() == 'создать карту')
async def btn_create_card(message: types.Message):
    acc = Account.get_acc(message.from_user.id)
    pool = Account.get_prof(message.from_user.id)
    if acc:
        card_id = Account.create_card(message.from_user.id)
        if card_id:
            await message.answer(f'Карта успешно создана\n*ID карты:* {card_id}\nСтоимость: {pool["count_cards"] * 5}', parse_mode=ParseMode.MARKDOWN)
            await bot.send_message(
                "-1002480162505",
                f'ID карты: {card_id}\nПользователь: {message.from_user.first_name}\nID пользователя: {message.from_user.id}',
                message_thread_id=6
            )
        else:
            await message.answer(f'У вас недостаточно средств, чтобы создать еще одну карту')
    else:
        await message.answer(f'Ошибка получения данных аккаунта')

@dp.message(F.text.lower() == 'профиль')
async def btn_prof(message: types.Message):
    prof = Account.get_prof(message.from_user.id)
    if not prof:
        await message.answer("Ошибка получения профиля")
        return
    profile_text = (
        f'*Профиль пользователя* {message.from_user.first_name}\n\n'
        f'Баланс: {int(prof["balance"]) // 64} ст. {int(prof["balance"]) % 64}\n'
        f'Количество карт: {prof["count_cards"]}\n'
        f'Количество совершеных транзакций: {prof["count_transactions"]}\n'
        f'Роль: {prof["role"]}\n'
        f'Ник: {prof["name"]}'
    )
    if prof["cards"]:
        kb = [
            [InlineKeyboardButton(text=f'Карта {card}', callback_data=f'{card}')]
            for card in prof["cards"]
        ]
        kb = InlineKeyboardMarkup(inline_keyboard=kb)
        await message.answer(profile_text, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)
    else:
        await message.answer(profile_text, parse_mode=ParseMode.MARKDOWN)

@dp.message(F.text.lower() == 'помощь')
async def btn_help(message: types.Message):
    await message.answer(
        'Список команд:\n'
        '/проф - просмотр профиля\n'
        '/создать_карту - создание карты\n'
        '/кард_инфо - информация о карте\n'
        '/помощь - помощь\n'
        '/банк_инфо - информация транзакций\n'
        '/get_code - получить ваш реферальный код\n'
        '/activate [code] - активировать реферальный код'
        )

@dp.message(Command("проф", 'prof'))
async def cmd_prof(message: types.Message):
    mention = re.search(r'@(\w+)', message.text)
    if mention and (Account.get_prof(message.from_user.id)["role"] in ["admin", "bank"]):
        user_id = Account.get_id_by_usn(mention.group(1))
        name = mention.group(1)
    else:
        user_id = message.from_user.id
        name = message.from_user.first_name
    prof = Account.get_prof(user_id)
    if prof["cards"]:
        kb = [
            [InlineKeyboardButton(text=f'Карта {card}', callback_data=f'{card}')]
            for card in prof["cards"]
        ]
        kb = InlineKeyboardMarkup(inline_keyboard=kb)
        await message.answer(
            f'*Профиль пользователя* {name}\n\n'
            f'Баланс: {int(prof["balance"]) // 64} ст. {int(prof["balance"]) % 64} \n'
            f'Количество карт: {prof["count_cards"]}\n'
            f'Количество совершеных транзакций: {prof["count_transactions"]}\n'
            f'Роль: {prof["role"]}\n'
            f'Часов на сервере: {int(int(get_mc.getstat(Account.get_prof(user_id)["uuid"], IP_PORT)) // 20 / 60 / 60)}\n'
            f'Пригласил: {prof["invites"]} чел.',
            parse_mode=ParseMode.MARKDOWN, reply_markup=kb
        )
    else:
        await message.answer(
            f'*Профиль пользователя* {name}\n\n'
            f'Баланс: {int(prof["balance"]) % 64} ст.\n'
            f'Количество карт: {prof["count_cards"]}\n'
            f'Количество совершеных транзакций: {prof["count_transactions"]}\n'
            f'Роль: {prof["role"]}\n'
            f'Часов на сервере: {int(int(get_mc.getstat(Account.get_prof(user_id)["uuid"], IP_PORT)) // 20 / 60 / 60)}\n'
            f'Пригласил: {prof["invites"]} чел.',
            parse_mode=ParseMode.MARKDOWN
        )

@dp.callback_query()
async def cb_card(call: types.CallbackQuery):
    if (call.data.startswith('0')):
        card_id = call.data
        pool = Bank.bank_info(card_id)
        user = Account.get_usn_by_id(pool["user"])
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Назад', callback_data='back')]])
        await call.message.edit_text(
            f'*Информация о карте* {card_id}\n\n'
            f'Баланс: {int(pool["balance"]) // 64} ст. {int(pool["balance"]) % 64}\n'
            f'Последние транзакции: {pool["last_transactions"]}\n'
            f'Количество транзакций: {pool["count_transactions"]}\n'
            f'Пользователь: {user}\n',
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=kb
        )
    elif call.data.startswith('back'):
        # Вернуться к профилю
        prof = Account.get_prof(call.from_user.id)
        if prof["cards"]:
            kb = [
                [InlineKeyboardButton(text=f'Карта {card}', callback_data=f'{card}')]
                for card in prof["cards"]
            ]
            kb = InlineKeyboardMarkup(inline_keyboard=kb)
            await call.message.edit_text(
                f'*Профиль пользователя* {call.from_user.first_name}\n\n'
                f'Баланс: {int(prof["balance"]) // 64} ст. {int(prof["balance"]) % 64}\n'
                f'Количество карт: {prof["count_cards"]}\n'
                f'Количество совершеных транзакций: {prof["count_transactions"]}\n'
                f'Роль: {prof["role"]}\n'
                f'Часов на сервере: {int(int(get_mc.getstat(Account.get_prof(call.from_user.id)["uuid"], IP_PORT)) // 20 / 60 / 60)}\n'
                f'Пригласил: {prof["invites"]} чел.',
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=kb
            )
        else:
            await call.message.edit_text(
                f'*Профиль пользователя* {call.from_user.first_name}\n\n'
                f'Баланс: {int(prof["balance"]) % 64} ст. {int(prof["balance"]) % 64}\n'
                f'Количество карт: {prof["count_cards"]}\n'
                f'Количество совершеных транзакций: {prof["count_transactions"]}\n'
                f'Роль: {prof["role"]}\n'
                f'Часов на сервере: {int(int(get_mc.getstat(Account.get_prof(call.from_user.id)["uuid"], IP_PORT)) // 20 / 60 / 60)}\n'
                f'Пригласил: {prof["invites"]} чел.',
                parse_mode=ParseMode.MARKDOWN
            )


@dp.message(Command('server', 'сервер', 'казна', 'budg'))
async def cmd_server(message: types.Message):
    if Account.get_prof(message.from_user.id)['role'] in ['admin', 'bank', 'stuff']:
        pool = Account.get_prof('server')
        await message.answer(
            f'Баланс сервера: {int(pool["balance"]) // 64} ст. {int(pool["balance"]) % 64}'
        )
    else:
        message.answer('Недостаточно прав доступа')

@dp.message(Command('tup_serv', 'тупс'))
async def cmd_tupc(message: types.Message):

    ars = message.text.split(' ')
    if len(ars) != 2: await message.answer('/tup_server [amount]')
    if int(ars[-1]): amount = int(ars[-1])
    else: await message.answer('/tup_server [amount]')
    if Account.get_prof(message.from_user.id)['role'] in ['admin', 'bank']:
        if Bank.tups(amount):
            await message.answer('Баланс сервера пополнен')
        else: await message.answer('Возникла ошибка')
    else:
        message.answer('Недостаточно прав доступа')

@dp.message(Command('access', 'доступ'))
async def cmd_access(message: types.Message):

    ars = message.text.split(' ')
    if len(ars) != 2: await message.answer('/access [username]')
    if ars[-1]: username = ars[-1]

    if Account.get_prof(message.from_user.id)['role'] == 'admin':
        if Account.dostup(username):
            await message.answer(f'{username} получил доступ')
        else:
            await message.answer('Возникла ошибка')

@dp.message(Command('unaccess', 'недоступ'))
async def cmd_access(message: types.Message):

    ars = message.text.split(' ')
    if len(ars) != 2: await message.answer('/unaccess [username]')
    if ars[-1]: username = ars[-1]

    if Account.get_prof(message.from_user.id)['role'] == 'admin':
        if Account.nedostup(username):
            await message.answer(f'{username} утратил доступ')
        else:
            await message.answer('Возникла ошибка')


@dp.message(Command('пкд', 'get_code'))
async def cmd_get_code(message: types.Message):
    if Ref.gen_code(str(message.from_user.id)):
        await message.answer(f'Ваш реферальный код {Ref.get_code(str(message.from_user.id))}')
    else:
        await message.answer(f'Возникла ошибка.')

@dp.message(Command('реф', 'activate'))
async def cmd_activate(message: types.Message):
    ars = message.text.split(' ')
    if len(ars) != 2:
        await message.answer(
            'Команда /реф, /activate'
            '\t/activate [ref_code]'
            'Нельзя вводить собственный код, также вы должны сыграть на сервере 5+ часов!'
            )
    else:
        ch1 = int(get_mc.getstat(Account.get_prof(message.from_user.id)['uuid'], IP_PORT)) // 20 / 60 / 60 >= 5
        ch2 = int(get_mc.getstat(Account.get_prof(message.from_user.id)['uuid'], IP_PORT)) // 20 / 60 / 60 <= 1000
        if not ch1: await message.answer(f'Вы играли всего {int(get_mc.getstat(Account.get_prof(message.from_user.id)["uuid"], IP_PORT)) // 20 / 60 / 60} ч. Минимальное количество для получения вознаграждения - 5!')
        elif not ch2: await message.answer(f'Вы играли слишком много и теперь не можете получить вознаграждение как новичок(')
        else: 
            print(ars[1])
            ch3 = Ref.activate_code(str(message.from_user.id), ars[1])
            if ch3:
                await message.answer(f'Реферальный код активирован! Вы получили 20 АР!')
                print(ars[1])
                await bot.send_message(Ref.get_referal(ars[1]), f'Ваш код активировал @{message.from_user.username}. Вы получили 10 АР!')
                await bot.send_message(GROUP_ID, f'Активация реферального кода\nПриглашенный: {Account.get_prof(message.from_user.id)["name"]}\nПригласивший: {Account.get_prof(Ref.get_referal(ars[1]))["name"]}', message_thread_id = 153)


            else:
                await message.answer('Возникла ошибка активации код. Возможные причины:\n'
                                     '-Вы активируете свой код\n'
                                     '-Проблемы сети и вам стоит попробовать позже\n'
                                     '-Вы уже активировали реферальный код\n'
                                     '-Возникла проблема при проверке валидности кода')


@dp.message(Command("создать_карту", "make_card"))
async def cmd_create_card(message: types.Message):
    acc = Account.get_acc(message.from_user.id)
    pool = Account.get_prof(message.from_user.id)
    if acc:
        card_id = Account.create_card(str(message.from_user.id))
        if card_id:
            await message.answer(f'Карта успешно создана\n*ID карты:* {card_id}\nСтоимость: {pool["count_cards"] * 5}', parse_mode=ParseMode.MARKDOWN)
            await bot.send_message(
                "-1002480162505",
                f'ID карты: {card_id}\nПользователь: {message.from_user.first_name}\nID пользователя: {message.from_user.id}',
                message_thread_id=6
            )
        else:
            await message.answer(f'У вас недостаточно средств, чтобы создать еще одну карту')
    else:
        await message.answer(f'Ошибка получения данных аккаунта')

@dp.message(Command('удалить', 'delete'))
async def cmd_delete(message: types.Message):
    ars = message.text.split()
    if len(ars) != 2: await message.answer('Формат команды:\n/delete [card_id]\nНельзя удалить карты с отрицательным балансом, главную карту, а также карты, непринадлежащие вам!')
    else:
        ch = Account.del_card(str(message.from_user.id), str(ars[-1]))
        if ch:
            if ch == -1:
                await message.answer('Вы не можете удалить свою главную карту!!')
                return
            if ch == -2:
                await message.answer('Вы не можете удалить чужую карту!!')
                return
            if ch == -3:
                await message.answer('Вы не можете удалить карту с отрицательным балансом')
                return

            await message.answer(f'Карта {ars[-1]} успешно удалена!')

        else:
            await message.answer('Произошла ошибка удаления, обратитесь в поддержку!')

@dp.message(Command("кард_инфо", 'card_info'))
async def cmd_card_info(message: types.Message):
    if Account.get_prof(message.from_user.id)['role'] in ['admin', 'bank']:
        c_search = re.search(r'0(\w+)', message.text)
        if c_search:
            card_id = c_search.group(0)
            pool = Bank.bank_info(card_id)
            user = Account.get_usn_by_id(pool["user"])
            await message.answer(
                f'*Информация о карте* {card_id}\n\n'
                f'Баланс: {pool["balance"]}\n'
                f'Последние транзакции: {pool["last_transactions"]}\n'
                f'Количество транзакций: {pool["count_transactions"]}\n'
                f'Пользователь: {user}\n',
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await message.answer('Введите ID карты!')
    else:
        await message.answer('У вас нет доступа к этой команде')

@dp.message(Command("банк_инфо", 'bank_info'))
async def cmd_bank_info(message: types.Message):
    ars = message.text.split(' ')
    if len(ars) == 2 and ars[-1].isdigit():
        pool = Bank.trans_info(ars[-1])
        if pool and Account.get_prof(message.from_user.id)['role'] in ['bank', 'admin']:
            await message.reply(
                f"*От кого:* {pool['from']}\t{pool['from_card']}\n"
                f"*Кому:*    {pool['to']}\t{pool['to_card']}\n"
                f"*Сумма:*   {pool['amount']} АР\n"
                f"*Сообщение:* {pool['message']}"
            )
        elif pool and Account.get_prof(message.from_user.id)['name'] in [pool['from'], pool['to']]:
            await message.reply(
                f"*От кого:* {pool['from']}\t{pool['from_card']}\n"
                f"*Кому:*    {pool['to']}\t{pool['to_card']}\n"
                f"*Сумма:*   {pool['amount']} АР\n"
                f"*Сообщение:* {pool['message']}"
            )
        else:
            await message.answer('Недостаточно прав доступа')
    else:
        await message.answer('Введите номер транзакции!')


def get_card(value):
    if value.startswith('.') and Account.get_acc_by_name(value[1::]):
        card_id = Account.get_prof(Account.get_acc_by_name(value[1::])['user_id'])['main_card']
    elif value.startswith('@') and Account.get_id_by_usn(value[1::]):
        card_id = Account.get_prof(Account.get_id_by_usn(value[1::]))['main_card']
        print(card_id)
    elif value.startswith(',') and len(value[1::]) == 4:
        card_id = value[1::]
    else: return False
    return card_id

pending_penalty = {}

@dp.message(Command('штраф', 'penalty'))
async def cmd_penalty(message: types.Message):
    # Доступно только админам и банкирам
    if Account.get_prof(message.from_user.id)['role'] not in ['admin', 'bank']:
        await message.answer("Недостаточно прав доступа для наложения штрафа.")
        return
    user_id = message.from_user.id
    pending_penalty[user_id] = {"step": "input_target"}
    await message.answer("Введите gamename пользователя для наложения штрафа:")

@dp.message(lambda m: m.from_user.id in pending_penalty and pending_penalty[m.from_user.id]["step"] == "input_target")
async def penalty_input_target(message: types.Message):
    user_id = message.from_user.id
    pending_penalty[user_id]["target"] = message.text.strip()
    pending_penalty[user_id]["step"] = "comment_decision"
    # Клавиатура для выбора да/нет для комментария
    decision_buttons = [[KeyboardButton(text="Да")], [KeyboardButton(text="Нет")]]
    kb = ReplyKeyboardMarkup(keyboard=decision_buttons, resize_keyboard=True, one_time_keyboard=True)
    await message.answer("Хотите добавить комментарий к штрафу? (Введите 'Да' или 'Нет')", reply_markup=kb)

@dp.message(lambda m: m.from_user.id in pending_penalty and pending_penalty[m.from_user.id]["step"] == "comment_decision")
async def penalty_comment_decision(message: types.Message):
    user_id = message.from_user.id
    decision = message.text.strip().lower()
    if decision == "да":
        pending_penalty[user_id]["step"] = "input_comment"
        await message.answer("Введите комментарий к штрафу:", reply_markup=types.ReplyKeyboardRemove())
    elif decision == "нет":
        pending_penalty[user_id]["comment"] = ""
        pending_penalty[user_id]["step"] = "input_amount"
        await message.answer("Введите сумму штрафа:", reply_markup=types.ReplyKeyboardRemove())
    else:
        await message.answer("Пожалуйста, введите 'Да' или 'Нет'.")

@dp.message(lambda m: m.from_user.id in pending_penalty and pending_penalty[m.from_user.id]["step"] == "input_comment")
async def penalty_input_comment(message: types.Message):
    user_id = message.from_user.id
    pending_penalty[user_id]["comment"] = message.text.strip()
    pending_penalty[user_id]["step"] = "input_amount"
    await message.answer("Введите сумму штрафа:")

@dp.message(lambda m: m.from_user.id in pending_penalty and pending_penalty[m.from_user.id]["step"] == "input_amount")
async def penalty_input_amount(message: types.Message):
    user_id = message.from_user.id
    try:
        amount = int(message.text.strip())
        if amount <= 0:
            await message.answer("Сумма штрафа должна быть больше 0. Введите корректную сумму:")
            return
    except ValueError:
        await message.answer("Введите число для суммы штрафа:")
        return
    pending_penalty[user_id]["amount"] = amount
    data = pending_penalty.pop(user_id)
    target_input = data.get("target")
    comment = data.get("comment", "")
    # Определяем карту штрафуемого пользователя по gamename
    target_card = get_card(target_input)
    if not target_card:
        await message.answer("Неверные данные получателя. Операция отменена.")
        return
    # Для штрафа сумма передается со знаком минус (снимаем деньги)
    penalty_amount = amount
    tr = Bank.top_up(target_card, 'казна', comment, penalty_amount, 'Штраф')
    if tr:
        await message.answer(f"Штраф наложен успешно. Транзакция №{tr}")
        # Отправляем уведомление штрафуемому пользователю (если данные доступны)
        if target_input.startswith('.'):
            penalized = Account.get_acc_by_name(target_input[1:])
            if penalized:
                await bot.send_message(penalized['user_id'], f"Вам был наложен штраф на {amount} АР.\nКомментарий: {comment}")
        await bot.send_message(GROUP_ID, f'ШТРАФ\nИсполнитель: {Account.get_prof(message.from_user.id)["name"]}\nПолучатель: {target_input[1:]}\nСумма: {amount}\nКомментарий: {comment}', message_thread_id=8)
    else:
        await message.answer("Произошла ошибка при наложении штрафа.")

@dp.message(Command('начать_работу', 'begin'))
async def start_work(message: types.Message):
    user_id = message.from_user.id
    if Account.get_prof(user_id)['role'] in ['bank', 'admin']:
        if user_id in banned_users:
            await message.reply("Вы заблокированы и не можете начать работу.")
            return
        if user_id in users_data:
            await message.reply("Вы уже начали работу. Завершите её перед новым стартом.")
        else:
            users_data[user_id] = datetime.datetime.now()
            save_work_data()  # Сохраняем обновлённые рабочие данные
            await message.reply("Вы начали работу! Таймер запущен.", reply_markup=work_keyboard)
            await  bot.send_message(GROUP_ID, f"Пользователь {message.from_user.full_name} (@{message.from_user.username}) начал работу.", message_thread_id = 11)

    else:
        await message.answer('У вас нет доступа для выполнения данного действия')
        
@dp.message(F.text.lower() == 'начать работать')
async def start_workk(message: types.Message):
    user_id = message.from_user.id
    if Account.get_prof(user_id)['role'] in ['bank', 'admin']:
        if user_id in banned_users:
            await message.reply("Вы заблокированы и не можете начать работу.")
            return
        if user_id in users_data:
            await message.reply("Вы уже начали работу. Завершите её перед новым стартом.")
        else:
            users_data[user_id] = datetime.datetime.now()
            save_work_data()  # Сохраняем обновлённые рабочие данные
            await message.reply("Вы начали работу! Таймер запущен.", reply_markup=work_keyboard)

            await  bot.send_message(GROUP_ID, f"Пользователь {message.from_user.full_name} (@{message.from_user.username}) начал работу.", message_thread_id = 11)
    else:
        await message.answer('У вас нет доступа для выполнения данного действия')


@dp.message(Command("завершить_работу", "finish"))
async def stop_work(message: types.Message):
    user_id = message.from_user.id
    now = datetime.datetime.now()
    if user_id not in users_data:
        await message.reply("Вы ещё не начали работу. Используйте 'Начать работу'.")
        return
    start_time = users_data.pop(user_id)
    save_work_data()  # обновляем work.json
    worked_hours = (now - start_time).total_seconds() / 3600
    if worked_hours > MAX_HOURS:
        worked_hours = MAX_HOURS
        await message.reply("Время работы ограничено 12 часами. Остаток времени не засчитывается.")
    earnings = math.ceil(worked_hours * PAY_RATE)
    await message.reply(f"Вы отработали {worked_hours:.2f} часов.")
    if Bank.top_up('казна', Account.get_prof(message.from_user.id)['main_card'], '', earnings, 'Зарплата'):
        await message.answer(f'Вам выплачено: {earnings} АР')
        await bot.send_message(GROUP_ID, f"Пользователь {message.from_user.full_name} (@{message.from_user.username}) закончил работу.\nЗаработано: {earnings} AR.", message_thread_id = 11)
    else:
        await message.answer('Возникла ошибка')

    # Клавиатура как при команде /start
    await message.answer("Рабочая сессия завершена.")

@dp.message(F.text.lower() == 'завершить работу')
async def stop_work(message: types.Message):
    user_id = message.from_user.id
    now = datetime.datetime.now()
    if user_id not in users_data:
        await message.reply("Вы ещё не начали работу. Используйте 'Начать работу'.")
        return
    start_time = users_data.pop(user_id)
    save_work_data()  # обновляем work.json
    worked_hours = (now - start_time).total_seconds() / 3600
    if worked_hours > MAX_HOURS:
        worked_hours = MAX_HOURS
        await message.reply("Время работы ограничено 12 часами. Остаток времени не засчитывается.")
    earnings = math.ceil(worked_hours * PAY_RATE)
    await message.reply(f"Вы отработали {worked_hours:.2f} часов.")
    if Bank.top_up('казна', Account.get_prof(message.from_user.id)['main_card'], '', earnings, 'Зарплата'):
        await message.answer(f'Вам выплачено: {earnings} АР')
        await bot.send_message(GROUP_ID, f"Пользователь {message.from_user.full_name} (@{message.from_user.username}) закончил работу.\nЗаработано: {earnings} AR.", message_thread_id = 11)
    else:
        await message.answer('Возникла ошибка')
    role = Account.get_prof(message.from_user.id)['role']

    await message.answer("Рабочая сессия завершена.")

@dp.message(Command('status'))
async def work_status(message: types.Message):
    user_id = message.from_user.id
    if user_id in users_data:
        start_time = users_data[user_id]
        elapsed = (datetime.datetime.now() - start_time).total_seconds() / 3600
        elapsed = min(elapsed, MAX_HOURS)
        await message.reply(f"Вы работаете уже {elapsed:.2f} часов.")
    else:
        await message.reply("Вы не начали работу. Используйте 'Начать работу'.")

@dp.message(F.text.lower() == 'статус')
async def work_statuss(message: types.Message):
    user_id = message.from_user.id
    if user_id in users_data:
        start_time = users_data[user_id]
        elapsed = (datetime.datetime.now() - start_time).total_seconds() / 3600
        elapsed = min(elapsed, MAX_HOURS)
        await message.reply(f"Вы работаете уже {elapsed:.2f} часов.")
    else:
        await message.reply("Вы не начали работу. Используйте 'Начать работу'.")

@dp.message(Command('report'))
async def request_report(message: types.Message):
    user_id = message.from_user.id
    if user_id in banned_users:
        await message.reply("Вы заблокированы и не можете отправлять отчет.")
        return
    waiting_for_video[user_id] = True
    await message.reply("Пожалуйста, отправьте видео для отчета. Видео без нажатия на кнопку не принимаются!")

@dp.message(F.text.lower() == "отчет")
async def request_report(message: types.Message):
    user_id = message.from_user.id
    if user_id in banned_users:
        await message.reply("Вы заблокированы и не можете отправлять отчет.")
        return
    waiting_for_video[user_id] = True
    await message.reply("Пожалуйста, отправьте видео для отчета. Видео без нажатия на кнопку не принимаются!")

@dp.message(lambda message: message.content_type == "video")
async def handle_video(message: types.Message):
    user_id = message.from_user.id
    if user_id not in waiting_for_video or not waiting_for_video[user_id]:
        await message.reply("Вы не нажали кнопку 'Отчет'. Пожалуйста, нажмите 'Отчет' перед отправкой видео.")
        return
    if user_id in banned_users:
        await message.reply("Вы заблокированы и не можете отправить отчет.")
        return
    waiting_for_video[user_id] = False
    await message.reply("Ваше видео принято и передано админу. Ожидайте ответа!")
    await bot.send_message(GROUP_ID, f"Видео от @{message.from_user.username} ({user_id}):", message_thread_id=20)
    await bot.forward_message(GROUP_ID, message.chat.id, message.message_id, message_thread_id=20)

@dp.message(lambda message: message.content_type in [
    "photo", "audio", "document", "sticker", "voice",
    "location", "contact", "animation", "video_note", "poll", "dice"
])
async def handle_invalid_content(message: types.Message):
    await message.reply("Я принимаю только видео. Пожалуйста, отправьте видео, иначе ваш отчет не будет принят.")

@dp.message(Command('call'))
async def contact_admin(message: types.Message):
    user_id = message.from_user.id
    if user_id in banned_users:
        await message.reply("Вы заблокированы и не можете связаться с админом.")
        return
    waiting_for_admin_message[user_id] = True
    await message.reply("Введите ваше сообщение для администратора:")

@dp.message(F.text.lower() == 'поддержка')
async def contact_admin(message: types.Message):
    user_id = message.from_user.id
    if user_id in banned_users:
        await message.reply("Вы заблокированы и не можете связаться с админом.")
        return
    waiting_for_admin_message[user_id] = True
    await message.reply("Введите ваше сообщение для администратора:")

@dp.message(lambda message: message.from_user.id in waiting_for_admin_message and waiting_for_admin_message[message.from_user.id])
async def process_admin_message(message: types.Message):
    user_id = message.from_user.id
    # Если это ответ на запрос "Связь с админом"
    await bot.send_message(ADMIN_ID,
                           f"📩 Сообщение от пользователя @{message.from_user.username} ({user_id}):\n\n{message.text}")
    await bot.send_message(DEV_ID,
                           f"📩 Сообщение от пользователя @{message.from_user.username} ({user_id}):\n\n{message.text}")
    await message.reply("Ваше сообщение отправлено администратору!")
    waiting_for_admin_message[user_id] = False

@dp.message(Command('stat') )
async def admin_stats(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    if not users_data:
        await bot.send_message(ADMIN_ID, "Сейчас никто не работает.")
        return
    working_users_count = len(users_data)
    stats_message = f"Сейчас работают {working_users_count} человек(а):\n"
    for uid, start_time in users_data.items():
        try:
            user = await bot.get_chat(uid)
            username = user.username if user.username else user.full_name
        except Exception:
            username = "Неизвестен"
        elapsed = (datetime.datetime.now() - start_time).total_seconds() / 3600
        elapsed = min(elapsed, MAX_HOURS)
        stats_message += f"Пользователь: @{username} ({uid}) — {elapsed:.2f} часов\n"
    await bot.send_message(ADMIN_ID, stats_message)

@dp.message(F.text.lower() == "статистика")
async def admin_stats(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    if not users_data:
        await bot.send_message(ADMIN_ID, "Сейчас никто не работает.")
        return
    working_users_count = len(users_data)
    stats_message = f"Сейчас работают {working_users_count} человек(а):\n"
    for uid, start_time in users_data.items():
        try:
            user = await bot.get_chat(uid)
            username = user.username if user.username else user.full_name
        except Exception:
            username = "Неизвестен"
        elapsed = (datetime.datetime.now() - start_time).total_seconds() / 3600
        elapsed = min(elapsed, MAX_HOURS)
        stats_message += f"Пользователь: @{username} ({uid}) — {elapsed:.2f} часов\n"
    await bot.send_message(ADMIN_ID, stats_message)

@dp.message(Command("ban"))
async def ban_user(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.reply("Только администратор может блокировать пользователей.")
        return
    args = message.text.split()
    if len(args) < 2:
        await message.reply("Укажите ID пользователя для блокировки. Пример: /ban 123456789")
        return
    try:
        uid = int(args[1])
        banned_users.add(uid)
        save_banned_users()
        await message.reply(f"Пользователь с ID {uid} заблокирован и не может начать работу.")
        await bot.send_message(ADMIN_ID, f"Пользователь с ID {uid} заблокирован.")
    except ValueError:
        await message.reply("Неверный формат ID пользователя.")

@dp.message(Command("unban"))
async def unban_user(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.reply("Только администратор может разбанивать пользователей.")
        return
    args = message.text.split()
    if len(args) < 2:
        await message.reply("Укажите ID пользователя для разблокировки. Пример: /unban 123456789")
        return
    try:
        uid = int(args[1])
        if uid in banned_users:
            banned_users.remove(uid)
            save_banned_users()
            await message.reply(f"Пользователь с ID {uid} разбанен и теперь может работать.")
            await bot.send_message(ADMIN_ID, f"Пользователь с ID {uid} разбанен.")
        else:
            await message.reply("Этот пользователь не заблокирован.")
    except ValueError:
        await message.reply("Неверный формат ID пользователя.")

@dp.message(Command("check_id"))
async def request_check_id(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    global waiting_for_user_id_check
    waiting_for_user_id_check = True
    await message.reply("Введите ID пользователя для проверки:")

@dp.message(F.text.lower() == 'проверить айди')
async def request_check_id(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    global waiting_for_user_id_check
    waiting_for_user_id_check = True
    await message.reply("Введите ID пользователя для проверки:")

@dp.message(lambda message: waiting_for_user_id_check and message.text.isdigit() and message.from_user.id == ADMIN_ID)
async def check_user_id(message: types.Message):
    global waiting_for_user_id_check
    uid = int(message.text)
    try:
        user = await bot.get_chat(uid)
        username = user.username if user.username else user.full_name
        await message.reply(f"Пользователь с ID {uid} - {username}")
    except Exception:
        await message.reply("Не удалось найти информацию о пользователе с этим ID.")
    waiting_for_user_id_check = False

@dp.message(Command("send"))
async def request_user_message(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    global waiting_for_message, target_user_id
    waiting_for_message = True
    target_user_id = None
    await message.reply("Введите ID пользователя, которому хотите отправить сообщение.")

@dp.message(F.text.lower() == 'отправить')
async def request_user_message(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    global waiting_for_message, target_user_id
    waiting_for_message = True
    target_user_id = None
    await message.reply("Введите ID пользователя, которому хотите отправить сообщение.")

@dp.message(lambda message: waiting_for_message and target_user_id is None and message.from_user.id == ADMIN_ID)
async def receive_user_id(message: types.Message):
    global target_user_id
    try:
        target_user_id = int(message.text)
        await message.reply("Введите текст сообщения для отправки.")
    except ValueError:
        await message.reply("Ошибка! Введите корректный ID пользователя.")

@dp.message(lambda message: waiting_for_message and target_user_id is not None and message.from_user.id == ADMIN_ID)
async def send_user_message(message: types.Message):
    global waiting_for_message, target_user_id
    user_message = message.text
    try:
        await bot.send_message(target_user_id, f"✉️ Сообщение от администратора:\n\n{user_message}")
        await message.reply(f"Сообщение отправлено пользователю {target_user_id}.")
    except Exception:
        await message.reply("Ошибка! Не удалось отправить сообщение пользователю.")
    waiting_for_message = False


# Новый глобальный словарь для сессий перевода командой /перевод
pending_transfer = {}

@dp.message(Command('перевод'))
async def cmd_transfer(message: types.Message):
    user_id = message.from_user.id
    prof = Account.get_prof(user_id)
    if not prof or not prof.get("cards"):
        await message.answer("У вас нет карт для перевода.")
        return
    # Отправляем пользователю клавиатуру с кнопками — вариант: "Карта <card>"
    buttons = [[KeyboardButton(text=f"Карта {card}")] for card in prof["cards"]]
    kb = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True, one_time_keyboard=True)
    pending_transfer[user_id] = {"step": "choose_card"}
    await message.answer("Выберите карту для списания средств:", reply_markup=kb)

@dp.message(F.text.lower() == 'перевод')
async def cmd_transfer(message: types.Message):
    user_id = message.from_user.id
    prof = Account.get_prof(user_id)
    if not prof or not prof.get("cards"):
        await message.answer("У вас нет карт для перевода.")
        return
    # Отправляем пользователю клавиатуру с кнопками — вариант: "Карта <card>"
    buttons = [[KeyboardButton(text=f"Карта {card}")] for card in prof["cards"]]
    kb = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True, one_time_keyboard=True)
    pending_transfer[user_id] = {"step": "choose_card"}
    await message.answer("Выберите карту для списания средств:", reply_markup=kb)

def get_card2(value):
    if len(str(value)) == 4:
        card_id = value
    else:
        return False
    return card_id

@dp.message(F.text.lower() == 'пополнить')
async def cmd_transfer(message: types.Message):
    user_id = message.from_user.id
    prof = Account.get_prof(user_id)
    if not prof or not prof.get("cards"):
        await message.answer("У вас нет карт для перевода.")
        return
    # Отправляем пользователю клавиатуру с кнопками — вариант: "Карта <card>"
    if prof['role'] in ['admin', 'bank']: buttons = [[KeyboardButton(text=f"Карта z")], [KeyboardButton(text=f"Наличка")]]
    else: await message.answer('У вас недостаточно прав доступа')
    kb = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True, one_time_keyboard=True)
    pending_transfer[user_id] = {"step": "choose_card"}
    await message.answer("Выберите карту для списания средств:", reply_markup=kb)

@dp.message(lambda m: m.from_user.id in pending_transfer and pending_transfer[m.from_user.id]["step"] == "choose_card")
async def transfer_choose_card(message: types.Message):
    user_id = message.from_user.id
    text = message.text.strip()
    if not text.startswith("Карта ") and not text.startswith("Наличка"):
        await message.answer("Пожалуйста, выберите карту, нажав одну из кнопок.")
        return
    if text.startswith('Карта'): card_value = text[len("Карта "):].strip()
    if text.startswith('Наличка'): card_value = text
    if card_value == 'z':
        card_id = 'казна'
    if card_value == 'Наличка':
        card_id = 'Наличка'
    else:
        card_id = get_card2(card_value)
    if not card_id:
        await message.answer("Неверный формат карты. Повторите ввод.")
        return
    pending_transfer[user_id]["from_card"] = card_id
    pending_transfer[user_id]["step"] = "choose_method"
    # Клавиатура для выбора метода перевода
    method_buttons = [
        [KeyboardButton(text="game")],
        [KeyboardButton(text="username")],
        [KeyboardButton(text="card")]
    ]
    kb = ReplyKeyboardMarkup(keyboard=method_buttons, resize_keyboard=True, one_time_keyboard=True)
    await message.answer("Выберите метод перевода:\nВведите 'game' для геймнейма, 'username' для юзернейма, или 'card' для номера карты.", reply_markup=kb)

@dp.message(lambda m: m.from_user.id in pending_transfer and pending_transfer[m.from_user.id]["step"] == "choose_method")
async def transfer_choose_method(message: types.Message):
    user_id = message.from_user.id
    method = message.text.strip().lower()
    if method not in ['game', 'username', 'card']:
        await message.answer("Неверный метод. Введите: game, username или card.")
        return
    
    if method == 'game':
        with open('data/gameacc.json', 'r', encoding = 'utf-8') as file:
            data = json.load(file)
        
    if method == 'username':
        with open('data/usernames.json', 'r', encoding = 'utf-8') as file:
            data = json.load(file)

    if method == 'card':
        with open('data/cards.json', 'r', encoding = 'utf-8') as file:
            data = json.load(file)

    kb = []
    qw = [i for i in data.keys()]

    for i in range(2, len(data.keys())):
        kb.append([KeyboardButton(text=f'{qw[i]}')])

    kb = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, one_time_keyboard=True)

    pending_transfer[user_id]["method"] = "method_" + method
    pending_transfer[user_id]["step"] = "input_target"
    await message.answer("Введите данные получателя (в зависимости от выбранного метода):", reply_markup = kb)

@dp.message(lambda m: m.from_user.id in pending_transfer and pending_transfer[m.from_user.id]["step"] == "input_target")
async def transfer_input_target(message: types.Message):
    user_id = message.from_user.id
    pending_transfer[user_id]["target"] = message.text.strip()
    pending_transfer[user_id]["step"] = "comment_decision"
    # Клавиатура для выбора, добавлять комментарий или нет
    decision_buttons = [[KeyboardButton(text="Да")], [KeyboardButton(text="Нет")]]
    kb = ReplyKeyboardMarkup(keyboard=decision_buttons, resize_keyboard=True, one_time_keyboard=True)
    await message.answer("Хотите добавить комментарий к переводу? (Введите 'Да' или 'Нет')", reply_markup=kb)

@dp.message(lambda m: m.from_user.id in pending_transfer and pending_transfer[m.from_user.id]["step"] == "comment_decision")
async def transfer_comment_decision(message: types.Message):
    user_id = message.from_user.id
    decision = message.text.strip().lower()
    if decision == "да":
        pending_transfer[user_id]["step"] = "input_comment"
        await message.answer("Введите комментарий к переводу:", reply_markup=types.ReplyKeyboardRemove())
    elif decision == "нет":
        pending_transfer[user_id]["comment"] = ""
        pending_transfer[user_id]["step"] = "input_amount"
        await message.answer("Введите сумму перевода:", reply_markup=types.ReplyKeyboardRemove())
    else:
        await message.answer("Пожалуйста, введите 'Да' или 'Нет'.")

@dp.message(lambda m: m.from_user.id in pending_transfer and pending_transfer[m.from_user.id]["step"] == "input_comment")
async def transfer_input_comment(message: types.Message):
    user_id = message.from_user.id
    pending_transfer[user_id]["comment"] = message.text.strip()
    pending_transfer[user_id]["step"] = "input_amount"
    await message.answer("Введите сумму перевода:")

@dp.message(lambda m: m.from_user.id in pending_transfer and pending_transfer[m.from_user.id]["step"] == "input_amount")
async def transfer_input_amount(message: types.Message):
    user_id = message.from_user.id
    role = Account.get_prof(message.from_user.id)['role']

    if role == "admin":
        kb = admin_keyboard
    elif role == "bank":
        kb = banker_keyboard
    else:
        kb = common_user_kb
    try:
        amount = int(message.text.strip())
        if amount <= 0:
            await message.answer("Сумма должна быть больше 0. Введите корректную сумму:")
            return
    except ValueError:
        await message.answer("Введите число для суммы:")
        return
    pending_transfer[user_id]["amount"] = amount
    data = pending_transfer.pop(user_id)
    from_card = data.get("from_card")
    method = data.get("method")
    target_input = data.get("target")
    comment = data.get("comment", "")
    target_card = None

    # Определяем полученную карту в зависимости от метода
    if method == "method_username":
        uid = Account.get_id_by_usn(target_input)
        if not uid:
            await message.answer("Неверный username получателя. Операция отменена.", reply_markup=kb)
            return
        prof_target = Account.get_prof(uid)
        if not prof_target:
            await message.answer("Не удалось получить данные получателя. Операция отменена.", reply_markup=kb)
            return
        target_card = prof_target.get("main_card")
    elif method == "method_game":
        target_card = Account.get_prof(Account.get_acc_by_name(target_input)['user_id'])['main_card']
        uid = Account.get_acc_by_name(target_input)['user_id']
    elif method == "method_card":
        target_card = get_card2(target_input)
        uid = Bank.bank_info(target_card)['user']
    if not target_card:
        await message.answer("Неверные данные получателя. Операция отменена.", reply_markup=kb)
        return
    prof = Account.get_prof(user_id)
    # Проверяем, что ни одна из карт пользователя не имеет отрицательный баланс
    if from_card != 'казна' and target_card not in prof.get("cards", []):
       
        for card in prof.get("cards", []):
            card_info = Bank.bank_info(card)
            if card_info and int(card_info['balance']) < 0:
                await message.answer("На одной из ваших карт обнаружен отрицательный баланс. Перевод не разрешён.", reply_markup=kb)
                return
    

    # Дополнительно проверяем баланс выбранной исходной карты
    source_info = Bank.bank_info(from_card)
    if not source_info:
        await message.answer("Не удалось получить данные по исходной карте.", reply_markup=kb)
        return
    if int(source_info['balance']) < amount:
        await message.answer("Недостаточно средств на исходной карте для перевода.", reply_markup=kb)
        return

    tr = Bank.top_up(from_card, target_card, comment, amount, 'Перевод')
    if tr:
        await message.answer(f"Перевод осуществлен успешно. Транзакция №{tr}", reply_markup=kb)
        await bot.send_message(uid, 
            f'Вам поступил перевод от @{message.from_user.username} в размере {amount} АР\n' +
            (f"Комментарий отправителя: {comment}" if comment else "") +
            f'\nИсточник поступления: {"банк" if from_card == "казна" else from_card}')
        await bot.send_message(
            "-1002480162505",
            f'Транзакция №{tr}'
            f'\nОтправитель: {Account.get_prof(user_id)["name"]}\t {from_card}'
            f'\nПолучатель: {Account.get_prof(uid)["name"]}\t {target_card}'
            f'\nСумма: {amount}'
            f'\nСообщение: {comment}',
            message_thread_id=4
        )
    else:
        await message.answer("Произошла ошибка при переводе.", reply_markup=kb)

@dp.message(lambda m: m.text.lower() == 'финансы')
async def finances_handler(message: types.Message):
    prof = Account.get_prof(message.from_user.id)
    # Если пользователь - банкир, показываем клавиатуру банкира, иначе стандартную для обычного пользователя
    if prof and prof.get("role") == "bank":
        await message.answer("Меню финансов (банкир)", reply_markup=banker_finances_kb)
    else:
        await message.answer("Меню финансов", reply_markup=finances_kb)

@dp.message(lambda m: m.text.lower() == 'назад')
async def back_handler(message: types.Message):
    prof = Account.get_prof(message.from_user.id)
    if prof:
        role = prof.get("role")
        if role == "admin":
            kb = admin_keyboard
        elif role == "bank":
            kb = banker_keyboard
        else:
            kb = common_user_kb
    else:
        kb = common_user_kb
    await message.answer("Главное меню", reply_markup=kb)

@dp.message(lambda m: m.text.lower() == 'юзер')
async def user_handler(message: types.Message):
    await message.answer("Пользовательское меню", reply_markup=adm_user_kb)

@dp.message(lambda m: m.text.lower() == 'работа')
async def work_handler(message: types.Message):
    prof = Account.get_prof(message.from_user.id)
    if prof and prof.get("role") in ["admin", "bank"]:
        # Если банкир, показываем клавиатуру банкира, иначе админскую клавиатуру работы
        if prof.get("role") == "bank":
            await message.answer("Рабочее меню (банкир)", reply_markup=banker_work_kb)
        else:
            await message.answer("Рабочее меню", reply_markup=admin_work_kb)
    else:
        await message.answer("Недостаточно прав доступа.")

@dp.message(lambda m: m.text.lower() == 'админ')
async def admin_handler(message: types.Message):
    prof = Account.get_prof(message.from_user.id)
    if prof and prof.get("role") in ["admin", "bank"]:
        await message.answer("Админ действия", reply_markup=admin_actions_kb)
    else:
        await message.answer("Недостаточно прав доступа.")

@dp.message(lambda m: m.text.lower() == 'состояние')
async def status_handler(message: types.Message):
    active_users_count = len(users_data)
    # Здесь можно добавить реальную логику для получения состояния сервера и соединения.
    server_status = "Online"
    connection_status = "Stable"
    status_text = (
        f"Состояние бота:\n"
        f"Активных пользователей: {active_users_count}\n"
        f"Сервер: {server_status}\n"
        f"Соединение: {connection_status}"
    )
    prof = Account.get_prof(message.from_user.id)
    if prof:
        role = prof.get("role")
        if role == "admin":
            kb = admin_actions_kb
        elif role == "bank":
            kb = banker_keyboard
        else:
            kb = common_user_kb
    else:
        kb = common_user_kb
    await message.answer(status_text, reply_markup=kb)

# Новый глобальный словарь для сессий команды снятия средств
pending_withdraw = {}

@dp.message(Command('снять'))
async def cmd_withdraw(message: types.Message):
    # Команда доступна только для администраторов и банкиров
    if Account.get_prof(message.from_user.id)['role'] not in ['admin', 'bank']:
        await message.answer("Недостаточно прав доступа для снятия средств.")
        return
    user_id = message.from_user.id
    pending_withdraw[user_id] = {"step": "input_target"}
    await message.answer("Введите gamename пользователя, с которого нужно снять средства:")

@dp.message(lambda m: m.from_user.id in pending_withdraw and pending_withdraw[m.from_user.id]["step"] == "input_target")
async def withdraw_input_target(message: types.Message):
    user_id = message.from_user.id
    target_gamename = message.text.strip()
    uid = Account.get_acc_by_name(target_gamename)
    if not uid:
        await message.answer("Неверный gamename. Операция отменена.")
        pending_withdraw.pop(user_id, None)
        return
    pending_withdraw[user_id]["user_id"] = uid
    pending_withdraw[user_id]["step"] = "choose_card"
    # Получаем данные пользователя и его карты
    prof_target = Account.get_prof(uid['user_id'])
    if not prof_target or not prof_target.get("cards"):
        await message.answer("У пользователя нет карт или не удалось получить данные.")
        pending_withdraw.pop(user_id, None)
        return
    # Формируем клавиатуру для выбора карты
    buttons = [[KeyboardButton(text=f"Карта {card}")] for card in prof_target["cards"]]
    kb = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True, one_time_keyboard=True)
    await message.answer("Выберите карту пользователя для снятия средств:", reply_markup=kb)

@dp.message(lambda m: m.from_user.id in pending_withdraw and pending_withdraw[m.from_user.id]["step"] == "choose_card")
async def withdraw_choose_card(message: types.Message):
    user_id = message.from_user.id
    text = message.text.strip()
    if not text.startswith("Карта "):
        await message.answer("Пожалуйста, нажмите на кнопку с нужной картой.")
        return
    card_value = text[len("Карта "):].strip()
    pending_withdraw[user_id]["card"] = card_value
    pending_withdraw[user_id]["step"] = "input_amount"
    await message.answer("Введите сумму для снятия средств:", reply_markup=types.ReplyKeyboardRemove())

@dp.message(lambda m: m.from_user.id in pending_withdraw and pending_withdraw[m.from_user.id]["step"] == "input_amount")
async def withdraw_input_amount(message: types.Message):
    user_id = message.from_user.id
    try:
        amount = int(message.text.strip())
        if amount <= 0:
            await message.answer("Сумма должна быть больше 0. Введите корректную сумму:")
            return
    except ValueError:
        await message.answer("Введите число для суммы:")
        return
    data = pending_withdraw.pop(user_id)
    target_card = data.get("card")
    comment = data.get("comment", "")
    # Вызов новой функции для снятия средств: деньги просто вычитаются с карты,
    # без перевода на другую (например, 'казну')
    tr = Bank.withdraw(target_card, comment, amount)
    if tr:
        await message.answer(f"Снятие средств выполнено успешно. Транзакция №{tr}")
        uid = data.get("user_id")
        await bot.send_message(uid['user_id'], f"С вашей карты {target_card} было снято {amount} АР командой /снять.")
        await bot.send_message(
            "-1002480162505",
            f'Транзакция №{tr}'
            f'\nВладелец/карта: {uid["name"]}\t {target_card}'
            f'\nСумма: {amount}'
            f'\nСообщение: {comment}',
            message_thread_id=4
        )
    else:
        await message.answer("Произошла ошибка при снятии средств.")

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
