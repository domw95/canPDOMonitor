from can import Device, Frame
from canlib import canlib
import threading
import time

bitrates = {
    '1M': canlib.canBITRATE_1M,
    '500K': canlib.canBITRATE_500K,
    '250K': canlib.canBITRATE_250K,
    '125K': canlib.canBITRATE_125K,
    '100K': canlib.canBITRATE_100K,
    '62K': canlib.canBITRATE_62K,
    '50K': canlib.canBITRATE_50K,
    '83K': canlib.canBITRATE_83K,
    '10K': canlib.canBITRATE_10K,
}

class Kvaser(Device):
    """
    Class for communicating with kvaser hardware using the kvaser canlib
    
    inherits from Device
    """
    def __init__(self, bitrate='1M', channel=0):
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
        #self._stop()
        
        # clear the buffer
        self.ch.iocontrol.flush_rx_buffer()
        
        # activate the CAN device
        self.ch.busOn()
        
        # start the read thread
        self.reading.set()
        self.read_thread.start()
    
    def _stop(self):
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
        time.sleep(1)
        
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
            self._read_messages()
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
        print("\rQueue size: {}".format(self.ch.iocontrol.rx_buffer_level),
              flush=True,end="\r")
        while(self.reading.is_set()):
            
            try:
                # try get a message
                frame = self.ch.read()
                
                # If got a frame, convert to custom frame type and place in 
                # queue
                self._add_to_queue(Frame(id=frame.id,data=frame.data,
                                   timestamp=frame.timestamp,dlc=frame.dlc))
                # print(type(frame.data))
                
            except canlib.CanNoMsg:
                # no more messages available
                return

class KvaserError(Exception):
    def __init__(self,msg="Kvaser Error"):
        super().__init__(msg)
    
if __name__ == "__main__":
    k = Kvaser()
    k.start()
    count = 0
    while(count < 100):
        frame = k.get_frame()
        if (frame is not None):
            count = count + 1
            print(frame.id)            
        else:
            break
    k.stop()
    time.sleep(1)
    