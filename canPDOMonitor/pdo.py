# -*- coding: utf-8 -*-
"""
Created on Wed Sep 23 14:32:57 2020

@author: Dom
"""

import threading
import time
import struct


class PDOConverter:
    """
    Pulls can frames from can.Device, converts them into data

    Requires an active can.Device and Format instance to take raw frames
    and convert them into data
    """

    def __init__(self, device, format):
        self.device = device
        self.format = format

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

    def start(self):
        """
        Starts the CAN hardware device and a thread to read the frames


        """
        self.device.start()
        self.state = "Starting"
        self.read_thread.start()

    def stop(self):
        """
        Stops the underlying can Device and the read thread

        Current implmentation will read at most 1 or 2 more can frames from
        queue before stopping

        """
        self.device.stop()
        self.read_active.clear()
        if self.read_thread.is_alive():
            self.read_thread.join(timeout=1)
            if self.read_thread.is_alive():
                # error ending thread, do something
                raise ThreadCloseError("PDO Converter read thread not closing")

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
                break

            # check if frame is of interest
            if frame.id not in self.format.order:
                continue

            # if still in starting mode
            if (self.pre_msg_count):
                self.pre_msg_count = self.pre_msg_count - 1
            else:
                # pass the frame to processor
                self._process_frame(frame)
                # print(frame.id,flush=True)

        self.read_active.clear()

    def _process_frame(self, frame):
        """
        Takes a frame and uses format to convert to signals

        Parameters
        ----------
        frame : can.Frame

        """
        # print(frame.id,flush=True)
        # ditch frame if we arent interested in it
        # if (frame.id not in self.format.order):
        #     return
        # check if still waiting for initial message
        if (self.state == "Starting" and frame.id == self.format.order[0]):
            # have recieved first message in sequence
            print("Converter Running")
            self.state = "Running"

            # set prev index to last in list (so order check works)
            self.prev_frame_ind = len(self.format.order) - 1

        if (self.state == "Running"):
            # check frame order
            self._check_frame_order(frame)
            self.frame_count = self.frame_count + 1

    def _check_frame_order(self, frame):
        """
        Takes frame, checks id against format.order using prev frame index

        Parameters
        ----------
        frame : Frame
            DESCRIPTION.

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
            self.stop()
            raise FrameOrderError("{},{},{}".format(frame.id,
                                                    expected_ind,
                                                    self.prev_frame_ind))


class FrameOrderError(Exception):
    def __init__(self, msg):
        super().__init__(msg)


class ThreadCloseError(Exception):
    def __init__(self, msg):
        super().__init__(msg)


class Format:
    """
    Contains all PDO format info for the incoming messages

    Init an instance and use add function to add a FrameFormat with id
    the order in which the frames are added determines expected order
    of frames on the bus
    """

    def __init__(self):
        # init list for storing order of frame ids
        self.order = []
        # init dict for storing frameFormats
        self.frame = {}

    def add(self, frame_format):
        # add tje frame format to the dict
        self.frame[frame_format.id] = frame_format
        self.order.append(frame_format.id)


class FrameFormat:
    """
    Specifies the format of a PDO frame

    Used in conjunction with Format which holds all details of incoming PDO
    frames and the order which they are expected
    """

    def __init__(self, id, active=True, use7Q8=True,
                 gain=[1, 1, 1, 1],
                 offset=[0, 0, 0, 0], name=None):
        self.id = id
        self.active = active
        self.use7Q8 = use7Q8
        self.gain = gain
        self.offset = offset
        if name is None:
            self.name = ["sig1", "sig2", "sig3", "sig4"]
        else:
            self.name = name


def num_2_f7Q8(num):
    """
    returns a 2 byte array (LSB) of the given number in 7Q8 format

    If the value of num is less than -128 or greater than 127.99,
    the value will be saturated
    """
    pass


def f7Q8_2_num(byte_arr):
    """
    Converts the given LSB 2 byte array to a number using 7Q8 format

    """
    pass


def num_2_single(num):
    """
    Converts the given number to 4 byte array (LSB) in single format
    """
    return bytearray(struct.pack('>i', num))


def single_2_num(byte_arr):
    """
    Converts the LSB 4 byte array to a single float number
    """
    pass


if __name__ == "__main__":
    # use kvaser device for demo
    from kvaser import Kvaser
    device = Kvaser()

    format = Format()
    format.add(FrameFormat(0x181))
    format.add(FrameFormat(0x281))
    format.add(FrameFormat(0x381))
    format.add(FrameFormat(0x481))
    pdo_converter = PDOConverter(device, format)
    pdo_converter.start()
    while(pdo_converter.frame_count < 4000*60):
        time.sleep(1)
        pass

    pdo_converter.stop()
    time.sleep(1)
