"""
Classes for displaying data live on the screen
"""

from PyQt5 import QtWidgets
from PyQt5.QtCore import QTimer
import pyqtgraph as pg
from enum import Enum
from collections import deque
import threading
import queue
import logging

# Enable antialiasing for prettier plots
pg.setConfigOptions(antialias=True)
# main qt wotsit
app = QtWidgets.QApplication([])


class ScopeWindow(pg.GraphicsLayoutWidget):
    """
    Window for displaying scopes
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # set window title
        self.setWindowTitle("Scope")
        # create layout widget in which to place scopes
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
                        self.addItem(
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
    :param samples: Number of datapoints to display
    :type samples: :class: `Int`
    :param trigger: Trigger for start of plot
    :type trigger: :class:`ScopeTrigger`
    :param mode: Rolling, Redraw or Sliding
    :type mode: :class:`DisplayMode`
    :param yrange: Single value for symmetric or list for min/max, auto if not
        set
    :type yrange: :class:`Float`
    :param title: Title to display above scope
    :type title: :class:`String`
    :param time_zero: If true, the scope starts at t=0 for each trigger.
        For rolling scopes this has no effect
    :type time_zero: :class:`Bool`
    """
    Line_Colours = ["c", "m", "y", "g", "r", "b"]

    def __init__(self, signals,
                 nsamples=None, samplerate=None, samplelength=None,
                 trigger=None, mode=None,
                 yrange=None, title=None, time_zero=True):
        super(Scope, self).__init__()
        # store args
        self.signal_names = signals
        if trigger is not None and isinstance(trigger, dict):
            self.trigger = ScopeTrigger(**trigger)
        else:
            self.trigger = trigger
        self.title = title
        if mode is None:
            self.mode = DisplayMode.Rolling
        elif isinstance(mode, str):
            # convert string or enum to enum type
            self.mode = DisplayMode[mode]
        else:
            self.mode = mode

        if (nsamples is None and samplerate is not None
                and samplelength is not None):
            # calc number of samples from rate and time
            nsamples = round(samplerate * samplelength)
        elif (nsamples is not None and samplerate is None
                and samplelength is not None):
            # calc rate from samples and time
            samplerate = nsamples / samplelength
        elif (nsamples is not None and samplerate is not None
                and samplelength is None):
            # calc length from samples and rate
            samplelength = nsamples / samplerate
        else:
            raise InsufficientArgumentsError

        self.nsamples = nsamples
        self.samplelength = samplelength
        self.samplerate = samplerate

        # queue for incoming datapoints
        self.data_queue = queue.Queue()
        # buffer for holding the plot data and time values
        self.buffer = ScopeBuffer(
            signal_names=self.signal_names + ["Time"],
            ndatapoints=self.nsamples,
            mode=mode
        )
        self.addLegend(offset=(10, -10))
        self.setTitle(title)
        # plot data items to display on scope
        self.plot_data_item = {}
        for i, signal in enumerate(self.signal_names):
            # create a plot item (line) for displaying and add to scope
            self.plot_data_item[signal] = self.plot(name=signal)
            self.plot_data_item[signal].setPen(color=self.Line_Colours[i])

        # thread for pulling in data
        self.data_thread = threading.Thread(target=self._data_loop)
        # time that runs in event loop to refresh scope
        self.display_timer = QTimer()
        self.display_timer.timeout.connect(self._refresh_scope)

        # plot item stuff
        self.showGrid(x=True, y=True)
        self.setMouseEnabled(False, False)
        # initiall disable autorange
        self.disableAutoRange()
        # set yrange if argument given
        if yrange is not None:
            if isinstance(yrange, list):
                self.setYRange(*yrange)
            else:
                self.setYRange(-yrange, yrange)
        else:
            # enable autorange if no yrange specified
            self.enableAutoRange(y=True)

        # offset used to time data to align first datapoint on plot with 0
        self.time_offset = 0
        # cannot offset time with no trigger
        if trigger is None:
            time_zero = False
        self.time_zero = time_zero

        if self.mode is DisplayMode.Rolling:
            # always autorange as time is alwasy changing
            self.enableAutoRange(x=True)
            # disable zeroing time as irrelevant for rolling
            self.time_zero = False
        elif self.mode is DisplayMode.Redraw:
            if time_zero:
                # can fix range
                self.setXRange(0, self.samplelength, padding=0)
            else:
                # autorange for incrementing time
                self.enableAutoRange(x=True)
        elif self.mode is DisplayMode.Sliding:
            if time_zero:
                # can fix range
                self.setXRange(0, self.samplelength, padding=0)
            else:
                # autorange for incrementing time
                self.enableAutoRange(x=True)

    def start(self):
        # start the scope threads
        self.data_thread.start()
        self.display_timer.start(100)

    def add_datapoints(self, datapoints):
        """
        Add a list of datapoints to the data queue, potentially to be shown
        """
        self.data_queue.put(datapoints)
        

    def _data_loop(self):
        """
        Pulls datapoints from data_queue and adds the values to deques
        """
        # flag to determine if data should be put in buffer
        self.triggered = False

        while(True):
            # get next datapoitns from queue
            # logger.debug("Get next datapoint")
            datapoints = self.data_queue.get()
            
            # end if None
            if datapoints is None:
                break

            signals = [d for d in datapoints if d.name in self.signal_names]

            if len(signals) == 0:
                logger.warn("No Matching Signal names")
                continue

            # create dict of values, offsetting time value if required
            values = {"Time": signals[0].time}
            for sig in signals:
                values[sig.name] = sig.value
            if self.trigger is None:
                # free run mode, all datapoints to buffer
                self.buffer.append(values)
            else:
                # get the value of the trigger signal if not already
                if self.trigger.name not in self.signal_names:
                    for d in datapoints:
                        if d.name == self.trigger.name:
                            values[self.trigger.name] = d.value
                if self.triggered:
                    # scope has been triggered, put data in buffer
                    # adjust time
                    values["Time"] = values["Time"] - self.time_offset
                    if self.buffer.append(values):
                        # buffer has filled, rearm trigger with current values
                        logger.debug("Buffer Full")
                        self.trigger.reset(values)
                        self.triggered = False
                else:
                    # need to check trigger
                    if self.trigger.check(values):
                        logger.debug("Triggered")
                        self.triggered = True
                        # check if time should start at 0
                        if self.time_zero:
                            self.time_offset = values["Time"]
                            values["Time"] = 0
                        self.buffer.append(values)

    def _refresh_scope(self):
        """
        Refreshes the data displayed on scope according to scope settings
        """
        # go through each signal and set data on plot
        # logger.debug("Updating scope")
        data = self.buffer.get_data()
        # logger.debug("{}".format(data))
        if data is not None:
            for signal in self.signal_names:
                self.plot_data_item[signal].setData(
                    data["Time"],
                    data[signal]
                )

            # set ranges if required


