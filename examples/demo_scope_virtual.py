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
format = Format(odr="CAN_SYS_PDO_virtual_demo.odr")

# device
device = Virtual()

# create the monitor
monitor = Monitor(format=format, device=device)

# create a scope window
scope_window = ScopeWindow()

# create a position scope that triggers on wave gen out
scope_window.add_scope(Scope(["Wave Gen Out", "In EncoderPos"],
                             1000, 1000, mode=DisplayMode.Rolling,
                             title="Free Run Rolling"
                             ))

scope_window.add_scope(Scope(["Wave Gen Out", "In EncoderPos"],
                             1000, 1000, mode=DisplayMode.Redraw,
                             title="Free Run Redraw"
                             ))


scope_window.add_scope(Scope(["Wave Gen Out", "In EncoderPos"],
                             1000, 1000, mode=DisplayMode.Sliding,
                             title="Free Run Sliding"
                             ))

scope_window.add_scope(Scope(["Wave Gen Out", "In EncoderPos"],
                             1000, 1000, mode=DisplayMode.Redraw,
                             title="Trigger Redraw",
                             trigger=ScopeTrigger(
                                 "Wave Gen Out",
                                 TriggerEdge.Rising
                             )))

scope_window.add_scope(Scope(["Wave Gen Out", "In EncoderPos"],
                             1000, 1000, mode=DisplayMode.Sliding,
                             title="Trigger Sliding",
                             yrange=1.1,
                             trigger=ScopeTrigger(
                                 "Wave Gen Out",
                                 TriggerEdge.Rising
                             )))

scope_window.add_scope(Scope(["Sig{}".format(i+1) for i in range(6)],
                             2000, 1000, mode=DisplayMode.Sliding,
                             title="Colours",
                             yrange=1.1,
                             trigger=ScopeTrigger(
                                 "Sig1",
                                 TriggerEdge.Rising
                             )))

# scope_window.add_scope(Scope(["Wave Gen Out", "In EncoderPos"],
#                              1000, 1000, mode=DisplayMode.Redraw,
#                              title="Trigger Redraw - no time reset",
#                              time_zero=False,
#                              trigger=ScopeTrigger(
#                                  "Wave Gen Out",
#                                  TriggerEdge.Rising
#                              )))
#
# scope_window.add_scope(Scope(["Wave Gen Out", "In EncoderPos"],
#                              1000, 1000, mode=DisplayMode.Sliding,
#                              title="Trigger Sliding - no time reset",
#                              time_zero=False,
#                              trigger=ScopeTrigger(
#                                  "Wave Gen Out",
#                                  TriggerEdge.Rising
#                              )))
scope_window1 = ScopeWindow()
scope_window1.add_scope(Scope(["Sig{}".format(i+1) for i in range(6)],
                             2000, 1000, mode=DisplayMode.Sliding,
                             title="Colours",
                             yrange=1.1,
                             trigger=ScopeTrigger(
                                 "Sig1",
                                 TriggerEdge.Rising
                             )))
# attach the scope to the monitor
monitor.add_scope_window(scope_window)
monitor.add_scope_window(scope_window1)

# start everything
monitor.start()
# start the gui event loop
app.exec_()
# tidy up on scope exit
monitor.stop()
