import RPi.GPIO as GPIO
import random, time, csv
from math import trunc
from PIL import Image as ImagePIL
from picamera import PiCamera
from io import BytesIO
import __main__

# Initialization of image resolution parameters
width = 20
height = 20

# Initialization of communication pins
pin_clk = 2
pin_data = 3
pin_wr = 4
pin_chk_a = 17
pin_chk_b = 27
pin_done = 22

GPIO.setmode(GPIO.BCM)

GPIO.setup(pin_clk, GPIO.OUT)
GPIO.setup(pin_data, GPIO.OUT)
GPIO.setup(pin_wr, GPIO.OUT)
GPIO.setup(pin_chk_a, GPIO.IN)
GPIO.setup(pin_chk_b, GPIO.IN)
GPIO.setup(pin_done, GPIO.OUT)

# Defining lengths of each packet section, including the packet length
len_addr = 9
len_data = 7
len_decimal = 0
len_sign = 1
len_rs = 1

len_packet = len_rs + len_addr + len_sign + len_data + len_decimal
range_packet = range(len_packet)
val_dec = ""

for i in range(len_decimal):
    val_dec += "0"

val_weight_max = 127
val_weight_min = -128
val_weight_range = val_weight_max + abs(val_weight_min)

len_data_bias = 23
len_packet_bias = len_rs + len_addr + len_data_bias + len_sign + len_decimal
val_bias_max = 2 ** len_data_bias - 1
val_bias_min = - 2 ** len_data_bias

# Sensor initialization
camera = PiCamera()
camera.resolution = (40, 40) # would need to be changed in case of base resolution change
camera.color_effects = (128,128) # Making it grayscale

class Sendable:
    def __init__(self, data=None, addr=None, path=None):   
        if not hasattr(self, "data"):
            if data is None:
                data = None
            self.data = data
        if self.data is not None:
            self.get_data_param()
        
        if not hasattr(self, "addr"):
            if addr is None:
                addr = None
            self.addr = addr

        if not hasattr(self, "path"):
            if path is None:
                path = None
            self.path = path
            
        if self.addr is None:
            self.type_addr = "default"
        else:
            self.type_addr = "custom"

        self.avg = None
            
        if isinstance(self, Image):
            self.type_data = "image"
        elif isinstance(self, Bias):
            self.type_data = "bias"
        else:
            self.type_data = "default"
        self.addr_dict = {
        "default" : self.get_addr_def,
        "custom" : self.get_addr_custom
        }
        self.store_addr_dict = {
        "default" : self.get_send_def,
        "custom" : self.get_send_custom
        }

        self.i = 0

    def get_data_param(self):
        self.len = len(self.data)
        self.rang = range(self.len)

    def send(self):
        for self.i in self.rang:
            addr = self.addr_dict[self.type_addr]()
            data = self.get_data()
            message = self.rs + addr + data
            # print(f"len of message: {len(message)}")
            # print(f"rs: {self.rs} addr: {i} data: {self.data[i]} ")
            # print(f" Sending - Register: {self.rs} Address: {addr} Data: {data} Type: {self.type_data}")
            send_packet(message)

    def load(self, path=None):
        if path is None:
            path = self.path
        f = open(path, "r")
        reader = csv.reader(f, delimiter=",")
        ncol = len(next(reader))
        f.seek(0)
        self.data = []
        for row in reader:
            self.data.append(float(row[0]))
        if ncol > 1:
            for row in reader:  
                self.addr.append(int(row[1]))
        f.close()
        # super().__init__() ----> this used to be here!! but its probably okay to only call the get data param function, change if not!
        self.get_data_param()
        self.avg = None

    def store(self, path=None):
        if path is None:
            path = self.path
        f = open(path, "w")
        writer = csv.writer(f, delimiter=",")
        for self.i in self.rang:
            row = self.store_addr_dict[self.type_addr]()
            writer.writerow(row)
        f.close()

    def get_avg(self):
        if self.avg is None:
            self.avg = sum(self.data) / self.len
        try:
            return self.avg
        finally:
            pass

        self.preview_img.show()

    def get_send_def(self):
        ret = [self.data[self.i]]
        return ret

    def get_send_custom(self):
        return [self.data[self.i], self.addr[self.i]]

    def get_addr_def(self):
        return f"{self.i:0{len_addr}b}"

    def get_addr_custom(self):
        return f"{self.addr[self.i]:0{len_addr}b}"

    def get_data(self): #default data conversion method, called if object doesn't have its own specialised method under the same name
        return convert_gemba(convert_pregemba(round(self.data[self.i])))

    def get_data_dec(self): # old, unused, not gon be used again probably
        return convert_gemba_dec(self.data[self.i])

