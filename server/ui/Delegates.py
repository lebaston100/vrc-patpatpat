"""
This module provides multiple custom item delegates.

The `FloatSpinBoxDelegate` class is a custom item delegate that uses a
QDoubleSpinBox to handle float values. This class can be used as a
delegate for a QTableView or similar widget to allow for editing of
float values within the view.

The `IntSpinBoxDelegate` does the same as `FloatSpinBoxDelegate` just
for ints.

Additional classes may be added to this module in the future to handle
other data types.

Example:
    Here is an example of how to use `FloatSpinBoxDelegate`:

    ```python
    from PyQt6.QtWidgets import QTableView
    from your_module import FloatSpinBoxDelegate

    # Assuming you have a QAbstractTableModel `model`
    view = QTableView()
    view.setModel(model)

    delegate = FloatSpinBoxDelegate(view)
    view.setItemDelegate(delegate)
    ```

Note:
    The range of the QDoubleSpinBox is currently set to
    [-20.0000, 20.0000]. This can be adjusted as needed.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtCore import pyqtSignal as QSignal
from PyQt6.QtWidgets import (QDoubleSpinBox, QHBoxLayout, QItemDelegate,
                             QLineEdit, QPushButton, QSpinBox, QWidget)


class FloatSpinBoxDelegate(QItemDelegate):
    """Custom Item Delegate using a QSpinBox for float values."""

    def __init__(self, decimals: int = 4, min: float = -20.0000,
                 max: float = 20.000, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._decimals = decimals
        self._min = min
        self._max = max

    def createEditor(self, parent, option, index):
        """Create a QSpinBox as the editor for float values."""
        editor = QDoubleSpinBox(parent)
        editor.setFrame(False)
        editor.setDecimals(self._decimals)
        editor.setMinimum(self._min)
        editor.setMaximum(self._max)
        editor.setStepType(QDoubleSpinBox.StepType.AdaptiveDecimalStepType)
        return editor

    def setEditorData(self, spinBox: QDoubleSpinBox, index) -> None:
        """Set the data for the editor."""
        value = index.model().data(index, Qt.ItemDataRole.EditRole)
        spinBox.setValue(value)

    def setModelData(self, spinBox: QDoubleSpinBox, model, index) -> None:
        """Write value from editor into models data"""
        spinBox.interpretText()
        value = spinBox.value()
        model.setData(index, value, Qt.ItemDataRole.EditRole)


class IntSpinBoxDelegate(QItemDelegate):
    """Custom Item Delegate using a QSpinBox for int values."""

    def __init__(self, min: int = 0, max: int = 1, step: int = 1,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._step = step
        self._min = min
        self._max = max

    def createEditor(self, parent, option, index):
        """Create a QSpinBox as the editor for float values."""
        editor = QSpinBox(parent)
        editor.setFrame(False)
        editor.setSingleStep(self._step)
        editor.setMinimum(self._min)
        editor.setMaximum(self._max)
        editor.setStepType(QDoubleSpinBox.StepType.AdaptiveDecimalStepType)
        return editor

    def setEditorData(self, spinBox: QSpinBox, index) -> None:
        """Set the data for the editor."""
        value = index.model().data(index, Qt.ItemDataRole.EditRole)
        spinBox.setValue(value)

    def setModelData(self, spinBox: QSpinBox, model, index) -> None:
        """Write value from editor into models data."""
        spinBox.interpretText()
        value = spinBox.value()
        model.setData(index, value, Qt.ItemDataRole.EditRole)


class LineEditMoreButtonEditWidget(QWidget):
    buttonClicked = QSignal(int)

    def __init__(self, rowId, parent=None):
        super().__init__(parent)
        self.rowId = rowId

        self.selfLayout = QHBoxLayout(self)
        self.selfLayout.setContentsMargins(0, 0, 0, 0)
        self.lineEdit = QLineEdit(self)
        self.button = QPushButton("...", self)
        self.button.setMaximumWidth(28)

        self.selfLayout.addWidget(self.lineEdit)
        self.selfLayout.addWidget(self.button)

        self.button.clicked.connect(self.emitSignal)

    def emitSignal(self):
        self.buttonClicked.emit(self.rowId)


class LineEditMoreButtonDelegate(QItemDelegate):
    """Custom Item Delegate using a QLineEdit and QPushButton."""
    buttonClicked = QSignal(int)

    def createEditor(self, parent, option, index):
        """Create a custom widget as the editor."""
        editor = LineEditMoreButtonEditWidget(index.row(), parent)
        editor.buttonClicked.connect(self.buttonClicked)
        return editor

    def setEditorData(self, widget: LineEditMoreButtonEditWidget, index) -> None:
        """Set the data for the editor."""
        value = index.model().data(index, Qt.ItemDataRole.EditRole)
        widget.lineEdit.setText(value)
        widget.lineEdit.selectAll()

    def setModelData(self, widget: LineEditMoreButtonEditWidget, model, index) -> None:
        """Write value from editor into models data."""
        value = widget.lineEdit.text()
        model.setData(index, value, Qt.ItemDataRole.EditRole)
