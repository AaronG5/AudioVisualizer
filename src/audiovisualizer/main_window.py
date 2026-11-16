from PyQt6.QtWidgets import (
   QHBoxLayout,
   QLabel,
   QPushButton,
   QSlider,
   QVBoxLayout,
   QWidget,
)
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtCore import QElapsedTimer, QTimer
from PyQt6.QtGui import QCloseEvent, QFont

from numpy._typing._array_like import NDArray

from numpy import float64, int_
from typing import Any, override

import re
from pathlib import Path

import numpy as np
import pyqtgraph as pg

from pyqtgraph.widgets.PlotWidget import PlotWidget
from pyqtgraph.Qt import QtCore, QtWidgets


from audiovisualizer.types import RepeatMode, REPEAT_ICONS
from audiovisualizer.playlist import Playlist
from audiovisualizer.audio_file import AudioFile

DEFAULT_AUDIO_DIR: Path = Path.home() / "Music"


class AudioVisualizerWindow(QtWidgets.QMainWindow):
   def __init__(self) -> None:
      super().__init__()
      self.setWindowTitle("AudioVisualizer")
      self.playlist: Playlist = Playlist()
      self.audio_file: AudioFile | None = None

      # Background loading of the next track's AudioFile

      self.player: QMediaPlayer = QMediaPlayer()
      self.player.positionChanged.connect(self.update_position)
      self.player.durationChanged.connect(self.update_duration)
      self.audio_output: QAudioOutput = QAudioOutput()
      self.player.setAudioOutput(self.audio_output)
      self.player.playbackStateChanged.connect(self.handle_playback_state)
      self.player.mediaStatusChanged.connect(self.handle_media_status)

      # Central widget
      central: QWidget = QtWidgets.QWidget()
      layout: QVBoxLayout = QtWidgets.QVBoxLayout()
      central.setLayout(layout)
      self.setCentralWidget(central)

      # Plot widgets
      plots: QHBoxLayout = QtWidgets.QHBoxLayout()

      self.waveform_plot_widget: PlotWidget = pg.PlotWidget()
      self.waveform_plot_widget.setYRange(-1, 1)
      self.waveform_curve: Any = self.waveform_plot_widget.plot(pen="y")  # pyright: ignore[reportExplicitAny]

      self.spectrum_plot_widget: PlotWidget = pg.PlotWidget()
      self.spectrum_plot_widget.getPlotItem().setLogMode(x=True, y=False)  # pyright: ignore[reportOptionalMemberAccess]
      self.spectrum_plot_widget.setYRange(-100, 100)
      self.spectrum_curve: Any = self.spectrum_plot_widget.plot(pen="g")  # pyright: ignore[reportExplicitAny]

      plots.addWidget(self.waveform_plot_widget)
      plots.addWidget(self.spectrum_plot_widget)
      layout.addLayout(plots)

      # Current audio file name
      self.track_label: QLabel = QtWidgets.QLabel("No file loaded")
      layout.addWidget(self.track_label)
      label_font: QFont = self.track_label.font()
      label_font.setBold(True)
      self.track_label.setFont(label_font)

      # Playback controls
      controls: QHBoxLayout = QtWidgets.QHBoxLayout()
      self.play_button: QPushButton = QtWidgets.QPushButton("►")
      self.pause_button: QPushButton = QtWidgets.QPushButton("❚❚")
      self.stop_button: QPushButton = QtWidgets.QPushButton("◼")
      self.skip_backward_button: QPushButton = QtWidgets.QPushButton("⏮")
      self.skip_forward_button: QPushButton = QtWidgets.QPushButton("⏭")
      self.repeat_button: QPushButton = QtWidgets.QPushButton("X")

      # for button in (self.play_button, self.pause_button, self.stop_button):
      #    button.setStyleSheet("font-size: 24px;")

      font: QFont = self.play_button.font()
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
      self.slider: QSlider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
      self.slider.sliderMoved.connect(self.player.setPosition)
      layout.addWidget(self.slider)

      # Time label
      self.time_label: QLabel = QtWidgets.QLabel("00:00 / 00:00")
      layout.addWidget(self.time_label)

      # Load button
      self.load_button: QPushButton = QtWidgets.QPushButton("Load Audio File")
      self.load_button.clicked.connect(self.open_file_dialog)
      layout.addWidget(self.load_button)

      self.visual_timer: QTimer = QtCore.QTimer()
      self.visual_timer.setInterval(24)
      self.visual_timer.timeout.connect(self.update_spectrum)

      self.elapsed_timer: QElapsedTimer = QtCore.QElapsedTimer()
      self.position_offset_ms: int = 0

   def open_file_dialog(self) -> None:
      start_dir: str = (
         str(self.playlist.files[0].parent)
         if self.playlist.files
         else str(DEFAULT_AUDIO_DIR)
      )
      file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
         parent=self,
         caption="Select audio file",
         directory=start_dir,
         filter="WAV files (*.wav *.WAV);;All files (*.*)",
      )
      if file_path:
         picked: Path = Path(file_path).resolve()
         self.playlist.set_files(
            files=sorted(
               (
                  p
                  for p in picked.parent.iterdir()
                  if p.is_file() and p.suffix.lower() == ".wav"
               ),
               key=self.natural_key,
            )
         )
         self.load_track(self.playlist.files.index(picked))

   def load_track(self, index: int) -> None:
      file_path: Path = self.playlist.files[index]
      self.player.setSource(QtCore.QUrl.fromLocalFile(str(file_path)))
      self.audio_file = self.playlist.load(index)
      self.reset_position()
      self.track_label.setText(
         f"{file_path.stem} [{index + 1} / {len(self.playlist.files)}]"
      )
      self.player.play()

   def update_spectrum(self) -> None:
      if self.audio_file is None:
         return

      current_sec: float = (
         self.position_offset_ms + self.elapsed_timer.elapsed()
      ) / 1000.0
      chunk = self.audio_file.get_chunk_at_time(current_sec)

      # Waveform
      x_waveform: NDArray[int_] = np.arange(len(chunk))
      self.waveform_curve.setData(x_waveform, chunk)

      # Spectrum
      windowed: NDArray[float64] = chunk * np.hanning(len(chunk))
      magnitude = np.abs(np.fft.rfft(windowed))
      magnitude_db = 20 * np.log10(magnitude + 1e-10)
      freqs = np.fft.rfftfreq(len(windowed), d=1.0 / self.audio_file.sample_rate)
      self.spectrum_curve.setData(freqs[1:], magnitude_db[1:])

   def update_position(self, position_ms: int) -> None:
      self.slider.setValue(position_ms)
      self.time_label.setText(
         f"{self.format_time(position_ms)} / {self.format_time(self.player.duration())}"
      )
      self.position_offset_ms = position_ms
      self.elapsed_timer.restart()

   def reset_position(self) -> None:
      self.player.setPosition(0)

   def update_duration(self, duration_ms: int) -> None:
      self.slider.setRange(0, duration_ms)

   def handle_playback_state(self, state) -> None:  # pyright: ignore[reportUnknownParameterType, reportMissingParameterType]
      if state == QMediaPlayer.PlaybackState.PlayingState:
         self.visual_timer.start()
         self.elapsed_timer.restart()
      else:
         self.visual_timer.stop()

   def handle_media_status(self, status: QMediaPlayer.MediaStatus) -> None:
      if status == QMediaPlayer.MediaStatus.EndOfMedia:
         self.skip_forward()

   def skip_forward(self) -> None:
      next_index = self.playlist.next_index()
      if next_index is not None:
         self.load_track(next_index)

   def skip_backward(self) -> None:
      prev_index: int | None = self.playlist.prev_index()
      if self.player.position() > 3000 or prev_index is None:
         self.reset_position()
      else:
         self.load_track(prev_index)

   @staticmethod
   def natural_key(path: Path) -> list[int | str]:
      return [
         int(c) if c.isdigit() else c.lower() for c in re.split(r"(\d+)", path.name)
      ]

   def cycle_repeat_mode(self) -> None:
      mode: RepeatMode = RepeatMode(
         value=(self.playlist.repeat_mode.value + 1) % len(RepeatMode)
      )
      self.playlist.repeat_mode = mode
      self.repeat_button.setText(REPEAT_ICONS[mode])
      if mode == RepeatMode.ONE:
         self.player.setLoops(-1)
      else:
         self.player.setLoops(1)
      self.playlist.start_preload()

   @override
   def closeEvent(self, a0: QCloseEvent | None) -> None:
      self.playlist.shutdown()
      super().closeEvent(a0)

   @staticmethod
   def format_time(ms: int) -> str:
      seconds: float = ms // 1000
      return f"{seconds // 60:02d}:{seconds % 60:02d}"
