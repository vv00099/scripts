#!/usr/bin/python3.6
# -*- coding: utf-8 -*-

import re
import copy
import time
import argparse
import os
import json

'''Этот скрипт автоматизирует создание кода
для записи данных GPON терминалов в
GPON станции HUAWEI типа MA5683T и подобных.
Данные предварительно создаются вручную
определенным образом в json файле,
другоим скриптом.В процессе выполнения
скрипта эти данные преобразуются в
нужный вид.
Параметры скрипта можно
внести в самом теле или использовать
ключи при запуске из терминала ОС.
В процессе выполнения будет создан
на каждую станцию отдельный фаил,
содержащий дату создания в названии

Самые главные параметры:

:param path_files - каталог с файлом данных
:param file = path_files + назвние файла - полный путь к файлу данных
:param output_path - каталог для записи данных.Может совпадать с path_files

### Пример созданной записи конфигурации для GPON станции ###

interface gpon 0/4 
 
ont add 3 sn-auth 53434F4D14786125 omci ont-lineprofile-id 1\
ont-srvprofile-id 1 desc AZOV_Turgeneva_11_Ivanov_I_A__SC6699 
 
quit 
 
service-port vlan 423 gpon 0/4/3 ont XX gemport 0 multi-service\
user-vlan 300 tag-transform default 


#######################
Примеры запуска с аргументами:

Запустить скрипт, данные взять из указанной директории из
последнего измененного в ней json файла,созданный файл
записать туда же:
python3 GCG.py --diaf "/home/user/work/"

Указание файла-источника и директории для записи вручную:
python3 GCG.py --do "/home/user/work/" --f "/home/user/work/SN.json"
'''

##############Run-keys#################
parser = argparse.ArgumentParser(description='A tutorial of argparse!')
parser.add_argument("--do")
parser.add_argument("--f")
parser.add_argument("--diaf")
args = parser.parse_args()

##############Pre-data#################
#значения директории по умолчанию

path_files = ""
file = path_files + ''
output_path = ""

if args.f != None:
    if args.do != None:
        if os.path.exists(args.f):
            file = args.f
        else:
            print('Файл-источник отсутствует или недоступен.Выполнение прервано...')
            quit()
    else:
        print('Каталог для записи файла не найден или не доступен.Выполнение прервано...')
        quit()


if args.do != None:
    if not os.path.exists(args.do):
        print('Выбранный каталог не доступен.Попытаться создать его?')
        choise = input('y/n')
        if choise == 'y':
            os.mkdir(args.do)
            print('Каталог создан', args.do)
            output_path = args.do
        else:
            print('Выполнение прервано...')
            exit()
    else:
        output_path = args.do
else:
    output_path = path_files


nl = '\n'
#Список всех словарей
abo_list = []
station0 = []
station1 = []
station2 = []
station3 = []
station4 = []
######
ab_name = ""
ab_adress = ""
defaults_onu = ('6699', '8245', '8145')
#######################################

###############Templates###############
#Шаблон словаря с данными абонента
abo_data  = { 'OLT' : 'NULL',
              'PORT' : 'NULL',
              'ONU' : 'NULL', 
              'SN' : 'NULL', 
              'DESC' : 'NULL',
              'TYPE_A' : 'PPPOE IPOE BRIDGE',
              'FIO' : 'NULL',
              'ADRESS' : 'NULL',
              'LOGIN' : 'NULL',
              'PASSWORD' : 'NULL',
              'PROFILE' : 'NULL',
              'COUNT_NATIVE_VLAN' : 0,
              'USER_VLAN' : 'NULL',
              'SERVICE_PORT_VLAN' : 'NULL',
              'GEMPORT' : 'NULL'}


