import SendLib as SL
import RPi.GPIO as GPIO
from SendLib import Sendable, Weight, Bias, Array, ImageCap, ImageTraining, done, generate_list_zero

weights = Weight()
weights.load()

weights_old = Weight()
weights.load()

bias = Bias(data=0)
# bias.load()

img = ImageTraining()

weights.send()
bias.send()

try:
    while True:
        for j in range(img.index_max + 1): 
            img.load_next() 
            img.send()

            # state_cal = SL.calculate(img.data, weights.data, bias.data[0])
            state_ret = SL.get_result()

            if state_ret != img.istarget:
                weights.modify(img, istarget_in=state_ret, istarget_real=img.istarget)
                weights.send()
        
except KeyboardInterrupt:
    pass
finally:
    weights.store()
    if weights.data == weights_old.data:
        print("bruh wtf")
    weights.create_preview()
    weights.store_preview(0)
    weights.show_preview()
    GPIO.cleanup()
