from virtual import Virtual
from pdo import PDOConverter, Format, FrameFormat

# open the virutal device
device = Virtual()

# set PDO format
format = Format()
format.add(FrameFormat(0x181, use7Q8=False, name=["Sine", "Rand"]))
format.add(FrameFormat(0x281))
format.add(FrameFormat(0x381))
format.add(FrameFormat(0x481))


# create PDO converter
pdo_converter = PDOConverter(device, format)

# start everything
pdo_converter.start()

# pull a bunch of data from converter and display
while pdo_converter.data_count < 1000:
    # get list of datapoints
    # this is up to 16 channels at 1kHz
    datapoints = pdo_converter.data_queue.get()

    # display info from first one
    d = datapoints[0]
    print("Time:{}, {}:{} | ".format(d.time, d.name, d.value), end='')
    d = datapoints[1]
    print("Time:{}, {}:{}".format(d.time, d.name, d.value))

pdo_converter.stop()
