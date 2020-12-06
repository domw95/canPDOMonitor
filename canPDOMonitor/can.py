# -*- coding: utf-8
"""
Group of classes for CAN and PDO
"""

from abc import ABC, abstractmethod
from canPDOMonitor.datalog import Datapoint
from canPDOMonitor.common import params_from_file
import queue
import threading
import logging
import time
import struct


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
    DEFAULT_QUEUE_SIZE = 8000

    def __init__(self, bitrate, check_loop_time=10):
        # can bitrate of device
        self.bitrate = bitrate
        # queue to hold can frames
        self.frame_queue = queue.Queue(maxsize=self.DEFAULT_QUEUE_SIZE)
        # time in seconds to report device info
        self.check_loop_time = int(check_loop_time)

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

        # thread used for stopping device
        self.stop_thread = threading.Thread(target=self.stop_check)
        # event used to trigger device stopping
        self.stop_trigger = threading.Event()

    def start(self):
        """
        To be called externally, calls _start method of class

        Clears the frame queue
        then calls the device-specific _start method
        """

        logger.info("Starting CAN Device")
        # clear the frame queue and start device
        self.clear_queue()

        # acquire lock to ensure active state change isnt interrupted by thread
        with self.active_lock:
            self._start()
            self.active.set()

        # start the checking thread
        self.check_thread.start()

        # start the internal stop thread
        self.stop_thread.start()

    def stop(self):
        """
        To be called externally, calls _stop method of class

        Calls the device specific _stop method
        Doesn't clear queue in case messages still need processing
        """
        if self.active.is_set():
            logger.debug("Stopping CAN Device")
            # add None to queue to indicate to consumer to stop
            self._add_to_queue(None)

            # stop the device
            with self.active_lock:
                self._stop()
                self.active.clear()
                if self.check_thread.is_alive():
                    self.check_thread.join()
            # finally, stop the stop check thread
            self.stop_trigger.set()
            logger.info("CAN Device Stopped")

    def stop_check(self):
        """
        Waits for the command to stop, and calls stop, for internal threads
        """
        # wait for the stop trigger
        self.stop_trigger.wait()
        # check if device is still active
        if self.active.is_set():
            self.stop()


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
        """
        pass

    @abstractmethod
    def _stop(self):
        """
        Exits the bus and clears the queue, stop adding frames to queue
        """
        pass

    def _add_to_queue(self, frame):
        """
        Called to add a frame to the queue

        Method adds frame to queue whilst checking for overflow etc
        """

        # if queue is not full, put frame on queue
        if self.frame_queue.full():
            # wait for a second for something to remove item from queue
            logging.error("CAN Device Frame Overflow")
            logger.debug("Frame Count {}".format(self.frame_count))
            self.stop_trigger.set()
            return False
  
        self.frame_queue.put(frame)

        # record frame stats
        if self.frame_start_time is None:
            # this if first frame, record time
            self.frame_start_time = time.time()
        self.frame_count = self.frame_count + 1
        return True

    def _check_loop(self):
        """
        Updates stats on Device, such as frame rate, at a slow rate
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

                logger.debug("CAN Frame Rate: {}, Frame Count {}, Queue: {}".
                             format(total_frame_rate,
                                    self.frame_count, self.frame_queue.qsize()))

            # record this check time and frame count, and wait for next loop
            self.check_time = time.time()
            self.check_frame_count = self.frame_count
            for i in range(self.check_loop_time):
                if not self.active.is_set():
                    break
                time.sleep(1)


class Frame:
    """
    Class to hold frame information
    """

    def __init__(self, id=0, data=None,
                 timestamp=0, dlc=8, error=False):
        self.id = id
        if data is None:
            self.data = bytearray((0, 0, 0, 0, 0, 0, 0, 0))
        else:
            self.data = data
        self.timestamp = timestamp
        self.dlc = dlc
        self.error = error

    def __str__(self):
        """
        Override the str function
        """
        return "ID: {}, Data: {}, Timestamp: {}".format(self.id, self.data, self.timestamp)


