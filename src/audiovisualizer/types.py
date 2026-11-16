from enum import Enum


class RepeatMode(Enum):
   NONE = 0  # Play through list, stop at end
   ALL = 1  # Play through list, wrap to start
   ONE = 2  # Repeat current track


REPEAT_ICONS = {
   RepeatMode.NONE: "X",
   RepeatMode.ALL: "🔁",
   RepeatMode.ONE: "🔂",
}
