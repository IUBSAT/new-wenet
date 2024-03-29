#!/bin/bash

# Transmit Script (transmit.sh)
# 1. Start RF module (init_rfm98w.py)
# 2. Start Image Script (image.py)

MYCALL=KD9ZSC

# The centre frequency of the transmission.
TXFREQ=423.000

# Baud Rate
# Known working transmit baud rates are 115200 (the preferred default).
# Lower baud rates *may* work, but will need a lot of testing on the receiver
# chain to be sure they perform correctly.
BAUDRATE=115200

# CHANGE THE FOLLOWING LINE TO REFLECT THE ACTUAL PATH TO THE TX FOLDER.
# i.e. it may be /home/username/dev/wenet/tx/
#cd ~/wenet/tx/

python3 init_rfm98w.py --frequency $TXFREQ --baudrate $BAUDRATE --spidevice 1
python3 luke_imagev2.py --baudrate $BAUDRATE | tee ~/wenet_$(date '+%d_%H-%M-%S').log
