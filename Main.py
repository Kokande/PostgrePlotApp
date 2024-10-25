if __name__ == "__main__":
    import sys

    from PyQt5 import QtWidgets
    from AppWindow import MainWindow

    app = QtWidgets.QApplication([])

    main = MainWindow()
    main.show()

    sys.exit(app.exec())