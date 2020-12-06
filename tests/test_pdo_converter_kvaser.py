from canPDOMonitor.kvaser import Kvaser
from canPDOMonitor.can import PDOConverter, FrameFormat, Format
import logging
import time

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
logger.info("Running PDO Converter test")

# setup virtual device
device = Kvaser()

# set up PDO formats
format = Format()
format.add(FrameFormat(0x181, use7Q8=False,
                       name=["Wave Gen Out", "Encoder Pos"]))
format.add(FrameFormat(0x281))
format.add(FrameFormat(0x381))
format.add(FrameFormat(0x481))

# start PDO converter
pdo_converter = PDOConverter(device, format)
pdo_converter.start()

for i in range(1000*60):
    datapoints = pdo_converter.data_queue.get()
    if datapoints is None:
        break
    # print(datapoints[0])
    if i % 10 == 0:
        time.sleep(0.01)


pdo_converter.stop()
