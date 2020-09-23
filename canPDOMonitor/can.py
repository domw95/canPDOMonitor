# -*- coding: utf-8
"""
Group of classes for general can stuff
"""

from abc import ABC, abstractmethod
import queue
import threading

class Device(ABC):
    """Main class for interfacing with CAN hardware.
    
    Specific hardware devices inherit from this.
    classes must implement _start and _stop methods
    CAN frames must be read from devices and placed into frame_queue async
    and thread safe following call to _start method
    """
    
    # maximum number of CAN frames to hold in queue
    # 4000 is 1 second of 4 PDOs at 1KHz 
    DEFAULT_QUEUE_SIZE = 4000
    def __init__(self, bitrate):
        self.bitrate = bitrate
        self.frame_queue = queue.Queue(maxsize=self.DEFAULT_QUEUE_SIZE)
        
        # active flag true when device running, false when stopped
        self.active = False
        # lock for reading/changing active flag
        self.active_lock = threading.Lock()
        
    def start(self):
        """
        To be called externally, calls _start method of class

        Clears the frame queue        
        then calls the device-specific _start method
        

        Returns
        -------
        None.

        """
        # clear the frame queue and start device
        self.clear_queue()
        
        # acquire lock to ensure active state change isnt interrupted by thread
        with self.active_lock:
            self._start()
            self.active = True
        
    def stop(self):
        """
        To be called externally, calls _stop method of class
        
        Calls the device specific _stop method
        Doesn't clear queue in case messages still need processing

        Returns
        -------
        None.

        """
        # add None to queue to indicate to consumer to stop
        self._add_to_queue(None)
        
        # stop the device
        with self.active_lock:
            self._stop()
            self.active = False
        
        
        
        
    def get_frame(self):
        """
        Gets the next frame from the queue, blocking execution
        
        Should be regularly called by whatever process is reciveing the frames
        returns None when can device has been stopped

        Returns
        -------
        frame : Frame
            The next CAN frame from the fifo queue
            None is passed to queue when stopped called

        """
        
        # Blocking call to get function
        return self.frame_queue.get(True)
        
    def clear_queue(self):
        """
        Safely empties the queue
        
        This will not work well if the CAN device is still running

        Returns
        -------
        None.

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

        Returns
        -------
        None.

        """
        pass
    
    @abstractmethod
    def _stop(self):
        """
        Exits the bus and clears the queue, stop adding frames to queue

        Returns
        -------
        None.

        """
        pass
    
    def _add_to_queue(self,frame):
        """
        Called to add a frame to the queue
        
        Method adds frame to queue whilst checking for overflow etc

        Parameters
        ----------
        frame : Frame
            Item of Frame class from CAN device

        Returns
        -------
        None.

        """
        if self.frame_queue.full():
            raise FrameQueueOverflowError()
        self.frame_queue.put(frame)
   
class Frame:
    """
    Class to hold frame information
    
    Properties:
        id = decimal representation of can frame id
        data = byte array length 8
        timestamp = timestamp in ms
        dlc = length of data
        error = true if frame is error frame
    """
    
    def __init__(self,id=0,
                 data=bytearray((0,0,0,0,0,0,0,0)),
                 timestamp=0,dlc=8,error=False):
        self.id = id
        self.data = data
        self.timestamp = timestamp
        self.dlc = dlc
        self.error = error
        
class FrameQueueOverflowError(Exception):
    pass
        
