class Datapoint:
    def __init__(self,name,value,time,timestamp,index,raw_value=None):
        # signal name: string
        self.name = name
        # value: float
        self.value = value
        # timestamp from canbus
        self.timestamp = timestamp
        # sequence time since start
        self.time = time
        # index of datapoint since start
        self.index = index
        # raw value of signal before offset/gain applied (if not 0/1)
        self.raw_value = raw_value
