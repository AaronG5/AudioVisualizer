import re
from pathlib import Path
from enum import Enum

import numpy as np
import pyqtgraph as pg 

from pyqtgraph.Qt import QtCore, QtWidgets
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput

from scipy.fft import rfft, rfftfreq
from AudioFile import AudioFile

class RepeatMode(Enum):
   NONE = 0    # Play through list, stop at end
   ALL  = 1    # Play through list, wrap to start
   ONE  = 2    # Repeat current track

REPEAT_ICONS = {
   RepeatMode.NONE: 'X',
   RepeatMode.ALL: '🔁',
   RepeatMode.ONE: '🔂',
}

class AudioVisualizerWindow(QtWidgets.QMainWindow):
   def __init__(self):
      super().__init__()
      self.setWindowTitle('AudioVisualizer')
      self.audio_file = None
      self.repeat_mode = RepeatMode.NONE

      self.player = QMediaPlayer()
      self.player.positionChanged.connect(self.update_position)
      self.player.durationChanged.connect(self.update_duration)
      self.audio_output = QAudioOutput()
      self.player.setAudioOutput(self.audio_output)
      self.player.playbackStateChanged.connect(self.handle_playback_state)
      self.player.mediaStatusChanged.connect(self.handle_media_status)

      # Central widget
      central = QtWidgets.QWidget()
      layout = QtWidgets.QVBoxLayout()
      central.setLayout(layout)
      self.setCentralWidget(central)

      # Plot widgets
      plots = QtWidgets.QHBoxLayout()

      self.waveform_plot_widget = pg.PlotWidget()
      self.waveform_plot_widget.setYRange(-1, 1)
      self.waveform_curve = self.waveform_plot_widget.plot(pen='y')

      self.spectrum_plot_widget = pg.PlotWidget()
      self.spectrum_plot_widget.getPlotItem().setLogMode(x=True, y=False)
      self.spectrum_plot_widget.setYRange(-100, 100)
      self.spectrum_curve = self.spectrum_plot_widget.plot(pen='g')

      plots.addWidget(self.waveform_plot_widget)
      plots.addWidget(self.spectrum_plot_widget)
      layout.addLayout(plots)

      # Current audio file name
      self.track_label = QtWidgets.QLabel('No file loaded')
      layout.addWidget(self.track_label)
      self.track_label.font().setBold(True)

      # Playback controls
      controls = QtWidgets.QHBoxLayout()
      self.play_button = QtWidgets.QPushButton('►')
      self.pause_button = QtWidgets.QPushButton('❚❚')
      self.stop_button = QtWidgets.QPushButton('⏮')
      self.skip_forward_button = QtWidgets.QPushButton('⏭')
      self.repeat_button = QtWidgets.QPushButton('X')

      # for button in (self.play_button, self.pause_button, self.stop_button):
	   #    button.setStyleSheet("font-size: 24px;")

      font = self.play_button.font()
      font.setPointSize(24)
      self.play_button.setFont(font)
      self.pause_button.setFont(font)
      self.stop_button.setFont(font)
      self.skip_forward_button.setFont(font)
      self.repeat_button.setFont(font)

      self.play_button.clicked.connect(self.player.play)
      self.pause_button.clicked.connect(self.player.pause)
      self.stop_button.clicked.connect(self.player.stop)
      # self.skip_forward_button.clicked.connect(self.player.skip_forward) # TODO: Implement
      self.repeat_button.clicked.connect(self.cycle_repeat_mode)

      controls.addWidget(self.play_button)
      controls.addWidget(self.pause_button)
      controls.addWidget(self.stop_button)
      controls.addWidget(self.skip_forward_button)
      controls.addWidget(self.repeat_button)
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
      self.visual_timer.setInterval(24)
      self.visual_timer.timeout.connect(self.update_spectrum)

      self.elapsed_timer = QtCore.QElapsedTimer()
      self.position_offset_ms = 0

   def open_file_dialog(self):
      file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
         self, 'Select audio file', '', 'WAV files (*.wav);;All files (*.*)'
      )
      if file_path:
         folder = Path(file_path).parent
         self.wav_files = sorted(folder.glob('*.wav'), key=self.natural_key)
         picked = Path(file_path).resolve()
         index = self.wav_files.index(picked.resolve())
         self.load_track(index)

   def load_track(self, index: int):
      self.current_index = index
      file_path = self.wav_files[index]
      self.audio_file = AudioFile(str(file_path))
      self.player.setSource(QtCore.QUrl.fromLocalFile(str(file_path)))
      self.reset_position()
      self.track_label.setText(f'{file_path.stem} [{index + 1} / {len(self.wav_files)}]')

   def update_spectrum(self):
      if self.audio_file is None:
         return

      current_sec = (self.position_offset_ms + self.elapsed_timer.elapsed()) / 1000.0
      chunk = self.audio_file.get_chunk_at_time(current_sec)

      # Waveform
      x_waveform = np.arange(len(chunk))
      self.waveform_curve.setData(x_waveform, chunk)

      # Spectrum
      windowed = chunk * np.hanning(len(chunk))
      magnitude = np.abs(rfft(windowed))
      magnitude_db = 20 * np.log10(magnitude + 1e-10)
      freqs = rfftfreq(len(windowed), d=1.0 / self.audio_file.sample_rate)
      self.spectrum_curve.setData(freqs[:-1], magnitude_db[:-1])

   def update_position(self, position_ms):
      self.slider.setValue(position_ms)
      self.time_label.setText(
         f'{self.format_time(position_ms)} / {self.format_time(self.player.duration())}'
      )
      self.position_offset_ms = position_ms
      self.elapsed_timer.restart()

   def reset_position(self):
      self.update_position(0)

   def update_duration(self, duration_ms):
      self.slider.setRange(0, duration_ms)

   def handle_playback_state(self, state):
      if state == QMediaPlayer.PlaybackState.PlayingState:
         self.visual_timer.start()
         self.elapsed_timer.restart()
      else:
         self.visual_timer.stop()

   def handle_media_status(self, status: QMediaPlayer.MediaStatus):
      if status == QMediaPlayer.MediaStatus.EndOfMedia:
         if self.repeat_mode == RepeatMode.NONE:
            pass
         if self.repeat_mode == RepeatMode.ALL:
            pass # Handle loading the next track in the index list

   def natural_key(self, path: Path):
      return [int(c) if c.isdigit() else c.lower()
            for c in re.split(r'(\d+)', path.name)]

   def cycle_repeat_mode(self):
      self.repeat_mode = RepeatMode((self.repeat_mode.value + 1) % len(RepeatMode))
      self.repeat_button.setText(REPEAT_ICONS[self.repeat_mode])
      if self.repeat_mode == RepeatMode.ONE:
         self.player.setLoops(-1)
      else:
         self.player.setLoops(1)

   @staticmethod
   def format_time(ms):
      seconds = ms // 1000
      return f'{seconds // 60:02d}:{seconds % 60:02d}'