"""
Main classes for running the canPDOMonitor

Monitor routes datapoints from a pdo_converter to attached dataloggers,
managing the stopping and starting of each.  Can use a CAN_SYS_PDO.order
object dictionary to choose PDO format
"""

from canPDOMonitor.can import PDOConverter, DefaultFormat
from canPDOMonitor.virtual import Virtual
from canPDOMonitor.datalog import Datapoint
from abc import ABC, abstractmethod
import threading
import time
import logging


class Monitor:
    """
    Routes datapoints from the pdo_converter to any attached dataloggers

    Typical usage: Optionally include a Device, leave format and pdo_converter
    blank.  Format will then include the PDO specifications from the
    CAN_SYS_PDO.odr file in the current directory

    :param device: Defaults to :class:`virtual.Virtual`, with its defaults
    :type device: :class:`can.Device`
    :param format: Defaults to object dict in local directory, then class
        default for :class:`can.Format`
    :type format: :class:`can.Format`
    :param pdo_converter: Defaults to PDOConverter with device and format
        given in the constructor
    :type pdo_converter: :class:`can.PDOConverter`
    """

    def __init__(self, device=None, format=None, pdo_converter=None):
        if (device is not None and pdo_converter is not None
                or format is not None and pdo_converter is not None):
            raise InvalidArgumentsError

        # assign the arguments to the instance
        if device is None:
            self.device = Virtual()
        else:
            self.device = device

        if format is None:
            # Look for odr in local directory

            # or use defaults
            self.format = DefaultFormat()
        else:
            self.format = format

        if pdo_converter is None:
            self.pdo_converter = PDOConverter(self.device, self.format)

        # list of filters
        self.filters = []
        # List of dataloggers
        self.dataloggers = []
        # List of scope windows
        self.scope_windows = []

        # thread to pass all the datapoints around
        self.route_thread = threading.Thread(target=self._route_loop)
        # flag to indicate thread is running
        self.active = threading.Event()

        # slow rate checking thread to monitor status of things
        # ends at same time as routing loop
        self.check_thread = threading.Thread(target=self._check_loop)

    def add_datalogger(self, datalogger):
        """
        Adds a datalogger to the monitor

        :param datalogger:
        :type datalogger: :class:`datalog.DataLogger`
        """
        self.dataloggers.append(datalogger)

    def add_filter(self, filter):
        """
        Add filter to be applied in between the pdo converter and logger/graphs

        filter is one the classes deriving from :class:`FilterType` base class

        :param filter: A filter to be applied the datapoints
        :type filter: :class:`FilterType`
        """
        self.filters.append(filter)

    def add_scope_window(self, scope_window):
        """
        Adds a scope window for the monitor to send datapoints to

        :param scope_window:
        :type scope_window: :class: `scope.ScopeWindow`
        """
        self.scope_windows.append(scope_window)

    def start(self):
        """
        Starts the pdo converter and begins routing data to loggers

        This must be called after all the dataloggers are added
        """

        logger.info("Monitor Started")
        # Start the pdo_converter
        self.pdo_converter.start()

        # start all the DataLoggers
        for datalogger in self.dataloggers:
            datalogger.start()

        # start all the scope windows
        for scope_window in self.scope_windows:
            scope_window.start()

        self.active.set()
        # start the routing thread
        self.route_thread.start()

        # start the check thread
        self.check_thread.start()

    def stop(self):
        """
        Stops the monitor and all attached items

        Calling this should successfully end all threads in PDOConverter,
        Device and all dataloggers
        """
        # stop pdo converter
        self.pdo_converter.stop()

        # stop all the data loggers
        for datalogger in self.dataloggers:
            datalogger.stop()

        # stop the routing thread
        self.active.clear()
        if self.route_thread.is_alive():
            self.route_thread.join()

    def _route_loop(self):
        """
        Continuous loop run in thread to pass datapoints around

        Will stop automatically if all dataloggers are done
        """

        while(self.active.is_set()):
            # get the next set of datapoints
            datapoints = self.pdo_converter.get_datapoints()
            if datapoints is None:
                # pdo converter has stopped
                break

            # pass the datapoints through filters
            for filter in self.filters:
                filter.process(datapoints)

            # pass all the datapoints to the dataloggers
            for datalogger in self.dataloggers:
                datalogger.put(datapoints)

            # pass the datapoints to the scope window
            for scope_window in self.scope_windows:
                scope_window.add_datapoints(datapoints)

    def _check_loop(self):
        while(self.active.is_set()):
            dl_active = False
            # check if all the dataloggers are still active
            for datalogger in self.dataloggers:
                if datalogger.active.is_set():
                    dl_active = True
            scope_active = False
            if (len(self.scope_windows)):
                scope_active = True


            if not dl_active and not scope_active:
                logger.info("No more active dataloggers")
                # no more dataloggers are running, stop monitor
                self.stop()
                return

            time.sleep(2)


class FilterType(ABC):
    """
    Base class for Filter

    Child classes must implement the process method that acts on a list of
    datapoints, can change values, add more etc
    """

    @abstractmethod
    def process(self, datapoints):
        pass


class Calibrate(FilterType):
    """"
    Defines an offset and gain to be applied to the named signal

    Create a new signal by giving a new_name, keep the old one as well
    by setting keep to True

    :param name: Name of signal to act on
    :type name: :class:`String`
    :param offset: Offset applied to signal before gain
    :type offset: :class:`Float`
    :param gain: Gain applied to signal after offset
    :type gain: :class:`Float`
    :param new_name: Name of new signal. If None, signal value replaced
    :type new_name: :class:`String`
    :param keep: If True, creates a new signal with name new_name
    :type keep: :class:`Bool`
    """

    def __init__(self, name, offset=0, gain=1, new_name=None, keep=False):
        self.name = name
        self.offset = offset
        self.gain = gain
        self.new_name = new_name
        self.keep = keep

    def process(self, datapoints):
        # find the signal name
        for datapoint in datapoints:
            if datapoint.name == self.name:
                # calc new value
                value = (datapoint.value + self.offset) * self.gain
                # change in place if no new name
                if self.new_name is None:
                    datapoint.value = value
                else:
                    # if not keeping old, change in place
                    if not self.keep:
                        datapoint.value = value
                        datapoint.name = self.new_name
                    else:
                        # create a new datapoint and add to list
                        new_datapoint = Datapoint(
                            name=self.new_name,
                            value=value,
                            time=datapoint.time,
                            timestamp=datapoint.timestamp,
                            index=datapoint.index,
                        )
                        datapoints.append(new_datapoint)
                # Found datapoint, break from loop
                break


class InvalidArgumentsError(Exception):
    pass


logger = logging.getLogger(__name__)
