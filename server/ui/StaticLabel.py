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
        self._prefixText = prefixText
        self.setText(text or "")

    def setText(self, text: str) -> None:
        """Update label text.

        Args:
            text (str): The new text to set the label to

        Returns:
            None
        """

        return super().setText(self._prefixText + text)

    def setNum(self, num: int) -> None:
        self.setText(str(num))

    def setFloat(self, num: float, dec: int = 2) -> None:
        self.setText(str(round(num, dec)))


if __name__ == "__main__":
    print("There is no point running this file directly")
