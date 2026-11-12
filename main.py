import sys

from pyqtgraph.Qt import QtWidgets

from MainWindow import AudioVisualizerWindow

def main():
   app = QtWidgets.QApplication(sys.argv)
   app.setStyle('Fusion')
   window = AudioVisualizerWindow()
   window.show()
   sys.exit(app.exec())
   
if __name__ == '__main__':
   main()