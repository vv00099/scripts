#!/usr/bin/python3.6
# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
#import fake_useragent
import os
import time
import copy
import argparse
import re
import json

#Данный скрипт собирает необходимые данные со страницы задания CRM системы
#для настройки ONU и выгружает их для последующей обработки
#в скрипте создании кода для станции
#Значения NULL будут заполнены на следующем этапе

#Реальных данных абонентов или нашей компании здесь нет

parser = argparse.ArgumentParser(description='')
#путь к скрипту --do C:\Users\vadim\Desktop\py --n 81267,81240,81185,81155
parser.add_argument("--do")
parser.add_argument("--n")
args = parser.parse_args()

output_path = '/home/user/work/'
numbers_tasts = ['84166', '84165', '84014', '84237']


if args.do != None:
    if not os.path.exists(args.do):
        print('Выбранная каталог не доступен.Попытаться создать его?')
        choise = input('y/n')
        if choise == 'y':
            os.mkdir(args.do)
            print('Каталог создан', args.do)
            output_path = args.do
        else:
            print('Выполнение прервано...')
            quit()
    else:
        output_path = args.do

#Установка директорий по умолчанию если никаких
#других путей нет
if args.do == None:
    if output_path == "":
        output_path = (os.path.dirname(os.path.abspath(__file__)) + os.sep)
        
if args.n != None or "":
    numbers_tasts = args.n.split(",")

for task in numbers_tasts:
    check =(re.fullmatch(r'\d{5}', task))
    if check:
        print("Номер задания корректен (" + task + ")")
    else:
        print("Номер задания не верный, отмена... (" + task + ")")
        quit()

nl = '\n'

abo_list = []

abo_data  = { 'OLT' : 'NULL',
              'PORT' : 'NULL',
              'ONU' : 'NULL',
              'SN' : 'NULL',
              'TYPE_A' : 'PPPOE IPOE BRIDGE',
              'FIO' : 'NULL',
              'ADRESS' : 'NULL',
              'LOGIN' : 'NULL',
              'PASSWORD' : 'NULL'}

#Настоящий url убран
link = 'http://crmurl.ru/oper/'
user = 'Mozilla/5.0 (X11; Linux x86_64; rv:97.0) Gecko/20100101 Firefox/97.0'

header = {
    'user-agent': user
}
data = {
    "action" : "login",
    "username" : "login",
    "password" : "passord"
}


if numbers_tasts == []:
    print("Нет заданий для выполнения, отмена...")
    quit()

session = requests.Session()

responce = session.post(link, data=data, headers=header)
print(responce.status_code)

def data_get(tasts):
    for task in tasts:
        if check:
			#Формируем get запрос
            task_info = 'http://crmurl.ru/oper/?core_section=task&action=show&id=' + task
            task_info_responce = session.get(task_info, headers=header).text
            
            soup = BeautifulSoup(task_info_responce, 'lxml')
            block = soup.find('div', class_ = 'j_card_div')
            
            fio = block.find_all('a')[1].text
            adress = block.find_all('a')[2].text
            olt = block.find('span', id='dopf_value_19_id').text
            port = block.find('span', id='dopf_value_20_id').text
            login = block.find_all('a')[1].next_element.next_element.next_element.text
            

            abo_data["FIO"] = fio
            abo_data["ADRESS"] = adress
            abo_data["OLT"] = olt
            abo_data["PORT"] = port
            abo_data["LOGIN"] = login
            abo_data["ONU"] = '6688 6699 8245 G84 8145'
            abo_data["TYPE_A"]= 'PPPOE BRIDGE'
            abo_list.append(copy.deepcopy(abo_data))
            for key,value in abo_data.items():
                    abo_data[key] = 'NULL'

data_get(numbers_tasts)   


try:
	with open (output_path + os.sep + "SN" + time.strftime('_%d_%m') + ".json", "w",encoding='utf-8') as file_save:
		json.dump(abo_list, file_save, ensure_ascii=False, indent=4)
except FileNotFoundError:
	os.system(output_path + os.sep + "SN" + time.strftime('_%d_%m') + ".json")
	with open (output_path + os.sep + "SN" + time.strftime('_%d_%m') + ".json", "w",encoding='utf-8') as file_save:
		json.dump(abo_list, file_save, ensure_ascii=False, indent=4)
    
print(file_save)
