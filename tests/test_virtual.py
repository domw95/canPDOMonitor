"""
Creates a virtual can Device and generates 100 frames
"""

from canPDOMonitor.virtual import Virtual
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
logger.info("Running Virtual CAN Device test")

v = Virtual()
v.start()

for i in range(40000):
    f = v.get_frame()
v.stop()
