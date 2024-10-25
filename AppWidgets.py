from PyQt5.QtWidgets import QDialog, QWidget, QTableWidgetItem, QComboBox, QLineEdit
from PyQt5.QtCore import Qt
from PyQt5 import uic


def baselineUI(self):
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setFixedSize(self.size().width(), self.size().height())


class ConnectionDialog(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi("designs/ConnectionDialog.ui", self)

        self.initUI()

    def initUI(self):
        baselineUI(self)

        self.hostLineEdit.setText('localhost')
        self.userLineEdit.setText('postgres')
        self.passwordLineEdit.setText('asd1029f')
        self.dbnameLineEdit.setText('advertisement')


class MessageDialog(QDialog):
    def __init__(self, mType: str, mText: str):
        super().__init__()
        uic.loadUi("designs/MessageDialog.ui", self)

        self.mType = mType
        self.mText = mText

        self.initUI()

    def initUI(self):
        baselineUI(self)

        self.setWindowTitle(self.mType)
        self.label.setText(self.mText)


class GraphDialog(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi("designs/GraphDialog.ui", self)

        self.initUI()

    def initUI(self):
        baselineUI(self)

        self.buttonBox.accepted.connect(self.accept)

        self.typeComboBox.addItems(['plot', 'scatter'])
        self.typeComboBox.setCurrentText('plot')


class CalculatedValueDialog(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi("designs/CalculatedValueDialog.ui", self)

        self.initUI()

    def initUI(self):
        baselineUI(self)


class QueryDialog(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi("designs/QueryDialog.ui", self)

        self.initUI()

    def initUI(self):
        baselineUI(self)


class QueryResult(QWidget):
    def __init__(self, parent, data):
        super().__init__()
        uic.loadUi("designs/QueryResult.ui", self)

        self.main = parent
        self.data = data
        self.fillTable()

        self.initUI()

    def initUI(self):
        baselineUI(self)

    def closeEvent(self, a0):
        self.main.windows.remove(self)

    def fillTable(self):
        self.tableWidget.clear()
        self.tableWidget.verticalHeader().setVisible(False)

        self.tableWidget.setColumnCount(len(self.data[0]))
        self.tableWidget.setRowCount(len(self.data[1]) + 1)

        for i in range(len(self.data[0])):
            self.tableWidget.setItem(0, i, QTableWidgetItem(self.data[0][i][0]))

        for i in range(len(self.data[1])):
            for j in range(len(self.data[0])):
                self.tableWidget.setItem(i + 1, j,
                                         QTableWidgetItem(str(self.data[1][i][j])))


class FilterDialog(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi("designs/FilterDialog.ui", self)

        self.columns = []

        self.initUI()

    def initUI(self):
        baselineUI(self)

    def setColumns(self, tableInfo):
        self.columns.clear()
        for column in tableInfo:
            self.columns.append(column)

        for element in self.children():
            if type(element) is QComboBox:
                element.clear()
                element.addItems([''] + self.columns)
            elif type(element) is QLineEdit:
                element.clear()


class InsertWindow(QDialog):
    def __init__(self, parent):
        super().__init__()
        uic.loadUi("designs/InsertWindow.ui", self)

        self.main = parent

        self.initUI()

    def initUI(self):
        baselineUI(self)

        self.okPushButton.clicked.connect(self.close)
        self.insertPushButton.clicked.connect(self.insert)

        self.tableWidget.verticalHeader().setVisible(False)

        self.tableWidget.setColumnCount(len(self.main.selectedTableInfo))
        self.tableWidget.setRowCount(2)

        for i in range(len(self.main.selectedTableInfo)):
            self.tableWidget.setItem(0, i,
                                     QTableWidgetItem(self.main.selectedTableInfo[i]))
            self.tableWidget.setItem(1, i, QTableWidgetItem(''))

    def closeEvent(self, a0):
        self.main.windows.remove(self)

    def insert(self):
        query = f"""INSERT INTO "{self.main.selectedTable}" VALUES ("""
        for i in range(len(self.main.selectedTableInfo)):
            item = self.tableWidget.item(1, i).text()
            if item:
                query += '\'' + item + '\', '
            else:
                query += 'Null, '
        query = query[:-2] + ')'
        self.main.insertOperation(query)
