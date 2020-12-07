from canPDOMonitor.kvaser import Kvaser
import logging
import time

# Runs the kvaser for 10 seconds, printing debug info and occasionally frames
# initial frame order may be wrong. Other classes must deal with it

logging.basicConfig(level=logging.DEBUG)

# create the device
device = Kvaser()

# start reading frames from hardware
device.start()

# read 1000 frames and print to screen

for i in range(4000*15):
    frame = device.get_frame()
    # time.sleep(.001)
    if frame is not None:
        if not i % 4001:
            print(frame)
    else:
        break

# stop the device to stop all threads from running
device.stop()
