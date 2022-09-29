# Control-software-for-FPGA-computer-vision
A project made to interface with an FPGA wired for simple computer vision.

This project consists of a library, and a couple of scripts which utilize it. It's designed to be used with a Raspberry Pi connected to an FPGA and a Pi Camera Module. The library (SendLib) consists of classes and their respective methods, intended for easy use and interaction with the FPGA.

Some of the functions the library provides are:
- capturing images
- storing/opening images
- storing image metadata into a separate CSV file 
- formatting images into the correct data type for the FPGA 
- training the neural network by determining proper pixel weights
- storing/opening saved weights
- sending weights and image data to the FPGA in the proper format
- retrieving results from the FPGA

Utilizing these functions, it's possible to train a simple perceptron to recognize objects most similar to a target shape (in this case, a circle). This setup lets the Raspberry Pi capture, format and save training/live data, ultimately sending it to the FPGA, which performs all neural network related computing. The FPGA then returns the result through two check pins.

The FPGA side of this project was done on a Digilent Artix A7 100T FPGA development board.

The Raspberry Pi communicates with the FPGA through its GPIO pins, defined in SendLib.py using GPIO.BCM pin numbering:
- pin_clk = 2
- pin_data = 3
- pin_wr = 4
- pin_chk_a = 17
- pin_chk_b = 27
- pin_done = 22

Any returning data is read through pin_chk_a and pin_chk_b.
