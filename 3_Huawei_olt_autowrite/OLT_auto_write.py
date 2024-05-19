import telnetlib
import time
import re
import os
import copy
import winsound
import inline
import argparse

#Данный скрипт в автоматическом режиме (будет только запрос логина-пароля от GPON станции)
#прописывает абоненские терминалы на станции из файлов, сформированных скриптом из пункта 2
#этой репозитории.Скрипт PS1 нужен для автоматической зиписи работы скрипта на windows.

#Реальных ip тут нет
#Сопоставление ip и локации станции
station_dic = { 'station0' : '192.168.1.10',
            'station1' : '192.168.1.12',
            'station2' : '192.168.1.13',
            'station3' : '192.168.1.11',
            'station4' : '192.168.1.14'}
            
station_dic_reverse = { '192.168.1.10' : 'station0',
            '192.168.1.12' : 'station1',
            '192.168.1.13' : 'station2',
            '192.168.1.11' : 'station3',
            '192.168.1.14' : 'station4'}            


##RUN_KEY 
parser = argparse.ArgumentParser(description='Path to file')
parser.add_argument('--path', type=str)
args = parser.parse_args()

general_list_string = []
list_string = []
#Метод для замены стандартного ввода на *
hide_input = inline.input
sn_exists_list = []
#Переход на следующую строку
nl = '\n'
#Хранение ввода-вывода для дальнейшей записи в файл
if args.path == None:
    args.path = (os.path.dirname(os.path.abspath(__file__)) + os.sep + "txt")

#список файлов .txt, из которых будут взяты данные
def get_list_files(path1):

    list_tmp = []
    with os.scandir(path1) as listOfEntries:  
        for entry in listOfEntries:
            if entry.is_file() and ".txt" in str(entry.name):
                station = re.search(r'\w+[A-Z]', entry.name)
                if station[0] in station_dic:
                    list_tmp.append(os.sep + entry.name)
                    
    return list_tmp

#Считывание данных с файла
def open_file(path1, filename):
    list_string.clear()
    #Берем из заранее свормированного файла локацию станции
    #Одна и таже операция режет глаз, нужно придумать как сократить
    station = re.search(r'\w+[A-Z]', filename)
    #Преобразуем локацию в ip и заносим в список строк
    list_string.append(station_dic[station[0]])
    
    with open(path1 + filename) as file1:
        list_string.append("\n")
        list_string.append("enable\n")
        list_string.append("config\n")
        while True:
            # считываем строки
            line = file1.readline()
            if not line:
                break
            if len(line) > 1:
                list_string.append(line)
        #Сохранение конфигурации всегда должно быть последней командой
        list_string.append("save\n")
    #Добавляем список в общий список хранения
    general_list_string.append(copy.deepcopy(list_string))

#Вывод считанных данных
def print_data(list1):
    for i in list1:
        for string in i:
            print(string)


def connect_to_station(commands):
    #Первая строка всегда содержит ip адрес станции
    ONTID_list = []
    current_position_ONTID = -1
    formatted_i = ""
    SN_exist = False
    def authorization():
        result = ""
        #Попытка авторизоваться пока не получим приглашение
        #После 3х неудачных попыток станция сама разорвет соединение
        while "Huawei Integrated Access Software" not in str(result):
            result = telnet.read_very_eager().decode('ascii')
            time.sleep(2)
            if "User name:" in str(result):
                #Системное звуковое оповещение что нужно обратить внимание
                winsound.PlaySound('SystemQuestion', winsound.SND_ALIAS)
                login = input("LOGIN = ")
                telnet.write(login.encode('ascii'))
                telnet.write(b"\n")
                time.sleep(3)
                #Вместо символов при вводе будут *
                password = hide_input("PASSWORD = ", secret=True)
                telnet.write(password.encode('ascii'))
                telnet.write(b"\n")
                time.sleep(3)

    first_string = True
    for list1 in commands:
        for i in list1:
            #print("Текущая строка = " + i)
            if first_string:
                print("Подключение к станции " + i + " (" + station_dic_reverse[i] + ")")
                current_ip_station = i
                telnet = telnetlib.Telnet(i)
                #Обновляем переменные
                first_string = False
                current_position_ONTID = -1
                formatted_i = ""
                ONTID_list = []
                time.sleep(2)
                authorization()
                #print("Значение current_position_ONTID " + str(current_position_ONTID))
                continue
            if 'sn-auth' in i:
                SN_exist = False
                print(i)
                telnet.write(i.encode('ascii') + b"\n")
                time.sleep(2)
                #Обрезаем вывод до номера ONTID на станции
                telnet.read_until(b'ONTID :', timeout=5)
                time.sleep(2)
                ONTID_string = str(telnet.read_very_eager().decode('ascii'))
                print("Номер ONTID: ",ONTID_string)
                #Сохраняем цифры номера ONTID
                ONTID = re.search(r'\d+', ONTID_string)
                try:
                    print(ONTID_list.append(ONTID[0]))
                #Если SN прописать не удалось, то будет ошибка TypeError:
                except TypeError:
                    SN_exist = True
                    print("SN already exists")
                    sn_exists_list.append("SN " + i[18:35] + " не удалось прописать на станции " + station_dic_reverse.get(current_ip_station))
                    #Сформируем ONTID, который не даст прописать service-port и будет понятно почему
                    ONTID_list.append(str("---SN already exists--- "))
                continue
            if 'native-vlan' in i:
                if not SN_exist:
                    formatted_i = re.sub(r'XX', str(ONTID[0]), i)
                    #print(formatted_i)
                    telnet.write(formatted_i.encode('ascii') + b"\n")
                    time.sleep(2)
                    print(formatted_i)
                    hide_result = telnet.read_very_eager().decode('ascii')
                continue             
            if 'service-port' in i:
                #Потому что первый индекс позиции 0
                current_position_ONTID += 1
                #Меняем шаблон на реальное значение ONTID
                i = re.sub(r'XX', str(ONTID_list[current_position_ONTID]), i)
                telnet.write(i.encode('ascii') + b"\n")
                time.sleep(2)
                all_result = telnet.read_very_eager().decode('ascii')
                print(all_result)
                continue
            if 'save' in i:
                telnet.write(i.encode('ascii') + b"\n")
                time.sleep(3)       
                all_result = telnet.read_very_eager().decode('ascii')
                print(all_result)
                first_string = True
                continue
   
            telnet.write(i.encode('ascii'))
            time.sleep(3)       
            all_result = telnet.read_very_eager().decode('ascii')
            print(all_result)
            
         
list_files = get_list_files(args.path)
for i in list_files:
    print("Открытие файла " + args.path + i)
    open_file(args.path, i)

connect_to_station(general_list_string)
#Если были обнаруженны ошибки при записи на станции
if len(sn_exists_list) != 0:
    winsound.PlaySound('SystemQuestion', winsound.SND_ALIAS)
    for sn in sn_exists_list:
        #Заменяем возможные двойные пробелы
        sn = re.sub('  ', ' ', sn)
        print(sn)

time.sleep(6000)
