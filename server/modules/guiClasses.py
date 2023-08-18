from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QFrame
from PyQt6.QtCore import Qt

# a normal gui row with text left and some element on the right
class CGui2Row(QFrame):
    def __init__(self, title: str, content: QWidget, height: int=85, 
                 AlignRight: bool=True, DefaultColor: bool=True) -> None:
        super().__init__()
        self.setObjectName("section")
        self.setFixedHeight(height)

        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setContentsMargins(20, 20, 20, 20)

        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(title_label)

        if AlignRight:
            content.setAlignment(Qt.AlignmentFlag.AlignRight)
        if DefaultColor:
            content.setStyleSheet("color: #b94029; font-size: 30px;")
        layout.addWidget(content)
        self.setLayout(layout)