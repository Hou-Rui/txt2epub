#!/usr/bin/env python

import asyncio
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Callable

import PySide6.QtAsyncio as QtAsyncio
from PySide6.QtCore import QStringListModel
from PySide6.QtGui import QIcon, Qt
from PySide6.QtWidgets import (QApplication, QFileDialog, QFormLayout,
                               QHBoxLayout, QLineEdit, QListView, QMessageBox,
                               QPushButton, QVBoxLayout, QWidget)

import txt2epub


class MainWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._book = txt2epub.Book()
        self._model = QStringListModel(self)
        self._setupUi()
        self._setupSignals()

    def _setupUi(self):
        self.setWindowTitle(self.tr("TXT to EPUB Converter"))

        self._form = QFormLayout()
        self._openIcon = QIcon.fromTheme(QIcon.ThemeIcon.DocumentOpen)

        self._inputLayout = QHBoxLayout()
        self._inputList = QListView(self)
        self._inputList.setModel(self._model)

        self._inputButtonLayout = QVBoxLayout()
        self._inputButtonLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._inputAddButton = QPushButton(self)
        self._inputRemoveButton = QPushButton(self)
        self._inputAddButton.setIcon(QIcon.fromTheme(QIcon.ThemeIcon.ListAdd))
        self._inputRemoveButton.setIcon(
            QIcon.fromTheme(QIcon.ThemeIcon.ListRemove))
        self._inputButtonLayout.addWidget(self._inputAddButton)
        self._inputButtonLayout.addWidget(self._inputRemoveButton)

        self._inputLayout.addWidget(self._inputList)
        self._inputLayout.addLayout(self._inputButtonLayout)

        self._outputLayout = QHBoxLayout()
        self._outputField = QLineEdit(self)
        self._outputButton = QPushButton(self)
        self._outputButton.setIcon(self._openIcon)
        self._outputLayout.addWidget(self._outputField)
        self._outputLayout.addWidget(self._outputButton)

        self._titleField = QLineEdit(self)
        self._authorField = QLineEdit(self)

        self._form.addRow(self.tr("Input Plain Text Path:"), self._inputLayout)
        self._form.addRow(self.tr("Output EPUB Path:"), self._outputLayout)
        self._form.addRow(self.tr("Book Title:"), self._titleField)
        self._form.addRow(self.tr("Book Author:"), self._authorField)

        self._layout = QVBoxLayout(self)
        self._generateButton = QPushButton(self.tr("Generate EPUB"), self)
        self._layout.addLayout(self._form)
        self._layout.addWidget(self._generateButton)

    async def _runAsync(self, func: Callable, *args):
        with ThreadPoolExecutor() as pool:
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(pool, lambda: func(*args))

    async def _loadFilesAsync(self, files: list[str]):
        self.setDisabled(True)
        await self._runAsync(self._book.load, files)
        self._model.setStringList(files)
        self.setDisabled(False)
        self._outputField.clear()
        if files:
            outputName = str(Path(files[0]).with_suffix(".epub"))
            self._outputField.setText(outputName)
        self._titleField.setText(self._book.title)
        self._authorField.setText(','.join(self._book.authors))

    def _selectInputFiles(self):
        caption = self.tr("Select Input Text File")
        filter = self.tr("Plain Text (*.txt);; All Files (*.*)")
        files, _ = QFileDialog.getOpenFileNames(self, caption, filter=filter)
        asyncio.ensure_future(self._loadFilesAsync(files))

    def _removeSelectedFiles(self):
        files = self._model.stringList()
        for index in self._inputList.selectedIndexes():
            files.pop(index.row())
        asyncio.ensure_future(self._loadFilesAsync(files))

    def _selectOutputFile(self):
        caption = self.tr("Select Output EPUB File")
        filter = self.tr("EBook file (*.epub);; All Files (*.*)")
        fileName, _ = QFileDialog.getSaveFileName(self, caption, filter=filter)
        self._outputField.setText(fileName)

    async def _writeBookAsync(self, output: str):
        try:
            self.setDisabled(True)
            await self._runAsync(self._book.write, output)
            message = self.tr("Epub file generated.")
            ok = QMessageBox.StandardButton.Ok
            QMessageBox.information(self, self.tr("Finished"), message, ok)
        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"), str(e))
        finally:
            self.setDisabled(False)

    def _generateEpub(self):
        self._book.title = self._titleField.text()
        self._book.authors = self._authorField.text().split(',')
        if not self._book.title:
            message = self.tr("Book title cannot be empty.")
            QMessageBox.critical(self, self.tr("Error"), message)
            return
        output = self._outputField.text()
        asyncio.ensure_future(self._writeBookAsync(output))

    def _setupSignals(self):
        self._inputAddButton.clicked.connect(self._selectInputFiles)
        self._inputRemoveButton.clicked.connect(self._removeSelectedFiles)
        self._outputButton.clicked.connect(self._selectOutputFile)
        self._generateButton.clicked.connect(self._generateEpub)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setApplicationName("txt2epub")
    win = MainWindow()
    win.show()
    sys.exit(QtAsyncio.run(handle_sigint=True))
