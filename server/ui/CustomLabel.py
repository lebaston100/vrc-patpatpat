"""A simple QLabel expansion with a static text prefix.

Typical usage example:

    myLabel = StaticLabel("Name: ") -> "Name: "
    myLabel = StaticLabel("Name: ", "Initial Text", "Suffix") -> "Name: Initial Text Suffix"
    myLabel.setText("patpatpat") -> "Name: patpatpat"
"""

from PyQt6.QtWidgets import QLabel

from utils.Logger import LoggerClass

logger = LoggerClass.getSubLogger(__name__)


class StaticLabel(QLabel):
    """A simple expansion of QLabel with a static prefix text."""

    def __init__(self, prefixText: str,
                 text: str = "",
                 suffixText: str = "",
                 *args, **kwargs) -> None:
        """Initialize the label.

        Args:
            prefixText (str): The static prefix text
        """
        super().__init__(*args, **kwargs)
        self.__prefixText = prefixText
        self.__suffixText = suffixText
        self.setText(text or "")

    def setText(self, text: str) -> None:
        """Update label text.

        Args:
            text (str): The new text to set the label to

        Returns:
            None
        """
        return super().setText(self.__prefixText + text + self.__suffixText)

    def setNum(self, num: int) -> None:
        self.setText(str(num))

    def setFloat(self, num: float, dec: int = 2) -> None:
        self.setText(str(round(num, dec)))


class StatefulLabel(QLabel):
    """A label with text based on states"""

    def __init__(self, stateTexts: tuple[str, ...], *args, **kwargs) -> None:
        """Initialize the label.

        Args:
            stateTexts (tuple): The different state texts
        """
        super().__init__(*args, **kwargs)
        self.__states = stateTexts

    def setState(self, state: int | bool = 0) -> None:
        """Update label text to new state.

        Args:
            state (int | bool): The new state. Defaults to 0.

        Returns:
            None
        """
        return super().setText(self.__states[state])


if __name__ == "__main__":
    print("There is no point running this file directly")