station0_vlans = {'0/0' : '100',
              '0/1' : '101',
              '0/2' : '102',
              '0/3' : '103',
              '0/4' : '104',
              '0/5' : '105',
              '0/6' : '106',
              '0/7' : '107',
              '0/8' : '108',
              '0/9' : '109',
              '0/10' : '150',
              '0/11' : '151',
              '0/12' : '152',
              '0/13' : '153',
              '0/14' : '154',
              '0/15' : '155',
              '1/0' : '110',
              '1/1' : '111',
              '1/2' : '112',
              '1/3' : '113',
              '1/4' : '114',
              '1/5' : '115',
              '1/6' : '116',
              '1/7' : '117',
              '1/8' : '118',
              '1/9' : '119',
              '1/10' : '120',
              '1/11' : '121',
              '1/12' : '122',
              '1/13' : '123',
              '1/14' : '124',
              '1/15' : '125',
              '2/0' : '220',
              '2/1' : '221',
              '2/2' : '222',
              '2/3' : '223',
              '2/4' : '224',
              '2/5' : '225',
              '2/6' : '226',
              '2/7' : '227',
              '2/8' : '228',
              '2/9' : '229',
              '2/10' : '230',
              '2/11' : '231',
              '2/12' : '232',
              '2/13' : '233',
              '2/14' : '234',
              '2/15' : '235',
              '3/0' : '310',
              '3/1' : '311',
              '3/2' : '312',
              '3/3' : '313',
              '3/4' : '314',
              '3/5' : '315',
              '3/6' : '316',
              '3/7' : '317',
              '3/8' : '318',
              '3/9' : '319',
              '3/10' : '320',
              '3/11' : '321',
              '3/12' : '322',
              '3/13' : '323',
              '3/14' : '324',
              '3/15' : '325',
              '4/0' : '420',
              '4/1' : '421',
              '4/2' : '422',
              '4/3' : '423',
              '4/4' : '424',
              '4/5' : '425',
              '4/6' : '426',
              '4/7' : '427',
              '4/8' : '428',
              '4/9' : '429',
              '4/10' : '430',
              '4/11' : '431',
              '4/12' : '432',
              '4/13' : '433',
              '4/14' : '434',
              '4/15' : '435'}
    
station1_vlans = { '0/0' : '1000',
                    '0/1' : '1001',
                    '0/2' : '1002',
                    '0/3' : '1003',
                    '0/4' : '1004',
                    '0/5' : '1005',
                    '0/6' : '1006',
                    '0/7' : '1007',
                    '0/8' : '1008',
                    '0/9' : '1009',
                    '0/10' : '1010',
                    '0/11' : '1011',
                    '0/12' : '1012',
                    '0/13' : '1013',
                    '0/14' : '1014',
                    '0/15' : '1015',
                    '1/0' : '2000',
                    '1/1' : '2001',
                    '1/2' : '2002',
                    '1/3' : '2003',
                    '1/4' : '2004',
                    '1/5' : '2005',
                    '1/6' : '2006',
                    '1/7' : '2007',}
    
station2_vlans = {'0/0' : '130',
                  '0/1' : '131',
                  '0/2' : '132',
                  '0/3' : '133',
                  '0/4' : '134',
                  '0/5' : '135',
                  '0/6' : '136',
                  '0/7' : '137'}

station3_vlans = {'0/0' : '3000',
                    '0/1' : '3001',
                    '0/2' : '3002',
                    '0/3' : '3003',
                    '0/4' : '3004',
                    '0/5' : '3005',
                    '0/6' : '3006',
                    '0/7' : '3007',
                    '0/8' : '3008',
                    '0/9' : '3009',
                    '0/10' : '3010',
                    '0/11' : '3011',
                    '0/12' : '3012',
                    '0/13' : '3013',
                    '0/14' : '3014',
                    '0/15' : '3015'}

