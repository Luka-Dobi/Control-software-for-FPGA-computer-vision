import SendLib as SL
import RPi.GPIO as GPIO
from SendLib import Sendable, Weight, Bias, Array, ImageCap, ImageTraining, done, generate_list_zero


weights = Weight()
weights.load()

img = ImageCap()
weights.show_preview()

GPIO.cleanup()
