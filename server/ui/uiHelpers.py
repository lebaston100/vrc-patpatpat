"""Some helper functions and classes for use in the UI.

Exposes:
    handleCloseEvent: A simple message box popup to reject a close event
        when a dialog has unsaved changes

"""

from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import QMessageBox, QWidget


def handleCloseEvent(parent: QWidget | None, event: QCloseEvent) -> bool:
    """Asks the user if they want to close the settings without saving.

    Args:
        parent (QWidget | None): The parent QWidget.
        event (QCloseEvent): The QCloseEvent to handle.

    Returns:
        bool: If event was accepted or not.
    """
    result = QMessageBox.question(parent, "Unsaved changes",
                                  "You have unsaved changes, do you "
                                  + "want to close anyways?",
                                  QMessageBox.StandardButton.Cancel |
                                  QMessageBox.StandardButton.Yes,
                                  QMessageBox.StandardButton.Cancel)
    if result == QMessageBox.StandardButton.Yes:
        event.accept()
        return True
    else:
        event.ignore()
        return False


if __name__ == "__main__":
    print("There is no point running this file directly")