station4_vlans = {'0/0' : '1500',
                    '0/1' : '1501',
                    '0/2' : '1502',
                    '0/3' : '1503',
                    '0/4' : '1504',
                    '0/5' : '1505',
                    '0/6' : '1506',
                    '0/7' : '1507',
                    '0/8' : '1508',
                    '0/9' : '1509',
                    '0/10' : '1510',
                    '0/11' : '1511',
                    '0/12' : '1512',
                    '0/13' : '1513',
                    '0/14' : '1514',
                    '0/15' : '1515',
                    '1/0' : '1600',
                    '1/1' : '1601',
                    '1/2' : '1602',
                    '1/3' : '1603',
                    '1/4' : '1604',
                    '1/5' : '1605',
                    '1/6' : '1606',
                    '1/7' : '1607',
                    '1/8' : '1608',
                    '1/9' : '1609',
                    '1/10' : '1610',
                    '1/11' : '1611',
                    '1/12' : '1612',
                    '1/13' : '1613',
                    '1/14' : '1614',
                    '1/15' : '1615'}

#######################################

###############Functions###############
#Получение последнего измененного json файла в директории
#откуда запущен скрипт
def get_last_modified_file(path1):
    dir_list = [os.path.join(path1, x) for x in os.listdir(path1)]
    sort_date_list_only_json = []
    if dir_list:
        # Создадим список из путей к файлам и дат их создания.
        date_list = [[x, os.path.getctime(x)] for x in dir_list]
        # Отсортируем список по дате создания в обратном порядке
        sort_date_list = sorted(date_list, key=lambda x: x[1], reverse=True)
        for file in sort_date_list:
            #Поскольку это списк со вложенными списками, перебираем дальше
            for i in file:
                if ".json" in str(i):
                    sort_date_list_only_json.append(file)
        # Выведем первый элемент списка. Он и будет самым последним по дате
        file_last_modified = sort_date_list_only_json[0][0]
        return file_last_modified


#Обрезание полного ФИО до фамилиии + инициалы
def abo_convection(string):
    #Если это юрик, то пропускаем обрезку
    check_string = re.search(r'(\bООО|\bИП|\bОАО|\bЗАО|\bГСК|\bМП)', string)
    
    if check_string != None:
        #Убираем пробелы
        string = re.sub(r' ', "_", string)
        return string
    else:
        new_list = string.split(' ')
        #Метка что фамилия еще не обработанна
        v = False
        #Подставка перед адресом
        final_string = "_"
        for i in new_list:
            #Если это не слово тогда пропускаем итерацию
            if len(i) < 1:
                continue
            if v == False:
               final_string = i + '_'
               v = True
            else:
                #берем первую букву i и получается инициал
                final_string += i[0] + '_'
        return final_string

#Обрезание полного адреса до нужной формы
def adress_convection(abo):
    #обрезка текста под маску "АЗОВ_Первомайская_44"
    abo = re.sub(r'\bг.|\bпер.|\д.|\bСНТ|\bРостовская обл.|\bспуск|\bДНТ|\bс.|\bСН|\bул.|\bАзовский р-н.|\Bичуринец|\bх.', "", abo)
    abo = re.sub(r'кв.', "_кв.", abo)
    abo = re.sub(r'\ |\A,', "", abo)
    abo = re.sub(r',', "_", abo)
    abo = re.sub(r'\A_', "", abo)
    #преобразование в список и изменение регистра первого слова
    abo_list = abo.split('_')
    abo_list[0]= abo_list[0].upper()
    #Собираем обратно в строку
    abo = '_'.join(abo_list)
    return abo

