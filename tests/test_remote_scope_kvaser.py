from canPDOMonitor.kvaser import Kvaser
from canPDOMonitor.monitor import Monitor, Calibrate
from canPDOMonitor.can import Format
import logging
from canPDOMonitor.scopeserver import Client
from canPDOMonitor.scope import (ScopeSettings, TriggerSettings,
                                    TriggerEdge, DisplayMode)

import time

logging.basicConfig(level=logging.DEBUG)
# pdo format
format = Format(odr="CAN_SYS_PDO_fctrl.odr")

# device
device = Kvaser()

# create the monitor
monitor = Monitor(format=format, device=device)

# add some offsets and gains to 7Q8 signals
for i in range(1,5):
    monitor.add_filter(Calibrate(
        name="Fctrl_Pressure_Log{}".format(i),
        offset=100,
        gain=1,
        new_name="Pressure {}".format(i),
        keep=False
    ))

monitor.add_filter(Calibrate(
    name="Fctrl_Position_Log",
    offset=0,
    gain = 1/2.5,
    new_name="Act Position",
    keep=False
))

monitor.add_filter(Calibrate(
    name="Fctrl_Velocity_Log",
    offset=0,
    gain = 4,
    new_name="Act Velocity",
    keep=False
))

monitor.add_filter(Calibrate(
    "Fctrl_force_filter_out",
    offset=0,gain=1,
    new_name="Force"
))


# create client to communicate with remote scope
client = Client()
# add a remote scope
for i in range(1):
    client.add_scope(ScopeSettings(["Wave Gen Out","Force"], 2000, 1000,
            # mode=DisplayMode.Rolling,
            trigger=TriggerSettings("Wave Gen Out",
                edge=TriggerEdge.Rising)))

    
for i in range(1):
    client.add_scope(ScopeSettings(["Pressure {}".format(i+1) for i in range(4)],
                                    nsamples=2000,samplerate=1000,
                                    title="Pressures",
                                    trigger=TriggerSettings("Wave Gen Out",
                                    edge=TriggerEdge.Rising)))

monitor.add_scope_window(client)
monitor.start()
time.sleep(100000)
monitor.stop()