class ScopeSettings():
    """
    Holds scope settings for passing to Scope and sending as JSON
    """
    def __init__(self, signals,
                 nsamples, samplerate,
                 mode=None, title="", trigger=None,
                 yrange=None, time_zero=True):
        self.signals = signals
        self.nsamples = nsamples
        self.samplerate = samplerate
        if mode is not None:
            self.mode = str(mode)
        self.title = title
        if trigger is not None:
            self.trigger = trigger.__dict__
        if yrange is not None:
            self.yrange = yrange


class ScopeBuffer():
    """
    Implements a couple of deques for live and capture data.

    Calls to append and get data are processed depending on mode
    """

    def __init__(self, signal_names, ndatapoints, mode=None):
        if mode is None:
            self.mode = DisplayMode.Rolling
        else:
            self.mode = mode
        self.ndatapoints = ndatapoints
        self.signal_names = signal_names
        # create 3 buffers:
        # 0 or 1 are for live and collect (can switch)
        # 2 is for copying into when scope retrieves data
        # each buffer contains a dict with signal name key to deque
        self.buffers = []
        for i in range(3):
            self.buffers.append(dict(zip(
                signal_names,
                [deque(maxlen=ndatapoints) for sig in signal_names])))

        self.switched = False
        self.live_buffer = self.buffers[0]
        self.collect_buffer = self.buffers[1]
        self.output_buffer = self.buffers[2]
        # flag to indicate that new data is availabe to be redrawn
        self.updated = threading.Event()

        # lock to make whole class thread safe
        # this will block gui event loop so make sure things are quick
        self.lock = threading.Lock()

    def append(self, values):
        """
        Adds new data to the correct buffer and sets updated event when new
        data is to draw to screen

        returns True in the following cases

        DisplayMode.Rolling: Never
        DisplayMode.Redraw: when the collect buffer fills and swtches to live
        DisplayMode.Sliding when the live buffer fills

        :param values: dict with keys to match signal names
        :param type: :class:`dict`
        """
        with self.lock:
            # If in rolling mode, always add to live
            
            if self.mode == DisplayMode.Rolling:
                self._add_to_buffer(values, self.live_buffer)
                self.updated.set()
                return False
            # if in redraw mode, double buffer and switch
            elif self.mode == DisplayMode.Redraw:
                # this mode always appends to collect buffer
                self._add_to_buffer(values, self.collect_buffer)
                # When it overflows, indicate that new data is available
                if self._buffer_full(self.collect_buffer):
                    self.updated.set()
                    # switch buffers
                    self._switch_buffers()
                    # clear the collect buffer
                    self._clear_buffer(self.collect_buffer)
                    return True
                return False

            # if in sliding mode, add to live until full, then switch
            elif self.mode == DisplayMode.Sliding:
                # check if live buffer is full
                if self._buffer_full(self.live_buffer):
                    if (self.updated.is_set()):
                        # buffer is full but has not been displayed yet
                        # add to collect buffer
                        self._add_to_buffer(values, self.collect_buffer)
                        if self._buffer_full(self.collect_buffer):
                            raise BufferOverflowError(
                                "Sliding Scope: Collect buffer"
                            )
                        return False
                    else:
                        # full live buffer has been shown, switch buffers
                        self._switch_buffers()
                        # clear out the collect buffer
                        self._clear_buffer(self.collect_buffer)

                # stick it in live buffer
                self._add_to_buffer(values, self.live_buffer)
                self.updated.set()
                # if live is full, return True
                if self._buffer_full(self.live_buffer):
                    return True
                # indicate that things have been updated

                return False

    def get_data(self, live=True):
        """
        Returns dictionary of deques, where the key is signal name

        The return value is made thread safe by copying
        """
        with self.lock:
            if self.updated.is_set():
                self._update_output_buffer()
                self.updated.clear()
                return self.output_buffer
            else:
                return None

    def _update_output_buffer(self):
        """
        copys over the values from the live buffer to the output
        """
        for key in self.live_buffer:
            # shallow copy should be sufficent as deque contains floats
            self.output_buffer[key] = self.live_buffer[key].copy()

    def _add_to_buffer(self, values, buffer):
        """
        Internal function for appending a set of data to buffer deques
        """
        # go through all signals, add them to queue
        if abs(len(values) - len(self.signal_names)) > 1:
            raise SignalMismatchError
        for key in values:
            if key in buffer:
                buffer[key].append(values[key])

    def _clear_buffer(self, buffer):
        """
        internal function used to clear all deques in a buffer
        """
        # go through each deque
        for deck in buffer.values():
            deck.clear()

    def _buffer_full(self, buffer):
        """
        Returns a boolean to indicate if a buffer is full
        """
        # get arbitrary deque from buffer dict (if they arent the same length
        # something has gone very wrong)
        d = list(buffer.values())[0]
        if len(d) == d.maxlen:
            return True
        else:
            return False

    def _switch_buffers(self):
        """
        Switches which buffer live_buffer and collect_buffer point to:
        """
        if self.switched:
            # set live to 0 and collect to 1
            self.live_buffer = self.buffers[0]
            self.collect_buffer = self.buffers[1]
        else:
            # set live to 1 and collect to 0
            self.live_buffer = self.buffers[1]
            self.collect_buffer = self.buffers[0]
        # invert the flag
        self.switched = not self.switched


