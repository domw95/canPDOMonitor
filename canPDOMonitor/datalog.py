# -*- coding: utf-8 -*-
"""
Created on Thu Sep 24 15:39:29 2020

@author: Research
"""
import threading
import queue
from abc import ABC, abstractmethod
from enum import Enum


class DataLog:
    """
    Writes datapoints to file

    :param filename: Name of file to write to, relative or absolute path
    :type filename: :class:`String`
    :param start_condition: Indicates when to start logging. If None, will be
        started straight away
    :type start_condition: :class:`Condition`
    :param end_condition: Indicates when to end logging. If None, will be
        end only when stop is called
    :type end_condition: :class:`Condition`
    """

    def __init__(self, filename, start_condition=None, end_condition=None):
        # open file used to log data
        self.file = open(filename, 'w')

        # queue of lists of datapoints to write to file
        self.data_queue = queue.Queue()

        # thread to run file write
        self.write_thread = threading.Thread(target=self._write_loop)

        # flag to indicate if logger thread is running
        self.active = threading.Event()

        # flag to indicate if writing to file has begun
        self.writing = threading.Event()

        # list of strings written as the file header
        self.header = []

    def start(self):
        """
        Starts logging data that is fed to it, or waits for trigger

        Starts running the write to file thread, which will place
        data in file or wait until trigger to do so

        Returns
        -------
        None.

        """

        # start the thead to write the datpoints to file
        self.write_thread.start()

    def stop(self):
        self.data_queue.put(None)
        self.active.clear()
        if self.write_thread.is_alive():
            self.write_thread.join()

    def put(self, datapoints):
        """
        External function for placing lists of datapoints on queue

        Will put datapoints on queue if the logger is active

        Parameters
        ----------
        datapoints : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        if self.active.is_set():
            self.data_queue.put(datapoints)

    def _write_loop(self):
        self.active.set()

        while(self.active.is_set()):
            # pull datapoints from queue
            datapoints = self.data_queue.get()

            # None indicates end of logging
            if datapoints is None:
                break

            # check if writing to file has begun
            if not self.writing.is_set():
                # need to write header to file

                # create header with time and all signal names
                self.header.append("time")
                for datapoint in datapoints:
                    self.header.append(datapoint.name)
                    if datapoint.raw_value is not None:
                        self.header.append(datapoint.name + "_raw")

                # indicate that writing to file has begun
                self.writing.set()

                # write the header
                self.file.write(self.header[0])
                for h in self.header[1:]:
                    self.file.write("," + h)
                self.file.write("\n")
                print(self.header)

            # write all the datapoints from list
            self.file.write(str(datapoints[0].time))
            for d in datapoints:
                self.file.write("," + str(d.value))
                if d.raw_value is not None:
                    self.file.write("," + str(d.raw_value))
            self.file.write("\n")

        self.active.clear()
        self.file.close()


class Condition(ABC):
    """
    parent class to start and stop datalogger

    Call check function with datapoint list, returns true if condition check
    passes
    """

    def __init__(self):
        pass

    @abstractmethod
    def check(self, datapoints):
        """
        Return true if check passes, false otherwise
        """
        pass


class TriggerCondition(Condition):
    """
    Specifiy a rising, falling, changing edge trigger on 0 or value

    Used to start or end datalogger

    :param edge: Rising, Falling, Either
    :type edge: :class:`Edge`
    :param value: Value to check edge on, Default is 0
    :type value: Float, optional
    :param signal_name: Name of signal to check edge, defaults to first signal
    :type signal_name: String, optional
    """

    def __init__(self, edge, signal_name=None, value=0):
        self.edge = edge
        self.signal_name = signal_name
        self.value = value
        self.prev_data = None

    def check(self, datapoints):
        """
        Checks for signal edge given the new set of datapoints

        :param datapoints:
        :type datapoints: :class:`data.Datapoint`
        """

        # get the datapoint of interest
        if self.signal_name is None:
            # no name has been set, use first datapoint
            datapoint = datapoints[0]
        else:
            for datapoint in datapoints:
                if datapoint.name == self.signal_name:
                    break

        # check if it is the first call to check
        if self.prev_datapoint is None:
            # remember first datapoint
            self.prev_datapoint = datapoint
            return False

        # Look for a rising edge`
        if ((self.edge == Edge.Rising or self.edge == Edge.Either)
                and self.prev_datapoint.value < self.value
                and datapoint.value > self.value):
            self.prev_datapoint = datapoint
            return True

        # Look for a falling edge
        if ((self.edge == Edge.Falling or self.edge == Edge.Either)
                and self.prev_datapoint.value > self.value
                and datapoint.value < self.value):
            self.prev_datapoint = datapoint
            return True
        self.prev_datapoint = datapoint
        return False


class CountCondition(Condition):
    """
    Condtion will return true when the number of datapoints reaches count
    """

    def __init__(self, count):
        pass

    def check(self, datapoints):
        pass


class TimeCondition(Condition):

    def __init__(self, time):
        pass

    def check(self, datapoints):
        pass


class Edge(Enum):
    Rising = 1
    Falling = 2
    Either = 3


if __name__ == "__main__":

    from kvaser import Kvaser
    from pdo import PDOConverter, FrameFormat, Format

    # set up kvaser device
    device = Kvaser()

    # create logger
    dlog = DataLog("test.txt")

    # set up PDO formats
    format = Format()
    format.add(FrameFormat(0x181, use7Q8=False,
                           name=["Wave Gen Out", "Encoder Pos"]))
    format.add(FrameFormat(0x281))
    format.add(FrameFormat(0x381))
    format.add(FrameFormat(0x481))

    # start PDO converter
    pdo_converter = PDOConverter(device, format)
    pdo_converter.start()
    dlog.start()

    while(pdo_converter.data_count < 1000*10):
        datapoints = pdo_converter.data_queue.get()
        dlog.put(datapoints)

    pdo_converter.stop()
    dlog.stop()
