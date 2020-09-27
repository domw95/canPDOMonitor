"""
Main classes for running the canPDOMonitor

Monitor routes datapoints from a pdo_converter to attached dataloggers,
managing the stopping and starting of each.  Can use a CAN_SYS_PDO.order
object dictionary to choose PDO format
"""

from canPDOMonitor.can import PDOConverter, DefaultFormat
from canPDOMonitor.virtual import Virtual
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

        # List of dataloggers
        self.dataloggers = []

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

            # pass all the datapoints to the dataloggers
            for datalogger in self.dataloggers:
                datalogger.put(datapoints)

    def _check_loop(self):
        while(self.active.is_set()):
            dl_active = False
            # check if all the dataloggers are still active
            for datalogger in self.dataloggers:
                if datalogger.active.is_set():
                    dl_active = True

            if not dl_active:
                logging.info("No more active dataloggers")
                # no more dataloggers are running, stop monitor
                self.stop()
                return

            time.sleep(2)


class InvalidArgumentsError(Exception):
    pass


logger = logging.getLogger(__name__)
