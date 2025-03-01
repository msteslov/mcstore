import datetime
import json

from src import Account

CARD_DEFAULT = {
    "balance": 0,
    "last_transactions": {},
    "count_transactions": 0,
    "user": "",
}

def bank_info(card_id):
    with open('data/cards.json', 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data[str(card_id)]

def reg_transaction(from_card, to_card, from_user, to_user, amount, message, type, status):

    from_user = Account.get_prof(from_user)
    to_user = Account.get_prof(to_user)

    with open('data/transactions.json', 'r', encoding='utf-8') as file:
        transactions = json.load(file)

    transactions[len(transactions)] = {
        "from": from_user["name"],
        "from_card": from_card,
        "to": to_user["name"],
        "to_card": to_card,
        "amount": amount,
        "date": "date",
        "type": type,
        "id": '_'+str(len(transactions)),
        "status": status,
        "message": message
    }

    with open('data/transactions.json', 'w', encoding='utf-8') as file:
        json.dump(transactions, file, ensure_ascii=False, indent=4)

    return int(len(transactions)) - 1

def trans_info(transaction):
    with open('data/transactions.json', 'r', encoding = 'utf-8') as file:
        data = json.load(file)

    if data[transaction]:
        return data[transaction]
    else:
        return False


def top_up_card(from_card, to_card, user_id, amount):
    fc = from_card
    tc = to_card
    from_card = bank_info(from_card)
    to_card = bank_info(to_card)
    user = Account.get_prof(user_id)
    user2 = Account.get_prof(to_card["user"])
    amount = (int(amount))
    if from_card['user'] != f'{user_id}' or (to_card['user'] != user_id and user['role'] not in ['admin', 'bank']):
        print('ok')
        return False
    else:
        if from_card['balance'] < amount:
            print('ok2')
            return False
        if from_card['user'] != str(user_id):
            print('ok3')
            return False
        else:
            from_card['balance'] -= amount
            to_card['balance'] += amount
            from_card['count_transactions'] += 1
            to_card['count_transactions'] += 1
            trans = reg_transaction(fc, tc, from_card['user'], to_card['user'], amount, '', 'пополнение', 1)
            from_card['last_transactions'].insert(len(from_card['last_transactions']) % 10, trans)
            to_card['last_transactions'].insert(len(to_card['last_transactions']) % 10, trans)

            if user != user2:
                user['balance'] -= amount
                user2['balance'] += amount
            
            user['last_transactions'].insert(len(user['last_transactions']) % 10, trans)
            user['count_transactions'] += 1
            user2['last_transactions'].insert(len(user2['last_transactions']) % 10, trans)
            user2['count_transactions'] += 1

            with open('data/account.json', 'r', encoding = 'utf-8') as file:
                data = json.load(file)

            with open('data/cards.json', 'r', encoding = 'utf-8') as file2:
                data2 = json.load(file2)

            data[str(user_id)] = user
            data[str(to_card['user'])] = user2
            print(data)
            data2[str(fc)] = from_card
            data2[str(tc)] = to_card

            with open('data/cards.json', 'w', encoding='utf-8') as file2:
                json.dump(data2, file2, ensure_ascii=False, indent=4)
            with open('data/account.json', 'w', encoding='utf-8') as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
            with open('logs.txt', 'a', encoding='utf-8') as file:
                file.write(f'Пополнение {trans}: \t from_card: {user_id}\t to_card: {user_id}\t Дата: {datetime.datetime.now()}\n')

            return trans
        
def top_up_adm(sender, username, amount, message):
    user1 = Account.get_prof(sender)
    user2 = Account.get_prof(Account.get_id_by_usn(username))
    user2_card = bank_info(user2['main_card'])
    card_id = user2['main_card']
    server = Account.get_prof('000')
    amount = int(amount)

    if server['balance'] < amount:
        return False
    else:
        server['balance'] -= amount
        user2['balance'] += amount
        user2_card['balance'] += amount
        
        trans = reg_transaction('server', card_id, sender, Account.get_id_by_usn(username), amount, message, 'адм_пополнение', 1)

        user2['count_transactions'] += 1
        user2_card['count_transactions'] += 1
        user1['count_transactions'] += 1
        user2['last_transactions'].insert(len(user2['last_transactions']) % 5, trans)
        user2_card['last_transactions'].insert(len(user2_card['last_transactions']) % 5, trans) 
        user1['last_transactions'].insert(len(user1['last_transactions']) % 5, trans)

        with open('data/account.json', 'r', encoding = 'utf-8') as file:
            data = json.load(file)
        with open('data/cards.json', 'r', encoding = 'utf-8') as file2:
            data2 = json.load(file2)

        data[Account.get_id_by_usn(user1['user'])] = user1
        data[Account.get_id_by_usn(username)] = user2
        data['000'] = server
        data2[card_id] = user2_card

        with open('data/account.json', 'w', encoding = 'utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent = 4)
        with open('data/cards.json', 'w', encoding = 'utf-8') as file2:
            json.dump(data2, file2, ensure_ascii=False, indent = 4)
        with open('logs.txt', 'a', encoding='utf-8') as file:
            file.write(f'Адм_пополнение {trans}: \t from: {user1["user"]}\t to: {username}\t Дата: {datetime.datetime.now()}\n')

        return trans
    

def top_up(from_card, to_card, message, amount, type):

    amount = int(amount)

    with open('data/cards.json', 'r', encoding = 'utf-8') as file:
        cards = json.load(file)

    with open('data/account.json', 'r', encoding = 'utf-8') as file2:
        users = json.load(file2)
    if cards[from_card]['balance'] < amount:
        return -1
    elif cards[from_card]['balance'] >= amount:

        tr = reg_transaction(from_card, to_card, cards[from_card]['user'], cards[to_card]['user'], amount, message, type, 1)
        if not tr: return 0

        cards[from_card]['balance'] -= amount
        cards[from_card]['last_transactions'].insert(len(cards[from_card]['last_transactions']) % 5, tr)
        cards[from_card]['count_transactions'] += 1

        cards[to_card]['balance'] += amount
        cards[to_card]['last_transactions'].insert(len(cards[to_card]['last_transactions']) % 5, tr)
        cards[to_card]['count_transactions'] += 1

        user1 = cards[from_card]['user']
        user2 = cards[to_card]['user']

        print(users[user1]['balance'])

        users[user1]['last_transactions'].insert(len(users[user1]['last_transactions']) % 5, tr)
        users[user1]['count_transactions'] += 1
        users[user1]['balance'] -= amount

        print(users[user1]['balance'])


        users[user2]['last_transactions'].insert(len(users[user2]['last_transactions']) % 5, tr)
        users[user2]['count_transactions'] += 1
        users[user2]['balance'] += amount

        with open('data/cards.json', 'w', encoding = 'utf-8') as file:
            json.dump(cards, file, ensure_ascii=False, indent=4)

        with open('data/account.json', 'w', encoding = 'utf-8') as file2:
            json.dump(users, file2, ensure_ascii=False, indent=4)

        return tr
        
def tups(amount):

    with open('data/account.json', 'r', encoding = 'utf-8') as file:
        data = json.load(file)
    with open('data/cards.json', 'r', encoding = 'utf-8') as file:
        cards = json.load(file)

    data['server']['balance'] += amount
    cards['z']['balance'] += amount

    with open('data/cards.json', 'w', encoding = 'utf-8') as file:
        json.dump(cards, file, ensure_ascii=False, indent=4)

    with open('data/account.json', 'w', encoding = 'utf-8') as file2:
        json.dump(data, file2, ensure_ascii=False, indent=4)

    return True


