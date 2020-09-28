"""
Checks the scope display from the monitor
"""

from canPDOMonitor.monitor import Monitor
from canPDOMonitor.scope import Scope, ScopeWindow, app
from canPDOMonitor.kvaser import Kvaser
from canPDOMonitor.can import Format
from canPDOMonitor.datalog import (DataLogger, TimeCondition, CountCondition,
                                   TriggerCondition, Trigger)
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

# pdo format
format = Format(odr="CAN_SYS_PDO_default.odr")

# device
device = Kvaser()

# create the monitor
monitor = Monitor(format=format, device=device)

# create a scope window
scope_window = ScopeWindow()

# create a scope to display a signal
scope = Scope(["Wave Gen Out"], 2000)

scope_window.add_scope(scope)

monitor.add_scope_window(scope_window)

# monitor.add_datalogger(DataLogger("short_test.csv",
#                                   start_condition=TriggerCondition(
#                                     Trigger.Rising, "Wave Gen Out"
#                                   ),
#                                   end_condition=CountCondition(20001)))

# start the monitor, which ends automagically
monitor.start()

app.exec_()
