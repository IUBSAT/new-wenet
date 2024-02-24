from multiprocessing import Process, Queue, Value
import PacketTX, sys, os, argparse
import time

callsign = "KD9ZSC"
image_range = range(1, 20)
debug_output = False
new_size = ["800x608"]

def capture_process(capture_queue):
    while True:
        for i in image_range:
            cmd = "libcamera-still --immediate -o new_images/%d.jpg" % i
            os.system(cmd)
            capture_queue.put(i)
            #time.sleep(1)  # Adjust sleep time based on capture frequency

def ssdv_process(capture_queue, encode_queue, encoded_set, transmitted_set, latest_image):
    while True:
        if not capture_queue.empty():
            image_num = capture_queue.get()
            if image_num > latest_image.value:
                encode_image(image_num)
                encode_queue.put(image_num)
                encoded_set.add(image_num)
                latest_image.value = image_num

def transmit_process(encode_queue, transmitted_set, latest_image):
    while True:
        if not encode_queue.empty():
            image_num = encode_queue.get()
            if image_num > latest_image.value and image_num not in transmitted_set:
                transmit_image(image_num)
                transmitted_set.add(image_num)

def encode_image(image_num):
    # Similar to your existing ssdv function
    #filename = "%d.jpg" % image_num
    os.system("cp new_images/%d.jpg new_images/%d_raw.jpg" % (image_num, image_num))
    # Build up our imagemagick 'convert' command line
    overlay_str = "convert new_images/%d.jpg -gamma 0.8 -font Helvetica -pointsize 40 -gravity North " % image_num
    overlay_str += "-strokewidth 2 -stroke '#000C' -annotate +0+5 \"%s\" " % "test"
    overlay_str += "-stroke none -fill white -annotate +0+5 \"%s\" " % "test"
	# Add on logo overlay argument if we have been given one.
    # if args.logo != "none":
    #     overlay_str += "%s -gravity SouthEast -composite " % args.logo

    overlay_str += "new_images/%d.jpg" % image_num

    #tx.transmit_text_message("Adding overlays to image.")
    os.system(overlay_str)
    for size in new_size:
        os.system(
            "convert new_images/%d.jpg -resize %s\! new_images/%d_%s.jpg" % (
                image_num, size, image_num, size))

    new_size.append("raw")

    for size in new_size:
        os.system(
            "ssdv -e -n -q 6 -c %s -i %d new_images/%d_%s.jpg new_images/%d_%s.bin" % (
                callsign, image_num, image_num, size, image_num, size))

def transmit_image(image_num):
    tx = PacketTX.PacketTX(debug=debug_output, serial_baud=args.baudrate)
    tx.start_tx()
    filename = f"new_images/{image_num}_800x608.bin"
    print("\nTXing: %s" % filename)
    transmit_file(filename, tx)
    tx.close()

def transmit_file(filename, tx_object):
    file_size = os.path.getsize(filename)
    if file_size % 256 > 0:
        print("File Size not a multiple of 256 bytes")
        return

    print("Transmitting %d Packets." % (file_size // 256))

    f = open(filename, 'rb')

    for x in range(file_size // 256):
        data = f.read(256)
        tx_object.tx_packet(data)

    f.close()
    print("Waiting for tx queue to empty...")
    tx_object.wait()

parser = argparse.ArgumentParser()
parser.add_argument("--baudrate", default=115200, type=int,
                    help="Transmitter baud rate. Defaults to 115200 baud.")
args = parser.parse_args()

if __name__ == "__main__":

    capture_queue = Queue()
    encode_queue = Queue()
    encoded_set = set()
    transmitted_set = set()
    latest_image = Value('i', 0)

    # Start the capture process
    capture_process = Process(target=capture_process, args=(capture_queue,))
    capture_process.start()

    # Start the ssdv process
    ssdv_process = Process(target=ssdv_process, args=(capture_queue, encode_queue, encoded_set, transmitted_set, latest_image))
    ssdv_process.start()

    # Start the transmit process
    transmit_process = Process(target=transmit_process, args=(encode_queue, transmitted_set, latest_image))
    transmit_process.start()

    try:
        capture_process.join()
        ssdv_process.join()
        transmit_process.join()
    except KeyboardInterrupt:
        print("Terminating processes...")
        capture_process.terminate()
        ssdv_process.terminate()
        transmit_process.terminate()
