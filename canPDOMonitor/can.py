# -*- coding: utf-8
"""
Group of classes for general can stuff
"""

from abc import ABC, abstractmethod
import queue
import threading
import logging
import time


class Device(ABC):
    """Main class for interfacing with CAN hardware.

    Specific hardware devices inherit from this.
    Child classes must implement _start and _stop methods

    CAN frames must be read from devices and placed into frame_queue async
    and thread safe following call to _start method.

    init should call parent constructor with bitrate

    :param bitrate: CAN Bus bitrate in b/s
    :type bitrate: :class:`Int`
    """

    # maximum number of CAN frames to hold in queue
    # 4000 is 1 second of 4 PDOs at 1KHz
    DEFAULT_QUEUE_SIZE = 4000

    def __init__(self, bitrate):
        self.bitrate = bitrate
        self.frame_queue = queue.Queue(maxsize=self.DEFAULT_QUEUE_SIZE)

        # total number of frames from device
        self.frame_count = 0
        # time that first one arrived
        self.frame_start_time = None
        # approx rate of frames
        self.frame_rate = 0
        # thread for checking device stats
        self.check_thread = threading.Thread(target=self._check_loop)
        # time the check was last run
        self.check_time = None
        # frame count on last check
        self.check_frame_count = 0

        # active flag true when device running, false when stopped
        self.active = threading.Event()
        # lock for reading/changing active flag
        self.active_lock = threading.Lock()

    def start(self):
        """
        To be called externally, calls _start method of class

        Clears the frame queue
        then calls the device-specific _start method
        """

        logger.info("Starting can Device")
        # clear the frame queue and start device
        self.clear_queue()

        # acquire lock to ensure active state change isnt interrupted by thread
        with self.active_lock:
            self._start()
            self.active.set()

        # start the checking thread
        self.check_thread.start()

    def stop(self):
        """
        To be called externally, calls _stop method of class

        Calls the device specific _stop method
        Doesn't clear queue in case messages still need processing
        """

        logger.info("Stopping can Device")
        # add None to queue to indicate to consumer to stop
        self._add_to_queue(None)

        # stop the device
        with self.active_lock:
            self._stop()
            self.active.clear()
            if self.check_thread.is_alive():
                self.check_thread.join()

    def get_frame(self):
        """
        Gets the next frame from the queue, blocking execution

        Should be regularly called by whatever process is reciveing the frames
        returns None when can device has been stopped
        :return: Next frame from queue
        :rtype: :class:`can.Frame`

        """

        # Blocking call to get function
        return self.frame_queue.get(True)

    def clear_queue(self):
        """
        Safely empties the queue

        This will not work well if the CAN device is still running

        Returns
        -------
        None.

        """
        # Thread safe method of clearing the queue
        with self.frame_queue.mutex:
            self.frame_queue.queue.clear()

    @abstractmethod
    def _start(self):
        """
        Activates the bus, clears the queue/buffer, starts populating queue

        Is responsible for reading messages on bus and passing frames
        to queue.  This is specific to hardware, using callbacks, asyncio etc

        Returns
        -------
        None.

        """
        pass

    @abstractmethod
    def _stop(self):
        """
        Exits the bus and clears the queue, stop adding frames to queue

        Returns
        -------
        None.

        """
        pass

    def _add_to_queue(self, frame):
        """
        Called to add a frame to the queue

        Method adds frame to queue whilst checking for overflow etc

        """

        # if queue is not full, put frame on queue
        if self.frame_queue.full():
            raise FrameQueueOverflowError()
        self.frame_queue.put(frame)

        # record frame stats
        if self.frame_start_time is None:
            # this if first frame, record time
            self.frame_start_time = time.time()
        self.frame_count = self.frame_count + 1

    def _check_loop(self):
        """
        Updates stats on Device, such as frame rate, every second
        """
        while(self.active.is_set()):
            # if this is not the first run
            if self.check_time is not None:
                # calc frame rate
                frame_count = self.frame_count - self.check_frame_count
                elapsed_time = time.time() - self.check_time
                self.frame_rate = round(frame_count / elapsed_time)
                total_frame_rate = round(
                    self.frame_count / (time.time() - self.frame_start_time))

                logger.debug("Frame Rate: {}, Total Rate {}, Frame Count {}".
                             format(self.frame_rate,
                                    total_frame_rate,
                                    self.frame_count))

            # record this check time and frame count, and wait for next loop
            self.check_time = time.time()
            self.check_frame_count = self.frame_count
            time.sleep(1)


class Frame:
    """
    Class to hold frame information

    Properties:
        id = decimal representation of can frame id
        data = byte array length 8
        timestamp = timestamp in ms
        dlc = length of data
        error = true if frame is error frame
    """

    def __init__(self, id=0,
                 timestamp=0, dlc=8, error=False):
        self.id = id
        self.data = bytearray((0, 0, 0, 0, 0, 0, 0, 0))
        self.timestamp = timestamp
        self.dlc = dlc
        self.error = error


class FrameQueueOverflowError(Exception):
    pass


logger = logging.getLogger(__name__)
