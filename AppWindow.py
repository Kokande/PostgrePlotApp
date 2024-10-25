from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem, QComboBox, QLineEdit
from PyQt5.QtCore import QModelIndex, QTimer
from PyQt5.QtGui import QStandardItem, QStandardItemModel

import asyncio
import functools
import psycopg2 as pg
import matplotlib.pyplot as plt

import AppWidgets as Widgets


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("designs/MainWindow.ui", self)

        self.connectionDialog = Widgets.ConnectionDialog()
        self.graphDialog = Widgets.GraphDialog()
        self.calculatedValueDialog = Widgets.CalculatedValueDialog()
        self.queryDialog = Widgets.QueryDialog()
        self.filterDialog = Widgets.FilterDialog()

        self.listModel = QStandardItemModel()
        self.connectionChecker = QTimer(self)

        self.connection = None
        self.tables = []
        self.selectedTable = None
        self.selectedTableInfo = []
        self.selectedTableContents = []

        self.windows = []

        self.dbConnect()
        self.initUI()

    def initUI(self):
        self.setFixedSize(800, 600)

        self.tableWidget.verticalHeader().setVisible(False)

        self.tableListView.setModel(self.listModel)

        self.actionConnectDB.triggered.connect(self.dbConnect)
        self.actionGraph.triggered.connect(self.createGraph)
        self.actionCalculatedValue.triggered.connect(self.createCalculatedValue)
        self.actionQuery.triggered.connect(self.performQuery)
        self.actionDisconnect.triggered.connect(self.clearConnection)
        self.actionSelect.triggered.connect(self.selectQuery)
        self.actionDelete.triggered.connect(self.deleteQuery)
        self.actionInsert.triggered.connect(self.insertQuery)

        self.tableListView.clicked[QModelIndex].connect(self.listViewItemClicked)

        self.connectionChecker.timeout.connect(self.checkConnection)
        self.connectionChecker.start(1000)

        self.updateUI()

    def updateUI(self):
        self.listModel.clear()

        for i in self.tables:
            self.listModel.appendRow(QStandardItem(i))

    def clearConnection(self):
        self.connection = None
        self.tables = []
        self.selectedTable = None
        self.selectedTableInfo = []
        self.selectedTableContents = []
        self.dockWidget.setWindowTitle('No connection')
        self.listModel.clear()
        self.tableWidget.clear()
        self.tableWidget.setColumnCount(0)
        self.tableWidget.setRowCount(0)

    def checkConnection(self):
        if self.connection is not None:
            try:
                with self.connection.cursor() as cursor:
                    cursor.execute("""SELECT 0""")
            except pg.OperationalError as e:
                print(e)
                Widgets.MessageDialog("Error",
                                      "Connection terminated").exec()
                self.clearConnection()

    def closeEvent(self, a0):
        self.clearWindows()

    def clearWindows(self):
        while self.windows:
            self.windows[0].close()

    def dbConnect(self):
        if self.connectionDialog.exec():
            try:
                self.connection = pg.connect(host=self.connectionDialog.hostLineEdit.text(),
                                             user=self.connectionDialog.userLineEdit.text(),
                                             password=self.connectionDialog.passwordLineEdit.text(),
                                             dbname=self.connectionDialog.dbnameLineEdit.text())

                self.dockWidget.setWindowTitle(self.connectionDialog.dbnameLineEdit.text())

                self.updateTablesInfo()

                self.updateUI()
            except pg.OperationalError as e:
                print(e)
                Widgets.MessageDialog('Error',
                                      'Could not create connection\nwith given info').exec()

    def updateTablesInfo(self):
        self.tables = []

        with self.connection.cursor() as cursor:
            cursor.execute("""SELECT * 
                              FROM pg_tables 
                              WHERE schemaname = 'public'""")
            self.tables = list(map(lambda x: x[1], cursor.fetchall()))

    def updateAll(self):
        self.updateTablesInfo()
        self.updateUI()
        self.updateTable()

    def listViewItemClicked(self, index):
        self.clearWindows()

        self.selectedTable = self.listModel.itemFromIndex(index).text()

        self.updateTable()

    def updateTable(self):
        with self.connection.cursor() as cursor:
            cursor.execute(f"""SELECT * FROM {self.selectedTable}""")
            self.selectedTableInfo = list(map(lambda x: x.name, cursor.description))

            tablesString = ', '.join(["\"" + i + "\"" for i in self.selectedTableInfo])
            cursor.execute(f"""SELECT {tablesString}
                               FROM {self.selectedTable}""")
            self.selectedTableContents = [list(i) for i in cursor.fetchall()]

        self.tableWidget.clear()

        self.tableWidget.setColumnCount(len(self.selectedTableInfo))
        self.tableWidget.setRowCount(len(self.selectedTableContents) + 1)

        for i in range(len(self.selectedTableInfo)):
            self.tableWidget.setItem(0, i, QTableWidgetItem(self.selectedTableInfo[i]))

        for i in range(len(self.selectedTableContents)):
            for j in range(len(self.selectedTableInfo)):
                self.tableWidget.setItem(i + 1, j,
                                         QTableWidgetItem(str(self.selectedTableContents[i][j])))

    def createGraph(self):
        if self.graphDialog.exec():
            try:
                x = self.graphDialog.xLineEdit.text()
                y = self.graphDialog.yLineEdit.text()
                z = self.graphDialog.zLineEdit.text()

                fig = plt.figure(figsize=(4,4))

                if z:
                    points = list(zip([i[int(x) - 1] for i in self.selectedTableContents],
                                      [i[int(y) - 1] for i in self.selectedTableContents],
                                      [i[int(z) - 1] for i in self.selectedTableContents]))

                    points.sort()

                    x = [i[0] for i in points]
                    y = [i[1] for i in points]
                    z = [i[2] for i in points]

                    ax = fig.add_subplot(111, projection='3d')

                    if self.graphDialog.typeComboBox.currentText() == 'plot':
                        ax.plot3D(x, y, z)
                    elif self.graphDialog.typeComboBox.currentText() == 'scatter':
                        ax.scatter(x, y, z)
                    plt.show()
                else:
                    points = list(zip([i[int(x) - 1] for i in self.selectedTableContents],
                                      [i[int(y) - 1] for i in self.selectedTableContents]))

                    points.sort()

                    x = [i[0] for i in points]
                    y = [i[1] for i in points]

                    ax = fig.add_subplot()

                    if self.graphDialog.typeComboBox.currentText() == 'plot':
                        ax.plot(x, y)
                    elif self.graphDialog.typeComboBox.currentText() == 'scatter':
                        ax.scatter(x, y)
                    plt.show()
            except Exception as e:
                print(e)
                Widgets.MessageDialog('Error',
                                      'Could not create graph\nwith given info').exec()

    def createCalculatedValue(self):
        if self.calculatedValueDialog.exec():
            try:
                expression = self.calculatedValueDialog.expressionLineEdit.text()

                values = []

                for i in self.selectedTableContents:
                    currentRow = dict(zip([i[0] for i in self.selectedTableInfo], i))
                    currentValue = eval(expression.format(**currentRow))
                    values.append(currentValue)

                self.selectedTableInfo.append((self.calculatedValueDialog.nameLineEdit.text(),
                                               'double precision'))

                for i in range(len(self.selectedTableContents)):
                    self.selectedTableContents[i].append(values[i])

                self.updateTable()
            except Exception as e:
                print(e)
                Widgets.MessageDialog('Error',
                                      'Could not create calculated '
                                      'value\nwith given info').exec()

    def performQuery(self):
        if self.queryDialog.exec():
            try:
                with self.connection.cursor() as cursor:
                    cursor.execute(self.queryDialog.queryTextEdit.toPlainText())

                    if cursor.description is None:
                        Widgets.MessageDialog('Success', cursor.statusmessage).exec()
                        self.connection.commit()
                        self.updateAll()
                    else:
                        self.windows.append(Widgets.QueryResult(self, (cursor.description,
                                                                       cursor.fetchall())))
                        self.windows[-1].show()
            except Exception as e:
                print(e)

                self.connection.rollback()

                Widgets.MessageDialog('Error', e.args[0]).exec()

    def getFilters(self):
        self.filterDialog.setColumns(self.selectedTableInfo)
        if self.filterDialog.exec():
            filters = []

            for i in range(1, 17):
                table = eval(f"self.filterDialog.comboBox_{i}.currentText()")
                condition = eval(f"self.filterDialog.lineEdit_{i}.text()")
                if table and condition:
                    filters.append((table, condition))
            return filters
        return 0

    def selectQuery(self):
        self.filterDialog.setWindowTitle('Select')
        filters = self.getFilters()
        if filters:
            try:
                if len(filters) == 0:
                    raise Exception

                query = f"""SELECT * FROM "{self.selectedTable}" 
                            WHERE "{filters[0][0]}" {filters[0][1]}"""
                for i in range(1, len(filters)):
                    query += f""" AND "{filters[i][0]}" {filters[i][1]}"""
                with self.connection.cursor() as cursor:
                    cursor.execute(query)

                    self.windows.append(Widgets.QueryResult(self, (cursor.description,
                                                                  cursor.fetchall())))
                    self.windows[-1].show()
            except Exception as e:
                print(e)

                self.connection.rollback()

                Widgets.MessageDialog('Error', 'Invalid parameters').exec()

    def deleteQuery(self):
        self.filterDialog.setWindowTitle('Delete')
        filters = self.getFilters()
        if filters:
            try:
                if len(filters) == 0:
                    raise Exception

                query = f"""DELETE FROM "{self.selectedTable}" 
                            WHERE "{filters[0][0]}" {filters[0][1]}"""
                for i in range(1, len(filters)):
                    query += f""" AND "{filters[i][0]}" {filters[i][1]}"""
                with self.connection.cursor() as cursor:
                    cursor.execute(query)
                    Widgets.MessageDialog('Success', cursor.statusmessage).exec()
                    self.connection.commit()
                    self.updateAll()
            except Exception as e:
                print(e)

                self.connection.rollback()

                Widgets.MessageDialog('Error', 'Invalid parameters').exec()

    def insertQuery(self):
        self.windows.append(Widgets.InsertWindow(self))
        self.windows[-1].show()

    def insertOperation(self, query):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query)
                Widgets.MessageDialog('Success', cursor.statusmessage).exec()
                self.connection.commit()
                self.updateAll()
        except Exception as e:
            print(e)

            self.connection.rollback()

            Widgets.MessageDialog('Error', 'Invalid parameters').exec()