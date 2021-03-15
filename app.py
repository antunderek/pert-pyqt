#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import scipy.stats as st

from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QDialog, QTableWidgetItem, QPushButton, qApp
)

from main_window import Ui_MainWindow
from add_task_dialog import Ui_Dialog
from edit_task_dialog import Ui_EditDialog

TASKS = []

class Window(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.addTaskSignalSlot()
    
    def updateTable(self):
        self.tableWidget.clearContents()
        self.clearTable(self.tableWidget)
        for i in range(len(TASKS)):
            self.tableWidget.insertRow(i)
            self.tableWidget.setItem(i, 0, QTableWidgetItem(TASKS[i].name))
            self.tableWidget.setItem(i, 1, QTableWidgetItem(str(TASKS[i].optimistic_time)))
            self.tableWidget.setItem(i, 2, QTableWidgetItem(str(TASKS[i].realistic_time)))
            self.tableWidget.setItem(i, 3, QTableWidgetItem(str(TASKS[i].pessimistic_time)))
            buttonDelete = QPushButton("Delete")
            buttonDelete.clicked.connect(lambda: self.deleteTask(i))
            self.tableWidget.setCellWidget(i, 4, buttonDelete)
            self.buttonEdit = QPushButton("Edit")
            self.buttonEdit.clicked.connect(self.editTaskDialog)
            self.tableWidget.setCellWidget(i, 5, self.buttonEdit)

        if len(TASKS) != 0:
            self.lockTable(self.tableWidget, 4)
    

    def updateResultsTable(self):
        self.clearTable(self.tableWidget_2)
        sumExpectedTime = sumVariance = 0
        for i in range(len(TASKS)):
            self.tableWidget_2.insertRow(i)
            self.tableWidget_2.setItem(i, 0, QTableWidgetItem(TASKS[i].name))
            self.tableWidget_2.setItem(i, 1, QTableWidgetItem(str(round(TASKS[i].expected_time(), 3))))
            self.tableWidget_2.setItem(i, 2, QTableWidgetItem(str(round(TASKS[i].standard_deviation(), 3))))
            self.tableWidget_2.setItem(i, 3, QTableWidgetItem(str(round(TASKS[i].variance(), 3))))
            sumExpectedTime += TASKS[i].expected_time()
            sumVariance += TASKS[i].variance()
        
        if len(TASKS) != 0:
            self.tableWidget_2.insertRow(len(TASKS))
            self.tableWidget_2.setItem(len(TASKS), 0, QTableWidgetItem())
            self.tableWidget_2.setItem(len(TASKS), 1, QTableWidgetItem("\u2211t " + str(round(sumExpectedTime, 3))))
            self.tableWidget_2.item(len(TASKS), 1).setBackground(QtGui.QColor(211,211,211))
            self.tableWidget_2.setItem(len(TASKS), 2, QTableWidgetItem())
            self.tableWidget_2.setItem(len(TASKS), 3, QTableWidgetItem("\u2211V " + str(round(sumVariance, 3))))
            self.tableWidget_2.item(len(TASKS), 3).setBackground(QtGui.QColor(211,211,211))
            self.lockTable(self.tableWidget_2)
    
    def lockTable(self, tableWidget, columns=None):
        rows = tableWidget.rowCount()
        if columns == None:
            columns = tableWidget.columnCount()
        for i in range(rows):
            for j in range(columns):
                item = tableWidget.item(i, j)
                item.setFlags(QtCore.Qt.ItemIsEnabled)
    
    def clearTable(self, tableWidget):
        rows = tableWidget.rowCount()
        for i in range(rows):
            tableWidget.removeRow(i)
        tableWidget.setRowCount(0)
    
    def reset(self):
        self.clearTable(self.tableWidget)
        self.clearTable(self.tableWidget_2)
        TASKS.clear()
        self.resultLabel.setText('')
    
    def calculate(self):
        if len(TASKS) != 0:
            self.updateResultsTable()
            completionTime = self.completionTime.value()
            probability = probability_of_finishing(TASKS, completionTime)
            if probability == 'NaN':
                self.resultLabel.setText(probability)
            else:
                self.resultLabel.setText(f"{round(probability, 2)}%")

    def deleteTask(self, index):
        button = qApp.focusWidget()
        index = self.tableWidget.indexAt(button.pos())
        TASKS.pop(index.row())
        self.updateTable()

    def addTaskSignalSlot(self):
        self.addTaskButton.clicked.connect(self.addTaskDialog)
        self.resetTasksButton.clicked.connect(self.reset)
        self.calculateButton.clicked.connect(self.calculate)

    def addTaskDialog(self):
        dialog = AddTaskDialog(self)
        if dialog.exec():
            self.updateTable()

    def editTaskDialog(self):
        button = qApp.focusWidget()
        index = self.tableWidget.indexAt(button.pos())
        dialog = EditTaskDialog(self)
        dialog.displayDefaultValues(TASKS[index.row()])
        dialog.setTaskIndex(index.row())
        if dialog.exec():
            self.updateTable()


class AddTaskDialog(QDialog, Ui_Dialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
    
    def accept(self):
        if not self.taskName.text():
            self.taskName.setFocus()
            return
        task = Task(self.taskName.text(), self.optimisticTime.value(), self.realisticTime.value(), self.pessimisticTime.value())
        TASKS.append(task)
        self.done(1)


class EditTaskDialog(QDialog, Ui_EditDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
    
    def displayDefaultValues(self, task):
        self.taskName_2.setText(task.name)
        self.optimisticTime_2.setValue(task.optimistic_time)
        self.realisticTime_2.setValue(task.realistic_time)
        self.pessimisticTime_2.setValue(task.pessimistic_time)
    
    def setTaskIndex(self, index):
        self.index = index

    def accept(self):
        if not self.taskName_2.text():
            self.taskName_2.setFocus()
            return
        task = Task(self.taskName_2.text(), self.optimisticTime_2.value(), self.realisticTime_2.value(), self.pessimisticTime_2.value())
        TASKS[self.index] = task
        self.done(1)


class Task:
    def __init__(self, name, optimistic_time, realistic_time, pessimistic_time):
        self.name = name
        self.optimistic_time = optimistic_time
        self.realistic_time = realistic_time
        self.pessimistic_time = pessimistic_time

    def expected_time(self):
        return (self.optimistic_time + 4 * self.realistic_time + self.pessimistic_time) / 6


    def standard_deviation(self):
        return abs(self.pessimistic_time - self.optimistic_time) / 6


    def variance(self):
        return pow(self.standard_deviation(), 2)


def probability_of_finishing(tasks, desired_complition_time):
    expected_time_sum = 0.0
    variance_sum = 0.0

    for task in tasks:
        expected_time_sum += task.expected_time()
        variance_sum += task.variance()

    try:
        z = (desired_complition_time - expected_time_sum) / pow(variance_sum, 0.5)
        print(f"\nExpected time sum: {expected_time_sum}")
        print(f"Variance sum: {variance_sum}")
        print(f"Z: {z}")
    except ZeroDivisionError:
        return "NaN"
    else:
        return 100 * st.norm.cdf(z)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Window()
    win.show()
    sys.exit(app.exec())