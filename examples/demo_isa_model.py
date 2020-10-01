"""
Shows the scope usage using defulat odr, with pressure and force calibration
"""

from canPDOMonitor.monitor import Monitor, Calibrate
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

# create a position scope that triggers on wave gen out
scope_window.add_scope(Scope(["Wave Gen Out", "mLoad Position mm"],
                             1000, mode=DisplayMode.Redraw,
                             title="Position Tracking",
                             trigger=ScopeTrigger(
                             "Wave Gen Out",
                             edge=TriggerEdge.Rising)))

scope_window.add_scope(Scope(["mAct P1", "mAct P2"],
                             1000, mode=DisplayMode.Redraw,
                             title="Position Tracking",
                             trigger=ScopeTrigger(
                             "Wave Gen Out",
                             edge=TriggerEdge.Rising)))

scope_window.add_scope(Scope(["Spl Loop Demand", "mSpl Position"],
                             1000, mode=DisplayMode.Redraw,
                             title="Position Tracking",
                             trigger=ScopeTrigger(
                             "Wave Gen Out",
                             edge=TriggerEdge.Rising)))

scope_window.add_scope(Scope(["mAct Fh"],
                             1000, mode=DisplayMode.Redraw,
                             title="Position Tracking",
                             trigger=ScopeTrigger(
                             "Wave Gen Out",
                             edge=TriggerEdge.Rising)))

# # create a pressure scope that freeruns
# scope_window.add_scope(Scope(
#     ["In Pressure{}".format(i) for i in range(1, 5)],
#     1000, mode=DisplayMode.Rolling,
#     title="Pressures",
#     trigger=ScopeTrigger(
#         "Wave Gen Out",
#         edge=TriggerEdge.Rising)))
#
# # create a spool position scope that triggers on wave gen out
# scope_window.add_scope(Scope(["Spl Loop Demand", "In SpoolPos"],
#                              1000, mode=DisplayMode.Redraw,
#                              trigger=ScopeTrigger(
#                              "Wave Gen Out",
#                              edge=TriggerEdge.Rising)))


# attach the scope to the monitor
monitor.add_scope_window(scope_window)

# start everything
monitor.start()
# start the gui event loop
app.exec_()
# tidy up on scope exit
monitor.stop()
