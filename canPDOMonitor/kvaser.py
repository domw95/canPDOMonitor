from canPDOMonitor.can import Device, Frame
from canlib import canlib
import threading
import time
import logging

bitrates = {
    1000000: canlib.canBITRATE_1M,
    500000: canlib.canBITRATE_500K,
    25000: canlib.canBITRATE_250K,
    125000: canlib.canBITRATE_125K,
    100000: canlib.canBITRATE_100K,
    62000: canlib.canBITRATE_62K,
    50000: canlib.canBITRATE_50K,
    83000: canlib.canBITRATE_83K,
    10000: canlib.canBITRATE_10K,
}


class Kvaser(Device):
    """
    Class for communicating with kvaser hardware using the kvaser canlib

    inherits from :class:`can.Device`
    """

    def __init__(self, bitrate=1000000, channel=0):
        super().__init__(bitrate)
        # reinit library to clearup any previous connections
        canlib.reinitializeLibrary()

        # create the channel
        self.ch = canlib.openChannel(
            channel,
            bitrate=bitrates[bitrate],
            flags=canlib.Open.EXCLUSIVE)

        # set the device mode to normal (sends ACKs)
        self.ch.setBusOutputControl(canlib.Driver.NORMAL)

        # clear the recieve buffer
        self.ch.iocontrol.flush_rx_buffer()

        # filter out heartbeats as they seem to screw up the buffer
        self.ch.canSetAcceptanceFilter(0x080, 0x080)

        # thread for fetching messages form device
        self.read_thread = threading.Thread(target=self._read_loop)

        # variable to indicate if thread is running. clear to stop it
        self.reading = threading.Event()
        self.reading.clear()

    def _start(self):
        # stop the device just in case
        # self._stop()

        logger.debug("Starting Kvaser")

        # clear the buffer
        self.ch.iocontrol.flush_rx_buffer()

        # activate the CAN device
        self.ch.busOn()

        # start the read thread
        self.reading.set()
        self.read_thread.start()

    def _stop(self):
        logger.debug("Stopping Kvaser")
        # clear the reading event to inidicate thread to stop
        self.reading.clear()

        # wait for thread to end, give it a second to do so
        if self.read_thread.is_alive():
            self.read_thread.join(timeout=1)
        if self.read_thread.is_alive():
            # thread failed to end, something is borked
            raise KvaserError("Failed to stop read thread")

        # exit the bus
        self.ch.busOff()

        # clear the buffer
        self.ch.iocontrol.flush_rx_buffer()

        # give the canlib a change to garbage collect
        # time.sleep(1)

        logger.debug("Kvaser stopped")

    def _read_loop(self):
        """
        Started in thread. Continuously fetches all the message on device

        Returns
        -------
        None.

        """

        # check that stop hasnt been called
        while(self.reading.is_set()):
            # Get all the messages from the device
            if not self._read_messages():
                return
            # wait for a length of time to let other threads run
            # 10ms = 40 messages
            time.sleep(0.01)

        # thread ends here, do any clear up as required

    def _read_messages(self):
        """
        Reads all the messages from device and places them in queue

        Returns
        -------
        None.

        """
        # print("\rQueue size: {}".format(self.ch.iocontrol.rx_buffer_level),
        # flush=True,end="\r")
        while(self.reading.is_set()):

            try:
                # try get a message
                frame = self.ch.read()

                # If got a frame, convert to custom frame type and place in
                # queue
                if not self._add_to_queue(Frame(id=frame.id, data=frame.data,
                                         timestamp=frame.timestamp,
                                         dlc=frame.dlc)):
                    return False
                # print(type(frame.data))

            except canlib.CanNoMsg:
                # no more messages available
                return True


class KvaserError(Exception):
    def __init__(self, msg="Kvaser Error"):
        super().__init__(msg)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    k = Kvaser()
    k.start()
    count = 0
    while(count < 100):
        frame = k.get_frame()
        if (frame is not None):
            count = count + 1
            print(frame)
        else:
            break
    
    k.stop()
    time.sleep(1)
