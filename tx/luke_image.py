from multiprocessing import Process, Queue
import PacketTX, sys, os, argparse
import time

callsign = "KD9ZSC"
image_range = range(1, 20)
debug_output = False
new_size = ["800x608"]

def capture_proc(capture_queue):
    while True:
        for i in image_range:
            cmd = "libcamera-still -o new_images/%d.jpg" % i
            os.system(cmd)
            capture_queue.put(i)
            #time.sleep(1)  # Adjust sleep time based on capture frequency

def ssdv_proc(capture_queue, encode_queue, encoded_set, transmitted_set):
    while True:
        if not capture_queue.empty():
            image_num = capture_queue.get()
            if image_num not in transmitted_set:
                encode_image(image_num)
                encode_queue.put(image_num)
                encoded_set.add(image_num)

def transmit_proc(encode_queue, transmitted_set):
    while True:
        if not encode_queue.empty():
            image_num = encode_queue.get()
            if image_num not in transmitted_set:
                transmit_image(image_num)
                transmitted_set.add(image_num)

def encode_image(image_num):
    # Similar to your existing ssdv function
    os.system("cp new_images/%d.jpg new_images/%d_raw.jpg" % (image_num, image_num))
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

    # Start the capture process
    capture_proc = Process(target=capture_proc, args=(capture_queue,))
    capture_proc.start()

    # Start the ssdv process
    ssdv_proc = Process(target=ssdv_proc, args=(capture_queue, encode_queue, encoded_set, transmitted_set))
    ssdv_proc.start()

    # Start the transmit process
    transmit_proc = Process(target=transmit_proc, args=(encode_queue, transmitted_set))
    transmit_proc.start()

    try:
        capture_proc.join()
        ssdv_proc.join()
        transmit_proc.join()
    except KeyboardInterrupt:
        print("Terminating processes...")
        capture_proc.terminate()
        ssdv_proc.terminate()
        transmit_proc.terminate()
