import threading
import time
import sys

import RPi.GPIO as GPIO
import HX711_init_ as Loadcell

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

GPIO.setwarnings(False)

#firebase 연동코드
cred = credentials.Certificate("./sangsang1-7e2a7-firebase-adminsdk-ichn0-2bb9a41ce0.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

#전철마다 컬렉션이 달라짐
doc_ref1 = db.collection(u'train2').document(u'compartment1')
doc_ref2 = db.collection(u'train2').document(u'compartment2')
doc_ref3 = db.collection(u'train2').document(u'compartment3')

loadcell_dt_1         = 5
loadcell_sck_1        = 6
loadcell_dt_2         = 17
loadcell_sck_2        = 27
loadcell_dt_3         = 23
loadcell_sck_3        = 24

hx1 = Loadcell.HX711(loadcell_dt_1, loadcell_sck_1)
hx2 = Loadcell.HX711(loadcell_dt_2, loadcell_sck_2)
hx3 = Loadcell.HX711(loadcell_dt_3, loadcell_sck_3)

hx2.set_reading_format("MSB", "MSB")
hx1.set_reference_unit(-30)
hx1.reset()
hx1.tare()

hx2.set_reading_format("MSB", "MSB")
hx2.set_reference_unit(-21)
hx2.reset()
hx2.tare()

hx3.set_reading_format("MSB", "MSB")
hx3.set_reference_unit(-50)
hx3.reset()
hx3.tare()

def Round_Off(weight, get_weight):

	if weight-int(get_weight) < 0.5:
		weight = int(get_weight)
	else:
		weight = int(get_weight)+1

	return weight

def HX711_Run_1():

        #rising edge에서 측정하기 떄문에 up설정
	hx1.power_up()
	time.sleep(0.1)
	get_weight1 = hx1.get_weight(5)
	parameter1 = get_weight1

        #무게 소수점 반올림
	weight1 = Round_Off(parameter1, get_weight1)

        #rising edge에서 측정하기 떄문에 down설정-serial clock 만들기
	hx1.power_down()
	time.sleep(0.1)

	doc_ref1.set({
		u'weight' : str(weight1)
	})

	global timer1
	timer1 = threading.Timer(5, HX711_Run_1)
	timer1.deamon = True
	timer1.start()

def HX711_Run_2():

        #rising edge에서 측정하기 떄문에 up설정
	hx2.power_up()
	time.sleep(0.1)
	get_weight2 = hx2.get_weight(5)
	parameter2 = get_weight2

        #무게 소수점 반올림
	weight2 = Round_Off(parameter2, get_weight2)

        #rising edge에서 측정하기 떄문에 down설정-serial clock 만들기
	hx2.power_down()
	time.sleep(0.1)

	doc_ref2.set({
		u'weight' : str(weight2)
	})

	global timer2
	timer2 = threading.Timer(5, HX711_Run_2)
	timer2.deamon = True
	timer2.start()

def HX711_Run_3():

        #rising edge에서 측정하기 떄문에 up설정
	hx3.power_up()
	time.sleep(0.1)
	get_weight3 = hx3.get_weight(5)
	parameter3 = get_weight3

        #무게 소수점 반올림
	weight3 = Round_Off(parameter3, get_weight3)

        #rising edge에서 측정하기 떄문에 down설정-serial clock 만들기
	hx3.power_down()
	time.sleep(0.1)

	doc_ref3.set({
		u'weight' : str(weight3)
	})

	global timer3
	timer3 = threading.Timer(5, HX711_Run_3)
	timer3.deamon = True
	timer3.start()

count_start = 1

HX711_Run_1()
HX711_Run_2()
HX711_Run_3()

while True:
	try:
		if count_start == 1:
			print('system start now')
			time.sleep(0.3)
			count_start = 0

	except (KeyboardInterrupt, SystemExit):
		print("Bye")
		GPIO.cleanup()
		sys.exit()