class PDOConverter:
    """
    Pulls can frames from can.Device, converts them into data

    Requires an active :class:`can.Device` and Format instance to take raw
    frames and convert them into data
    :param device:
    :type device: :class:`can.Device`
    """

    def __init__(self, device, format, check_loop_time=10):
        self.device = device
        self.format = format
        self.check_loop_time = check_loop_time

        # thread for pulling frames from device
        self.read_thread = threading.Thread(target=self._read_loop)
        # event to control deactiviation of thread
        self.read_active = threading.Event()

        # state of conversion
        # Initiated = before starting
        # Starting = read messages, waiting for first
        # Running = reading messages, normal running
        self.state = "Initiated"

        # index of previous frame id recieved
        self.prev_frame_ind = 0

        # how many messages to read before entering running mode
        # this is required because kvaser doesnt seem to clear buffer well
        self.pre_msg_count = 1000

        # total messages recieved in running mode
        self.frame_count = 0

        # list of datapoints at current timestep
        self.datapoints = []

        # queue with each item a list of datapoints at a particular timestep
        self.data_queue = queue.Queue(maxsize=1000)

        # current index of datapoint timestep
        self.data_count = 0
        self.check_data_count = 0

        # marks the pdo converter as active 
        self.active = threading.Event()
        # thread to stop the device internally
        self.stop_thread = threading.Thread(target=self.stop_check)
        self.stop_trigger = threading.Event()

        # check loop
        self.check_thread = threading.Thread(target=self._check_loop)
        self.check_time = None
        self.check_frame_count = 0
        self.frame_start_time = None

    def start(self):
        """
        Starts the CAN hardware device and a thread to read the frames
        """
        logger.info("Starting PDO Converter")
        self.active.set()
        self.read_thread.start()
        self.stop_thread.start()
        self.check_thread.start()
        self.device.start()
        self.state = "Starting"
        logger.info("Started PDO Converter")

    def stop(self):
        """
        Stops the underlying can Device and the read thread

        Current implmentation will read at most 1 or 2 more can frames from
        queue before stopping
        """
        
        if self.active.is_set():
            logger.debug("Stopping PDO Converter")
            # Pop None on the queue to indicate to consumer that stop is called
            self.active.clear()
            self.stop_trigger.set()
            self.data_queue.put(None)

            # Call for underlying device to stop and wait for thread to end
            self.device.stop()
            self.read_active.clear()
            if self.read_thread.is_alive():
                self.read_thread.join(timeout=1)
                if self.read_thread.is_alive():
                    # error ending thread, do something
                    raise ThreadCloseError("PDO Converter read thread not closing")
            logger.info("Stopped PDO Converter")

    def stop_check(self):
        """
        Waits for the command to stop, and calls stop, for internal threads
        """
        # wait for the stop trigger
        self.stop_trigger.wait()
        # check if device is still active
        if self.active.is_set():
            self.stop()

    def get_datapoints(self):
        """
        Returns the next list of datapoints, None if device has stopped
        """

        return self.data_queue.get(True)

    def _read_loop(self):
        """
        Infinite loop called in thread to pull frames from device and process
        """

        # set the thread flag
        self.read_active.set()

        # start loop to get and process messages
        while(self.read_active.is_set()):
            # get frame from device
            frame = self.device.get_frame()

            # if None, device is disabled, end read thread
            if (frame is None):
                logger.info("PDO converter: Device has stopped")
                self.stop_trigger.set()
                break

            # check if frame is of interest
            if frame.id not in self.format.order:
                logger.debug("Frame {} not used".format(frame))
                continue

            # if still in starting mode
            if (self.pre_msg_count):
                self.pre_msg_count = self.pre_msg_count - 1
                continue

            # pass the frame to processor
            if not self._process_frame(frame):
                # Exit loop if it was unable to place a frame on the queue
                break

        self.read_active.clear()

    def _process_frame(self, frame):
        """
        Takes a frame and uses format to convert to signals
        """

        # check if still waiting for initial message
        if (self.state == "Starting" and frame.id == self.format.order[0]):
            # have recieved first message in sequence
            self.state = "Running"

            # set prev index to last in list (so order check works)
            self.prev_frame_ind = len(self.format.order) - 1

        if (self.state == "Running"):
            # check frame order
            self._check_frame_order(frame)

            # convert the frame to datpoints and add to list
            self._extract_datapoints(frame, self.format.frame[frame.id])

            # check if at end of timestep
            if frame.id == self.format.order[-1]:
                if self.data_queue.full():
                    # queue overflow
                    # stop the device from reading can frames
                    logger.error("PDO conveter queue full")
                    self.device.stop()
                    # stop the pdo converter
                    self.stop_trigger.set()
                    return False
                else:
                    # place datapoint list onto queue for consumer
                    self.data_queue.put(self.datapoints.copy())

                # clear the list
                self.datapoints = []

                # increment counter
                self.data_count = self.data_count + 1
            if self.frame_start_time is None:
                self.frame_start_time = time.time()
            self.frame_count = self.frame_count + 1
        return True

    def _check_frame_order(self, frame):
        """
        Takes frame, checks id against format.order using prev frame index
        """
        # calc expected index for this id
        expected_ind = self.prev_frame_ind + 1
        if(expected_ind >= len(self.format.order)):
            expected_ind = 0

        if(self.format.order[expected_ind] == frame.id):
            self.prev_frame_ind = expected_ind
            return
        else:
            # error, incorrect frame order
            # pop None on the queue as that will indicate for higher devices
            # to stop
            self.data_queue.put(None)
            raise FrameOrderError("{},{},{}".format(frame.id,
                                                    expected_ind,
                                                    self.prev_frame_ind))

    def _extract_datapoints(self, frame, frame_format):
        """
        Extracts the data from the frame according to format, adds to list
        """
        # go through at least 2 for single, 4 for 7Q8
        for i in range(4):

            if frame_format.use7Q8:
                # extract the value
                value = f7Q8_2_num(frame.data[2*i:(2*i)+2])

            elif i >= 2:
                # out of range for single, return
                return
            else:
                # extract single value
                value = single_2_num(frame.data[4*i:(4*i)+4])

            # create a new datapoint
            datapoint = Datapoint(name=frame_format.name[i])

            datapoint.value = value

            # add the timestamp and time info
            datapoint.timestamp = frame.timestamp
            datapoint.time = self.data_count/self.format.rate
            datapoint.index = self.data_count

            # add the datapoint to the list
            self.datapoints.append(datapoint)

    def _check_loop(self):
        """
        Prints debug info at slow rate in its own thread
        """
        while(self.active.is_set()):
            # if this is not the first run
            if self.check_time is not None and self.frame_start_time is not None:
                # calc frame rate
                frame_count = self.frame_count - self.check_frame_count
                data_count = self.data_count - self.check_data_count
                elapsed_time = time.time() - self.check_time
                self.frame_rate = round(frame_count / elapsed_time)
                self.data_rate =  round(data_count / elapsed_time)
                total_frame_rate = round(
                    self.frame_count / (time.time() - self.frame_start_time))

                logger.debug("PDO Frame Rate: {}, Data Rate: {}, Queue: {}".
                             format(total_frame_rate, self.data_rate, self.data_queue.qsize()))

            # record this check time and frame count, and wait for next loop
            self.check_time = time.time()
            self.check_frame_count = self.frame_count
            self.check_data_count = self.data_count
            for i in range(self.check_loop_time):
                if not self.active.is_set():
                    break
                time.sleep(1)

