import itertools
import secrets
import threading


class ExtranonceAllocator:
    def __init__(self) -> None:
        self._prefix = secrets.token_bytes(2)
        self._counter = itertools.count()
        self._lock = threading.Lock()

    def allocate(self) -> str:
        with self._lock:
            value = next(self._counter) & 0xFFFFFFFF
        return (self._prefix + value.to_bytes(4, "big")).hex()
