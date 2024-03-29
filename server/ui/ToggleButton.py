"""A simple toggable QPushButton expansion with state-drive text changes.

Typical usage example:

    myButton = ToggleButton(("Unchecked", "Checked"))
    myButton = ToggleButton(("Unchecked", "Checked"), "Prefix")
"""

from PyQt6.QtCore import pyqtSignal as Signal
from PyQt6.QtWidgets import QPushButton

from utils.Logger import LoggerClass

logger = LoggerClass.getSubLogger(__name__)


class ToggleButton(QPushButton):
    """A simple expansion of the QPushButton that is toggable and
    changes it's text depending on the toggle state.

    Signals:
        toggledOn: Emitted when the button state changed to on
        toggleOff: Emitted when the button state changed to off
    """

    toggledOn = Signal()
    toggledOff = Signal()

    def __init__(self, stateText: tuple, prefixText: str | None = None,
                 *args, **kwargs) -> None:
        """Initialize the toggle button.

        Args:
            stateText (tuple): A tuple with 2 strings for the two states
                (a, b) where a is unchecked and b is checked
            prefixText ([str | None], optional): A static prefix. 
                Defaults to None.
        """
        super().__init__(*args, **kwargs)
        self._stateText = stateText
        self._togglesStates = (self.toggledOff, self.toggledOn)
        self._prefixText = prefixText + " " if prefixText else ""
        self.setCheckable(True)
        self.toggled.connect(self.setStateText)
        self.setStateText(self.isChecked())

    def setStateText(self, state: bool) -> None:
        """Set own text based on state received by signal.

        Args:
            state (bool): The new state that the button is in.

        Returns:
            None
        """
        self.setText(self._prefixText + self._stateText[state])
        self._togglesStates[state].emit()


if __name__ == "__main__":
    print("There is no point running this file directly")
