from numpy._typing import NDArray

import numpy as np
import soundfile as sf


class AudioFile:
   def __init__(self, file_path: str) -> None:
      self.file_path: str = file_path
      self.samples, self.sample_rate = sf.read(file=file_path, always_2d=False)  # pyright: ignore[reportUnannotatedClassAttribute, reportAttributeAccessIssue]

      if self.samples.ndim > 1:
         self.samples: NDArray[np.float64] = self.samples.mean(axis=1)

      self.num_samples: int = len(self.samples)
      self.duration_sec: float = self.num_samples / self.sample_rate

   def get_chunk_at_time(
      self, time_sec: float, chunk_size: int = 1024
   ) -> NDArray[np.float64]:  # typeof(time_sec) = float
      start: int = max(0, int(time_sec * self.sample_rate) - chunk_size // 2)
      end: int = start + chunk_size

      chunk: NDArray[np.float64] = self.samples[start:end]
      if len(chunk) < chunk_size:
         chunk = np.pad(chunk, (0, chunk_size - len(chunk)))
      return chunk