class Format:
    """
    Contains all PDO format info for the incoming messages

    Init an instance and use add function to add a FrameFormat with id
    the order in which the frames are added determines expected order
    of frames on the bus

    :param odr: Path to a tREU object dictionary to extract PDO info
    :type odr: :class:`String`
    """

    def __init__(self, odr=None, rate=1000):
        # init list for storing order of frame ids
        self.order = []
        # init dict for storing frameFormats
        self.frame = {}
        # rate of data in Hz
        self.rate = rate

        if odr is None:
            return
        # check for object dictionary
        else:
            params = params_from_file(odr)
            if params is None:
                print("No parameters in odr")
                return

        # go through the params
        # check for data rate
        if "CAN Sys PDO Tx Divider" in params:
            self.rate = 10000/float(
                params["CAN Sys PDO Tx Divider"])

        # go through each of the PDOs
        for i in range(1, 5):
            # transtype must be 255 for PDO Tx
            transtype = "CAN Sys PDO{} Tx TransType".format(i)
            if transtype in params:
                if params[transtype] == "255":
                    # PDO<i> enabled, create format with correct id
                    frame_format = FrameFormat(i*0x100 + 0x81)
                    # check for 7Q8
                    if params["CAN Sys Use7q8Format PDO{}".format(i)] == "0":
                        frame_format.use7Q8 = False
                        n_values = 2
                    else:
                        frame_format.use7Q8 = True
                        n_values = 4

                    # get all the signal names
                    for j in range(n_values):
                        frame_format.name[j] = (
                            params["CAN Sys PDO{} Tx Ptr{}".format(i, j+1)]
                        )
                    self.add(frame_format)

    def add(self, frame_format):
        # add the frame format to the dict
        self.frame[frame_format.id] = frame_format
        self.order.append(frame_format.id)


class DefaultFormat(Format):
    """
    Creates a :class:`Format` object with some default Frameformats
    """

    def __init__(self):
        # init parent Frame class
        super().__init__()
        # create the 4 frame classes and add
        self.add(FrameFormat(0x181, use7Q8=False))
        self.add(FrameFormat(0x281))
        self.add(FrameFormat(0x381))
        self.add(FrameFormat(0x481))


class FrameFormat:
    """
    Specifies the format of a PDO frame

    Used in conjunction with Format which holds all details of incoming PDO
    frames and the order which they are expected
    """

    def __init__(self, id, active=True, use7Q8=True,
                 name=None):
        self.id = id
        self.active = active
        self.use7Q8 = use7Q8
        if name is None:
            self.name = [str(id) + '_' + str(x) for x in range(4)]
        else:
            self.name = name


def num_2_f7Q8(num):
    """
    returns a 2 byte array (LSB) of the given number in 7Q8 format

    If the value of num is less than -128 or greater than 127.99,
    the value will be saturated
    """
    # multiply to int16 then pack that
    num = round(num * 256)
    if num < -(2**15):
        num = -(2**15)
    elif num > ((2**15)-1):
        num = ((2**15)-1)
    return bytearray(struct.pack('<h', num))


def f7Q8_2_num(byte_arr):
    """
    Converts the given LSB 2 byte array to a number using 7Q8 format
    """
    return struct.unpack('<h', byte_arr)[0]/256.0


def num_2_single(num):
    """
    Converts the given number to 4 byte array (LSB) in single format
    """
    return bytearray(struct.pack('<f', num))


def single_2_num(byte_arr):
    """
    Converts the LSB 4 byte array to a single float number
    """
    return struct.unpack('<f', byte_arr)[0]


class FrameOrderError(Exception):
    def __init__(self, msg):
        super().__init__(msg)


class ThreadCloseError(Exception):
    def __init__(self, msg):
        super().__init__(msg)


class FrameQueueOverflowError(Exception):
    pass


logger = logging.getLogger(__name__)
