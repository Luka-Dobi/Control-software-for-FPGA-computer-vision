import SendLib as SL
import RPi.GPIO as GPIO
from SendLib import Sendable, Weight, Bias, Array, ImageCap, ImageTraining, done, generate_list_zero
import random

weights = Weight(data=SL.generate_list_zero())
weights.store()
