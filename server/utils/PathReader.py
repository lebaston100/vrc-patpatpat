"""
This module provides the PathReader class for reading and modifying
nested dictionaries.

The PathReader class provides static methods to get, set, and delete
options in a nested dictionary. The path to the option is specified in
dot notation.

Example:
    # Create a nested dictionary
    config = {
        "option1": "value1",
        "nested": {
            "option2": "value2"
        }
    }

    # Use PathReader to get an option
    print(PathReader.getOption(config, "nested.option2")) 
        # Output: "value2"

    # Use PathReader to set an option
    new_config = PathReader.setOption(config, "nested.option2",
        "new_value")
    print(PathReader.getOption(new_config, "nested.option2"))
        # Output: "new_value"

    # Use PathReader to delete an option
    PathReader.delOption(new_config, "nested.option2")
    print(PathReader.getOption(new_config, "nested.option2", "default"))
        # Output: "default"

"""

from copy import deepcopy
from functools import reduce

from utils import LoggerClass

logger = LoggerClass.getSubLogger(__name__)

type validValueTypes = str | int | float | bool | list | dict


class PathReader:
    @staticmethod
    def getOption(inputDict: dict, path: str) -> validValueTypes:
        """Returns a value of the dict specified by the path.

        Args:
            inputDict (dict): The dict to get the value from.
            path (str): The path to the option written in dot notation.

        Raises:
            KeyError: When specified option is not found.

        Returns:
            validValueTypes: The options's value.
        """

        try:
            # convert str to ints for list indices
            keys = list(map(lambda a: int(a) if a.isdigit()
                        else a, path.split(".")))
            reduced = reduce(lambda a, b: a[b], keys, inputDict)
        except:
            raise KeyError
        else:
            return reduced

    @staticmethod
    def setOption(inputDict: dict, path: str, newValue: validValueTypes,
                  inPlace: bool = False) -> dict:
        """Updates an option inside a (nested) dict.

        Args:
            inputDict (dict): The dict to modify.
            path (str): The path to the option written in dot notation.
            nv (validValueTypes): The new value.
            inPlace (bool): If the dict should be modified in-place.
                Defaults to False.

        Raises:
            KeyError: When specified option is not found.

        Returns:
            dict: A new copy of the input dict but with the updated
                value.
        """

        try:
            # create copy of settings to work on
            workingDict = inputDict if inPlace else deepcopy(inputDict)
            # convert str to ints for list indices
            keys = map(lambda k: int(k) if k.isdigit() else k, path.split("."))
            # run recursive function over dict
            _recurse(workingDict, list(keys), newValue)
        except:
            raise Exception
        else:
            return workingDict

    @staticmethod
    def delOption(inputDict: dict, path: str) -> None:
        """Deletes something from inside a (nested) dict.

        Args:
            inputDict (dict): The dict to modify.
            path (str): The path to the option to delete written in
                dot notation.

        Returns:
            None
        """

        try:
            # convert str to ints for list indices
            keys = map(lambda k: int(k) if k.isdigit() else k, path.split("."))
            # run recursive function over dict
            _recurseDelete(inputDict, list(keys))
        except:
            pass
        return


def _recurse(d: dict, p: list, newValue: validValueTypes) -> None:
    """Recursive function to navigate through the dictionary.

    Args:
        d (dict): The dict to go though.
        p (list): The path to traverse.
        newValue (validValueTypes): The new value to set the option to.
    """

    key = p.pop(0)
    if p:
        _recurse(d[key], p, newValue)
    else:
        if type(d) == list and len(d) <= key:
            d.append(newValue)
        else:
            d[key] = newValue


def _recurseDelete(d: dict, p: list) -> None:
    """Recursive function to delete a key from a dict.

    Args:
        d (dict): The dict to go though.
        p (list): The path to traverse.
    """

    key = p.pop(0)
    if p:
        _recurseDelete(d[key], p)
    else:
        del d[key]


if __name__ == "__main__":
    print("There is no point running this file directly")
