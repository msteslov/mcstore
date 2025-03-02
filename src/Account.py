import datetime
import json
import random

from src import Bank

PROF_DEFAULT = {
    "cards": [],
    "last_transactions": [],
    "count_transactions": 0,
    "balance": 0,
    "count_cards": 0,
    "role": "user",
    "user": "",
    "main_card": "",
    "uuid": "",
    "name": "",
    "code": "",
    "invites": 0,
    "invited": 0,
    "trans_limit": 192,
    "bank_premium": 0
}

USERNAME_DEFAULT = {
    "user_id": "",
    "uuid": "",
    "name": ""
}
GAMEACC_DEFAULT = {
    "name": "",
    "uuid": "",
    "user_id": "",
    "username": ""
}

CARD_DEFAULT = {
    "balance": 0,
    "last_transactions": [],
    "count_transactions": 0,
    "user": "",
    "name": "",
    "uuid": ""
}

TRANSACTION_DEFAULT = {
    "from": "",
    "from_card": "",
    "to": "",
    "to_card": "",
    "amount": 0,
    "date": "",
    "message": "",
    "id": "",
    "type": "",
    "status": 0,
}

BANK_STAT_DEFAULT = {
    "quantity": 0,
    "premium": 0,
    "limit": 192,
    "trans_count": 0
}

def check_prof(user_id, username, uuid, name) -> bool:
    with open('data/account.json', 'r', encoding='utf-8') as file:
        data = json.load(file)
    with open('data/stat.json', 'r', encoding = 'utf-8') as file:
        stat = json.load(file)
    
    if str(user_id) not in data and str(user_id) not in stat:
        try:
            data[str(user_id)] = PROF_DEFAULT
            data[str(user_id)]["user"] = str(username)
            data[str(user_id)]["uuid"] = uuid
            data[str(user_id)]["name"] = name

            stat[str(user_id)] = BANK_STAT_DEFAULT

            with open('data/stat.json', 'w', encoding = 'utf-8') as file:
                json.dump(stat, file, ensure_ascii = False, indent = 4)

            with open('data/account.json', 'w', encoding='utf-8') as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
                return True
        except Exception as e:
            print(e)
            return False
    return True

def add_username(user_id, username, uuid, name):
    with open('data/usernames.json', 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    if str(username) not in data:
        try:
            data[str(username)] = USERNAME_DEFAULT
            data[str(username)]["user_id"] = str(user_id)
            data[str(username)]["uuid"] = uuid
            data[str(username)]["name"] = name
            with open('data/usernames.json', 'w', encoding='utf-8') as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print('ok')
            print(e)
            return False
        
def create_acc(name, uuid, user_id, username):
    with open('data/gameacc.json', 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    if str(name) not in data:
        try:
            data[name] = GAMEACC_DEFAULT
            data[name]["username"] = username
            data[name]["user_id"] = str(user_id)
            data[name]["uuid"] = uuid
            with open('data/gameacc.json', 'w', encoding='utf-8') as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print('ok2')
            print(e)
            return False
        
def get_acc(user_id):
    with open('data/gameacc.json', 'r', encoding = 'utf-8') as file:
        data = json.load(file)

    user = get_prof(user_id)
    name = user['name']
    
    if name in data.keys():
        return data[name]

    return False

def get_acc_by_name(name):
    with open('data/gameacc.json', 'r', encoding = 'utf - 8') as file:
        data = json.load(file)

    if name in data:
        return data[name]
    else:
        return False
        
def get_id_by_usn(username):
    with open('data/usernames.json', 'r', encoding='utf-8') as file:
        data = json.load(file)
    try:
        return data[str(username)]["user_id"]
    except Exception as e:
        print(e)
        return False
    
def get_usn_by_id(user_id):
    with open('data/account.json', 'r', encoding='utf-8') as file:
        data = json.load(file)
    try:
        return data[str(user_id)]["user"]
    except Exception as e:
        print(e)
        return False

def get_prof(user_id) -> dict:
    with open('data/account.json', 'r', encoding='utf-8') as file:
        data = json.load(file)
    try:
        return data[str(user_id)]
    except Exception as e:
        print(e)
        return False

def create_card(user_id: str) -> int:

    user_id = str(user_id)

    with open('data/account.json', 'r', encoding = 'utf-8') as file:
        users = json.load(file)

    with open('data/cards.json', 'r', encoding = 'utf-8') as file2:
        cards = json.load(file2)

    id = str(len(cards))
    while len(id) < 4:
        id = '0' + id

    if id not in cards:
        if users[user_id]['cards']: #if card not first
            if Bank.bank_info(users[user_id]['main_card'])['balance'] < (len(users[user_id]['cards'])) * 5:
                return 0
            else:
                tr = Bank.top_up(users[user_id]['main_card'], 'казна', '', (len(users[user_id]['cards']) - 1) * 5, 'Покупка карты')

                if tr:

                    cards[id] = CARD_DEFAULT
                    users[user_id]['cards'].append(id)
                    cards[id]['user'] = str(user_id)
                    cards[id]['name'] = get_acc(user_id)['name']
                    cards[id]['uuid'] = get_acc(user_id)['uuid']
                    cards[users[user_id]['main_card']]['balance'] -= (len(users[user_id]['cards']) - 1) * 5
                    users[user_id]['balance'] -= (len(users[user_id]['cards']) - 1) * 5

                    users[user_id]['count_cards'] += 1

                else:
                    return 0
        else:
            cards[id] = CARD_DEFAULT
            users[user_id]['cards'].append(id)
            cards[id]['user'] = str(user_id)
            cards[id]['name'] = get_acc(user_id)['name']
            cards[id]['uuid'] = get_acc(user_id)['uuid']
            users[user_id]['count_cards'] += 1
            users[user_id]['main_card'] = id


        with open('data/account.json', 'w', encoding='utf-8') as file:
            json.dump(users, file, ensure_ascii=False, indent=4)
        with open('data/cards.json', 'w', encoding='utf-8') as file:
            json.dump(cards, file, ensure_ascii=False, indent=4)
        with open('logs.txt', 'a', encoding='utf-8') as file:
            file.write(f'Создание карты: \tID карты: {id}\tПользователь: {user_id}\t Дата: {datetime.datetime.now()}\n')    

    else:
        return create_card(user_id)
    return id

def dostup(username):

    with open('data/account.json', 'r', encoding = 'utf-8') as file:
        data = json.load(file)

    data[get_acc_by_name(username)['user_id']]['role'] = 'staf'

    with open('data/account.json', 'w', encoding = 'utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent = 4)

    return True

def nedostup(username):
    with open('data/account.json', 'r', encoding = 'utf-8') as file:
        data = json.load(file)

    data[get_acc_by_name(username)['user_id']]['role'] = 'user'

    with open('data/account.json', 'w', encoding = 'utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent = 4)

    return True
    
