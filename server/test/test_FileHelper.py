import pytest


class TestFileHelper:
    def test_FileHelper_init(self):
        """Test that the module imports and can be created"""
        from pathlib import Path
        try:
            from patpatpat.jsonFile import FileHelper
            h = FileHelper(Path("test.conf"))
        except Exception:
            assert False

    @pytest.fixture(scope="class")
    def createFileHelper(self):
        """Return a class-persistant FileHper to test on"""
        from pathlib import Path
        from patpatpat.jsonFile import FileHelper
        path = Path("test/test.conf")
        yield FileHelper(path)
        path.unlink()

    def test_FileHelper_Write(self, createFileHelper):
        """Test if we can write to the file"""
        assert createFileHelper.write({"testkey": "testvalue"})

    def test_FileHelper_Read(self, createFileHelper):
        """Test if we can read from the file and get the expected values"""
        assert createFileHelper.read() == {"testkey": "testvalue"}
