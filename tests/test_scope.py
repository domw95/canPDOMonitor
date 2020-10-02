"""
Checks the scope display from the monitor
"""

from canPDOMonitor.monitor import Monitor
from canPDOMonitor.scope import (Scope, ScopeWindow, app, DisplayMode,
                                 ScopeTrigger, TriggerEdge)
from canPDOMonitor.kvaser import Kvaser
from canPDOMonitor.can import Format
from canPDOMonitor.datalog import (DataLogger, TimeCondition, CountCondition,
                                   TriggerCondition, Trigger)
import logging
import time

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

# pdo format
format = Format(odr="CAN_SYS_PDO_ISA_model.odr")

# device
device = Kvaser()

# create the monitor
monitor = Monitor(format=format, device=device)

# create a scope window
scope_window = ScopeWindow()

scope_window.add_scope(Scope(["Wave Gen Out", "mLoad Position mm"],
                             1000, 1000, mode=DisplayMode.Redraw,
                             title="Redraw",
                             yrange=50,
                             trigger=ScopeTrigger(
                             "Wave Gen Out",
                             edge=TriggerEdge.Rising)))

scope_window.add_scope(Scope(["Wave Gen Out", "mLoad Position mm"],
                             1000, 1000, mode=DisplayMode.Rolling,
                             title="Rolling",
                             yrange=50,
                             trigger=ScopeTrigger(
                             "Wave Gen Out",
                             edge=TriggerEdge.Rising)))

scope_window.add_scope(Scope(["Wave Gen Out", "mLoad Position mm", "Spl Loop Demand", "mSpl Position"],
                             1000, 1000, mode=DisplayMode.Sliding,
                             title="Sliding",
                             yrange=40,
                             trigger=ScopeTrigger(
                             "Wave Gen Out",
                             edge=TriggerEdge.Rising)))

scope_window.add_scope(Scope(["Wave Gen Out", "mLoad Position mm"],
                             1000, 1000, mode=DisplayMode.Sliding,
                             title="Sliding", time_zero=False,
                             yrange=50,
                             trigger=ScopeTrigger(
                             "Wave Gen Out",
                             edge=TriggerEdge.Rising)))

# scope_window.add_scope(Scope(["Wave Gen Out", "mLoad Position mm"],
#                              1000, 1000, mode=DisplayMode.Redraw,
#                              title="Position Tracking",
#                              yrange=50,
#                              trigger=ScopeTrigger(
#                              "Wave Gen Out",
#                              edge=TriggerEdge.Rising)))

monitor.add_scope_window(scope_window)

# monitor.add_datalogger(DataLogger("short_test.csv",
#                                   start_condition=TriggerCondition(
#                                     Trigger.Rising, "Wave Gen Out"
#                                   ),
#                                   end_condition=CountCondition(20001)))

# start the monitor, which ends automagically
monitor.start()

app.exec_()

monitor.stop()
