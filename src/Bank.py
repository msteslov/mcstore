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

def top_up(from_card, to_card, message, amount, type):

    amount = int(amount)

    with open('data/cards.json', 'r', encoding = 'utf-8') as file:
        cards = json.load(file)

    with open('data/account.json', 'r', encoding = 'utf-8') as file2:
        users = json.load(file2)

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
    cards['казна']['balance'] += amount

    with open('data/cards.json', 'w', encoding = 'utf-8') as file:
        json.dump(cards, file, ensure_ascii=False, indent=4)

    with open('data/account.json', 'w', encoding = 'utf-8') as file2:
        json.dump(data, file2, ensure_ascii=False, indent=4)

    return True

def withdraw(card_id, message, amount):
    amount = int(amount)
    with open('data/cards.json', 'r', encoding='utf-8') as file:
        cards = json.load(file)
    with open('data/account.json', 'r', encoding='utf-8') as file2:
        users = json.load(file2)

    # Регистрируем транзакцию, где отражается только снятие
    tr = reg_transaction(card_id, card_id, cards[card_id]['user'], cards[card_id]['user'], amount, message, 'Снятие', 1)
    if not tr:
        return 0

    cards[card_id]['balance'] -= amount
    cards[card_id]['last_transactions'].insert(len(cards[card_id]['last_transactions']) % 5, tr)
    cards[card_id]['count_transactions'] += 1

    user = cards[card_id]['user']
    users[user]['last_transactions'].insert(len(users[user]['last_transactions']) % 5, tr)
    users[user]['count_transactions'] += 1
    users[user]['balance'] -= amount

    with open('data/cards.json', 'w', encoding='utf-8') as file:
        json.dump(cards, file, ensure_ascii=False, indent=4)
    with open('data/account.json', 'w', encoding='utf-8') as file2:
        json.dump(users, file2, ensure_ascii=False, indent=4)

    return tr



