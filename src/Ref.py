import json
import random

from src import Bank

CODE_DEFAULT = {
    "user_id": ""
}

def gen_code(user_id: str) -> str:

    try:
        with open('data/account.json', 'r', encoding = 'utf-8') as file:
            data = json.load(file)
        
        with open('data/codes.json', 'r', encoding = 'utf-8') as file2:
            codes = json.load(file2)

        source = 'qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM1234567890'
        code = ''.join([random.choice(source) for i in range(5)])
        try:
            if data[user_id]['code']:
                return data[user_id]['code']
        except:
            print('ok3')

        if code in codes:
            return gen_code(user_id)

        data[user_id]["code"] = code
        if code not in codes:
            codes[code] = CODE_DEFAULT
        codes[code]['user_id'] = user_id

        with open('data/account.json', 'w', encoding = 'utf-8') as file_:
            json.dump(data, file_, ensure_ascii=False, indent=4)

        with open('data/codes.json', 'w', encoding = 'utf-8') as file_2:
            json.dump(codes, file_2, ensure_ascii=False, indent=4)

        return code
    
    except Exception as e:
        print(e)

def get_code(user_id: str) -> str:
    with open('data/account.json', 'r', encoding = 'utf-8') as file:
        data = json.load(file)

    return data[user_id]['code']

def activate_code(user_id: str, code: str) -> bool:
    with open('data/account.json', 'r', encoding = 'utf-8') as file:
        data = json.load(file)
    with open('data/codes.json', 'r', encoding = 'utf-8') as file2:
        codes = json.load(file2)

    if code in codes:
        if data[codes[code]['user_id']]['code'] and codes[code]['user_id'] != user_id:
            if data[codes[code]['user_id']]['code'] == code and not data[user_id]['invited']: 
                data[user_id]['invited'] = 1
                data[codes[code]['user_id']]['invites'] += 1

                with open('data/account.json', 'w', encoding = 'utf-8') as file_:
                    json.dump(data, file_, ensure_ascii=False, indent=4)

                with open('data/codes.json', 'w', encoding = 'utf-8') as file_2:
                    json.dump(codes, file_2, ensure_ascii=False, indent=4)

                if Bank.top_up('z', data[codes[code]['user_id']]['main_card'], '', 10, 'Активация приглашения') and\
                Bank.top_up('z', data[user_id]['main_card'], '', 20, 'Активация приглашения'):
                    return (codes[code]['user_id'])
                else:
                    return False
            
            else: return False
        else: return False
    else: return False

def get_referal(code):
    with open('data/codes.json', 'r', encoding = 'utf-8') as file:
        data = json.load(file[code])

    if data['user_id']:
        return data['user_id']
    else:
        return False
