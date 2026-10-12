import re
from pathlib import Path
from enum import Enum
from concurrent.futures import ThreadPoolExecutor

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
      self.wav_files = []
      self.current_index = None
      self.repeat_mode = RepeatMode.NONE

      # Background loading of the next track's AudioFile
      self.loader = ThreadPoolExecutor(max_workers=1)
      self.preload = None   # (index, Future) or None

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
      label_font = self.track_label.font()
      label_font.setBold(True)
      self.track_label.setFont(label_font)

      # Playback controls
      controls = QtWidgets.QHBoxLayout()
      self.play_button = QtWidgets.QPushButton('►')
      self.pause_button = QtWidgets.QPushButton('❚❚')
      self.stop_button = QtWidgets.QPushButton('◼')
      self.skip_backward_button = QtWidgets.QPushButton('⏮')
      self.skip_forward_button = QtWidgets.QPushButton('⏭')
      self.repeat_button = QtWidgets.QPushButton('X')

      # for button in (self.play_button, self.pause_button, self.stop_button):
	   #    button.setStyleSheet("font-size: 24px;")

      font = self.play_button.font()
      font.setPointSize(24)
      self.play_button.setFont(font)
      self.pause_button.setFont(font)
      self.stop_button.setFont(font)
      self.skip_backward_button.setFont(font)
      self.skip_forward_button.setFont(font)
      self.repeat_button.setFont(font)

      self.play_button.clicked.connect(self.player.play)
      self.pause_button.clicked.connect(self.player.pause)
      self.stop_button.clicked.connect(self.player.stop)
      self.skip_backward_button.clicked.connect(self.skip_backward)
      self.skip_forward_button.clicked.connect(self.skip_forward)
      self.repeat_button.clicked.connect(self.cycle_repeat_mode)

      controls.addWidget(self.skip_backward_button)
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
         picked = Path(file_path).resolve()
         self.wav_files = sorted(picked.parent.glob('*.wav'), key=self.natural_key)
         self.preload = None
         self.load_track(self.wav_files.index(picked))

   def load_track(self, index: int):
      self.current_index = index
      file_path = self.wav_files[index]
      self.player.setSource(QtCore.QUrl.fromLocalFile(str(file_path)))
      self.audio_file = self.take_preload(index) or AudioFile(str(file_path))
      self.reset_position()
      self.track_label.setText(f'{file_path.stem} [{index + 1} / {len(self.wav_files)}]')
      self.player.play()
      self.start_preload()

   def next_index(self):
      if not self.wav_files:
         return None
      next_index = self.current_index + 1
      if next_index < len(self.wav_files):
         return next_index
      if self.repeat_mode == RepeatMode.NONE:
         return None
      return 0

   def prev_index(self):
      if not self.wav_files:
         return None
      prev_index = self.current_index - 1
      if prev_index >= 0:
         return prev_index
      if self.repeat_mode == RepeatMode.NONE:
         return None
      return -1

   def start_preload(self):
      next_index = self.next_index()
      if self.preload is not None:
         preload_index, future = self.preload
         if preload_index == next_index:
            return
         future.cancel()
      if next_index is None:
         self.preload = None
         return
      future = self.loader.submit(AudioFile, str(self.wav_files[next_index]))
      self.preload = (next_index, future)

   def take_preload(self, index: int):
      if self.preload is None:
         return None
      preload_index, future = self.preload
      self.preload = None
      if preload_index != index:
         future.cancel()
         return None
      try:
         return future.result()
      except Exception as e:
         print(f'Preload failed: {e}')
         return None

   def skip_forward(self):
      next_index = self.next_index()
      if next_index is not None:
         self.load_track(next_index)

   def skip_backward(self):
      if self.player.position() > 3000:
         self.reset_position()
      else:
         prev_index = self.prev_index()
         if prev_index is None:
            self.reset_position()
         else:
            if prev_index < 0: 
               prev_index += len(self.wav_files)
            self.load_track(prev_index)

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
      self.player.setPosition(0)

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
         next_index = self.next_index()
         if next_index is not None:
            self.load_track(next_index)

   @staticmethod
   def natural_key(path: Path):
      return [int(c) if c.isdigit() else c.lower()
            for c in re.split(r'(\d+)', path.name)]

   def cycle_repeat_mode(self):
      self.repeat_mode = RepeatMode((self.repeat_mode.value + 1) % len(RepeatMode))
      self.repeat_button.setText(REPEAT_ICONS[self.repeat_mode])
      if self.repeat_mode == RepeatMode.ONE:
         self.player.setLoops(-1)
      else:
         self.player.setLoops(1)
      if self.current_index is not None:
         self.start_preload()

   def closeEvent(self, event):
      self.loader.shutdown(wait=False, cancel_futures=True)
      super().closeEvent(event)

   @staticmethod
   def format_time(ms):
      seconds = ms // 1000
      return f'{seconds // 60:02d}:{seconds % 60:02d}'