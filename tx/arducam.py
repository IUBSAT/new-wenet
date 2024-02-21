#import RPi.GPIO as gp
import os

#gp.setwarnings(False)
#gp.setmode(gp.BOARD)

#gp.setup(7, gp.OUT)
#gp.setup(11, gp.OUT)
#gp.setup(12, gp.OUT)


def main():
    
    capture(100)
    capture(101)

def capture(cam):
    cmd = "libcamera-still -o new_images/%d.jpg" % cam
    os.system(cmd)

if __name__ == "__main__":
    main()

    #gp.output(7, False)
    #gp.output(11, False)
    #gp.output(12, True)
