import pytest

from utils.PathReader import PathReader


class TestPathReader:
    @pytest.fixture
    def data(self):
        return {
            "key1": "value1",
            "key2": [
                1,
                {
                    "subsubkey": "value"
                }
            ]
        }

    def test_getOption(self, data):
        assert PathReader.getOption(data, "key1") == "value1"
        assert PathReader.getOption(data, "key2.1.subsubkey") == "value"
        with pytest.raises(KeyError):
            PathReader.getOption(data, "nonexistent")

    def test_setOption(self, data):
        new_data = PathReader.setOption(data, "key2.1.subsubkey", "new Value")
        assert new_data["key2"][1]["subsubkey"] == "new Value"
        with pytest.raises(Exception):
            PathReader.setOption(data, "nonexistent.key", "value")
