"""
Virtual can.Device for testing programs
"""
import threading
import time
import can
import pdo
import math


class Virtual(can.Device):

    """
    Virtual device class that sends all sorts of data in PDO frames

    """

    def __init__(self, n_pdo=4):

        # super init with bitrate that doesnt matter
        super().__init__(bitrate="1M")

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
        generates all the can frames and adds them to queue
        """
        print("Starting frame generation loop")
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
        frame = can.Frame(id=self.order[self.order_ind],
                          timestamp=time.time() - self.start_time)
        if frame.id == 0x181:
            value = math.sin(2*math.pi*1*self.data_count/1000)
            frame.data[0:4] = pdo.num_2_single(value)
            frame.data[4:8] = pdo.num_2_single(2)
        elif frame.id == 0x281:
            pass
        elif frame.id == 0x381:
            pass
        elif frame.id == 0x481:
            pass

        self._add_to_queue(frame)

        self.order_ind = self.order_ind + 1
        if self.order_ind >= len(self.order):
            # have reached end of data
            self.order_ind = 0
            self.data_count = self.data_count + 1
        self.frame_count = self.frame_count + 1


if __name__ == "__main__":
    print("Starting Virtual Can Device")
    v = Virtual()
    v.start()
    for i in range(10):
        frame = v.get_frame()
        print("id: {},time: {:.3f}, data:{}".format(frame.id,
                                                    frame.timestamp,
                                                    frame.data))
    v.stop()
