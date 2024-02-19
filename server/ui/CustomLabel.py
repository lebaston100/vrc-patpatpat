"""A simple QLabel expansion with a static text prefix.

Typical usage example:

    myLabel = StaticLabel("Name: ") -> "Name: "
    myLabel = StaticLabel("Name: ", "Initial Text") -> "Name: Initial Text"
    myLabel.setText("patpatpat") -> "Name: patpatpat"
"""

from PyQt6.QtWidgets import QLabel

from utils import LoggerClass
logger = LoggerClass.getSubLogger(__name__)


class StaticLabel(QLabel):
    """A simple expansion of QLabel with a static prefix text."""

    def __init__(self, prefixText: str, text: str | None = None, *args, **kwargs) -> None:
        """Initialize the label.

        Args:
            prefixText (str): The static prefix text
        """
        super().__init__(*args, **kwargs)
        self.__prefixText = prefixText
        self.setText(text or "")

    def setText(self, text: str) -> None:
        """Update label text.

        Args:
            text (str): The new text to set the label to

        Returns:
            None
        """
        return super().setText(self.__prefixText + text)

    def setNum(self, num: int) -> None:
        self.setText(str(num))

    def setFloat(self, num: float, dec: int = 2) -> None:
        self.setText(str(round(num, dec)))


class StatefulLabel(QLabel):
    """A label with text based on states"""

    def __init__(self, stateTexts: tuple, *args, **kwargs) -> None:
        """Initialize the label.

        Args:
            stateTexts (tuple): The different state texts
        """
        super().__init__(*args, **kwargs)
        self.__states = stateTexts

    def setState(self, state: int | bool) -> None:
        """Update label text to new state.

        Args:
            state (int | bool): The new state.

        Returns:
            None
        """
        return super().setText(self.__states[state])


if __name__ == "__main__":
    print("There is no point running this file directly")
