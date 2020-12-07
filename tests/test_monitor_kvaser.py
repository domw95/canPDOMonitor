"""
Runs the monitor with kvaser device
"""
from canPDOMonitor.monitor import Monitor, Calibrate
from canPDOMonitor.datalog import DataLogger, TimeCondition
from canPDOMonitor.can import Format
from canPDOMonitor.kvaser import Kvaser
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

# pdo format
format = Format(odr="CAN_SYS_PDO_default.odr")

# device
device = Kvaser()

monitor = Monitor(format=format, device=device)

# create some dataloggers to add to Monitor
monitor.add_datalogger(DataLogger("montest1.csv",
                                  end_condition=TimeCondition(10)))
monitor.add_datalogger(DataLogger("montest2.csv",
                                  end_condition=TimeCondition(20)))

for i in range(5):
    monitor.add_filter(Calibrate(
        name="In Pressure{} Cal".format(i+1),
        offset=128,
        gain=16,
        new_name="In Pressure{} Raw".format(i+1),
    ))

# start the monitor, which ends automagically
monitor.start()
