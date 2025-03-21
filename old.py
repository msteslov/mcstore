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


logging.basicConfig(level=logging.INFO)

# Параметры бота и глобальные переменные (интеграция telebot-логики)
ADMIN_ID = 813373727  # Замените на ID создателя бота
GROUP_ID = -1002480162505 #For logs
IP_PORT = '65.108.206.102:25648' #address

bot = Bot(token='7368137489:AAFt7-k5vRWSTnTR8V6c8cBej93RzEdpZgA')  # текущий токен для aiogram
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

# Клавиатуры
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Начать работать"), KeyboardButton(text="Завершить работу")],
        [KeyboardButton(text="Статус"), KeyboardButton(text="Отчет")],
        [KeyboardButton(text="Поддержка")]
    ],
    resize_keyboard=True
)

admin_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Статистика")],
        [KeyboardButton(text="Начать работать"), KeyboardButton(text="Завершить работу")],
        [KeyboardButton(text="Статус")],
        [KeyboardButton(text="Проверить ID пользователя"), KeyboardButton(text="Отправить сообщение пользователю")]
    ],
    resize_keyboard=True
)# Создаём новую клавиатуру для пользователей, использующих команду /старт
start_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Профиль"), KeyboardButton(text="Помощь")],
        [KeyboardButton(text="Создать карту")],
        [KeyboardButton(text="Начать работать"), KeyboardButton(text="Поддержка")]
    ],
    resize_keyboard=True
)

# Новая клавиатура для рабочего процесса
work_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Статус"), KeyboardButton(text="Завершить работу")],
        [KeyboardButton(text="Поддержка")]
    ],
    resize_keyboard=True
)

# Новые reply‑клавиатуры



# Клавиатура для обычного пользователя (Main User Keyboard)
common_user_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="помощь"), KeyboardButton(text="начать работать")],
        [KeyboardButton(text="поддержка"), KeyboardButton(text="финансы")]
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
admin_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="юзер"), KeyboardButton(text="работа"), KeyboardButton(text="админ")],
        [KeyboardButton(text="назад")]
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
                kb = admin_keyboard if message.from_user.id == ADMIN_ID else start_keyboard
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
async def cmd_start(message: types.Message):
    all_users.add(message.from_user.id)
    kb = admin_keyboard if message.from_user.id == ADMIN_ID else start_keyboard
    await message.answer(
        f'Вы успешно запустили бота MC Store!\nДобро пожаловать, *{message.from_user.first_name}*!',
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=kb
    )

# --- Команды связанные с картами и профилем (сохранены из предыдущей версии) ---







@dp.message(F.text.lower() == 'создать карту')
async def btn_create_card(message: types.Message):
    acc = Account.get_acc(message.from_user.id)
    if acc:
        card_id = Account.create_card(message.from_user.id)
        if card_id:
            await message.answer(f'Карта успешно создана\n*ID карты:* {card_id}', parse_mode=ParseMode.MARKDOWN)
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
        '/пополнить - перевод между своими картами\n'
        '/банк_инфо - информация транзакций\n'
        'Также доступны команды рабочего процесса:\n'
        '"Начать работу", "Завершить работу", "Статус", "Отчет", "Связь с админом"\n'
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
            f'Роль: {prof["role"]}\n',
            parse_mode=ParseMode.MARKDOWN, reply_markup=kb
        )
    else:
        await message.answer(
            f'*Профиль пользователя* {name}\n\n'
            f'Баланс: {int(prof["balance"]) % 64} ст.\n'
            f'Количество карт: {prof["count_cards"]}\n'
            f'Количество совершеных транзакций: {prof["count_transactions"]}\n'
            f'Роль: {prof["role"]}\n',
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
            f'Баланс: {int(pool["balance"]) % 64} ст. {int(pool["balance"]) % 64}\n'
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
                f'Баланс: {int(prof["balance"]) % 64} ст. {int(prof["balance"]) % 64}\n'
                f'Количество карт: {prof["count_cards"]}\n'
                f'Количество совершеных транзакций: {prof["count_transactions"]}\n'
                f'Роль: {prof["role"]}\n',
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=kb
            )
        else:
            await call.message.edit_text(
                f'*Профиль пользователя* {call.from_user.first_name}\n\n'
                f'Баланс: {int(prof["balance"]) % 64} ст. {int(prof["balance"]) % 64}\n'
                f'Количество карт: {prof["count_cards"]}\n'
                f'Количество совершеных транзакций: {prof["count_transactions"]}\n'
                f'Роль: {prof["role"]}\n',
                parse_mode=ParseMode.MARKDOWN
            )


