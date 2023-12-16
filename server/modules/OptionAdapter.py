from typing import Any, cast

from PyQt6.QtWidgets import QComboBox, QLineEdit, QSpinBox, QRadioButton

from utils import LoggerClass, PathReader

logger = LoggerClass.getSubLogger(__name__)

# TODO:
# add more error handling

# TODO: Some day once i understand typing figure this all out
# type allowedWidgetTypes = QLineEdit | QSpinBox | QComboBox
# type validDataTypes = Type[str] | Type[int] | Type[float] | Type[bool] | Type[list[Any]
#   ] | Type[dict[Any, Any]]
type validValueTypes = type[str] | type[int] | type[float] \
    | type[bool] | type[list] | type[dict]


class OptionAdapter():
    """
    A class to manage UI elements and their options.

    This class provides methods to add UI elements, set and get their 
    options, and load options from a dictionary to the UI elements.

    Example:
        class MyWidget(QMainWindow, OptionAdapter):
            def __init__(self):
                super().__init__()
                self.addOpt('path1', QLineEdit(), str)
                self.addOpt('path2', QSpinBox(), int)
                self.loadOptsToGui({'path1': 'text', 'path2': 1})
    """

    def __init__(self) -> None:
        self._uiElems = {}

    def addOpt(self, path: str, uiObject,
               dataType: validValueTypes = str) -> None:
        """Adds an UI element and it's settings path to the list of
        UI elements

        Args:
            path (str): The path (name) of the option.
            uiObject (_type_): The UI object
                (probably some QWidget subclass).
            dataType (validValueTypes, optional): The data type to cast
                the option to. Defaults to str.
        """

        self._uiElems.update({path: (uiObject, dataType)})

    def setUiOpt(self, element, value) -> None:
        """
        Sets the value of a UI element based on its type.

        This function sets the value of a UI element based on its type. 
        If the element type is not supported, it logs an error message.

        Args:
            element (Union[QLineEdit, QSpinBox, QComboBox]): The UI
                element whose value is to be set.
            value (Any): The value to be set for the UI element.

        Returns:
            None
        """

        method = None
        match type(element).__name__:
            case "QLineEdit":
                method = cast(QLineEdit, element).setText
            case "QSpinBox":
                method = cast(QSpinBox, element).setValue
            case "QComboBox":
                method = cast(QComboBox, element).setCurrentText
            case "QRadioButton":
                method = cast(QRadioButton, element).setChecked
            case _:
                logger.error(
                    "tried to set a value for an unknown ui element type")
                return
        if method:
            method(value)

    def getUiOpt(self, element,
                 dataType=str) -> Any:
        """
        Retrieves the value of a UI element based on its type.

        This function retrieves the value of a UI element based on
        its type.
        If the element type is not supported, it logs a warning message.

        Args:
            element (Union[QLineEdit, QSpinBox, QComboBox,
                QRadioButton]): The UI
                    element whose value is to be retrieved.
            dataType (Type, optional): The expected return type of
                the value. Defaults to str.

        Returns:
            Any: The value of the UI element, cast to the 
                specified dataType.
        """

        method = None
        match type(element).__name__:
            case "QLineEdit":
                method = cast(QLineEdit, element).text
            case "QSpinBox":
                method = cast(QSpinBox, element).value
            case "QComboBox":
                method = cast(QComboBox, element).currentText
            case "QRadioButton":
                method = cast(QRadioButton, element).isChecked
            case _:
                logger.warn(
                    "tried to get a value for an unknown ui element type")
        if method:
            return dataType(method())

    def loadOptsToGui(self, options: dict) -> None:
        """
        Loads options from a dictionary to UI elements.

        This function iterates over a dictionary of options and sets the 
        corresponding UI elements to the values from the dictionary.

        Args:
            options (dict): A dictionary containing options to be loaded 
                to the UI.

        Returns:
            None
        """

        for path, (uiElem, dataType) in self._uiElems.items():
            newValue = dataType(PathReader.getOption(options, path))
            self.setUiOpt(uiElem, newValue)

    def getOptsFromGui(self, options: dict) -> tuple[dict, list]:
        """
        Retrieves values from UI elements and updates the options dict.

        This function iterates over all UI elements, retrieves their
        values, and updates the provided options dictionary. It also
        keeps track of the keys (or paths) that have changed.

        Args:
            options (dict): The options dictionary to be updated.

        Returns:
            tuple: A tuple containing the updated options dictionary and
            a list of keys that have changed.
        """

        changedKeys = []
        for path, (uiElem, dataType) in self._uiElems.items():
            oldValue = dataType(PathReader.getOption(options, path))
            newValue = self.getUiOpt(uiElem, dataType)
            if newValue != oldValue:
                changedKeys.append(path)
            options = PathReader.setOption(options, path, newValue)
        return options, changedKeys


if __name__ == "__main__":
    print("There is no point running this file directly")
