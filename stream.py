from roboflow import Roboflow
from picamera2 import Picamera2
import time
import cv2
import inference
import RPi.GPIO as GPIO
from time import sleep
import shutil

#load model
model = inference.get_roboflow_model("cockam/2")

#variables
mod_confidence = 0.4
mod_overlap = 0.4
max_light = 30
light_freq = 10000
fast_thres = 25000
const_x = 1286/30
const_y = 972/30

#setup picameraw
picam2 = Picamera2()
camera_config = picam2.create_still_configuration()
picam2.configure(camera_config)
picam2.start()
time.sleep(1)

#setup LED & servo
pinA = 11
pinB = 22
ledpin = 12				# PWM pin connected to LED
GPIO.setwarnings(False)			#disable warnings
GPIO.setmode(GPIO.BOARD)		#set pin numbering system
GPIO.setup(ledpin,GPIO.OUT)
pi_pwm = GPIO.PWM(ledpin, light_freq)		#create PWM instance with frequency
pi_pwm.start(0)				#start PWM of required Duty Cycle 

GPIO.setup(11,GPIO.OUT)
GPIO.setup(22,GPIO.OUT)  # Sets up pin 11 to an output (instead of an input)
p = GPIO.PWM(11, 50)     # Sets up pin 11 as a PWM pin
p.start(7.5)  
q = GPIO.PWM(22, 50)
q.start(7.5)
time.sleep(1)
p.ChangeDutyCycle(0)
q.ChangeDutyCycle(0)
time.sleep(1)
coor_x = []
coor_y = []
num_detected = 0

while True:
    #capture image
    array = picam2.capture_array("main")

    #save img as .jpg
    cv2.imwrite('image.jpg', cv2.cvtColor(array, cv2.COLOR_RGB2BGR))

    input = "image.jpg"

    #prediction
    data = model.infer(image=input, confidence = mod_confidence, overlap = mod_overlap)


    if len(data[0].predictions)>0:
        coor_x.append(data[0].predictions[0].x)
        coor_y.append(data[0].predictions[0].y)
        print(num_detected, coor_x[-1], coor_y[-1])

        shutil.copyfile(input, "detected/{}.jpg".format(num_detected))
        num_detected += 1

        #change direction
        thetax = 90 - (coor_x[-1] - 1286)/const_x
        thetay = 90 - (coor_y[-1] - 1286)/const_y
        dutyx = 2.5 + (10 * thetax / 180)
        dutyy = 2.5 + (10 * thetay / 180)

        if dutyx > 9:
           dutyx = 9
        if dutyx < 6:
            dutyx = 6

        if dutyy > 9:
           dutyy = 9
        if dutyy < 6:
            dutyy = 6
            
        p.ChangeDutyCycle(dutyx)
        q.ChangeDutyCycle(dutyy)

        #turn on light
        pi_pwm.ChangeDutyCycle(max_light)
        sleep(0.01)
        if len(coor_x)> 1: 
            movement = (coor_x[-1]-coor_x[-2])**2 + (coor_y[-1]-coor_y[-2])**2
            if movement > fast_thres:
                pi_pwm.ChangeDutyCycle(100)
                sleep(0.01)
                print('fast!')
            else:
                print('no movement detected')

        time.sleep(1)
        p.ChangeDutyCycle(0)
        q.ChangeDutyCycle(0)
        time.sleep(1)
    else:
        pi_pwm.ChangeDutyCycle(0)
        sleep(0.01)
        print('no cockroach detected!')