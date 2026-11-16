from PyQt6.QtWidgets import QApplication


import sys

from pyqtgraph.Qt import QtWidgets

from audiovisualizer.main_window import AudioVisualizerWindow


def main() -> None:
   app: QApplication = QtWidgets.QApplication(sys.argv)
   app.setStyle("Fusion")
   window: AudioVisualizerWindow = AudioVisualizerWindow()
   window.show()
   sys.exit(app.exec())


if __name__ == "__main__":
   main()