#Взял с инета
def transliterate(string):
    

    capital_letters = {u'А': u'A',
                       u'Б': u'B',
                       u'В': u'V',
                       u'Г': u'G',
                       u'Д': u'D',
                       u'Е': u'E',
                       u'Ё': u'E',
                       u'Ж': u'Zh',
                       u'З': u'Z',
                       u'И': u'I',
                       u'Й': u'Y',
                       u'К': u'K',
                       u'Л': u'L',
                       u'М': u'M',
                       u'Н': u'N',
                       u'О': u'O',
                       u'П': u'P',
                       u'Р': u'R',
                       u'С': u'S',
                       u'Т': u'T',
                       u'У': u'U',
                       u'Ф': u'F',
                       u'Х': u'H',
                       u'Ц': u'Ts',
                       u'Ч': u'Ch',
                       u'Ш': u'Sh',
                       u'Щ': u'Sch',
                       u'Ъ': u'',
                       u'Ы': u'Y',
                       u'Ь': u'',
                       u'Э': u'E',
                       u'Ю': u'Yu',
                       u'Я': u'Ya',}

    lower_case_letters = {u'а': u'a',
                       u'б': u'b',
                       u'в': u'v',
                       u'г': u'g',
                       u'д': u'd',
                       u'е': u'e',
                       u'ё': u'e',
                       u'ж': u'zh',
                       u'з': u'z',
                       u'и': u'i',
                       u'й': u'y',
                       u'к': u'k',
                       u'л': u'l',
                       u'м': u'm',
                       u'н': u'n',
                       u'о': u'o',
                       u'п': u'p',
                       u'р': u'r',
                       u'с': u's',
                       u'т': u't',
                       u'у': u'u',
                       u'ф': u'f',
                       u'х': u'h',
                       u'ц': u'ts',
                       u'ч': u'ch',
                       u'ш': u'sh',
                       u'щ': u'sch',
                       u'ъ': u'',
                       u'ы': u'y',
                       u'ь': u'',
                       u'э': u'e',
                       u'ю': u'yu',
                       u'я': u'ya',}

    translit_string = ""

    for index, char in enumerate(string):
        if char in lower_case_letters.keys():
            char = lower_case_letters[char]
        elif char in capital_letters.keys():
            char = capital_letters[char]
            if len(string) > index+1:
                if string[index+1] not in lower_case_letters.keys():
                    char = char.upper()
            else:
                char = char.upper()
        translit_string += char

    return translit_string

#Запись в txt файл
def new_write(list_dict_abo, olt):
    if len(list_dict_abo) != 0:
        #список строк,которые сформируем заранее, но допишем после quit 
        tmp_list1 = []
        #Платы на станции GPON
        frame_0 = []
        frame_1 = []
        frame_2 = []
        frame_3 = []
        frame_4 = []
        number_frame = -1
        #Разносим записи абонентов по платам
        for i in list_dict_abo:
            if i.get("PORT")[0] == "0":
                frame_0.append(i)
            elif i.get("PORT")[0] == "1":
                frame_1.append(i)
            elif i.get("PORT")[0] == "2":
                frame_2.append(i)
            elif i.get("PORT")[0] == "3":
                frame_3.append(i)
            elif i.get("PORT")[0] == "4":
                frame_4.append(i)
        
        frame_full_list = [frame_0, frame_1, frame_2, frame_3, frame_4]
                
        with open(output_path + os.sep + olt + time.strftime('_%d_%m') + ".txt", "a+") as f_result:
            print("Идет запись файла: " + output_path + os.sep + olt + time.strftime('_%d_%m') + ".txt")
            #Наверное не оптимально вызывать много раз write, нужно будет потом как то оптимизировать
            for frame in frame_full_list:
                number_frame += 1
                if len(frame) != 0:
                    f_result.write(
                    f'{nl}{nl}{nl}interface gpon 0/{str(number_frame)}')
                    for i in frame:
                        f_result.write(
                        f'{nl}{nl}ont add {i.get("PORT")[2:]} '
                        f'sn-auth {i.get("SN")} omci ont-lineprofile-id {i.get("PROFILE")} '
                        f'ont-srvprofile-id {i.get("PROFILE")} desc {i.get("DESC")}{nl}'
                        )
                        if i["COUNT_NATIVE_VLAN"] > 0:
                            for c in range(i.get("COUNT_NATIVE_VLAN")):
                                f_result.write(f'{nl}ont port native-vlan {i.get("PORT")[2:]}'
                                f' XX eth {c+1} vlan {i.get("USER_VLAN")} priority 0'
                                )
                        tmp_list1.append(f'{nl}service-port vlan {i.get("SERVICE_PORT_VLAN")} '
                            f'gpon 0/{i.get("PORT")} ont XX gemport {i.get("GEMPORT")} multi-service user-vlan '
                            f'{i.get("USER_VLAN")} tag-transform default'
                            )        
                    f_result.write(f'{nl}{nl}quit{nl}')
                    for i in tmp_list1:
                        f_result.write(f'{i}{nl}')
                    tmp_list1.clear()