class ScopeTrigger():
    def __init__(self, name, edge, threshold=0):
        self.name = name
        if isinstance(edge, str):
            self.edge = TriggerEdge[edge]
        else:
            self.edge = edge
        self.threshold = threshold
        self.prev_value = None
        self.trig_count = 0

    def check(self, values):
        """
        Checks a dict of signals against the trigger condition
        """
        # check that signal in values
        if self.name in values:
            # get the current value
            value = values[self.name]
            # check if first call to trigger
            if self.prev_value is None:
                self.prev_value = value
                return False

            trig = False
            # check for a rising edge
            if ((self.edge == TriggerEdge.Rising
                    or self.edge == TriggerEdge.Either)
                    and self.prev_value < self.threshold
                    and value >= self.threshold):
                trig = True

            # check for a falling edge
            elif ((self.edge == TriggerEdge.Falling
                    or self.edge == TriggerEdge.Either)
                    and self.prev_value > self.threshold
                    and value <= self.threshold):
                trig = True

            # check for an equals condition
            elif (self.edge == TriggerEdge.Equal
                    and value == self.threshold):
                trig = True
            if trig:
                self.trig_count = self.trig_count + 1
            self.prev_value = value
            return trig

        else:
            raise TriggerNameError

    def reset(self, values=None):
        """
        resets the trigger, optionally holds the prev value from values
        """
        if values is None:
            self.prev_value = None
        else:
            self.prev_value = values[self.name]


class TriggerSettings():
    """
    Holds trigger settings for passing to ScopeTrigger or sending as JSON
    """
    def __init__(self, name, edge, threshold=0):
        self.name = name
        self.edge = str(edge)
        self.threshold = threshold


class TriggerEdge(Enum):
    Rising = 1
    Falling = 2
    Either = 3
    Equal = 4
    Increment = 5
    Decrement = 6

    def __str__(self):
        return self.name


class DisplayMode(Enum):
    # Refreshes data live, pop and appending data (only with freerun)
    Rolling = 1
    # Waits until full collection of data then updates screen
    Redraw = 2
    # Live update of data collection
    Sliding = 3

    def __str__(self):
        return self.name


class NoScopesError(Exception):
    pass


class InvalidScopesError(Exception):
    pass


class BufferOverflowError(Exception):
    def __init__(self, msg=None):
        super().__init__(msg)


class SignalMismatchError(Exception):
    pass


class TriggerNameError(Exception):
    pass


class InsufficientArgumentsError(Exception):
    pass


logger = logging.getLogger(__name__)

if __name__ == '__main__':
    sw = ScopeWindow()
    for i in range(1):
        sw.add_scope(Scope(["Wave Gen Out"], 1000))
    sw.start()
    app.exec_()
