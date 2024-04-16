import telnetlib
import time
import re
import os
import winsound
import inline
import argparse

#Реальных данных здесь нет

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



onu_data = { 'FRAME' : 'NULL',
             'SLOT' : 'NULL',
             'PORT' : 'NULL',
             'INDEX' : 'NULL',
             'VPI' : 'NULL'}
##RUN_KEY 
parser = argparse.ArgumentParser(description='Path to file')
parser.add_argument('--path', type=str)
args = parser.parse_args()

#Если не указать файл с данными, будем искать его в папке со скриптом
if args.path == None:
    data_file = (os.path.dirname(os.path.abspath(__file__)) + os.sep + \
    "ONU_FOR_AUTO_DELETE.txt")
else:
    data_file = args.path

print("Файл данных " + data_file)

list_string, commands_list, report  = [], [], []
hide_input = inline.input
open_session = False
what_to_do, check, last_delete_choise, current_olt = "", "", "", ""
status_of_the_delete = ["Удален успешно", "Отменен", "Не найден"]
not_ask_confirmation_mode = 0

#Информируем о способе логгирования если нужно
if os.name == "nt":
    print("Для сохраниния лог файла рекомендуется использовать PowerShell (команда Start-Transcript)")
else:
    print("Для сохраниния лог файла рекомендуется использовать программу tee")

#Считывание данных с файла
def open_file():
    list_string.clear()
    #Берем из заранее сформированного файла данные
    
    try:
        with open(data_file,encoding='utf-8') as file1:
            list_string.append("\n")

            while True:
                # считываем строки
                line = file1.readline()
                if not line:
                    list_string.append("save")
                    list_string.append("\n")
                    list_string.append("\n")
                    break
                if len(line) > 1:
                    #Удаление скрытых символов и пробелов
                    line = re.sub('[\t\r\n\s]', '', line)
                    #Если строка содержит только буквы,значит это название станции
                    #Срез до 4 символа для того чтобы можно было проверить строку "AZOV_DACHI"
                    if line[:3].isalpha():
                        list_string.append(station_dic[line])
                        list_string.append("enable")
                        list_string.append("config")
                    elif ":" and "#" not in line:
                        list_string.append(line)
                    else:
                        pass
    except FileNotFoundError:
        print("Ошибка, файл не найден " + args.path)
        exit

#Вывод считанных данных
def print_data(list1):
    for i in list1:
        print(i)

           
