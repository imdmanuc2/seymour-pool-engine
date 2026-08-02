import itertools
import secrets
import threading


class ExtranonceAllocator:
    """Allocate unique four-byte Stratum extranonce1 values.

    Bitcoin job construction reserves exactly four bytes for extranonce1.
    Begin the counter at a random 32-bit value so process restarts do not
    predictably reuse the same sequence.
    """

    def __init__(self) -> None:
        self._counter = itertools.count(secrets.randbits(32))
        self._lock = threading.Lock()

    def allocate(self) -> str:
        with self._lock:
            value = next(self._counter) & 0xFFFFFFFF

        return value.to_bytes(4, "big").hex()