class Image(Sendable):
    def __init__(self, rs=None, addr=None, path=None):
        if rs is None:
            self.rs = "0"
        super().__init__(addr=addr, path=path)

    def capture(self):
        self.stream = BytesIO()
        camera.capture(self.stream, format="jpeg")
        self.image = ImagePIL.open(self.stream)
        self.scale() # scaling image because the cam is dumb

    def img_to_data(self):
        self.data = []
        for i in range(height):
            for j in range(width):
                coords = j, i
                self.data.append((self.image.getpixel(coords))[0] - 128) 

    def scale(self):
        self.image.thumbnail((width,height))

    def store_img(self, path=None):
        if path is None:
            path = self.path
        self.image.save(path)

    def get_data(self):
        return convert_gemba(convert_pregemba(self.data[self.i]))

class ImageCap(Image):
    def __init__(self, rs=None, addr=None, path=None):
        super().__init__(rs=rs, addr=addr, path=path)
        self.update()
        self.get_data_param()

    def update(self):
        self.capture()
        self.img_to_data()
        self.avg = None

# comment for future reference, it may be a better idea to make a big parent image class, to host both the capture and load types, but that is unnecessary atm
# nvm i did it
class ImageTraining(Image):
    def __init__(self, data=None, rs=None, addr=None, path=None, index=None, dir=None, metaname=None):
        if index is None:
            index = 0
        self.index = index
        if dir is None:
            dir = "training_storage"
        self.dir = dir
        if metaname is None:
            metaname = "metadata.csv"
        self.metaname = metaname
        self.get_max_index()
        super().__init__(rs=rs, addr=addr, path=path)

    def get_max_index(self, dir=None):
        if dir is None:
            dir = self.dir
        f = open((f"{dir}/{self.metaname}"), "r")
        reader = csv.reader(f)
        self.index_max = len(list(reader)) - 1
        # print(f"self.index_max: {self.index_max}")
        f.close()

    def load_next(self):
        self.load_train()
        self.increment_index_safe()

    def load(self):
        self.image = ImagePIL.open(self.path)
        #no scaling call!!! function assumes the loaded picture is going to be 20 x 20, may change? idk
        self.img_to_data()
        self.get_data_param()
        self.avg = None

    def load_train(self, dir=None):
        # print(f"index: {self.index}")
        if dir is None:
            dir = self.dir

        filepath = f"{dir}/{self.metaname}"
        imgname = f"img{str(self.index)}.jpg"
        self.path = f"{self.dir}/images/{imgname}"

        f = open(filepath, "r")
        reader = csv.reader(f)
        self.istarget = bool(int(list(reader)[self.index][0]))
        f.close()
        self.load()

    def load_custom(self, path):
        self.path = path
        self.load()

    def append_img(self, istarget=None, dir=None, loadpath=None):
        if dir is None:
            dir = self.dir
        if loadpath is None:
            camera.start_preview(fullscreen=False, window = (400, 200, 400, 400))
        while istarget is None:
            print("(You can KB interrupt program now)")
            a = input("Is captured image the target shape? (Y/N) ")
            if a.lower() == "y":
                istarget = True
            elif a.lower() == "n":
                istarget = False
            else:
                istarget = None
        if loadpath is None:
            self.capture()
            camera.stop_preview()
        else:
            self.load_custom(loadpath)
        
        self.index_append = self.index_max + 1 + self.index
        f = open((f"{dir}/{self.metaname}"), "a")
        writer = csv.writer(f)
        writer.writerow([str(int(istarget))])
        f.close()
        imgname = f"img{str(self.index_append)}.jpg"
        self.path = f"{dir}/images/{imgname}"
        self.store_img()
        self.increment_index()

    def reset_index(self):
        print("resetting index")
        self.index = 0

    def reset_index_append(self):
        self.index_append = 0

    def increment_index_safe(self):
        self.increment_index()
        if self.index > self.index_max:
            self.reset_index()

    def increment_index(self):
        self.index += 1

class Array(Sendable):
    def __init__(self, data=None, rs=None, addr=None, path=None):
        if rs is None:
            rs = "1"
        self.rs = rs
        super().__init__(data=data, addr=addr, path=path)

