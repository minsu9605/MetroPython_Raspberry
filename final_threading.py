import time
import sys
import threading

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

import matplotlib.pyplot as plt
import matplotlib.image as img
import matplotlib.font_manager as fm

import RPi.GPIO as GPIO
import LCD_init_ as LCD
import HX711_init_ as Loadcell
import ADS1015_init_ as ADC

#matplotlib 한글폰트 설정
plt.rcParams['axes.unicode_minus'] = False
fm.get_fontconfig_fonts()
font_path = "/usr/share/fonts/truetype/nanum/NanumGothicCoding.ttf"
font_prop = fm.FontProperties(fname=font_path)

#firebase 연동코드
cred = credentials.Certificate("./sangsang1-7e2a7-firebase-adminsdk-ichn0-2bb9a41ce0.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

#전철마다 컬렉션이 달라짐(메인: 1, 서브: 2)
doc_ref1 = db.collection(u'train1').document(u'compartment1')
doc_ref2 = db.collection(u'train1').document(u'compartment2')
doc_ref3 = db.collection(u'train1').document(u'compartment3')

#LCD1602 연결 핀 번호
lcd_rs        = 19
lcd_en        = 26
lcd_d4        = 12
lcd_d5        = 16
lcd_d6        = 20
lcd_d7        = 21

#LCD1602 표시 칸
lcd_columns = 16
lcd_rows    = 2

#HX711 연결 핀 번호
loadcell_dt        = 5
loadcell_sck        = 6

#각 모듈애 멎눈 값으로 객체생성
lcd = LCD.CharLCD(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6, lcd_d7,
                        lcd_columns, lcd_rows)
hx = Loadcell.HX711(loadcell_dt, loadcell_sck)
adc = ADC.ADS1015()

hx.set_reading_format("MSB", "MSB")
hx.set_reference_unit(-39)	#1g당 reference 값은 약 -39
hx.reset()
hx.tare()

#GAIN값에 따라 측정전압이 틀려짐
GAIN = 8

count_start = 1 #시스템 시작 카운트
count = 0       #첫번째 칸 이미지 카운트
count1 = 0      #두번째 칸 이미지 카운트
count2 = 0      #세번째 칸 이미지 카운트

#무게 초기값은 0
weight_1 = 0
weight_2 = 0
weight_3 = 0

#이미지 가져오기
image1 = img.imread('/home/pi/Desktop/project/picture/first_bad.jpg')
image2 = img.imread('/home/pi/Desktop/project/picture/first_good.jpg')
image3 = img.imread('/home/pi/Desktop/project/picture/first_normal.jpg')
image4 = img.imread('/home/pi/Desktop/project/picture/second_bad.jpg')
image5 = img.imread('/home/pi/Desktop/project/picture/second_good.jpg')
image6 = img.imread('/home/pi/Desktop/project/picture/second_normal.jpg')
image7 = img.imread('/home/pi/Desktop/project/picture/third_bad.jpg')
image8 = img.imread('/home/pi/Desktop/project/picture/third_good.jpg')
image9 = img.imread('/home/pi/Desktop/project/picture/third_normal.jpg')

def HX711_Run():

        #rising edge에서 측정하기 떄문에 up설정
	hx.power_up()
	get_weight = hx.get_weight(3)
	weight = get_weight

	#무게 소수점 반올림
	if weight-int(get_weight) < 0.5:
		weight = int(get_weight)
	else:
		weight = int(get_weight)+1

	#rising edge에서 측정하기 떄문에 down설정-serial clock 만들기
	hx.power_down()
	time.sleep(0.1)
	return weight

def ADS1015_Run():
	values = [0]*4		#압력센서 4개 측정을 위해 크기4 배열생성
	for i in range(4):
		values[i] = adc.read_adc(i, gain=GAIN)
	time.sleep(0.1)
	return values

def LCD1602_Run():
	try:
		check = 0
		m_values = ADS1015_Run()

		#측전전압 기준에 미도달시 자리체크, 측정전압기준을 넘어서면 다른 압력센서에 영향을 주기 때문에 오차범위 설정
		for i in range(4):
			if m_values[i] <= 200:
				check +=1
		lcd.clear()
		time.sleep(0.1)
		lcd.message('empty seat: '+str(check))

		#LCD표시(압력센서 감지)는 스레드로 실행
		timer = threading.Timer(2, LCD1602_Run)
		timer.deamon = True
		timer.start()

	except (KeyboardInterrupt, SystemExit):
		lcd.clear()

def Firebase_upload():
	#해당 칸만 무게값 업로드
	doc_ref1.set({
		u'weight' : str(HX711_Run())
	})

def Display():

	global weight_1
	global weight_2
	global weight_3
	global count
	global count1
	global count2

	#Firebase 값 불러오기
	doc1 = doc_ref1.get()
	doc2 = doc_ref2.get()
	doc3 = doc_ref3.get()
	plt.suptitle("현재 위치 : 1량", fontsize = 40, fontproperties=font_prop)

	#matplotlib로 이미지 변화 나타내기
	#첫번째 칸
	if weight_1 < 200:
		#파이어베이스에서 다운된 딕셔러니자료를 int형으로 변환
		dict1 = doc1.to_dict()
		weight_1 = int(dict1['weight'])

		if count == 1:
			ax[0].cla()		#이미지 초기화
			ax[0].imshow(image2)	#이미지 표시
			plt.show(block=False)	#창을 닫지 않아도 plot업데이트 가능

		if (weight_1 >= 200 and weight_1 < 370):
			ax[0].cla()
			ax[0].imshow(image3)

		elif weight_1 >= 370:
			ax[0].cla()
			ax[0].imshow(image1)

		ax[0].axis('off')   #좌표축 숨기기
		plt.show(block=False)

	elif (weight_1 >= 200 and weight_1 < 370):
		dict1 = doc1.to_dict()
		weight_1 = int(dict1['weight'])

		if count1 == 1:
			ax[0].cla()
			ax[0].imshow(image3)

		if weight_1 < 200:
			ax[0].cla()
			ax[0].imshow(image2)

		elif weight_1 >= 370:
			ax[0].cla()
			ax[0].imshow(image1)

		ax[0].axis('off')
		plt.show(block=False)

	elif weight_1 >= 370:
		dict1 = doc1.to_dict()
		weight_1 = int(dict1['weight'])

		if count2 == 1:
			ax[0].cla()
			ax[0].imshow(image1)

		if weight_1 < 200:
			ax[0].cla()
			ax[0].imshow(image2)

		elif (weight_1 >= 200 and weight_1 < 370):
			ax[0].cla()
			ax[0].imshow(image3)

		ax[0].axis('off')
		plt.show(block=False)

	#두번째 칸
	if weight_2 < 200:
		dict2 = doc2.to_dict()
		weight_2 = int(dict2['weight'])

		if count == 1:
			ax[1].cla()
			ax[1].imshow(image5)
			plt.show(block=False)

		if (weight_2 >= 200 and weight_2 < 370):
			ax[1].cla()
			ax[1].imshow(image6)

		elif weight_2 >= 370:
			ax[1].cla()
			ax[1].imshow(image4)

		ax[1].axis('off')
		plt.show(block=False)

	elif (weight_2 >= 200 and weight_2 < 370):
		dict2 = doc2.to_dict()
		weight_2 = int(dict2['weight'])

		if count1 == 1:
			ax[1].cla()
			ax[1].imshow(image6)
			plt.show(block=False)

		if weight_2 < 200:
			ax[1].cla()
			ax[1].imshow(image5)

		elif weight_2 >= 370:
			ax[1].cla()
			ax[1].imshow(image4)

		ax[1].axis('off')
		plt.show(block=False)

	elif weight_2 >= 370:
		dict2 = doc2.to_dict()
		weight_2 = int(dict2['weight'])

		if count2 == 1:
			ax[1].cla()
			ax[1].imshow(image4)
			plt.show(block=False)

		if weight_2 < 200:
			ax[1].cla()
			ax[1].imshow(image5)

		elif (weight_2 >= 200 and weight_2 < 370):
			ax[1].cla()
			ax[1].imshow(image6)

		ax[1].axis('off')
		plt.show(block=False)

	#세번째 칸
	if weight_3 < 3:
		dict3 = doc3.to_dict()
		weight_3 = int(dict3['weight'])

		if count == 1:
			ax[2].cla()
			ax[2].imshow(image8)
			plt.show(block=False)

		if (weight_3 >= 3 and weight_3 < 6):
			ax[2].cla()
			ax[2].imshow(image9)

		elif weight_3 >= 6:
			ax[2].cla()
			ax[2].imshow(image7)

		ax[2].axis('off')
		plt.show(block=False)

	elif (weight_3 >= 3 and weight_3 < 6):
		dict3 = doc3.to_dict()
		weight_3 = int(dict3['weight'])

		if count1 == 1:
			ax[2].cla()
			ax[2].imshow(image9)
			plt.show(block=False)

		if weight_3 < 3:
			ax[2].cla()
			ax[2].imshow(image8)

		elif weight_3 >= 6:
			ax[2].cla()
			ax[2].imshow(image7)

		ax[2].axis('off')
		plt.show(block=False)

	elif weight_3 >= 6:
		dict3 = doc3.to_dict()
		weight_3 = int(dict3['weight'])

		if count2 == 1:
			ax[2].cla()
			ax[2].imshow(image7)
			plt.show(block=False)

		if weight_3 < 3:
			ax[2].cla()
			ax[2].imshow(image8)

		elif (weight_3 >= 3 and weight_3 < 6):
			ax[2].cla()
			ax[2].imshow(image9)

		ax[2].axis('off')
		plt.show(block=False)

	#GUI 유지
	#show()의 인자 block=False가 없이 쓰이면 새창으로 이미지를 보여준다.
	plt.pause(10)
	count = 1      #첫번째 칸 이미지 카운트
	count1 = 1      #두번째 칸 이미지 카운트
	count2 = 1      #세번째 칸 이미지 카운트

#첫 화면제어
fig,ax = plt.subplots(1,3)  #matplotlib 객체지향 인터페이스로 한 화면에 여러 plot나타내기
ax[0].imshow(image2)
ax[1].imshow(image5)
ax[2].imshow(image8)
plt.show(block=False)

LCD1602_Run()	#스레드 반복실행으로 한번만 실행

while True:
	try:
		if count_start==1:
			print('system start now')
			time.sleep(0.3)
			count_start = 0

		Firebase_upload()
		Display()

	except (KeyboardInterrupt, SystemExit):
		plt.close()
		lcd.clear()
		GPIO.cleanup()
		print("Clear!!")
		sys.exit()
