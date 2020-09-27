from canPDOMonitor.virtual import Virtual
from canPDOMonitor.can import PDOConverter, FrameFormat, Format
from canPDOMonitor.datalog import (TriggerCondition, DataLogger, CountCondition,
                                   TimeCondition, Trigger)
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
logger.info("Running datalog test")

# set up kvaser device
device = Virtual()

# create logger to record one wave cycle
start_cond = TriggerCondition(Trigger.Rising, "Wave Gen Out")
end_cond = TriggerCondition(Trigger.Rising, "Wave Gen Out")
dlog1 = DataLogger("test1.txt", start_cond, end_cond)

start_cond = TriggerCondition(Trigger.Falling, "Wave Gen Out")
end_cond = CountCondition(1500)
dlog2 = DataLogger("test2.txt", start_cond, end_cond)

start_cond = TriggerCondition(Trigger.Rising, "Wave Gen Out")
end_cond = TimeCondition(2)
dlog3 = DataLogger("test3.txt", start_cond, end_cond)

# set up PDO formats
format = Format()
format.add(FrameFormat(0x181, use7Q8=False,
                       name=["Wave Gen Out", "Encoder Pos"]))
format.add(FrameFormat(0x281))
format.add(FrameFormat(0x381))
format.add(FrameFormat(0x481))

# start PDO converter
pdo_converter = PDOConverter(device, format)
pdo_converter.start()
dlog1.start()
dlog2.start()
dlog3.start()

# fetch a load of datapoints from converter and put them to logger
while(pdo_converter.data_count < 1000*10):
    datapoints = pdo_converter.data_queue.get()
    dlog1.put(datapoints)
    dlog2.put(datapoints)
    dlog3.put(datapoints)

pdo_converter.stop()
dlog1.stop()
dlog2.stop()
dlog3.stop()
