# -*- coding: utf-8

from abc import ABC, abstractmethod
import queue

class Device(ABC):
    """Main class for interfacing with CAN hardware.
    
    Specific hardware devices inherit from this
    """
    
    # maximum number of CAN frames to hold in queue
    # 4000 is 1 second of 4 PDOs at 1KHz 
    DEFAULT_QUEUE_SIZE = 4000
    def __init__(self, bitrate):
        self.bitrate = bitrate
        self.frame_queue = queue.Queue(maxsize=self.DEFAULT_QUEUE_SIZE)
        
    def start(self):
        """
        To be called externally, calls _start method of class

        Clears the frame queue        
        then calls the device-specific _start method
        

        Returns
        -------
        None.

        """
        self._start()
        
    def stop(self):
        """
        To be called externally, calls _stop method of class
        
        Calls the device specific _stop method
        then clears the queue

        Returns
        -------
        None.

        """
        self._stop()
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
    
    def _addToQueue(frame):
        """
        Called to add a frame to the queue
        
        Method adds frame to queue whilst checking for overflow etc

        Parameters
        ----------
        frame : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        


    

"""
Class to hold frame information
"""        
class Frame:
    def __init__(self):
        pass
        
