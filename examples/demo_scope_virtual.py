"""
Shows the scope usage using defulat odr, with pressure and force calibration
"""

from canPDOMonitor.monitor import Monitor
from canPDOMonitor.scope import (Scope, ScopeWindow, app, DisplayMode,
                                 ScopeTrigger, TriggerEdge)
from canPDOMonitor.virtual import Virtual
from canPDOMonitor.can import Format

import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

# pdo format
format = Format(odr="CAN_SYS_PDO_ISA_default.odr")

# device
device = Virtual()

# create the monitor
monitor = Monitor(format=format, device=device)

# create a scope window
scope_window = ScopeWindow()

# create a position scope that triggers on wave gen out
scope_window.add_scope(Scope(["Wave Gen Out", "In EncoderPos"],
                             1000, 1000, mode=DisplayMode.Rolling,
                             title="Position Tracking",
                             trigger=ScopeTrigger(
                             "Wave Gen Out",
                             edge=TriggerEdge.Rising)))


# attach the scope to the monitor
monitor.add_scope_window(scope_window)

# start everything
monitor.start()
# start the gui event loop
app.exec_()
# tidy up on scope exit
monitor.stop()
