from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg
import random

app = QtGui.QApplication([])
# create layout and add 4 plots to it in 2x2 grid
win = pg.GraphicsLayoutWidget(show=True)
win.showMaximized()
plots = []
for i in range(2):
    for j in range(2):
        plots.append(win.addPlot())
    win.nextRow()

# create plotdataitem for each plot
lines = [p.plot() for p in plots]


# add random data, with 1 plot much larger range than the rest
def update():
    lines[0].setData(range(100), [random.gauss(1e7, 1e5) for i in range(100)])
    for line in lines[1:4]:
        line.setData(range(100), [random.gauss(0, 1) for i in range(100)])


# update()
timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(2000)
app.exec_()
