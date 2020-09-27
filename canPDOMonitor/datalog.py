import threading
import queue
from abc import ABC, abstractmethod
from enum import Enum
import logging


class DataLogger:
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
    :param start_at_zero: If true, records log from t=0
    :type start_at_zero:
    """

    def __init__(self, filename, start_condition=None, end_condition=None,
                 start_at_zero=True, mode=None):
        # open file used to log data
        self.filename = filename
        self.file = open(filename, 'w')

        # Start and Stop conditions
        self.start_condition = start_condition
        self.end_condition = end_condition

        # offset subtracted time value when writing data
        self.time_offset = 0
        self.start_at_zero = start_at_zero

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
        """
        logger.info("{} datalog started".format(self.filename))
        # start the thead to write the datpoints to file
        self.active.set()
        self.write_thread.start()

    def stop(self, flush=False):
        """
        Stop logging data, flush = false could lose some data in queue
        """

        # pop None on queue so write thread will stop
        self.data_queue.put(None)

        # if not allowing all data to pass through, tell thread to end
        if not flush:
            self.active.clear()

        if self.write_thread.is_alive():
            self.write_thread.join()

    def put(self, datapoints):
        """
        External function for placing lists of datapoints on queue

        Will put datapoints on queue if the logger is active
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
                # check start condition
                if self.start_condition is not None:
                    # if False, go to next datapoint list in loop
                    if not self.start_condition.check(datapoints):
                        continue

                # start condition met, =need to write header to file
                # create header with time and all signal names
                self.header.append("time")
                for datapoint in datapoints:
                    self.header.append(datapoint.name)
                    if datapoint.raw_value is not None:
                        self.header.append(datapoint.name + "_raw")

                # indicate that writing to file has begun
                self.writing.set()
                logger.info("Writing to {}".format(self.filename))

                # write the header
                self.file.write(self.header[0])
                for h in self.header[1:]:
                    self.file.write("," + h)

                # record time_offset if neccessary
                if self.start_at_zero:
                    self.time_offset = datapoints[0].time

            # write all the datapoints from list
            self.file.write("\n")
            self.file.write("{:.4f}".format(
                datapoints[0].time - self.time_offset))
            for d in datapoints:
                self.file.write("," + str(d.value))
                if d.raw_value is not None:
                    self.file.write("," + str(d.raw_value))

            # check for end condition, and exit loop if true
            if self.end_condition is not None:
                if self.end_condition.check(datapoints):
                    break

        self.active.clear()
        self.file.close()
        logger.info("Writing to {} ended".format(self.filename))


class DataLoggerGroup(DataLogger):
    """
    Extends functionality of a datalogger to many loggers

    Used for testing, where switching to a new file can be
    automated based on a condition in a signal. Redcued overhead compared
    to have a list of dataloggers, as the datapoints only go where required.
    Also should be easier to setup

    NEEDS IMPLEMENTING
    """

    def __init__(self, filename):
        pass


class Datapoint:
    def __init__(self, name=None, value=0, time=0,
                 timestamp=0, index=0, raw_value=None):
        # signal name: string
        self.name = name
        # value: float
        self.value = value
        # timestamp from canbus
        self.timestamp = timestamp
        # sequence time since start
        self.time = time
        # index of datapoint since start
        self.index = index
        # raw value of signal before offset/gain applied (if not 0/1)
        self.raw_value = raw_value


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

    @abstractmethod
    def reset(self):
        """
        Resets the Condition
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

    def __init__(self, trigger, signal_name=None, value=0):
        self.trigger = trigger
        self.signal_name = signal_name
        self.value = value
        self.prev_datapoint = None

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
        if ((self.trigger == Trigger.Rising or self.trigger == Trigger.Either)
                and self.prev_datapoint.value < self.value
                and datapoint.value > self.value):
            self.prev_datapoint = datapoint
            return True

        # Look for a falling edge
        if ((self.trigger == Trigger.Falling or self.trigger == Trigger.Either)
                and self.prev_datapoint.value > self.value
                and datapoint.value < self.value):
            self.prev_datapoint = datapoint
            return True

        # check for an equal condition
        if self.trigger == Trigger.Equal:
            if datapoint == self.value:
                return True
        self.prev_datapoint = datapoint
        return False

    def reset(self):
        self.prev_datapoint = None


class CountCondition(Condition):
    """
    Condtion will return true when the number of datapoints reaches count
    """

    def __init__(self, count):
        self.count = count
        self.data_count = 0

    def check(self, datapoints):
        """
        Adds 1 to the data count and returns true if it equals count condition
        """

        self.data_count = self.data_count + 1
        if self.data_count == self.count:
            return True
        else:
            return False

    def reset(self):
        self.data_count = 0


class TimeCondition(Condition):
    """
    Check returns true after datapoint time has passed
    """

    def __init__(self, time):
        self.time = time
        self.start_time = None

    def check(self, datapoints):
        """
        Checks elasped data time between start and now
        """
        # check if this is the first check
        if self.start_time is None:
            self.start_time = datapoints[0].time

        # check elapsed_time
        if (datapoints[0].time - self.start_time) >= self.time:
            return True
        else:
            return False

    def reset(self):
        self.start_time = None


class Trigger(Enum):
    Rising = 1
    Falling = 2
    Either = 3
    Equal = 4


class DataLogMode(Enum):
    Once = 1
    Count = 2
    Continuous = 3


# module logger
logger = logging.getLogger(__name__)
