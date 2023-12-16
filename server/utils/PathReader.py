"""Provides helper methods to get and set dict values by using
a kinda-js-style dot notation path.

Usage example:

    data = {
        "key1": "value1",
        "key2": [
            1,
            {
                "subsubkey": "value"
            }
        ]
    }

    PathReader.getOption(data, "key2.1.subsubkey") -> "value"

    newdict = PathReader.setOption(data, "key2.1.subsubkey", "new Value")
    -> newdict = {
        "key1": "value1",
        "key2": [
            1,
            {
                "subsubkey": "new Value"
            }
        ]
    }

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
            path (str): The path to the option written in js dot notation.

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
    def setOption(inputDict: dict, path: str, newValue: validValueTypes) -> dict:
        """Updates an option inside a (nested) dict.

        Args:
            inputDict (dict): The dict to modify.
            path (str): The path to the option written in js dot notation.
            nv (validValueTypes): The new value.

        Raises:
            KeyError: When specified option is not found.

        Returns:
            dict: A new copy of the input dict but with the updated value.
        """

        try:
            # create copy of settings to work on
            workingDict = deepcopy(inputDict)
            # convert str to ints for list indices
            keys = map(lambda k: int(k) if k.isdigit() else k, path.split("."))
            # run recursive function over dict
            _recurse(workingDict, list(keys), newValue)
        except:
            raise Exception
        else:
            return workingDict


def _recurse(d: dict, p: list, newValue: validValueTypes) -> None:
    """Recursive function to navigate through the dictionary.

    Args:
        d (dict): The dict to go though
        p (list): The path to traverse
        newValue (validValueTypes): The new value to set the option to
    """

    key = p.pop(0)
    if p:
        _recurse(d[key], p, newValue)
    else:
        d[key] = newValue


if __name__ == "__main__":
    print("There is no point running this file directly")
