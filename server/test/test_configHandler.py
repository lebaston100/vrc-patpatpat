import pytest


class TestConfigHandler:
    def test_ConfigHandler_init(self):
        """Test that the module imports and can be created"""
        from pathlib import Path
        testPath = Path("test/test.conf")
        try:
            from patpatpat.configHandler import ConfigHandler
            c = ConfigHandler("test/test.conf")
        except Exception:
            assert False

    @pytest.fixture()
    def createConfigHandler(self):
        """Return a ConfigHelper to test on"""
        from pathlib import Path
        from patpatpat.configHandler import ConfigHandler
        path = Path("test/test.conf")
        yield ConfigHandler("test/test.conf")
        path.unlink()

    def test_ConfigHandler_parse(self, createConfigHandler):
        """Test if parsing throws an error"""
        try:
            createConfigHandler.parse()
        except Exception:
            assert False

    def test_ConfigHandler_get(self, createConfigHandler):
        """Test if the stored value can be read"""
        createConfigHandler._configOptions = {"testkey": "testvalue"}
        assert createConfigHandler.get("testkey") == "testvalue"

    def test_ConfigHandler_has(self, createConfigHandler):
        """Test if stored value can be checked for existance"""
        createConfigHandler.set("testkey", "testvalue")
        assert createConfigHandler.has("testkey") == True

    def test_ConfigHandler_set(self, createConfigHandler):
        """Test if a value has be stored"""
        assert createConfigHandler.set("testkey", "testvalue") == True
