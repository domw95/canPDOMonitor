from canPDOMonitor.monitor import Monitor, Calibrate
from canPDOMonitor.datalog import DataLogger, TimeCondition
from canPDOMonitor.can import Format
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

# pdo format
format = Format(odr="CAN_SYS_PDO.odr")

# create the monitor
monitor = Monitor(format=format)

# create some dataloggers to add to Monitor
monitor.add_datalogger(DataLogger("montest1.txt",
                                  end_condition=TimeCondition(1)))
monitor.add_datalogger(DataLogger("montest2.txt",
                                  end_condition=TimeCondition(2)))

monitor.add_filter(Calibrate(
    name="In Pressure1 Cal",
    offset=128,
    gain=16,
    new_name="In Pressure1 Raw",
    keep=True
))

monitor.add_filter(Calibrate(
    name="In Pressure2 Cal",
    offset=128,
    gain=16,
    new_name="In Pressure2 Raw",
))

# start the monitor, which ends automagically
monitor.start()
