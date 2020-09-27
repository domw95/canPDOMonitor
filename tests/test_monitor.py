from canPDOMonitor.monitor import Monitor
from canPDOMonitor.datalog import DataLogger, TimeCondition
import time
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

# create the monitor
monitor = Monitor()

# create some dataloggers to add to Monitor
monitor.add_datalogger(DataLogger("montest1.txt",
                                  end_condition=TimeCondition(1)))
monitor.add_datalogger(DataLogger("montest2.txt",
                                  end_condition=TimeCondition(2)))

# start the monitor
monitor.start()

# with logger end conditions, monitor should stop automatically
# while(monitor.active.is_set()):
#     time.sleep(1)
