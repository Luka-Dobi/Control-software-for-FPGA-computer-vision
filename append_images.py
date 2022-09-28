import SendLib as SL
import RPi.GPIO as GPIO
from SendLib import Sendable, Weight, Bias, Array, ImageCap, ImageTraining, done, generate_list_zero

img = ImageTraining()

try:
    while True:
        img.append_img()
        
except KeyboardInterrupt:
    GPIO.cleanup()
