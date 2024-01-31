from PyQt6.QtCore import QThread


def threadAsStr(thread: QThread | None) -> str:
    if thread:
        return str(int(thread.currentThreadId()))  # type:ignore
    return "Unknown"