@dp.message(Command('server', 'сервер', 'казна', 'budg'))
async def cmd_server(message: types.Message):
    if Account.get_prof(message.from_user.id)['role'] in ['admin', 'bank', 'stuff']:
        pool = Account.get_prof('server')
        await message.answer(
            f'Баланс сервера: {int(pool["balance"]) % 64} ст. {int(pool["balance"]) % 64}'
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
    elif int(get_mc.getstat(Account.get_prof(message.from_user.id)['uuid'], IP_PORT)) // 20 / 60 / 60 >= 0 and\
        Ref.activate_code(str(message.from_user.id), ars[1]) and\
            int(get_mc.getstat(Account.get_prof(message.from_user.id)['uuid'], IP_PORT)) // 20 / 60 / 60 <= 100:
        await message.answer(f'Реферальный код активирован! ')

    else:
        await message.answer('Возникла ошибка!')


@dp.message(Command("создать_карту", "make_card"))
async def cmd_create_card(message: types.Message):
    acc = Account.get_acc(message.from_user.id)
    if acc:
        card_id = Account.create_card(str(message.from_user.id))
        if card_id:
            await message.answer(f'Карта успешно создана\n*ID карты:* {card_id}', parse_mode=ParseMode.MARKDOWN)
            await bot.send_message(
                "-1002480162505",
                f'ID карты: {card_id}\nПользователь: {message.from_user.first_name}\nID пользователя: {message.from_user.id}',
                message_thread_id=6
            )
        else:
            await message.answer(f'У вас недостаточно средств, чтобы создать еще одну карту')
    else:
        await message.answer(f'Ошибка получения данных аккаунта')

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
        await message.reply(
            f"*От кого:* {pool['from']}\t{pool['from_card']}\n"
            f"*Кому:*    {pool['to']}\t{pool['to_card']}\n"
            f"*Сумма:*   {pool['amount']} АР\n"
            f"*Сообщение:* {pool['message']}"
        )
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


@dp.message(Command('перевести', 'trans'))
async def cmd_trans(message: types.Message):
    '''
    /перевести [,card_id/empty] [.gamename/,card_id/@username] message amount
    '''
    ars = message.text.split(' ')
    if int(ars[-1]) < 0:
        await message.answer('Сумма должна быть больше 0!')
        return
    
    fl1 = '-a' in ars
    fl2 = '-e' in ars
    fl3 = '-c' in ars

    if (fl1 + fl2 + fl3) != 1:
        await message.answer('Ошибка ввода!')
        return

    if Account.get_prof(message.from_user.id)['role'] in ['bank', 'admin'] and fl1:

        amount = ars[-1]
        messg = ''
        if len(ars) == 5: messg = ars[3]
        tr = Bank.top_up('z', get_card(ars[2]), messg, amount, 'адм.перевод')

        if tr:
            await message.answer(f'Перевод осуществлен успешно. Транзакция №{tr}')

    elif Account.get_prof(message.from_user.id)['role'] not in ['bank', 'admin'] and fl1:
        await message.answer('Недостаточно прав доступа для осуществления этой команды!')
        return 

    elif fl2:
        '''
        /перевести -e to mssg amount
        '''
        messg = ''
        if len(ars) == 5 and ars[2][0] in ',.@': messg = ars[3]
        amount = ars[-1]

        tr = Bank.top_up(Account.get_prof(message.from_user.id)['main_card'], get_card(ars[2]), messg, amount, 'Перевод')

        if tr:
            await message.answer(f'Перевод осуществлен успешно. Транзакция №{tr}')
        else:
            await message.answer('Произошла ошибка')

    elif fl3:

        '''
        /перевести -c from_card to_card message amount
        '''

        messg = ''
        if len(ars) == 6: messg = ars[4]
        amount = ars[-1]

        tr = Bank.top_up(get_card(ars[2]), get_card(ars[3]), messg, amount, 'Перевод')

        if tr:
            await message.answer(f'Перевод осуществлен успешно. Транзакция №{tr}')
        else:
            await message.answer('Произошла ошибка')

@dp.message(Command('штраф', 'penalty'))
async def cmd_shtraf(message: types.Message):

    ars = message.text.split()

    if Account.get_prof(message.from_user.id)['role'] not in ['admin', 'bank']:
        await message.answer('Недостаточно прав доступа')

    if len(ars) < 2: await message.answer('/штраф gamename [message] [amount]\nКомментарий к штрафу опционален')
    elif len(ars) > 4: await message.answer('/штраф gamename [message] [amount]\nКомментарий к штрафу опционален')
    else:

        amount = ars[-1]
        messge = ars[2] if len(ars) == 4 else ''

        tr = Bank.top_up(get_card(ars[1]), 'z', messge, amount, 'Штраф')
        if tr:
            await message.answer(f'Пользователь был оштрафован на {amount}. Его баланс составляет {Account.get_prof(Account.get_acc_by_name(ars[1][1::])["user_id"])["balance"]}')
            await bot.send_message(Account.get_acc_by_name(ars[1][1::])['user_id'], f'Вы были оштрафованы на {amount}')
        else:
            await message.answer(f'Возникла ошибка')
        


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
    if Bank.top_up('z', Account.get_prof(message.from_user.id)['main_card'], '', earnings, 'Зарплата'):
        await message.answer(f'Вам выплачено: {earnings} АР')
        await bot.send_message(GROUP_ID, f"Пользователь {message.from_user.full_name} (@{message.from_user.username}) закончил работу.\nЗаработано: {earnings} AR.", message_thread_id = 11)
    else:
        await message.answer('Возникла ошибка')

    # Клавиатура как при команде /start
    kb = start_keyboard
    await message.answer("Рабочая сессия завершена.", reply_markup=kb)

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
    if Bank.top_up('z', Account.get_prof(message.from_user.id)['main_card'], '', earnings, 'Зарплата'):
        await message.answer(f'Вам выплачено: {earnings} АР')
        await bot.send_message(GROUP_ID, f"Пользователь {message.from_user.full_name} (@{message.from_user.username}) закончил работу.\nЗаработано: {earnings} AR.", message_thread_id = 11)
    else:
        await message.answer('Возникла ошибка')

@dp.message(Command('status', 'статус'))
async def work_status(message: types.Message):
    user_id = message.from_user.id
    if user_id in users_data:
        start_time = users_data[user_id]
        elapsed = (datetime.datetime.now() - start_time).total_seconds() / 3600
        elapsed = min(elapsed, MAX_HOURS)
        await message.reply(f"Вы работаете уже {elapsed:.2f} часов.")
    else:
        await message.reply("Вы не начали работу. Используйте 'Начать работу'.")

@dp.message(F.text.lower() == 'Статус')
async def work_status(message: types.Message):
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

@dp.message(F.text == "Отчет")
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
    await bot.send_message(ADMIN_ID, f"Видео от @{message.from_user.username} ({user_id}):")
    await bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)

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

