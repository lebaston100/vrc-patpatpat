"""Only very basic tests for now"""

import pytest


class TestLoggerClass:
    def test_LoggerClass_init(self):
        """Test that the module imports and can be created"""
        try:
            from utils import LoggerClass
            logger = LoggerClass()
        except Exception:
            assert False

    def test_gettingRootLogger(self):
        """Tests that we get a valid Logger object"""
        import logging

        from utils import LoggerClass
        assert isinstance(LoggerClass.getRootLogger(), logging.Logger)

    def test_gettingSubLogger(self):
        """Tests that we get a valid Logger object"""
        import logging

        from utils import LoggerClass
        assert isinstance(LoggerClass.getSubLogger("test"), logging.Logger)

    def test_gettingLoggingLevelStrings(self):
        """Test that we get a proper list with the right values"""
        from utils import LoggerClass
        assert list(LoggerClass.getLoggingLevelStrings()) == [
            'CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG']


class TestLogWindowSignaler:
    def test_LogWindowSignaler(self):
        """Test if the Signal properly emits the string"""
        from utils.Logger import LogWindowSignaler

        def slot(s):
            assert s == "test"

        signaller = LogWindowSignaler()
        signaller.newLogEntry.connect(slot)
        signaller.newLogEntry.emit("test")


class TestSignalLogHandler:
    def test_signal_log_handler(self):
        import logging
        from datetime import datetime
        from logging import LogRecord

        from utils.Logger import SignalLogHandler

        # Create a logger
        logger = logging.getLogger('test_logger')

        # Create a SignalLogHandler and add it to the logger
        handler = SignalLogHandler()
        logger.addHandler(handler)

        # Test that the handler can be attached to a logger and properly emits the newLogEntry signal
        def slot(log_entry):
            now = datetime.now()
            current_time = now.strftime("%Y-%m-%d %H:%M:%S")
            current_ms = now.strftime("%f")[:3].zfill(3)
            assert log_entry == (f"[{current_time}] [DEBUG   ] "
                                 "test_logger: test message")
        handler.signal.newLogEntry.connect(slot)

        # Log a message
        logger.debug("test message")

        # Test that the format of the emitted string matches the specified formatter
        record = LogRecord('test_logger', logging.DEBUG, '', 0,
                           'test message', args=(), exc_info=None)
        now = datetime.now()
        current_time = now.strftime("%Y-%m-%d %H:%M:%S")
        current_ms = now.strftime("%f")[:3].zfill(3)
        assert handler.format(record) == (f"[{current_time}.{current_ms}] [DEBUG   ] "
                                          "test_logger: test message")

        # Test that the level can be changed with the changeLevel function and that change is properly reflected in the object's state
        handler.changeLevel('INFO')
        assert handler.level == logging.INFO
