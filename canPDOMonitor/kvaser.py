from device import Device
from canlib import canlib

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
        
    def _start(self):
        # clear the buffer
        self.ch.iocontrol.flush_rx_buffer()
        
        # activate the CAN device
        self.ch.busOn()
    
    def _stop(self):
        # exit the bus
        self.ch.busOff()
        
        # clear the buffer
        self.ch.iocontrol.flush_rx_buffer()
    
if __name__ == "__main__":
    k = Kvaser()
    