# -*- coding: utf-8 -*-
"""
Created on Thu Sep 24 15:39:29 2020

@author: Research
"""
import threading
import queue


class DataLog:
    """
    Writes datapoints to file
    """
    def __init__(self,filename,trigger=None):
        # open file used to log data
        self.file=open(filename,'w')
        
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
                    self.file.write(","+ h)
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
        
if __name__ == "__main__":
    
    from kvaser import Kvaser
    from pdo import PDOConverter, FrameFormat, Format
    
    # set up kvaser device
    device = Kvaser()
    
    # create logger
    dlog = DataLog("test.txt")
    
    # set up PDO formats
    format = Format()
    format.add(FrameFormat(0x181,use7Q8=False,
                           name=["Wave Gen Out","Encoder Pos"]))
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
        
    
    
    