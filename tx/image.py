#!/usr/bin/env python

#Image Script
# 1. Capture Image
# 2. Compress/SSDV Image (compress_test_images.py) 
# 3. Transmit Image (tx_test_images.py)

import PacketTX, sys, os, argparse, glob

callsign = "KD9ZSC"

image_range = range(1,20)

debug_output = False

def main():
    for i in image_range:
        capture(i)
        ssdv(i)
        
        tx = PacketTX.PacketTX(debug=debug_output, serial_baud=args.baudrate)
        tx.start_tx()
        filename = "new_images/%d_800x608.bin" % i #_800x608
        print("\nTXing: %s" % filename)
        transmit_file(filename,tx)  
        tx.close()
        
def capture(image_num):
    cmd = "libcamera-still -o new_images/%d.jpg" % image_num
    os.system(cmd)

new_size =["800x608"]

def ssdv(image_num):
    os.system("cp new_images/%d.jpg new_images/%d_raw.jpg" % (image_num,image_num))
    for size in new_size:
	    os.system("convert new_images/%d.jpg -resize %s\! new_images/%d_%s.jpg" % (image_num,size,image_num,size))

    new_size.append("raw")

    for size in new_size:
        os.system("ssdv -e -n -q 6 -c %s -i %d new_images/%d_%s.jpg new_images/%d_%s.bin" % (callsign,image_num,image_num,size,image_num,size))

def transmit_file(filename, tx_object):
    file_size = os.path.getsize(filename)
    if file_size % 256 > 0:
        print("File Size not a multiple of 256 bytes")
        return

    print("Transmitting %d Packets." % (file_size//256))
    
    f = open(filename, 'rb')
    
    for x in range(file_size//256):
        data = f.read(256)
        tx_object.tx_packet(data)

    f.close()
    print("Waiting for tx queue to empty...")
    tx_object.wait() 

parser = argparse.ArgumentParser()
parser.add_argument("--baudrate", default=115200, type=int, help="Transmitter baud rate. Defaults to 115200 baud.")
args = parser.parse_args()

if __name__ == "__main__":
    main()
