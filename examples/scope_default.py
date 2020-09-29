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
format = Format(odr="CAN_SYS_PDO_default.odr")

# device
device = Kvaser()

# create the monitor
monitor = Monitor(format=format, device=device)

# add the pressure calibrations
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
# create a scope window
scope_window = ScopeWindow()

# # create a position scope that triggers on wave gen out
# scope_window.add_scope(Scope(["Wave Gen Out", "In EncoderPos"],
#                              1000, mode=DisplayMode.Redraw,
#                              trigger=ScopeTrigger(
#                              "Wave Gen Out",
#                              edge=TriggerEdge.Rising)))
#
# # create a pressure scope that freeruns
# scope_window.add_scope(Scope(
#     ["In Pressure{}".format(i) for i in range(1, 5)],
#     1000, mode=DisplayMode.Rolling,
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

scope_window.add_scope(Scope(["In Pressure1 Raw"],
                             10000, mode=DisplayMode.Rolling,
                             ))

scope_window.add_scope(Scope(["In Pressure2 Raw"],
                             10000, mode=DisplayMode.Rolling,
                             ))

scope_window.add_scope(Scope(["In Pressure3 Raw"],
                             10000, mode=DisplayMode.Rolling,
                             ))
# create a scope for force
scope_window.add_scope(Scope(["In Pressure5 Raw"],
                             10000, mode=DisplayMode.Rolling,
                             ))


# attach the scope to the monitor
monitor.add_scope_window(scope_window)

# start everything
monitor.start()
# start the gui event loop
app.exec_()
# tidy up on scope exit
monitor.stop()
