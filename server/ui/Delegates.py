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
from PyQt6.QtWidgets import QDoubleSpinBox, QItemDelegate, QSpinBox


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
        """Write value from editor into models data"""

        spinBox.interpretText()
        value = spinBox.value()
        model.setData(index, value, Qt.ItemDataRole.EditRole)
