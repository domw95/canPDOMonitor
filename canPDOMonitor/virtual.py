"""Virtual can.Device for testing programs."""

import threading
import time
from . import can
from . import pdo
import math
import random
import logging


class Virtual(can.Device):
    """
    Virtual device class that sends all sorts of data in PDO frames

    inherits from :class:`can.Device`.

    Streams data at 1kHz, single float on 0x181
    and 7Q8 on 0x281, 0x381 and 0x481

    """

    def __init__(self):

        # super init with bitrate that doesnt matter
        super().__init__(bitrate=1000000)

        self.gen_thread = threading.Thread(target=self._gen_loop)

        self.thread_active = threading.Event()

        # how many frames should be sent per second
        self.frame_rate = 4000

        # how long to sleep for between bursts
        self.sleep_time = 0.01

        # how many frames to send in one go, to roughly mimic real device
        self.nframe_send = round(self.frame_rate * self.sleep_time)

        # order in which to send PDOs
        self.order = [0x181, 0x281, 0x381, 0x481]
        self.order_ind = 0

        # total datapoints sent
        self.data_count = 0

    def _start(self):
        self.start_time = time.time()

        self.frame_count = 0
        self.thread_active.set()
        self.gen_thread.start()

    def _stop(self):
        self.thread_active.clear()
        self.gen_thread.join()

    def _gen_loop(self):
        """
        Loop called in thread to create frames

        call :py:func:`self.thread_active.clear` to end
        """
        logger.info("Frame Generation Started")
        while(self.thread_active.is_set()):
            # check how long its been running and how many frames should
            # have been sent
            elapsed_time = time.time() - self.start_time
            frame_target = self.frame_rate * elapsed_time

            # if sent more than required, go to sleep
            if frame_target < self.frame_count:
                time.sleep(self.sleep_time)
                continue
            for i in range(self.nframe_send):
                self._gen_frame()

    def _gen_frame(self):
        """
        creates a frame for current id and adds to queue
        """

        frame = can.Frame(id=self.order[self.order_ind],
                          timestamp=time.time() - self.start_time)
        if frame.id == 0x181:
            value = math.sin(2*math.pi*1*self.data_count/1000)
            frame.data[0:4] = pdo.num_2_single(value)
            frame.data[4:8] = pdo.num_2_single(random.gauss(0, 1))

        elif frame.id == 0x281:
            frame.data[0:2] = pdo.num_2_f7Q8(1)
            pass
        elif frame.id == 0x381:
            pass
        elif frame.id == 0x481:
            frame.data[0] = 1
            pass

        self._add_to_queue(frame)
        self.order_ind = self.order_ind + 1
        if self.order_ind >= len(self.order):
            # have reached end of data
            self.order_ind = 0
            self.data_count = self.data_count + 1
        self.frame_count = self.frame_count + 1

def _test():
    """
    Creates a virtual can Device and generates 100 frames
    """
    logging.basicConfig(level=logging.DEBUG)
    logger.info("Running Virtual CAN Device test")
    v = Virtual()
    logger.info("Starting Device")
    v.start()
    for i in range(10):
        f = v.get_frame()
        logger.debug("id: {},time: {:.3f}, data:{}".format(f.id,
                                                    f.timestamp,
                                                    f.data))
    v.stop()


# set up a logger for this module
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    _test()
