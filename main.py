import SendLib as SL
import RPi.GPIO as GPIO
from SendLib import Sendable, Weight, Bias, Array, ImageCap, ImageTraining, done, generate_list_zero

weights = Weight()
weights.load()

a = 0
bias = Bias(data=0)
# bias.load()
# bias.send()

img = ImageCap()

weights.send()
print("sent weights")
SL.camera.start_preview(fullscreen=False, window = (400, 200, 400, 400))
try:
    while True:
        img.send()

        """state_ret = SL.get_result()
        state_cal = SL.calculate(img.data, weights.data, bias.data[0])
        if state_ret != state_cal:
            print("Return state does not match internally calculated result")
        print(f"state return: {state_ret}")"""

        img.update()

except KeyboardInterrupt:
    print(max(weights.data), min(weights.data))
    SL.camera.stop_preview()
    GPIO.cleanup()
