import telnetlib
import time
import json
import argparse
import re

#Данные для подключения
station_data = {}

#06 Ве ок, только причесать

onu_data = { 'FRAME' : 'NULL',
             'SLOT' : 'NULL',
             'PORT' : 'NULL',
             'INDEX' : 'NULL',
             'VPI' : 'NULL'}

##RUN_KEY 
parser = argparse.ArgumentParser(description='Path to onu and times')
parser.add_argument('--onu', type=str)
parser.add_argument('--time', type=int)
args = parser.parse_args()

onu = args.onu
#Проверяем что пусть к онушке имеет вид 0/1/2:33
match = re.fullmatch(r'0/\d/\d+:\d+', onu)

if match == None:
    print("Интерфейс onu введен некорректно")
    exit()

#Устанавливаем таймер, в ключе мы указываем минуты
#поэтому умножаем на 60
stop_time = time.time() + (args.time * 60)
signal_list = []
#Посчет кол-во повторов заросов
request_times = 0
#Если вдруг во время опроса онушка отвалилась, мы это тоже запомним
count_offline = 0

#Разделяем пусть на нужные части
index_slice_onu = onu.find(":")
onu_data['VPI'] = onu[(index_slice_onu + 1):]
text1 = onu[:index_slice_onu]
text_splitting = text1.split("/")
onu_data['FRAME'] = text_splitting[0]
onu_data['SLOT'] = text_splitting[1]
onu_data['PORT'] = text_splitting[2]

#Формируме команды для отправки в телнет
interface = ("interface gpon " + onu_data.get("FRAME") + "/" + onu_data.get("SLOT"))
request = ("display ont optical-info " + onu_data.get("PORT") + " " + onu_data.get("VPI"))

#Загружаем логин пароль и ip станции
with open("connect_data.json",encoding='utf-8') as file1:
    station_data = json.load(file1)
		
telnet = telnetlib.Telnet(station_data.get('ip'))

result = ""
#Попытка авторизоваться пока не получим приглашение
#После 3х неудачных попыток станция сама разорвет соединение
while "Huawei Integrated Access Software" not in str(result):
    result = telnet.read_very_eager().decode('ascii')
    time.sleep(2)
    if "User name:" in str(result):
        telnet.write(station_data.get('login').encode('ascii'))
        telnet.write(b"\n")
        time.sleep(3)
        telnet.write(station_data.get('password').encode('ascii'))
        telnet.write(b"\n")
        time.sleep(3)

telnet.write("enable".encode('ascii') + b"\n")
time.sleep(2)
telnet.write("config".encode('ascii') + b"\n")
time.sleep(2)
telnet.write(interface.encode('ascii') + b"\n")

while stop_time > time.time():
    request_times += 1
    time.sleep(2)
    telnet.write(request.encode('ascii') + b"\n")
    time.sleep(2)
    telnet.write("Q".encode('ascii') + b"\n")
    time.sleep(2)
    #all_result = telnet.read_very_eager().decode('ascii')
    #Отрезаем ненужную часть вывода
    all_result = telnet.read_until(b'Rx optical power(dBm)                  :', timeout=5)
    time.sleep(2)
    output = str(telnet.read_very_eager().decode('ascii'))
   
    RX = re.search(r'\s*-?\d+\.\d+', output)
    #print(float(RX[0].strip()))
    try:
        float_RX = float(RX[0].strip())
        signal_list.append(float_RX)
    except ValueError:
        print("Не удалось снять сигнал")
        count_offline += 1

print("Опрошен интерфейс "+onu+" станции "+station_data.get("ip"))
print("Опрошенно: " + str(request_times) + " раз(а)")
print("Неудачных опросов: " + str(count_offline) + " раз(а)")
print("Опрошенно нормальных сигналов: "+ str(len(list(filter(lambda x: x > -27, signal_list)))) + " шт.")
print("Опрошенно слабых сигналов: "+ str(len(list(filter(lambda x: x < -27, signal_list)))) + " шт.")
print("Минимальный сигнал: " + str(min(signal_list)) + " db")
print("Максимальный сигнал: " + str(max(signal_list)) + " db")
#print(signal_list)