@dp.message(F.text.lower() == "Статистика")
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

@dp.message(lambda m: m.from_user.id in pending_transfer and pending_transfer[m.from_user.id]["step"] == "choose_card")
async def transfer_choose_card(message: types.Message):
    user_id = message.from_user.id
    text = message.text.strip()
    if not text.startswith("Карта "):
        await message.answer("Пожалуйста, выберите карту, нажав одну из кнопок.")
        return
    card_value = text[len("Карта "):].strip()
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
    pending_transfer[user_id]["method"] = "method_" + method
    pending_transfer[user_id]["step"] = "input_target"
    await message.answer("Введите данные получателя (в зависимости от выбранного метода):", reply_markup=types.ReplyKeyboardRemove())

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
    kb = admin_keyboard if message.from_user.id == ADMIN_ID else start_keyboard
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

    elif method == 'method_game':
        target_card = Account.get_prof(Account.get_acc_by_name(target_input)['user_id'])['main_card']
        uid = Account.get_acc_by_name(target_input)['user_id']
    elif method == 'method_card':
        target_card = get_card2(target_input)
        uid = Bank.bank_info(target_card)['user']
    if not target_card:
        await message.answer("Неверные данные получателя. Операция отменена.", reply_markup=kb)
        return
    tr = Bank.top_up(from_card, target_card, comment, amount, 'Перевод')
    if tr:
        await message.answer(f"Перевод осуществлен успешно. Транзакция №{tr}", reply_markup=kb)
        await bot.send_message(uid, f'Вам поступил перевод от @{message.from_user.username} в размере {amount} АР\n {f"Комментарий отправителя: {comment}" if comment else "" }', )
        await bot.send_message(
                "-1002480162505",
                f'*Транзакция №{tr}*'
                f'*Отправитель:*   {Account.get_prof(message.from_user.id)["name"]}'
                f'\n*Получатель:*   {Account.get_prof(uid)["name"]}'
                f'\n*Сумма:*        {amount}'
                f'\n*Сообщение:*    {comment}',
                message_thread_id=4,
                parse_mode=ParseMode.MARKDOWN_V2
            )
    else:
        await message.answer("Произошла ошибка при переводе.")