def connect_to_station():
    global open_session
    global what_to_do
    global check
    global last_delete_choise
    global not_ask_confirmation_mode
    
    def get_data_onu(text):
        commands_list.clear()
        index_slice_onu = text.find(":")
        onu_data['VPI'] = text[(index_slice_onu + 1):]
        text1 = text[:index_slice_onu]
        text_splitting = text1.split("/")
        onu_data['FRAME'] = text_splitting[0]
        onu_data['SLOT'] = text_splitting[1]
        onu_data['PORT'] = text_splitting[2]
        commands_list.append("interface gpon " + onu_data.get("FRAME") + "/" + onu_data.get("SLOT"))
        commands_list.append("display ont info " + onu_data.get("PORT") + " " + onu_data.get("VPI"))
        commands_list.append("Q")
        commands_list.append("quit")
        commands_list.append("display service-port port " + text1 + " ont " + onu_data.get("VPI"))
        commands_list.append("ont delete " + onu_data.get("PORT") + " " + onu_data.get("VPI"))
    
    #Первая строка всегда содержит ip адрес станции
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
    
    def delete_onu(onu):
        #Удаление сервис порта и затем самой записи
        commands_list.append("undo service-port " + onu_data.get("INDEX"))
        telnet.write(commands_list[6].encode('ascii') + b"\n")
        time.sleep(1)
        telnet.write(commands_list[0].encode('ascii') + b"\n")
        time.sleep(1)
        telnet.write(commands_list[5].encode('ascii') + b"\n")
        time.sleep(1)
        telnet.write("quit".encode('ascii') + b"\n")
        time.sleep(1)
        all_result = telnet.read_very_eager().decode('ascii')
        if "success" in all_result:
            report.append(current_olt + " " + onu + " " + status_of_the_delete[0])
        print(all_result)
                
    for i in list_string:
        index = ""
        check = ""
        i = i.strip()
        if "." in i:
            if open_session:
                telnet.write(commands_list[3].encode('ascii') + b"\n")
                time.sleep(1)
                #Нужно анализировать последнее подтверждение чтобы попасть командной save
                if last_delete_choise == "n":
                    telnet.write("save".encode('ascii') + b"\n")
                    time.sleep(1)
                    last_delete_choise = ""
                else:
                    telnet.write("quit".encode('ascii') + b"\n")
                    time.sleep(1)
                    telnet.write("save".encode('ascii') + b"\n")
                    time.sleep(1)
                    telnet.write(b"\n")
                    time.sleep(2)
                    all_result = telnet.read_very_eager().decode('ascii')
                    print(all_result)
                    last_delete_choise = ""
                telnet.write(b"\n")
                time.sleep(1)
                all_result = telnet.read_very_eager().decode('ascii')
                print(all_result)
                time.sleep(3)
                telnet.close()
                time.sleep(2)
                telnet = telnetlib.Telnet(i)
                print("Подключение к станции " + i + " (" + station_dic_reverse[i] + ")")
                current_olt = station_dic_reverse.get(i)
                time.sleep(2)
                authorization()
                result = telnet.read_very_eager().decode('ascii')
                print(result)
                continue
            else:
                telnet = telnetlib.Telnet(i)
                print("Подключение к станции " + i + " (" + station_dic_reverse[i] + ")")
                current_olt = station_dic_reverse.get(i)
                time.sleep(2)
                authorization()
                open_session = True
                result = telnet.read_very_eager().decode('ascii')
                print(result)
                continue
        if ":" and "0/" in i:
            get_data_onu(i)
            print("ВЫПОЛНЯЕТСЯ УДАЛЕНИЕ ЗАПИСИ " + i)
            telnet.write(commands_list[0].encode('ascii') + b"\n")
            time.sleep(1)
            telnet.write(commands_list[1].encode('ascii') + b"\n")
            time.sleep(1)
            result = telnet.read_very_eager().decode('ascii')
            print(result)
            #В правильном ответе всегда будет --
            if "--" in result:
                telnet.write(commands_list[2].encode('ascii') + b"\n")
                time.sleep(1)
                all_result = telnet.read_very_eager().decode('ascii')
                print(all_result)
                telnet.write(commands_list[3].encode('ascii') + b"\n")
                time.sleep(1)
                telnet.write(commands_list[4].encode('ascii') + b"\n")
                time.sleep(1)
                telnet.write(b"\n")
                time.sleep(1)
                telnet.write(b"\n")
                time.sleep(1)
                all_result = telnet.read_very_eager().decode('ascii')
                if "Failure: No service" in all_result:
                    #Значит будем удалять без сервис порта
                    print("INDEX не найден!")
                    onu_data['INDEX'] = "NULL"
                    delete_onu(i)
                print(all_result)
                telnet.write(commands_list[4].encode('ascii') + b"\n")
                time.sleep(1)
                telnet.write(b"\n")
                time.sleep(1)
                #За символами PARA идет номер записи
                telnet.read_until(b'PARA', timeout=5)
                flow_list = str(telnet.read_very_eager().decode('ascii'))
                try:  
                    #Получаем index записи
                    index = re.search(r'\d+', flow_list)
                    print("INDEX = " + index[0])
                    onu_data['INDEX'] = index[0]
                    while check not in ["y", "n"] and not_ask_confirmation_mode == 0:
                        print("Проверьте INDEX и подтвердите удаление данной ONU. y/n")
                        check = input()
                        #Если yy то удаляем без подвтерждения только тех кто неонлайн
                        if check == "yy":
                            not_ask_confirmation_mode = 1
                        #Если yyy то удаляем без подвтерждения всех
                        elif check == "yyy":
                            not_ask_confirmation_mode = 2
                        last_delete_choise = "n"
                    if check == "y" or not_ask_confirmation_mode > 0:
                        if "up" in flow_list:
                            #Если запись онлайн, обращаем на это внимание
                            print("ВНИМАНИЕ! ONU " + i + " ONLINE!")
                            winsound.PlaySound('SystemQuestion', winsound.SND_ALIAS)
                            while not_ask_confirmation_mode <=1 and what_to_do not in ["y", "n"] :
                                print("Вы точно хотите удалить данную ONU в состоянии ONLINE? y/n")
                                what_to_do = input()
                            if what_to_do == "y" or not_ask_confirmation_mode == 2:
                                delete_onu(i)
                                what_to_do = ""
                                last_delete_choise = "y"
                                continue
                            elif what_to_do == "n":
                                print("Удаление ONU " + i + " отмененно")
                                what_to_do = ""
                                last_delete_choise = "n"
                                report.append(current_olt + " " + i + " " + status_of_the_delete[1])
                                continue

                        delete_onu(i)    
                        continue
                    elif check == "n":
                        print("Удаление отмененно!")
                        report.append(current_olt + " " + i + " " + status_of_the_delete[1])
                        continue
                #Чтобы не падать в ошибку когда запись без сервис порта    
                except TypeError:
                    pass
            else:
                print("Данная запись не найденна, операция удаления отмененна...")
                print("Переход к следующей записи...")
                report.append(current_olt + " " + i + " " + status_of_the_delete[2])
                telnet.write(commands_list[3].encode('ascii') + b"\n")
                time.sleep(1)
                continue
        #Возвращение шаблона к первоночальному виду
        for key,value in onu_data.items():
            onu_data[key] = 'NULL'
            continue
        #Не помню зачем, можно будет удалить
        try:
            telnet.write(i.encode('ascii') + b"\n")
            time.sleep(2)
            all_result = telnet.read_very_eager().decode('ascii')
            if "Check whether system data has been changed" in all_result:
                print("Зашло в Check whether system data has been changed")
                telnet.write("save".encode('ascii') + b"\n")
                time.sleep(2)
                telnet.write(b"\n")
                time.sleep(2)
            print(all_result)
            all_result = telnet.read_very_eager().decode('ascii')
            print(all_result)
        except UnboundLocalError:
            pass

open_file()
#print_data(list_string)
connect_to_station()
for i in report:
    if "Не найден" in i:
        #Цвет фона красный
        print("\033[41m{}".format(i))
    elif "Отменен" in i:
        #Цвет фона берюзовый
        print("\033[46m{}".format(i))
    else:
        print(i)

