from multiprocessing import Process, Queue, Value, Manager, Event
import PacketTX, sys, os, argparse, glob
import time

callsign = "KD9ZSC"
#image_range = range(1, 20)
debug_output = False
new_size = ["800x608"]

def capture_process(capture_list):
    i = 1
    while True:
        #for i in image_range:
            cmd = "libcamera-still --immediate -o tx_images/%d.jpg" % i
            os.system(cmd)
            capture_list.append(i)
            i += 1
            time.sleep(1.0)  # Adjust sleep time based on capture frequency

def ssdv_process(capture_list, encode_list, encoded_set, last_encoded):
    while True:
        if capture_list:
            
            tx_done_event.wait()
            tx_done_event.clear()

            image_num = capture_list[-1]
            list_of_files = glob.glob('tx_images/*.jpg') # * means all if need specific format then *.csv
            latest_file = max(list_of_files, key=os.path.getctime)
            
            print("Latest jpg from the camera: ",latest_file)
            
            if image_num > last_encoded.value:
                print("Encoding image {} because it is newer than {}" .format(image_num, last_encoded.value))
                encode_image(image_num)
                encode_list.append(image_num)
                encoded_set.add(image_num)
                last_encoded.value = image_num

def transmit_process(encode_list, transmitted_set, last_sent):
    while True:
        if encode_list:
            image_num = encode_list[-1]
            if image_num >= last_sent.value and image_num not in transmitted_set:
                print("Transmitting image {}" .format(image_num))
                transmit_image(image_num)
                transmitted_set.add(image_num)
                last_sent.value = image_num
                tx_done_event.set()

def encode_image(image_num):
    # Similar to your existing ssdv function
    #filename = "tx_images/%d.jpg" % image_num
    os.system("cp tx_images/%d.jpg tx_images/%d_raw.jpg" % (image_num, image_num))
    # Build up our imagemagick 'convert' command line
    overlay_str = "convert tx_images/%d.jpg -gamma 0.8 -font Helvetica -pointsize 40 -gravity North " % image_num
    overlay_str += "-strokewidth 2 -stroke '#000C' -annotate +0+5 \"%s\" " % "test"
    overlay_str += "-stroke none -fill white -annotate +0+5 \"%s\" " % "test"
	# Add on logo overlay argument if we have been given one.
    # if args.logo != "none":
    #     overlay_str += "%s -gravity SouthEast -composite " % args.logo

    overlay_str += "tx_images/%d.jpg" % image_num

    #tx.transmit_text_message("Adding overlays to image.")
    os.system(overlay_str)
    
    #resize the image
    for size in new_size:
        os.system(
            "convert tx_images/%d.jpg -resize %s\! tx_images/%d_%s.jpg" % (
                image_num, size, image_num, size))

    new_size.append("raw")

    #encode the image
    for size in new_size:
        os.system(
            "ssdv -e -n -q 6 -c %s -i %d tx_images/%d_%s.jpg tx_images/%d_%s.bin" % (
                callsign, image_num, image_num, size, image_num, size))

def transmit_image(image_num):
    tx = PacketTX.PacketTX(debug=debug_output, serial_baud=args.baudrate)
    tx.start_tx()
    filename = f"tx_images/{image_num}_800x608.bin"
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

    with Manager() as manager:
        capture_list = manager.list()
        encode_list = manager.list()
        #capture_queue =manager.Queue()
        #encode_queue = manager.Queue()
        encoded_set = set()
        transmitted_set = set()
        
        last_encoded = Value('i', 0)
        last_sent = Value('i', 0)

        tx_done_event = manager.Event()
        # Set the event manually for the first time
        tx_done_event.set()

        # Start the capture process
        print("Spawning Processes...")
        capture_process = Process(target=capture_process, args=(capture_list,))
        capture_process.start()

        # Start the ssdv process
        ssdv_process = Process(target=ssdv_process, args=(capture_list, encode_list, encoded_set, transmitted_set, last_encoded))
        ssdv_process.start()

        # Start the transmit process
        transmit_process = Process(target=transmit_process, args=(encode_list, transmitted_set, last_sent))
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
