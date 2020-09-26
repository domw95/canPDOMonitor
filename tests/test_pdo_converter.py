from canPDOMonitor.virtual import Virtual
from canPDOMonitor.can import PDOConverter, FrameFormat, Format
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
logger.info("Running PDO Converter test")

# setup virtual device
device = Virtual()

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

while(pdo_converter.data_count < 1000*10):
    datapoints = pdo_converter.data_queue.get()

pdo_converter.stop()
