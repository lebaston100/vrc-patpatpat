from typing import Any, cast

from PyQt6.QtWidgets import (QCheckBox, QComboBox, QLineEdit, QRadioButton,
                             QSlider, QSpinBox)

from utils import LoggerClass

logger = LoggerClass.getSubLogger(__name__)

# TODO: Some day once i understand typing figure this all out
# type allowedWidgetTypes = QLineEdit | QSpinBox | QComboBox
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
                self.addOpt('path1', QLineEdit())
                self.addOpt('path2', QSpinBox(), int)
                self.loadOptsToGui({'path1': 'text', 'path2': 1})
    """

    def __init__(self, *args, **kwargs) -> None:
        self._uiElems = {}

    def addOpt(self, path: str, uiObject: object,
               dataType: validValueTypes = str) -> None:
        """Adds an UI element and it's settings path to the list of
        UI elements

        Args:
            path (str): The path (name) of the option.
            uiObject (object): The UI object
                (probably some QWidget subclass).
            dataType (validValueTypes, optional): The data type to cast
                the option to. Defaults to str.
        """
        self._uiElems.update({path: (uiObject, dataType)})

    def _setUiOpt(self, element: object, value: Any) -> None:
        """Sets the value of a UI element based on its type.

        This function sets the value of a UI element based on its type. 
        If the element type is not supported, it logs an error message.

        Args:
            element (object): The UI element whose value is to be set.
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
            case "QCheckBox":
                method = cast(QCheckBox, element).setChecked
            case "QSlider":
                method = cast(QSlider, element).setValue
            case _:
                logger.error(
                    "tried to set value for an unknown ui element type")
                return
        if method:
            method(value)

    def _getUiOpt(self, element: object, dataType=str) -> Any:
        """Retrieves the value of a UI element based on its type.

        This function retrieves the value of a UI element based on
        its type.
        If the element type is not supported, it logs a warning message.

        Args:
            element (object): The UI element whose values
                to be retrieved.
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
            case "QCheckBox":
                method = cast(QCheckBox, element).isChecked
            case "QSlider":
                method = cast(QSlider, element).value
            case _:
                logger.warn(
                    "tried to get value from an unknown ui element type")
        if method:
            return dataType(method())

    def loadOptsToGui(self, config, configKey: str) -> None:
        """Loads options from a dictionary to UI elements.

        This function iterates over a dictionary of options and sets the 
        corresponding UI elements to the values from the dictionary.

        Args:
            config (GlobalConfigSingleton): The GlobalConfigSingleton
                instance to update.
            configKey (str): The base config key path.

        Returns:
            None
        """
        for path, (uiElem, dataType) in self._uiElems.items():
            try:
                newValue = dataType(config.get(f"{configKey}.{path}"))
                # logger.debug(f"{configKey}.{path}: {str(newValue)}")
            except TypeError:
                logger.error(f"Failed to read {configKey}.{path} from config")
            else:
                self._setUiOpt(uiElem, newValue)

    def saveOptsFromGui(self, config, configKey: str,
                        diff: bool = False) -> list[str | None]:
        """Retrieves values from UI elements and updates the options dict.

        This function iterates over all UI elements, retrieves their
        values, and updates the provided options dictionary. It also
        keeps track of the keys (or paths) that have changed.

        Args:
            config (GlobalConfigSingleton): The GlobalConfigSingleton
                instance to update.
            configKey (str): The base config key path.
            diff (bool): Only return the difference without saving.

        Returns:
            list[str | None]: A tuple containing the updated options dictionary and
            a list of keys that have changed.
        """
        changedKeys = []
        for path, (uiElem, dataType) in self._uiElems.items():
            path = f"{configKey}.{path}"
            newValue = self._getUiOpt(uiElem, dataType)
            keyChanged = newValue != dataType(config.get(path))
            if keyChanged:
                changedKeys.append(path)
            if not diff:
                config.set(path, newValue, keyChanged)
        if changedKeys:
            # This can only be ran from here
            config.configRootUpdateDone.emit(configKey)
        return changedKeys


if __name__ == "__main__":
    print("There is no point running this file directly")
