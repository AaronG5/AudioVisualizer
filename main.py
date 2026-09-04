import sys
import numpy as np
from scipy import io, signal

import sounddevice as sd

import pyqtgraph as pg 
from pyqtgraph.Qt import QtCore, QtWidgets
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtCore import QUrl

from MainWindow import AudioVisualizerWindow

def main():
   app = QtWidgets.QApplication(sys.argv)
   window = AudioVisualizerWindow()
   window.show()
   sys.exit(app.exec())

def graphics():
   app = pg.mkQApp("Plotting Example")
   #mw = QtWidgets.QMainWindow()
   #mw.resize(800,800)

   win = pg.GraphicsLayoutWidget(show=True, title="Basic plotting examples")
   win.resize(1000,600)
   win.setWindowTitle('pyqtgraph example: Plotting')

   # Enable antialiasing for prettier plots
   pg.setConfigOptions(antialias=True)


   p6 = win.addPlot(title="Updating plot")
   curve = p6.plot(pen='y')
   data = np.random.normal(size=(10,1000))
   ptr = 0
   def update():
      global curve, data, ptr, p6
      curve.setData(data[ptr%10])
      if ptr == 0:
         p6.enableAutoRange('xy', False)  ## stop auto-scaling after the first data set is plotted
      ptr += 1
   timer = QtCore.QTimer()
   timer.timeout.connect(update)
   timer.start(50)

   pg.exec()
   
if __name__ == '__main__':
   main()