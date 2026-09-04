import sys
import numpy as np
import scipy.signal as sp

import sounddevice as sd

import pyqtgraph as pg 
from pyqtgraph.Qt import QtCore, QtWidgets
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtCore import QUrl

class AudioVisualizerWindow(QtWidgets.QMainWindow):
   def __init__(self):
      super().__init__()
      self.setWindowTitle('AudioVisualizer')

      self.player = QMediaPlayer()
      self.player.positionChanged.connect(self.update_position)
      self.player.durationChanged.connect(self.update_duration)
      self.audio_output = QAudioOutput()
      self.player.setAudioOutput(self.audio_output)

      # Central widget
      central = QtWidgets.QWidget()
      layout = QtWidgets.QVBoxLayout()
      central.setLayout(layout)
      self.setCentralWidget(central)

      # Load button
      self.load_button = QtWidgets.QPushButton('Load Audio File')
      self.load_button.clicked.connect(self.open_file_dialog)
      layout.addWidget(self.load_button)

      # Plot widget
      self.plot_widget = pg.PlotWidget()
      layout.addWidget(self.plot_widget)

      # Playback controls
      controls = QtWidgets.QHBoxLayout()
      self.play_button = QtWidgets.QPushButton('Play')
      self.pause_button = QtWidgets.QPushButton('Pause')
      self.stop_button = QtWidgets.QPushButton('Stop')

      self.play_button.clicked.connect(self.player.play)
      self.pause_button.clicked.connect(self.player.pause)
      self.stop_button.clicked.connect(self.player.stop)

      controls.addWidget(self.play_button)
      controls.addWidget(self.pause_button)
      controls.addWidget(self.stop_button)
      layout.addLayout(controls)

      # Progress bar slider
      self.slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
      self.slider.sliderMoved.connect(self.player.setPosition)
      layout.addWidget(self.slider)

      # Time label
      self.time_label = QtWidgets.QLabel('00:00 / 00:00')
      layout.addWidget(self.time_label)

   def open_file_dialog(self):
      file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
         self, 'Select audio file', '', 'WAV files (*.wav);;All files (*.*)'
      )
      if file_path:
         self.player.setSource(QUrl.fromLocalFile(file_path))
         self.load_and_plot(file_path)

   def load_and_plot(self, file_path):
      pass

   def update_position(self, position_ms):
      self.slider.setValue(position_ms)
      self.time_label.setText(
         f'{self.format_time(position_ms)} / {self.format_time(self.player.duration())}'
      )

   def update_duration(self, duration_ms):
      self.slider.setRange(0, duration_ms)

   @staticmethod
   def format_time(ms):
      seconds = ms // 1000
      return f'{seconds // 60:02d}:{seconds % 60:02d}'

def main():
   pass

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
   app = QtWidgets.QApplication(sys.argv)
   window = AudioVisualizerWindow()
   window.show()
   sys.exit(app.exec())

   # graphics()