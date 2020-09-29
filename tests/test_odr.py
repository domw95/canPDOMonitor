from canPDOMonitor.can import Format

# try to create a format from file
format = Format(odr="CAN_SYS_PDO.odr")

# check all the parameters have been aquired
print(format.rate)
print(format.order)

for ff in format.frame.values():
    print(ff.id)
    print(ff.use7Q8)
    print(ff.name)
