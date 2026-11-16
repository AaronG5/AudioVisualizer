from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path

from audiovisualizer.types import RepeatMode
from audiovisualizer.audio_file import AudioFile


class Playlist:
   def __init__(self) -> None:
      self.files: list[Path] = []
      self.current_index: int | None = None
      self.repeat_mode: RepeatMode = RepeatMode.NONE
      self._loader: ThreadPoolExecutor = ThreadPoolExecutor(max_workers=1)
      self._preload: tuple[int, Future[AudioFile]] | None = None

   def set_files(self, files: list[Path]) -> None:
      self.files = files
      self.current_index = None
      self._cancel_preload()

   def next_index(self) -> int | None:
      if not self.files or self.current_index is None:
         return None
      next_index: int = self.current_index + 1
      if next_index < len(self.files):
         return next_index
      if self.repeat_mode == RepeatMode.NONE:
         return None
      return 0

   def prev_index(self) -> int | None:
      if not self.files or self.current_index is None:
         return None
      prev_index: int = self.current_index - 1
      if prev_index >= 0:
         return prev_index
      if self.repeat_mode == RepeatMode.NONE:
         return None
      return len(self.files) - 1

   def load(self, index: int) -> AudioFile:
      self.current_index = index
      audio: AudioFile = self._take_preload(index) or AudioFile(
         file_path=str(self.files[index])
      )
      self.start_preload()
      return audio

   def start_preload(self) -> None:
      next_index: int | None = self.next_index()
      if self._preload is not None and self._preload[0] == next_index:
         return
      self._cancel_preload()
      if next_index is not None:
         future: Future[AudioFile] = self._loader.submit(
            AudioFile, str(self.files[next_index])
         )
         self._preload = (next_index, future)

   def _cancel_preload(self) -> None:
      if self._preload is not None:
         _ = self._preload[1].cancel()
         self._preload = None

   def shutdown(self) -> None:
      self._loader.shutdown(wait=False, cancel_futures=True)

   def _take_preload(self, index: int) -> AudioFile | None:
      if self._preload is None or self._preload[0] != index:
         self._cancel_preload()
         return None
      _, future = self._preload
      self._preload = None
      try:
         return future.result()
      except Exception as e:
         print(f"Preload failed: {e}")
         return None