@dp.message(lambda m: m.text.lower() == 'финансы')
async def finances_handler(message: types.Message):
    # Показать клавиатуру раздела "финансы"
    await message.answer("Меню финансов", reply_markup=finances_kb)

@dp.message(lambda m: m.text.lower() == 'назад')
async def back_handler(message: types.Message):
    user_id = message.from_user.id
    prof = Account.get_prof(user_id)
    # Если роль админа или банка – вернуть админскую клавиатуру, иначе – обычное меню пользователя
    if prof and prof.get("role") in ["admin", "bank"]:
        await message.answer("Админ меню", reply_markup=admin_kb)
    else:
        await message.answer("Главное меню", reply_markup=common_user_kb)

@dp.message(lambda m: m.text.lower() == 'юзер')
async def user_handler(message: types.Message):
    # Выводим дефолтную клавиатуру для обычных пользователей
    await message.answer("Пользовательское меню", reply_markup=common_user_kb)

@dp.message(lambda m: m.text.lower() == 'работа')
async def work_handler(message: types.Message):
    # Доступно только администраторам/банкам
    if Account.get_prof(message.from_user.id).get("role") in ["admin", "bank"]:
        await message.answer("Рабочее админ меню", reply_markup=admin_work_kb)
    else:
        await message.answer("Недостаточно прав доступа.")

@dp.message(lambda m: m.text.lower() == 'админ')
async def admin_handler(message: types.Message):
    # Отображаем клавиатуру админских действий
    if Account.get_prof(message.from_user.id).get("role") in ["admin", "bank"]:
        await message.answer("Админ действия", reply_markup=admin_actions_kb)
    else:
        await message.answer("Недостаточно прав доступа.")

@dp.message(lambda m: m.text.lower() == 'состояние')
async def status_handler(message: types.Message):
    # Здесь можно собрать данные о состоянии бота, сервера и соединения.
    active_users_count = len(users_data)
    # Заглушки для статуса сервера и соединения. Замените на реальную логику при необходимости.
    server_status = "Online"
    connection_status = "Stable"
    status_text = (
        f"Состояние бота:\n"
        f"Активных пользователей: {active_users_count}\n"
        f"Сервер: {server_status}\n"
        f"Соединение: {connection_status}"
    )
    # Если админ, оставляем админскую клавиатуру, иначе – обычную
    prof = Account.get_prof(message.from_user.id)
    kb = admin_actions_kb if prof and prof.get("role") in ["admin", "bank"] else common_user_kb
    await message.answer(status_text, reply_markup=kb)

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())