class Weight(Array):
    def __init__(self, data=None, addr=None, path=None, train_factor=None):
        if path is None:
            path = "weight_storage/weights.csv"
        if train_factor is None:
            train_factor = 0.1
        self.train_factor = train_factor
        super().__init__(data=data, rs="1", addr=addr, path=path)

    def modify(self, image, istarget_in, istarget_real):
        """diff_list = [image.get_avg(), None]"""
        for i in self.rang:
            pixel = image.data[i]
            """diff_list[1] = pixel
            diff_factor = 1 + (abs(max(diff_list) - min(diff_list)) / val_weight_range) / 2"""

            delta = self.train_factor * (istarget_real - istarget_in) * pixel

            self.data[i] = self.data[i] + delta

        dn_max = max(self.data)
        dn_min = min(self.data)
        # some funky stuff, be careful if you relook - dn_min made to reduce range to -127, but is on +1 because it reduces before absolute
        print("bruh")
        if dn_min < 0:
            dn_min += 1
        dn_min = abs(dn_min)
        dn_res = max(dn_max, dn_min)
        print(f"dn_res: {dn_res}")
        map_factor = dn_res / val_weight_max
        print(f"map_factor: {map_factor}")
        for i in self.rang: 
            self.data[i] = self.data[i] / map_factor
            if self.data[i] > val_weight_max:
                self.data[i] = val_weight_max
            elif self.data[i] < val_weight_min + 1:
                self.data[i] = val_weight_min + 1

    def create_preview(self):
        img_list = []
        for i in self.rang:
            pixel = convert_pregemba(round(self.data[i]))
            img_list.append((pixel,pixel,pixel))
        self.preview_img = ImagePIL.new("RGB", [20,20])
        self.preview_img.putdata(img_list)

    def store_preview(self, i):
        if not hasattr(self, "preview_img"):
            self.create_preview()
        self.preview_img.save(f"weight_storage/weight_previews/{i}.jpg")

    def show_preview(self):
        if not hasattr(self, "preview_img"):
            self.create_preview()
        self.preview_img.show()

class Bias(Sendable):
    def __init__(self, data=None, addr=None, path=None):
        if addr is None:
            addr = 400
        if data is None:
            data = None
        if path is None:
            path = "weight_storage/bias.csv"
        self.addr = [addr]
        self.rs = "1"
        self.data = [data]
        self.len = len(self.data)
        super().__init__(path=path)
    
    def get_data(self):
        return convert_dobi(round(self.data[self.i]))

def send_packet(message):
    # print("message: " + message) # debug
    for i in reversed(message):
        #  # debug
        # print("val:" + message[i]) # debug
        transmit(i)
    write()

def transmit(val):
    GPIO.output(pin_data, int(val))
    # print(GPIO.input(pin_data))
    GPIO.output(pin_clk, GPIO.HIGH)
    # time.sleep_ms(1); #debug
    GPIO.output(pin_clk, GPIO.LOW)
    #time.sleep_ms(100) #debug

def write():
    GPIO.output(pin_wr, GPIO.HIGH)
    # print("write pulse!") # debug
    # time.sleep_ms(1); # debug
    GPIO.output(pin_wr, GPIO.LOW)

def done():
    GPIO.output(pin_done, GPIO.HIGH)
    GPIO.output(pin_done, GPIO.LOW)

def convert_gemba_dec(val):

    return convert_gemba(val) + val_dec

def convert_dobi(val):
    if val > val_bias_max:
        val -= val_bias_max + 1
        sign = "0"
    else:
        sign = "1"
    val_bin = f"{val:0{len_data_bias}b}"
    return sign + val_bin

# Convert number value into appropriate binary format (sign + number)
def convert_gemba(val):
    if val > 127:
        val -= 128
        sign = "0"
    else:
        sign = "1"
    val_bin = f"{val:0{len_data}b}"
    return sign + val_bin

# not in use anymore
def convert_pregemba_img(val):
    return int(trunc(val/2))

def convert_pregemba(val):
    return val + 128

def float_gemba(val):
    dec = 0
    if not isinstance(val, float):
        val = float(str(val) + ".0")
    whole, dec = str(val).split(".")
    whole = int(whole)
    dec = int(dec)
    res = convert_gemba(whole) + "."
    for i in range(len_decimal):
        if dec == 0:
            break
        whole, dec = str(decimal_converter(dec) * 2).split(".")
        dec = int(dec)
        res += whole
    whole, dec = str(res).split(".")
    delta = range(len_decimal - len(dec))
    for i in delta:
        res += "0"
    res = res.replace(".", "")
    return res

def decimal_converter(val):
    while val > 1:
        val /= 10
    return val

def calculate(list1, list2, bias):
    c = 0
    res = False
    for i in range(len(list1)):
        c += round(list1[i]) * round(list2[i])
    # print(c)

    if c > bias:
        res = True
    else:
        res = False
    # print(f"CALCULATE RETURN: {res}")
    return res

def generate_list_zero():
    list_ret = []
    for i in range(width * height):
        list_ret.append(0)
    return list_ret

def generate_list_rng(min=None, max=None):
    if min is None:
        min = val_weight_min
    if max is None:
        max = val_weight_max
    list_ret = []
    for i in range(width * height):
        list_ret.append(random.randint(min, max))
    return list_ret

def get_state():
    state_0 = GPIO.input(pin_chk_a)
    state_1 = GPIO.input(pin_chk_b)
    return state_0, state_1

def print_result():
    a, b = get_state()
    if a and not b:
        print("result equal to bias") # equal
    elif not a and b:
        print("result greater than bias") # greater than bias
    elif a and b:
        print("result lesser than bias") # lesser than bias

def get_result():
    a, b = get_state()
    ret = False
    if not a and b:
        ret = True
    elif (a and b) or (a and not b):
        ret = False
    else:
        print("bruh")
    # print(f"FPGA RETURN: {ret}")
    return ret