#######################################
#Установка директорий по умолчанию если никаких
#других путей нет
if args.diaf == None and args.do == None:
    if path_files == "":
        path_files = (os.path.dirname(os.path.abspath(__file__)) + os.sep)      

        if output_path == "":
            output_path = path_files
    if args.f == None:
        file = get_last_modified_file(path_files)


if args.diaf != None:
    if not os.path.exists(args.diaf):
        print('Выбранный каталог не доступен.Выполнение прервано...')
        quit()
    else:
        file = get_last_modified_file(args.diaf)
        if args.do == None:
            output_path = args.diaf

#######################################
#Чтение из json файла с данными
with open(file,encoding='utf-8') as file1:
    abo_list = json.load(file1)

#######################################
print("Файл источник:", file)
print('Каталог для записи:', output_path)
print('Считанные данные:')

#Заполнение доп данных на основе конфига на станции
for i in abo_list:
    ab_name = abo_convection(i["FIO"])
    ab_adress = adress_convection(i["ADRESS"])
    i['DESC'] = transliterate(ab_adress + "_" + ab_name + "_" + i.get("ONU") + "_" + i.get("TYPE_A"))
    if i["OLT"] == 'station0':
        i["SERVICE_PORT_VLAN"] = station0_vlans[i["PORT"]]
        station0.append(i)
    elif i["OLT"] == 'station1':
        i["SERVICE_PORT_VLAN"] = station1_vlans[i["PORT"]]
        station1.append(i)
    elif i["OLT"] == 'station2':
        i["SERVICE_PORT_VLAN"] = station2_vlans[i["PORT"]]
        station2.append(i)
    elif i["OLT"] == 'station3':
        i["SERVICE_PORT_VLAN"] = station3_vlans[i["PORT"]]
        station3.append(i)
    elif i["OLT"] == 'station4':
        i["SERVICE_PORT_VLAN"] = station4_vlans[i["PORT"]]
        station4.append(i)
    else:
        print("Невозможно назначить порт, проверьте данные")
        quit()
    if i["ONU"] == '6688':
        i["PROFILE"] = "8"
        i["COUNT_NATIVE_VLAN"] = 4
        i["USER_VLAN"] = "1000"
        i["GEMPORT"] = "1"
    if i["ONU"] == 'G84':
        i["PROFILE"] = "1"
        i["COUNT_NATIVE_VLAN"] = 4
        i["USER_VLAN"] = "300"
        i["GEMPORT"] = "0"
    if i["ONU"] == '6699' and i["TYPE_A"] == 'IPOE':
        i["PROFILE"] = "1"
        i["COUNT_NATIVE_VLAN"] = 4
        i["USER_VLAN"] = "300"
        i["GEMPORT"] = "0"
        i["SERVICE_PORT_VLAN"] = "4001"
    if i["ONU"] in defaults_onu and i["TYPE_A"] == 'PPPOE':
        i["PROFILE"] = "1"
        i["COUNT_NATIVE_VLAN"] = 0
        i["USER_VLAN"] = "300"
        i["GEMPORT"] = "0"
    if i["ONU"] == '8245' and i["TYPE_A"] == 'BRIDGE':
        i["PROFILE"] = "4"
        i["COUNT_NATIVE_VLAN"] = 0
        i["USER_VLAN"] = "400"
        i["GEMPORT"] = "2"
    if i["ONU"] == '8310':
        i["PROFILE"] = "6"
        i["COUNT_NATIVE_VLAN"] = 1
        i["USER_VLAN"] = "400"
        i["GEMPORT"] = "2"
        i["SERVICE_PORT_VLAN"] = "400"
        i["TYPE_A"] = 'BRIDGE'
    print(i)


new_write(station0, 'station0')
new_write(station1, 'station1')
new_write(station2, 'station2')
new_write(station3, 'station3')
new_write(station4, 'station4')
