import numpy as np
import soundfile as sf

class AudioFile:
   def __init__(self, file_path):
      self.file_path = file_path
      self.samples, self.sample_rate = sf.read(file_path, always_2d=False)

      if self.samples.ndim > 1:
         self.samples = self.samples.mean(axis=1)

      self.num_samples = len(self.samples)
      self.duration_sec = self.num_samples / self.sample_rate

   def get_chunk_at_time(self, time_sec, chunk_size=1024): # typeof(time_sec) = float
      start = max(0, int(time_sec * self.sample_rate) - chunk_size // 2)
      end = start + chunk_size

      chunk = self.samples[start:end]
      if len(chunk) < chunk_size:
         chunk = np.pad(chunk, (0, chunk_size - len(chunk)))
      return chunk
   