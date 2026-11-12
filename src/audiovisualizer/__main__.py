import sys

from pyqtgraph.Qt import QtWidgets

from audiovisualizer.main_window import AudioVisualizerWindow

def main():
   app = QtWidgets.QApplication(sys.argv)
   app.setStyle('Fusion')
   window = AudioVisualizerWindow()
   window.show()
   sys.exit(app.exec())
   
if __name__ == '__main__':
   main()