"""
Demonstrates using the monitor with odr and kvaser and calibrating the
values before they are logged to file
"""

from canPDOMonitor.monitor import Monitor, Calibrate
from canPDOMonitor.datalog import (DataLogger, TimeCondition, CountCondition,
                                   TriggerCondition, Trigger)
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
monitor.add_datalogger(DataLogger("large_test.csv",
                                  end_condition=TimeCondition(10)))
monitor.add_datalogger(DataLogger("short_test.csv",
                                  start_condition=TriggerCondition(
                                    Trigger.Rising, "Wave Gen Out"
                                  ),
                                  end_condition=CountCondition(2001)))
monitor.add_datalogger(DataLogger("wave_test.csv",
                                  start_condition=TriggerCondition(
                                    Trigger.Rising, "Wave Gen Out"
                                  ),
                                  end_condition=TriggerCondition(
                                    Trigger.Rising, "Wave Gen Out"
                                  )))

monitor.add_datalogger(DataLogger("wave5_test.csv",
                                  start_condition=TriggerCondition(
                                    Trigger.Rising, "Wave Gen Out"
                                  ),
                                  end_condition=TriggerCondition(
                                    Trigger.Rising, "Wave Gen Out", count=5
                                  )))

# reconstruct raw pressure values
for i in range(5):
    monitor.add_filter(Calibrate(
        name="In Pressure{} Cal".format(i+1),
        offset=128,
        gain=16,
        new_name="In Pressure{} Raw".format(i+1),
    ))

offset = [-2091, -2048, -2177, -2169, -2030]
gain = [0.2406, 0.2461, 0.2447, 0.245, 5.181]

for i, (o, g) in enumerate(zip(offset, gain)):
    monitor.add_filter(Calibrate(
        name="In Pressure{} Raw".format(i+1),
        offset=o,
        gain=g,
        new_name="In Pressure{}".format(i+1),
        keep=True
    ))


# start the monitor, which ends automagically
monitor.start()
