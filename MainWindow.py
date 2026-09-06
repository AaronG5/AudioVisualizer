import numpy as np
import pyqtgraph as pg 
from pyqtgraph.Qt import QtCore, QtWidgets
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput

from AudioFile import AudioFile

class AudioVisualizerWindow(QtWidgets.QMainWindow):
   def __init__(self):
      super().__init__()
      self.setWindowTitle('AudioVisualizer')
      self.audio_file = None

      self.player = QMediaPlayer()
      self.player.positionChanged.connect(self.update_position)
      self.player.durationChanged.connect(self.update_duration)
      self.audio_output = QAudioOutput()
      self.player.setAudioOutput(self.audio_output)
      self.player.playbackStateChanged.connect(self.handle_playback_state)

      # Central widget
      central = QtWidgets.QWidget()
      layout = QtWidgets.QVBoxLayout()
      central.setLayout(layout)
      self.setCentralWidget(central)

      # Plot widget
      self.plot_widget = pg.PlotWidget()
      self.plot_widget.setYRange(-1, 1)
      self.curve = self.plot_widget.plot(pen='y')
      layout.addWidget(self.plot_widget)

      # Playback controls
      controls = QtWidgets.QHBoxLayout()
      self.play_button = QtWidgets.QPushButton('►')
      self.pause_button = QtWidgets.QPushButton('❚❚')
      self.stop_button = QtWidgets.QPushButton('⏮')

      # for button in (self.play_button, self.pause_button, self.stop_button):
	   #    button.setStyleSheet("font-size: 24px;")

      font = self.play_button.font()
      font.setPointSize(24)
      self.play_button.setFont(font)
      self.pause_button.setFont(font)
      self.stop_button.setFont(font)

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

      # Load button
      self.load_button = QtWidgets.QPushButton('Load Audio File')
      self.load_button.clicked.connect(self.open_file_dialog)
      layout.addWidget(self.load_button)

      self.visual_timer = QtCore.QTimer()
      self.visual_timer.setInterval(10)
      self.visual_timer.timeout.connect(self.update_spectrum)

   def open_file_dialog(self):
      file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
         self, 'Select audio file', '', 'WAV files (*.wav);;All files (*.*)'
      )
      if file_path:
         self.audio_file = AudioFile(file_path)
         self.player.setSource(QtCore.QUrl.fromLocalFile(file_path))

   def update_spectrum(self): # TODO: Add FFT
      if self.audio_file is None:
         return

      current_sec = self.player.position() / 1000.0
      chunk = self.audio_file.get_chunk_at_time(current_sec)

      x = np.arange(len(chunk))
      self.curve.setData(x, chunk)

   def update_position(self, position_ms):
      self.slider.setValue(position_ms)
      self.time_label.setText(
         f'{self.format_time(position_ms)} / {self.format_time(self.player.duration())}'
      )

   def update_duration(self, duration_ms):
      self.slider.setRange(0, duration_ms)

   def handle_playback_state(self, state):
      if state == QMediaPlayer.PlaybackState.PlayingState:
         self.visual_timer.start()
      else:
         self.visual_timer.stop()

   @staticmethod
   def format_time(ms):
      seconds = ms // 1000
      return f'{seconds // 60:02d}:{seconds % 60:02d}'