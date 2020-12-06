from canPDOMonitor.virtual import Virtual
from canPDOMonitor.monitor import Monitor
from canPDOMonitor.can import Format
import logging
from canPDOMonitor.scopeserver import Client
from canPDOMonitor.scope import (ScopeSettings, TriggerSettings,
                                    TriggerEdge, DisplayMode)

import time

logging.basicConfig(level=logging.DEBUG)
# pdo format
format = Format(odr="CAN_SYS_PDO_virtual_demo.odr")

# device
device = Virtual()

# create the monitor
monitor = Monitor(format=format, device=device)

client = Client()
scope = ScopeSettings(["Wave Gen Out","In EncoderPos"], 2000, 1000,
        # mode=DisplayMode.Rolling,
        yrange=50,
        trigger=TriggerSettings("Wave Gen Out",
            edge=TriggerEdge.Rising))
client.add_scope(scope)

monitor.add_scope_window(client)
monitor.start()
time.sleep(20)
monitor.stop()