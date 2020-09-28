"""
Classes for displaying data live on the screen
"""

from PyQt5 import QtWidgets
import pyqtgraph as pg
from enum import Enum
from collections import deque
import threading
import queue
import logging
import time

# Enable antialiasing for prettier plots
pg.setConfigOptions(antialias=True)
# main qt wotsit
app = QtWidgets.QApplication([])


class ScopeWindow(QtWidgets.QMainWindow):
    """
    Window for displaying scopes
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # set window title
        self.setWindowTitle("Scope")
        # create layout widget in which to place scopes
        self.layout = pg.GraphicsLayoutWidget()
        # add layout as main widget
        self.setCentralWidget(self.layout)
        # maximise the window
        self.showMaximized()
        # list of scopes to show
        self.scopes = []

    def add_scope(self, scope):
        """
        Adds a scope to the list of scopes

        Doesn't actually create the graphics item yet as layout needs to be
        determined on calls to :py:func: `ScopeWindow.start`
        """

        self.scopes.append(scope)

    def start(self):
        """
        Starts the scope window and all contained scopes
        """

        # first create the layout
        self._create_layout()

        # start eahc scope and the ScopeWindow threads
        for scope in self.scopes:
            scope.start()

    def add_datapoints(self, datapoints):
        """
        Adds the list of datapoints to all attached scopes in window
        """
        for scope in self.scopes:
            scope.add_datapoints(datapoints)

    def _create_layout(self):
        """
        Creates the scope layout depending on the number of scopes
        that have been added
        """
        rect_layout = range(1, 10)
        rows = [1, 2, 2, 2, 2, 2, 2, 2, 3]
        cols = [1, 1, 2, 2, 3, 3, 4, 4, 3]
        # add_layout = [3, 5, 7]
        nscopes = len(self.scopes)
        if nscopes == 0:
            raise NoScopesError
        elif nscopes in rect_layout:
            # get the index of layout
            ind = rect_layout.index(nscopes)
            n = 0
            for i in range(rows[ind]):
                for j in range(cols[ind]):
                    if n < nscopes:
                        self.layout.addItem(
                            self.scopes[n],
                            row=i,
                            col=j
                        )
                    n = n + 1
        else:
            raise InvalidScopesError


class Scope(pg.PlotItem):
    """
    Implements a live scope as a pyqtgraph plot item

    :param signal_names: List of signals to show on this scope
    :type signal_names: :class: `String`
    :param ndatapoints: Number of datapoints to display
    :type ndatapoints: :class: `Int`
    """

    def __init__(self, signal_names, ndatapoints, trigger=None):
        super().__init__()
        # store args
        self.signal_names = signal_names
        self.ndatapoints = ndatapoints
        # queue for incoming datapoints
        self.data_queue = queue.Queue()
        # deques for storing plot data
        self.plot_buffer = {"Time": deque(maxlen=self.ndatapoints)}
        # plot data items to display on scope
        self.plot_data_item = {}
        for signal in self.signal_names:
            self.plot_buffer[signal] = deque(maxlen=self.ndatapoints)
            self.plot_data_item[signal] = pg.PlotDataItem()
            self.addItem(self.plot_data_item[signal])
        # flag to indicate

        # threads for pulling in data and displaying
        self.data_thread = threading.Thread(target=self._data_loop)
        self.display_thread = threading.Thread(target=self._display_loop)

    def start(self):
        # start the scope threads
        self.data_thread.start()
        self.display_thread.start()

    def add_datapoints(self, datapoints):
        """
        Add a list of datapoints to the data queue, potentially to be shown
        """
        self.data_queue.put(datapoints)

    def _data_loop(self):
        """
        Pulls datapoints from data_queue and adds the values to deques
        """

        while(True):
            # get next datapoitns from queue
            # logger.debug("Get next datapoint")
            datapoints = self.data_queue.get()
            # end if None
            if datapoints is None:
                break

            # get the datapoints we want
            signals = [d for d in datapoints if d.name in self.signal_names]

            if len(signals) == 0:
                logger.warn("No Matching Signal names")
                continue

            # assume we are rolling freerun for now
            # add all signals to deques
            for sig in signals:
                self.plot_buffer[sig.name].append(sig.value)
            self.plot_buffer["Time"].append(sig.time)
            # logger.debug(len(self.plot_buffer["Time"]))

    def _display_loop(self):
        """
        Refreshes the data displayed on scope according to scope settings
        """
        while(True):
            # go through each signal and set data on plot
            # logger.debug("Updating scope")
            for signal in self.signal_names:
                self.plot_data_item[signal].setData(
                    self.plot_buffer["Time"],
                    self.plot_buffer[signal]
                )
            time.sleep(.1)


class DisplayMode(Enum):
    # Refreshes data live, pop and appending data (only with freerun)
    Rolling = 1
    # Waits until full collection of data then updates screen
    Redraw = 2
    # Live update of data collection
    Sliding = 3


class NoScopesError(Exception):
    pass


class InvalidScopesError(Exception):
    pass


logger = logging.getLogger(__name__)

if __name__ == '__main__':
    sw = ScopeWindow()
    for i in range(1):
        sw.add_scope(Scope(["Wave Gen Out"], 1000))
    sw.start()
    app.exec_()
